import pandas as pd
import pytest
from src.independent_eval import evaluate_cash_forecast, recommendation_traceability

def test_actual_cash_evaluation_metrics():
    tx = pd.DataFrame([
        {'business_id':'A','business_name':'Alpha','date':'2026-01-01','direction':'inflow','category':'sales','amount':100,'counterparty_id':'C','description':'sale'},
        {'business_id':'A','business_name':'Alpha','date':'2026-01-02','direction':'outflow','category':'rent','amount':20,'counterparty_id':'S','description':'rent'}])
    actual = pd.DataFrame([{'date':'2026-01-01','actual_closing_cash':150},{'date':'2026-01-02','actual_closing_cash':180}])
    metrics, rows = evaluate_cash_forecast(tx,'A',50,'2026-01-01',actual)
    assert metrics['matched_days'] == 2
    assert metrics['mae_cash'] >= 0
    assert len(rows) == 2

def test_actual_cash_evaluation_rejects_bad_schema():
    tx = pd.DataFrame([{'business_id':'A','business_name':'Alpha','date':'2026-01-01','direction':'inflow','category':'sales','amount':100,'counterparty_id':'C','description':'sale'}])
    with pytest.raises(ValueError): evaluate_cash_forecast(tx,'A',50,'2026-01-01',pd.DataFrame({'date':['2026-01-01']}))

def test_traceability_matches_transaction_evidence():
    tx = pd.DataFrame([{'date':'2026-01-01','category':'sales','amount':100}])
    answer = {'evidence':tx.copy()}
    result = recommendation_traceability(answer,tx)
    assert result['pass'] and result['traceability_rate'] == 1.0
