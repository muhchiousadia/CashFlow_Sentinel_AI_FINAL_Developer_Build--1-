import pandas as pd

TRANSACTION_COLUMNS = {"business_id","business_name","date","direction","category","amount","counterparty_id","description"}
NETWORK_COLUMNS = {"from_business_id","to_business_id","amount","expected_date","delay_days","relationship_type"}

class DataValidationError(ValueError):
    pass

def validate_transactions(df):
    missing = TRANSACTION_COLUMNS - set(df.columns)
    if missing: raise DataValidationError(f"Missing transaction columns: {', '.join(sorted(missing))}")
    x=df.copy(); x["date"]=pd.to_datetime(x["date"], errors="coerce"); x["amount"]=pd.to_numeric(x["amount"], errors="coerce")
    if x.date.isna().any(): raise DataValidationError("Some transaction dates are invalid or missing.")
    if x.amount.isna().any() or (x.amount<0).any(): raise DataValidationError("Amounts must be valid non-negative numbers.")
    x["direction"]=x.direction.astype(str).str.lower().str.strip()
    if not x.direction.isin({"inflow","outflow"}).all(): raise DataValidationError("direction must be inflow or outflow.")
    for c in ["business_id","business_name","category"]:
        if x[c].isna().any() or (x[c].astype(str).str.strip()=="").any(): raise DataValidationError(f"{c} contains blank values.")
    x["business_id"]=x.business_id.astype(str); x["counterparty_id"]=x.counterparty_id.fillna("").astype(str); x["description"]=x.description.fillna("").astype(str)
    return x.sort_values(["business_id","date"]).reset_index(drop=True)

def validate_network(df):
    missing=NETWORK_COLUMNS-set(df.columns)
    if missing: raise DataValidationError(f"Missing network columns: {', '.join(sorted(missing))}")
    x=df.copy(); x["expected_date"]=pd.to_datetime(x.expected_date, errors="coerce"); x["amount"]=pd.to_numeric(x.amount, errors="coerce"); x["delay_days"]=pd.to_numeric(x.delay_days, errors="coerce")
    if x.expected_date.isna().any(): raise DataValidationError("Some network expected dates are invalid.")
    if x.amount.isna().any() or (x.amount<0).any(): raise DataValidationError("Network amounts must be non-negative numbers.")
    if x.delay_days.isna().any() or (x.delay_days<0).any(): raise DataValidationError("delay_days must be non-negative.")
    x["delay_days"]=x.delay_days.astype(int)
    for c in ["from_business_id","to_business_id","relationship_type"]:
        if x[c].isna().any() or (x[c].astype(str).str.strip()=="").any(): raise DataValidationError(f"{c} contains blank values.")
    return x.reset_index(drop=True)
