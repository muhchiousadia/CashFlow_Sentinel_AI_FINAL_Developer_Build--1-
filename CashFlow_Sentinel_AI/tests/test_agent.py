import pandas as pd
from src.agent import generate_agent_brief
from src.cashflow_engine import forecast_business

def test_agent_brief_has_evidence_and_control():
    tx = pd.DataFrame([
      {"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"inflow","category":"sale","amount":50,"counterparty_id":"B","description":"invoice"},
      {"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"outflow","category":"bill","amount":200,"counterparty_id":"","description":"supplier bill"},
    ])
    forecast = forecast_business(tx, "A", 100, "2026-10-15", 2)
    brief = generate_agent_brief(tx, "A", forecast)
    assert brief["actions"]
    assert all("evidence" in action and "approval" in action for action in brief["actions"])
    assert brief["summary"]["shortfall_days"] == 2
