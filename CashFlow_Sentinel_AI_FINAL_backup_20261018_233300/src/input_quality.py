"""Upload data quality checks and deterministic scenario construction."""
from __future__ import annotations
import pandas as pd
from .data_loader import validate_transactions, validate_network


def transaction_quality_report(df: pd.DataFrame) -> dict:
    """Validate schema and return non-destructive quality diagnostics.

    Duplicate rows are reported, not automatically removed: two identical rows may
    represent legitimate separate transactions. A stable transaction_id is strongly
    recommended for production reconciliation.
    """
    clean = validate_transactions(df)
    duplicate_mask = clean.duplicated(subset=[c for c in ["business_id", "date", "direction", "category", "amount", "counterparty_id", "description"] if c in clean.columns], keep=False)
    date_min = clean.date.min().date().isoformat() if not clean.empty else None
    date_max = clean.date.max().date().isoformat() if not clean.empty else None
    return {
        "valid": True,
        "rows": int(len(clean)),
        "businesses": int(clean.business_id.nunique()),
        "duplicate_like_rows": int(duplicate_mask.sum()),
        "missing_counterparty_rows": int(clean.counterparty_id.fillna("").astype(str).str.strip().eq("").sum()),
        "date_min": date_min,
        "date_max": date_max,
        "warnings": (["Duplicate-like rows detected; review before deleting any row."] if duplicate_mask.any() else []) + (["Some rows have no counterparty_id; dependency analysis may be incomplete."] if clean.counterparty_id.fillna("").astype(str).str.strip().eq("").any() else []),
    }


def network_quality_report(df: pd.DataFrame) -> dict:
    clean = validate_network(df)
    self_edges = clean.from_business_id.astype(str).eq(clean.to_business_id.astype(str))
    duplicate_edges = clean.duplicated(subset=["from_business_id", "to_business_id", "expected_date", "amount", "relationship_type"], keep=False)
    return {
        "valid": True,
        "edges": int(len(clean)),
        "self_edges": int(self_edges.sum()),
        "duplicate_like_edges": int(duplicate_edges.sum()),
        "warnings": (["Self-referential network edges detected; review these rows."] if self_edges.any() else []) + (["Duplicate-like network edges detected; verify whether they are separate obligations."] if duplicate_edges.any() else []),
    }


def build_scenario_transactions(transactions: pd.DataFrame, business_id: str, scenario_type: str,
                                amount: float, offset_days: int, start_date, horizon_days: int,
                                price_reduction_pct: float = 10.0) -> tuple[pd.DataFrame, str]:
    """Apply one explicit, auditable what-if assumption to a copy of transaction data."""
    tx = validate_transactions(transactions)
    amount = float(amount)
    offset_days = int(offset_days)
    if amount < 0: raise ValueError("Scenario amount cannot be negative.")
    if not 0 <= offset_days <= 180: raise ValueError("Scenario offset must be between 0 and 180 days.")
    if not 0 <= float(price_reduction_pct) <= 100: raise ValueError("Price reduction must be between 0 and 100 percent.")
    start = pd.Timestamp(start_date).normalize()
    end = start + pd.Timedelta(days=int(horizon_days) - 1)
    mask_business = tx.business_id.astype(str).eq(str(business_id))
    scenario = tx.copy()
    if scenario_type == "Baseline":
        return scenario, "No changes applied; this is the baseline."
    if scenario_type == "Customer payment delayed":
        mask = mask_business & tx.direction.eq("inflow") & tx.date.between(start, end)
        candidates = tx.loc[mask].sort_values(["amount", "date"], ascending=[False, True])
        if candidates.empty or amount == 0 or offset_days == 0:
            return scenario, "No change applied: no eligible inflow, zero amount, or zero-day delay."
        idx = candidates.index[0]
        original = float(scenario.loc[idx, "amount"])
        delayed = min(amount, original)
        row = scenario.loc[idx].copy()
        row["date"] = pd.Timestamp(row["date"]) + pd.Timedelta(days=offset_days)
        row["amount"] = delayed
        row["description"] = f"WHAT-IF delayed portion {delayed:,.2f}; original row retained only for remaining amount"
        remaining = original - delayed
        if remaining > 0:
            scenario.loc[idx, "amount"] = remaining
            scenario = pd.concat([scenario, pd.DataFrame([row])], ignore_index=True)
        else:
            scenario = scenario.drop(index=idx)
            scenario = pd.concat([scenario, pd.DataFrame([row])], ignore_index=True)
        return validate_transactions(scenario), f"Delayed {delayed:,.2f} from {candidates.iloc[0]['counterparty_id'] or 'unspecified counterparty'} by {offset_days} days; original expected total is preserved."
    scenario_date = start + pd.Timedelta(days=min(offset_days, max(0, int(horizon_days)-1)))
    business_rows = tx.loc[mask_business, "business_name"]
    name = str(business_rows.iloc[0]) if not business_rows.empty else str(business_id)
    if scenario_type == "Inventory purchase":
        if amount == 0: return scenario, "No inventory outflow added because amount is zero."
        row = {"business_id": str(business_id), "business_name": name, "date": scenario_date, "direction": "outflow", "category": "scenario_inventory", "amount": amount, "counterparty_id": "SCENARIO_SUPPLIER", "description": "WHAT-IF synthetic inventory purchase"}
        scenario = pd.concat([scenario, pd.DataFrame([row])], ignore_index=True)
        return validate_transactions(scenario), f"Added assumed inventory outflow {amount:,.2f} on {scenario_date.date()}."
    if scenario_type == "Price reduced":
        future = tx.loc[mask_business & tx.direction.eq("inflow") & tx.date.between(start, end)]
        affected = float(future.amount.sum()) * float(price_reduction_pct) / 100.0
        if affected:
            row = {"business_id": str(business_id), "business_name": name, "date": start, "direction": "outflow", "category": "scenario_price_reduction_assumption", "amount": affected, "counterparty_id": "SCENARIO", "description": f"WHAT-IF assumed {price_reduction_pct:g}% cash impact; not a demand/elasticity model"}
            scenario = pd.concat([scenario, pd.DataFrame([row])], ignore_index=True)
        return validate_transactions(scenario), f"Applied conservative cash-impact assumption {affected:,.2f} ({price_reduction_pct:g}% of forecast inflows). Not a pricing elasticity or profit model."
    raise ValueError(f"Unknown scenario type: {scenario_type}")
