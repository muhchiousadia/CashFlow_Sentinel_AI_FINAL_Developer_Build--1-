import pandas as pd
from .data_loader import validate_transactions, validate_network

def apply_payment_delay(transactions, network, payer_business_id, receiver_business_id, delay_days):
    if not 0 <= int(delay_days) <= 180: raise ValueError("delay_days must be between 0 and 180")
    tx=validate_transactions(transactions); net=validate_network(network)
    edge=net[(net.from_business_id.astype(str)==str(payer_business_id)) & (net.to_business_id.astype(str)==str(receiver_business_id))]
    if edge.empty: raise ValueError("No matching payer-to-receiver relationship exists.")
    mask=(tx.business_id.astype(str)==str(receiver_business_id)) & (tx.direction=="inflow") & (tx.counterparty_id.astype(str)==str(payer_business_id))
    if not mask.any(): raise ValueError("No matching incoming transaction found; check counterparty_id.")
    tx.loc[mask,"date"]=tx.loc[mask,"date"]+pd.to_timedelta(int(delay_days),unit="D")
    return tx.sort_values(["business_id","date"]).reset_index(drop=True), net
