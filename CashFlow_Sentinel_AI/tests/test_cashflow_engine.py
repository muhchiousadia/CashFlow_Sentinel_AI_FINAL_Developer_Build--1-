import pandas as pd
import pytest
from src.cashflow_engine import forecast_business,summarize_forecast
def tx(): return pd.DataFrame([{"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"inflow","category":"sale","amount":500,"counterparty_id":"B","description":"sale"},{"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"outflow","category":"bill","amount":300,"counterparty_id":"","description":"bill"},{"business_id":"A","business_name":"Alpha","date":"2026-10-16","direction":"outflow","category":"bill","amount":400,"counterparty_id":"","description":"bill"}])
def test_balance_calculation():
 r=forecast_business(tx(),"A",1000,"2026-10-15",2); assert r.closing_cash.tolist()==[1200.0,800.0]; assert summarize_forecast(r)["minimum_cash"]==800.0
def test_shortfall_day():
 s=summarize_forecast(forecast_business(tx(),"A",100,"2026-10-15",2)); assert s["shortfall_days"]==1; assert s["first_shortfall_date"]=="2026-10-16"
def test_bad_horizon():
 with pytest.raises(ValueError): forecast_business(tx(),"A",100,"2026-10-15",0)
