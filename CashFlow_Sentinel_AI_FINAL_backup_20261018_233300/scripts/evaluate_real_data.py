"""Evaluate a forecast against independently reconciled actual closing-cash outcomes.
Usage: python scripts/evaluate_real_data.py transactions.csv actual_daily_cash.csv BUSINESS_ID OPENING_CASH START_DATE
Actual CSV columns: date,actual_closing_cash. Use only data you are authorized to process.
"""
from pathlib import Path
import sys, json
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import validate_transactions
from src.independent_eval import evaluate_cash_forecast

def main(argv):
    if len(argv) != 6:
        print(__doc__); return 2
    tx_path, actual_path, business_id, opening, start = argv[1:]
    tx = validate_transactions(pd.read_csv(tx_path))
    actual = pd.read_csv(actual_path)
    metrics, rows = evaluate_cash_forecast(tx, business_id, float(opening), start, actual)
    out = Path('real_data_evaluation'); out.mkdir(exist_ok=True)
    rows.to_csv(out / 'forecast_vs_actual.csv', index=False)
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps(metrics, indent=2))
    print(f"Saved: {out / 'forecast_vs_actual.csv'} and {out / 'metrics.json'}")
    print('Important: metrics are meaningful only if actual outcomes are independently reconciled and representative; this script does not certify model quality.')
    return 0
if __name__ == '__main__': raise SystemExit(main(sys.argv))
