import pandas as pd
import pytest
from src.scenario_engine import apply_payment_delay
def tx(): return pd.DataFrame([{"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"inflow","category":"sale","amount":100,"counterparty_id":"B","description":"incoming"},{"business_id":"B","business_name":"Beta","date":"2026-10-15","direction":"outflow","category":"payment","amount":100,"counterparty_id":"A","description":"outgoing"}])
def net(): return pd.DataFrame([{"from_business_id":"B","to_business_id":"A","amount":100,"expected_date":"2026-10-15","delay_days":0,"relationship_type":"customer_payment"}])
def test_delay_moves_date():
 changed,_=apply_payment_delay(tx(),net(),"B","A",5); d=changed[(changed.business_id=="A")&(changed.direction=="inflow")].date.iloc[0]; assert d==pd.Timestamp("2026-10-20")
def test_unknown_edge_rejected():
 with pytest.raises(ValueError): apply_payment_delay(tx(),net(),"X","A",5)
