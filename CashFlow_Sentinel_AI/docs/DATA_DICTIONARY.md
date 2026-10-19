# Data Dictionary
## Transactions CSV
- `business_id`: unique business key (required)
- `business_name`: display name (required)
- `date`: transaction/expected cash date (required, ISO date)
- `direction`: `inflow` or `outflow` (required)
- `category`: transaction category (required)
- `amount`: non-negative amount in one consistent currency (required)
- `counterparty_id`: customer/supplier identifier (blank allowed)
- `description`: short description (blank allowed)

## Network CSV
- `from_business_id`: payer/source business
- `to_business_id`: receiver business
- `amount`: payment amount
- `expected_date`: expected date
- `delay_days`: non-negative integer metadata
- `relationship_type`: relationship category

Do not mix invoice issue dates and expected payment dates without defining the semantics. Bundled records are synthetic.
