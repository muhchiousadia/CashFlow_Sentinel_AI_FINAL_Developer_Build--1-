"""Evaluation utilities for permissioned business data; does not claim validation without labels/outcomes."""
from __future__ import annotations
import pandas as pd
from .data_loader import validate_transactions

def evaluate_cash_forecast(transactions: pd.DataFrame, business_id: str, opening_cash: float, start_date, actual_daily_cash: pd.DataFrame):
    """Compare a model forecast with independent observed daily closing cash.
    actual_daily_cash columns: date, actual_closing_cash. Use only authorized, reconciled data.
    """
    tx = validate_transactions(transactions)
    actual = actual_daily_cash.copy()
    required = {'date','actual_closing_cash'}
    if not required.issubset(actual.columns): raise ValueError('Actual outcomes must contain date and actual_closing_cash columns.')
    actual['date'] = pd.to_datetime(actual['date'], errors='coerce').dt.normalize()
    actual['actual_closing_cash'] = pd.to_numeric(actual['actual_closing_cash'], errors='coerce')
    if actual['date'].isna().any() or actual['actual_closing_cash'].isna().any(): raise ValueError('Actual outcomes contain invalid dates or cash values.')
    actual = actual.groupby('date', as_index=False)['actual_closing_cash'].last()
    from .cashflow_engine import forecast_business
    forecast = forecast_business(tx, business_id, opening_cash, start_date, max(1, min(365, len(actual))))
    joined = forecast.merge(actual, left_on=forecast.date.dt.normalize(), right_on='date', how='inner', suffixes=('_forecast','_actual'))
    if joined.empty: raise ValueError('No overlapping forecast and actual dates; align dates and timezone first.')
    error = joined['closing_cash'] - joined['actual_closing_cash']
    metrics = {'matched_days': int(len(joined)), 'mae_cash': float(error.abs().mean()), 'rmse_cash': float((error.pow(2).mean()) ** 0.5),
               'bias_cash': float(error.mean()), 'source': 'user-provided actual outcomes; verify independent reconciliation'}
    joined['absolute_error'] = error.abs()
    return metrics, joined

def recommendation_traceability(answer: dict, source_transactions: pd.DataFrame) -> dict:
    """Basic independent check that any displayed evidence rows map to uploaded source rows."""
    evidence = answer.get('evidence')
    if evidence is None or not isinstance(evidence, pd.DataFrame) or evidence.empty:
        return {'evidence_rows': 0, 'matched_rows': 0, 'traceability_rate': 0.0, 'pass': False}
    source = source_transactions.copy()
    keys = {'date','amount','category'}
    if not keys.issubset(evidence.columns) or not keys.issubset(source.columns):
        return {'evidence_rows': int(len(evidence)), 'matched_rows': 0, 'traceability_rate': 0.0, 'pass': False}
    ev = evidence.copy(); src = source.copy()
    ev['date'] = pd.to_datetime(ev['date'], errors='coerce').dt.normalize(); src['date'] = pd.to_datetime(src['date'], errors='coerce').dt.normalize()
    ev['amount'] = pd.to_numeric(ev['amount'], errors='coerce'); src['amount'] = pd.to_numeric(src['amount'], errors='coerce')
    matched = ev.merge(src[['date','amount','category']].drop_duplicates(), on=['date','amount','category'], how='inner')
    rate = len(matched) / max(1, len(ev))
    return {'evidence_rows': int(len(ev)), 'matched_rows': int(len(matched)), 'traceability_rate': float(rate), 'pass': bool(rate >= 0.99)}
