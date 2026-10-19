from __future__ import annotations
import pandas as pd
from .cashflow_engine import summarize_forecast

def generate_agent_brief(transactions: pd.DataFrame, business_id: str, forecast: pd.DataFrame) -> dict:
    """Explainable rule-based decision-support agent; not an LLM or trained model."""
    summary = summarize_forecast(forecast)
    rows = transactions[transactions['business_id'].astype(str) == str(business_id)].copy()
    rows['date'] = pd.to_datetime(rows['date'], errors='coerce')
    forecast_dates = set(pd.to_datetime(forecast['date']).dt.normalize())
    future = rows[rows['date'].dt.normalize().isin(forecast_dates)]
    inflows = future[future['direction'] == 'inflow'].sort_values('date')
    outflows = future[future['direction'] == 'outflow'].sort_values('date')
    actions = []
    if summary['shortfall_days']:
        actions.append({'priority':'HIGH','recommendation':'Review obligations before projected cash shortfall',
          'reason':f"Forecast has {summary['shortfall_days']} negative closing-cash day(s); first on {summary['first_shortfall_date']}.",
          'evidence':'Daily forecast closing_cash values','uncertainty':'Depends on supplied transaction dates and amounts.',
          'approval':'Business-owner review required'})
    else:
        actions.append({'priority':'MONITOR','recommendation':'Monitor the minimum projected cash point',
          'reason':f"Minimum projected cash is {summary['minimum_cash']:,.0f}; this forecast has no negative closing balance.",
          'evidence':'Daily forecast closing_cash values','uncertainty':'Not a liquidity guarantee; unrecorded transactions or late payments can change the result.',
          'approval':'Verify assumptions before acting'})
    if not inflows.empty:
        row = inflows.iloc[0]
        actions.append({'priority':'CHECK','recommendation':'Confirm the next expected customer payment',
          'reason':f"An inflow of {float(row['amount']):,.0f} is listed for {pd.Timestamp(row['date']).date().isoformat()}.",
          'evidence':f"{row.get('category','inflow')} / {row.get('description','')}",
          'uncertainty':'An expected payment is not guaranteed cash until received.',
          'approval':'Owner or finance staff should verify'})
    if not outflows.empty:
        row = outflows.iloc[0]
        actions.append({'priority':'CHECK','recommendation':'Review the next scheduled outflow',
          'reason':f"An outflow of {float(row['amount']):,.0f} is listed for {pd.Timestamp(row['date']).date().isoformat()}.",
          'evidence':f"{row.get('category','outflow')} / {row.get('description','')}",
          'uncertainty':'Do not defer essential or contractual payments without agreement.',
          'approval':'Owner approval required for any change'})
    return {'summary':summary,'actions':actions,'agent_type':'Explainable rule-based decision-support agent',
            'model_note':'No LLM, trained ML model, or probability prediction is used in this prototype.'}
