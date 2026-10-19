from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json
import pandas as pd
from src.data_loader import validate_network
from src.network_risk import propagate_payment_shock
from src.security_policy import authorize, AuthorizationError

OUT = ROOT / "evidence"
OUT.mkdir(exist_ok=True)
network = validate_network(pd.read_csv(ROOT / "data" / "sample_network.csv"))
prop = propagate_payment_shock(network, "BUYER_X", 10, liquidity_buffer=10000)
prop.to_csv(OUT / "network_propagation_demo.csv", index=False)

checks = []
for role, permission, expected in [
    ("viewer", "view", "allow"),
    ("viewer", "review", "block"),
    ("analyst", "simulate", "allow"),
    ("analyst", "review", "block"),
    ("owner", "review", "allow"),
]:
    try:
        authorize(role, permission)
        actual = "allow"
    except AuthorizationError:
        actual = "block"
    checks.append({"role": role, "permission": permission, "expected": expected,
                   "actual": actual, "pass": actual == expected})
pd.DataFrame(checks).to_csv(OUT / "authorization_checks.csv", index=False)
summary = {
    "dataset": "synthetic sample network",
    "network_edges_examined": int(len(prop)),
    "max_hop": int(prop["hop"].max()) if not prop.empty else 0,
    "authorization_checks_passed": sum(c["pass"] for c in checks),
    "authorization_checks_total": len(checks),
    "external_actions_executed": False,
    "note": "Reproducible demo evidence only; not real-world validation."
}
(OUT / "evidence_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
