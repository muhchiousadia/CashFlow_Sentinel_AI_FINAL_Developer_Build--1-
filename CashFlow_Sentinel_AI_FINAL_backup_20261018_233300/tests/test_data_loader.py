import pandas as pd
import pytest
from src.data_loader import validate_transactions, DataValidationError

def frame(): return pd.DataFrame([{"business_id":"A","business_name":"Alpha","date":"2026-10-15","direction":"inflow","category":"sale","amount":100,"counterparty_id":"B","description":"invoice"}])
def test_valid_rows_parse_date(): assert pd.api.types.is_datetime64_any_dtype(validate_transactions(frame()).date)
def test_bad_direction_rejected():
 d=frame(); d.loc[0,"direction"]="maybe"
 with pytest.raises(DataValidationError): validate_transactions(d)
def test_negative_amount_rejected():
 d=frame(); d.loc[0,"amount"]=-1
 with pytest.raises(DataValidationError): validate_transactions(d)
