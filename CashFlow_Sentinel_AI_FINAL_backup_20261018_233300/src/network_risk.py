from __future__ import annotations
import pandas as pd
from .data_loader import validate_network

def propagate_payment_shock(network: pd.DataFrame, payer_id: str, delay_days: int,
                             liquidity_buffer: float = 0.0, max_hops: int = 5) -> pd.DataFrame:
    """Deterministic graph stress test. Each delayed incoming payment may delay the
    receiver's outgoing network obligations by the same number of days when its
    assumed buffer is insufficient. This is a scenario rule, not a probability model.
    """
    if delay_days < 0 or delay_days > 180:
        raise ValueError("delay_days must be between 0 and 180.")
    if liquidity_buffer < 0:
        raise ValueError("liquidity_buffer must be non-negative.")
    if max_hops < 1 or max_hops > 20:
        raise ValueError("max_hops must be between 1 and 20.")
    net = validate_network(network)
    required = {"from_business_id","to_business_id","amount","expected_date","delay_days","relationship_type"}
    if not required.issubset(net.columns):
        raise ValueError("Network schema is invalid.")
    # An upstream payer delay affects its immediate receiver; if the affected payment
    # is larger than the available buffer, propagate to that receiver's downstream payees.
    queue = [(str(payer_id), int(delay_days), 0)]
    seen = set()
    results = []
    while queue:
        current_payer, current_delay, hop = queue.pop(0)
        if hop >= max_hops:
            continue
        outgoing = net[net["from_business_id"].astype(str) == current_payer]
        for _, edge in outgoing.iterrows():
            receiver = str(edge["to_business_id"])
            edge_key = (current_payer, receiver, hop)
            if edge_key in seen:
                continue
            seen.add(edge_key)
            amount = float(edge["amount"])
            # The liquidity buffer is a simplified user-supplied assumption applied per edge.
            propagates = current_delay > 0 and amount > liquidity_buffer
            results.append({
                "from_business_id": current_payer,
                "to_business_id": receiver,
                "payment_amount": amount,
                "shock_delay_days": current_delay,
                "hop": hop + 1,
                "assumed_liquidity_buffer": float(liquidity_buffer),
                "propagation_triggered": bool(propagates),
                "estimated_downstream_delay_days": current_delay if propagates else 0,
                "model_type": "deterministic_stress_test",
            })
            if propagates:
                queue.append((receiver, current_delay, hop + 1))
    return pd.DataFrame(results, columns=[
        "from_business_id","to_business_id","payment_amount","shock_delay_days","hop",
        "assumed_liquidity_buffer","propagation_triggered","estimated_downstream_delay_days","model_type"
    ])
