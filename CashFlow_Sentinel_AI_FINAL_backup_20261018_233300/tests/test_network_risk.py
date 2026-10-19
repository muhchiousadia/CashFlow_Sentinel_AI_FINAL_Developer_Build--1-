import pandas as pd
import pytest
from src.network_risk import propagate_payment_shock

def network():
    return pd.DataFrame([
        {"from_business_id":"BUYER","to_business_id":"A","amount":80000,"expected_date":"2026-10-15","delay_days":0,"relationship_type":"customer_payment"},
        {"from_business_id":"A","to_business_id":"B","amount":45000,"expected_date":"2026-10-16","delay_days":0,"relationship_type":"supplier_payment"},
        {"from_business_id":"B","to_business_id":"C","amount":30000,"expected_date":"2026-10-17","delay_days":0,"relationship_type":"supplier_payment"},
    ])

def test_shock_propagates_across_edges_above_buffer():
    result = propagate_payment_shock(network(), "BUYER", 10, liquidity_buffer=10000)
    assert len(result) == 3
    assert result["propagation_triggered"].all()
    assert result["hop"].max() == 3

def test_buffer_can_stop_propagation():
    result = propagate_payment_shock(network(), "BUYER", 10, liquidity_buffer=100000)
    assert len(result) == 1
    assert not result.iloc[0]["propagation_triggered"]

def test_invalid_delay_rejected():
    with pytest.raises(ValueError):
        propagate_payment_shock(network(), "BUYER", -1)

def test_zero_delay_does_not_propagate():
    result = propagate_payment_shock(network(), "BUYER", 0, liquidity_buffer=0)
    assert len(result) == 1
    assert not result.iloc[0]["propagation_triggered"]
