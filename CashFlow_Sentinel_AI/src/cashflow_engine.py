import pandas as pd
from .data_loader import validate_transactions

def forecast_business(transactions, business_id, opening_cash, start_date=None, horizon_days=30):
    if not 1 <= int(horizon_days) <= 365: raise ValueError("horizon_days must be between 1 and 365")
    if float(opening_cash)<0: raise ValueError("opening_cash must be non-negative")
    tx=validate_transactions(transactions)
    start=tx.date.min().normalize() if start_date is None else pd.Timestamp(start_date).normalize()
    dates=pd.date_range(start, periods=int(horizon_days), freq="D"); end=dates[-1]
    x=tx[(tx.business_id.astype(str)==str(business_id)) & (tx.date>=start) & (tx.date<=end)].copy()
    x["day"]=x.date.dt.normalize()
    inflow=x[x.direction=="inflow"].groupby("day").amount.sum(); outflow=x[x.direction=="outflow"].groupby("day").amount.sum()
    result=pd.DataFrame({"date":dates}); result["inflows"]=result.date.map(inflow).fillna(0.0); result["outflows"]=result.date.map(outflow).fillna(0.0)
    result["net_flow"]=result.inflows-result.outflows; cash=float(opening_cash); balances=[]
    for net in result.net_flow: cash+=float(net); balances.append(cash)
    result["closing_cash"]=balances; result["shortfall"]=result.closing_cash<0
    return result

def summarize_forecast(forecast):
    if forecast.empty: return {"ending_cash":0.0,"minimum_cash":0.0,"shortfall_days":0,"first_shortfall_date":None}
    short=forecast[forecast.shortfall]
    return {"ending_cash":float(forecast.closing_cash.iloc[-1]),"minimum_cash":float(forecast.closing_cash.min()),"shortfall_days":int(forecast.shortfall.sum()),"first_shortfall_date":None if short.empty else short.date.iloc[0].date().isoformat()}
