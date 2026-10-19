import pandas as pd
from src.copilot_features import explain_cashflow_question, risk_radar, financing_options, counterparty_vulnerability


def tx():
    return pd.DataFrame([
        {"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"inflow","category":"customer_payment","amount":1000,"counterparty_id":"BUYER","description":"Invoice"},
        {"business_id":"A","business_name":"Alpha","date":"2026-10-16","direction":"outflow","category":"supplier_bill","amount":700,"counterparty_id":"SUPPLIER","description":"Bill"},
    ])

def net():
    return pd.DataFrame([
        {"from_business_id":"BUYER","to_business_id":"A","amount":1000,"expected_date":"2026-10-15","delay_days":0,"relationship_type":"customer_payment"},
        {"from_business_id":"A","to_business_id":"SUPPLIER","amount":700,"expected_date":"2026-10-16","delay_days":0,"relationship_type":"supplier_payment"},
    ])

def fc():
    return pd.DataFrame([{"date":pd.Timestamp("2026-10-15"),"inflows":1000,"outflows":0,"net_flow":1000,"closing_cash":1000,"shortfall":False},{"date":pd.Timestamp("2026-10-16"),"inflows":0,"outflows":700,"net_flow":-700,"closing_cash":300,"shortfall":False}])

def test_copilot_returns_evidence():
    r=explain_cashflow_question("why is cash decreasing?",tx(),"A",fc())
    assert "inflows" in r["answer"]
    assert not r["evidence"].empty
    assert "Uncertainty" in r["uncertainty"] or "uploaded" in r["uncertainty"]

def test_risk_radar_has_risk_rows():
    r=risk_radar(tx(),net(),"A",fc())
    assert not r.empty
    assert {"Risk","Evidence","Recommended action"}.issubset(r.columns)

def test_financing_options_have_mock_costs():
    r=financing_options(10000)
    assert len(r)==3
    assert (r["Estimated 30-day cost"]>0).all()

def test_counterparty_matrix_top_three():
    r=counterparty_vulnerability(tx(),net(),"A")
    assert len(r)<=3
    assert "Criticality score" in r.columns

def test_financing_options_zero_gap_is_zero_cost():
    r = financing_options(0)
    assert len(r) == 3
    assert (r["Estimated 30-day cost"] == 0).all()


def test_financing_options_are_ranked_by_estimated_cost():
    r = financing_options(25000)
    costs = r["Estimated 30-day cost"].tolist()
    assert costs == sorted(costs)


def test_copilot_unknown_question_still_returns_evidence():
    r = explain_cashflow_question("give me a summary", tx(), "A", fc())
    assert "2 transactions" in r["answer"]
    assert len(r["evidence"]) == 2


def test_counterparty_matrix_empty_business_is_safe():
    r = counterparty_vulnerability(tx(), net(), "MISSING")
    assert r.empty
    assert "Counterparty" in r.columns
