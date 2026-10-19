import pandas as pd
import pytest
from src.input_quality import transaction_quality_report, network_quality_report, build_scenario_transactions
from src.cashflow_engine import forecast_business, summarize_forecast


def transactions():
    return pd.DataFrame([
        {"business_id":"A","business_name":"Alpha","date":"2026-10-16","direction":"inflow","category":"sales","amount":1000,"counterparty_id":"BUYER","description":"invoice 1"},
        {"business_id":"A","business_name":"Alpha","date":"2026-10-17","direction":"outflow","category":"supplier","amount":700,"counterparty_id":"SUPPLIER","description":"bill 1"},
    ])


def test_quality_report_validates_and_counts_rows():
    report = transaction_quality_report(transactions())
    assert report["valid"] is True
    assert report["rows"] == 2
    assert report["duplicate_like_rows"] == 0


def test_duplicate_like_rows_are_flagged_not_removed():
    tx = pd.concat([transactions(), transactions().iloc[[0]]], ignore_index=True)
    report = transaction_quality_report(tx)
    assert report["duplicate_like_rows"] == 2
    assert any("Duplicate-like" in x for x in report["warnings"])


def test_network_quality_reports_self_edge():
    network = pd.DataFrame([{"from_business_id":"A","to_business_id":"A","amount":10,"expected_date":"2026-10-16","delay_days":0,"relationship_type":"test"}])
    assert network_quality_report(network)["self_edges"] == 1


def test_scenario_a_and_b_can_be_compared_independently():
    tx = transactions()
    base = summarize_forecast(forecast_business(tx, "A", 500, "2026-10-16", 10))
    inventory, _ = build_scenario_transactions(tx, "A", "Inventory purchase", 300, 2, "2026-10-16", 10)
    delayed, _ = build_scenario_transactions(tx, "A", "Customer payment delayed", 1000, 5, "2026-10-16", 10)
    inv = summarize_forecast(forecast_business(inventory, "A", 500, "2026-10-16", 10))
    delay = summarize_forecast(forecast_business(delayed, "A", 500, "2026-10-16", 10))
    assert inv["ending_cash"] == base["ending_cash"] - 300
    assert delay["ending_cash"] == base["ending_cash"]
    assert delay["minimum_cash"] <= base["minimum_cash"]


def test_scenario_amount_and_percentage_validation():
    with pytest.raises(ValueError):
        build_scenario_transactions(transactions(), "A", "Inventory purchase", -1, 0, "2026-10-16", 10)
    with pytest.raises(ValueError):
        build_scenario_transactions(transactions(), "A", "Price reduced", 0, 0, "2026-10-16", 10, 101)
