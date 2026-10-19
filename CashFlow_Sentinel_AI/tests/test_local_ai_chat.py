import json
import urllib.error
from unittest.mock import patch
import pandas as pd
import pytest
from src.copilot_features import rule_based_chat, ask_local_ollama


def _sample():
    tx = pd.DataFrame([
        {"business_id": "B1", "date": "2026-10-01", "direction": "inflow", "category": "sales", "amount": 1000,
         "counterparty_id": "C1", "description": "invoice receipt"},
        {"business_id": "B1", "date": "2026-10-02", "direction": "outflow", "category": "rent", "amount": 400,
         "counterparty_id": "S1", "description": "rent"},
    ])
    fc = pd.DataFrame([
        {"date": "2026-10-01", "inflows": 1000, "outflows": 0, "net_flow": 1000, "closing_cash": 1000, "shortfall": False},
        {"date": "2026-10-02", "inflows": 0, "outflows": 400, "net_flow": -400, "closing_cash": 600, "shortfall": False},
    ])
    return tx, fc


def test_rule_based_chat_works_without_external_api():
    tx, fc = _sample()
    result = rule_based_chat("Why is cash decreasing?", tx, "B1", fc)
    assert result["mode"] == "Free Python rule-based chat"
    assert "inflows" in result["answer"]


def test_local_ollama_response_uses_local_api_and_returns_evidence():
    tx, fc = _sample()
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"message": {"content": "Recorded inflows exceed outflows in this sample."}}).encode()
    with patch("urllib.request.urlopen", return_value=FakeResponse()) as mocked:
        result = ask_local_ollama("Why is cash decreasing?", tx, "B1", fc)
    assert result["mode"] == "Ollama Local AI (local inference)"
    assert "inflows" in result["answer"]
    assert not result["evidence"].empty
    assert mocked.call_args.kwargs["timeout"] == 90


def test_local_ollama_reports_missing_model_separately_from_connection_error():
    tx, fc = _sample()
    error = urllib.error.HTTPError(
        "http://localhost:11434/api/chat", 404, "Not Found", {}, None
    )
    with patch.object(error, "read", return_value=b'{"error":"model \'qwen2.5:3b\' not found"}'):
        with patch("urllib.request.urlopen", side_effect=error):
            with pytest.raises(RuntimeError, match=r"Run `ollama list`.*ollama pull qwen2\.5:3b"):
                ask_local_ollama("Why is cash decreasing?", tx, "B1", fc)
