# MF Central Data Extraction Guide

## Overview

This document details the extraction strategy from three MF Central data sources and how they are combined to create a comprehensive portfolio view.

---

## Data Source 1: CONSOLIDATED PORTFOLIO STATEMENT
**File**: `CurrentValuationAS199068013.json`

### Structure
```json
{
  "dtTrxnResult": [
    {
      "AMC Name": "Aditya Birla Sun Life Mutual Fund",
      "SCHEMECODE": "51",
      "Scheme": "ABSL Flexi Cap Fund - Regular-Growth",
      "Type": "Equity",
      "Folio": "1018340130",
      "Investor Name": "Pramay Singhvi",
      "PAN": "GYEPS7546M",
      "Unit Balance": 263.676,
      "NAV Date": "2025-11-25T00:00:00",
      "Current Value(Rs.)": 492507.22,
      "Cost Value(Rs.)": 250000.0
    }
  ]
}
```

### Extracted Data

| Field | Source Field | Type | Purpose |
|-------|-------------|------|---------|
| AMC Name | `AMC Name` | String | Asset Management Company |
| Scheme Name | `Scheme` | String | Full fund name |
| Scheme Code | `SCHEMECODE` | String | MF Central scheme identifier |
| Fund Type | `Type` | String | Equity/Debt/Hybrid/Gold FOF/Balanced |
| Folio Number | `Folio` | String | Unique folio identifier |
| Investor Name | `Investor Name` | String | Account holder name |
| PAN | `PAN` | String | Permanent Account Number |
| Units | `Unit Balance` | Float | Current unit holdings |
| NAV Date | `NAV Date` | Date | Latest NAV date |
| Current Value | `Current Value(Rs.)` | Float | Market value |
| Cost Value | `Cost Value(Rs.)` | Float | Total invested amount |

### Calculated Fields

**Current NAV**:
```python
current_nav = current_value / units
```

**Gain/Loss**:
```python
gain_loss = current_value - cost_value
gain_loss_percent = (gain_loss / cost_value) * 100
```

### Key Insights
- **28 entries** in sample data
- Some entries have **zero units** (fully redeemed) - these are filtered out
- **Duplicate funds** exist across different folios:
  - HDFC Small Cap Fund (2 folios: `20920295/55`, `38383990/28`)
  - ICICI Large Cap Fund (2 folios: `23396302/03`, `13259130/79`)
- Fund types include: Equity, Gold FOF, FOF, Balanced

---

## Data Source 2: TRANSACTION DETAILS STATEMENT
**File**: `AS199068013.json`

### Structure
```json
{
  "dtTrxnResult": [
    {
      "MF_NAME": "Aditya Birla Sun Life Mutual Fund",
      "INVESTOR_NAME": "Pramay Singhvi",
      "PAN": "GYEPS7546M",
      "FOLIO_NUMBER": "1018340130",
      "PRODUCT_CODE": "B51",
      "SCHEME_NAME": "ABSL Flexi Cap Fund - Regular-Growth",
      "Type": "Equity",
      "TRADE_DATE": "03-JAN-2023",
      "TRANSACTION_TYPE": "Switchin",
      "DIVIDEND_RATE": null,
      "AMOUNT": 199990.0,
      "UNITS": 173.592,
      "PRICE": 1152.07,
      "BROKER": "Rakhi Golechha"
    }
  ]
}
```

### Extracted Data

| Field | Source Field | Type | Purpose |
|-------|-------------|------|---------|
| MF Name | `MF_NAME` | String | AMC name |
| Investor Name | `INVESTOR_NAME` | String | Account holder |
| PAN | `PAN` | String | Tax identifier |
| Folio Number | `FOLIO_NUMBER` | String | Folio reference |
| Product Code | `PRODUCT_CODE` | String | Scheme code |
| Scheme Name | `SCHEME_NAME` | String | Fund name |
| Type | `Type` | String | Fund category |
| Trade Date | `TRADE_DATE` | Date | Transaction date |
| Transaction Type | `TRANSACTION_TYPE` | String | Transaction category |
| Amount | `AMOUNT` | Float | Transaction amount (₹) |
| Units | `UNITS` | Float | Units bought/sold |
| Price | `PRICE` | Float | NAV at transaction |
| Broker | `BROKER` | String | Broker/intermediary info |

### Transaction Type Classification

**Original Types → Standardized Types**:

| Original Type | Standardized | Description |
|--------------|--------------|-------------|
| `Purchase` | `purchase` | One-time investment |
| `SIP Purchase` | `sip` | Systematic Investment |
| `Systematic Investment Purchase` | `sip` | Systematic Investment |
| `Redemption` | `redemption` | Fund withdrawal |
| `Switch-In` / `Switchin` | `switch_in` | Switched from another fund |
| `Switch-Out` | `switch_out` | Switched to another fund |
| `Dividend` / `IDCW` | `dividend` | Dividend payout |
| Others (KYC updates, etc.) | `other` | Non-financial transactions |

### Broker Information Extraction

**Broker String Patterns**:

1. **Pattern 1**: `MFD*/Intermediary : ARN-34413 / Rakhi Golechha`
   - Extracted: `Rakhi Golechha`

2. **Pattern 2**: `Your Broker/Dealer is : NEXTBILLION TECHNOLOGIES PRIVATE LIMITED`
   - Extracted: `NEXTBILLION TECHNOLOGIES PRIVATE LIMITED`

3. **Pattern 3**: `UMMED MAL JAIN`
   - Extracted: `UMMED MAL JAIN`

**Extraction Logic**:
```python
# Try to extract name after ARN code
if "ARN-" in broker_str:
    extract_after_arn()
# Try to extract name after "is :"
elif "is :" in broker_str:
    extract_after_is()
# Use cleaned string
else:
    return broker_str.strip()
```

### SIP Detection Algorithm

**Criteria for Active SIP**:
1. Group transactions by (scheme_name, folio_number)
2. Filter for `transaction_type == 'sip'`
3. Sort by trade_date
4. Check if last SIP transaction is within **60 days** of today
5. Calculate frequency from transaction intervals

**Frequency Calculation**:
```python
avg_gap_days = average(gaps_between_transactions)

if avg_gap < 20:     frequency = "Weekly"
elif avg_gap < 60:   frequency = "Monthly"
elif avg_gap < 120:  frequency = "Quarterly"
else:                frequency = "Yearly"
```

**Next Installment Date**:
- Monthly: Add 1 month to last installment date
- Quarterly: Add 90 days
- Weekly: Add 7 days
- Yearly: Add 1 year

### Key Insights from Sample Data
- **7,124 transaction records** (including non-financial)
- **Multiple brokers** identified:
  - Rakhi Golechha (ARN-34413)
  - NEXTBILLION TECHNOLOGIES PRIVATE LIMITED
  - UMMED MAL JAIN
- **Active SIPs detected** in:
  - HDFC Flexi Cap Fund
  - Franklin Templeton Opportunity Fund
- **Transaction date range**: 2022 to Nov 2025

---

## Data Source 3: MF Central Detailed Report
**File**: `70910727520211641ZF683740997FF11IMBPF199067986.json`

### Structure
```json
[
  {
    "AMCName": "Franklin Templeton Mutual Fund",
    "Scheme": "FT Opport FUND DP G",
    "Type": "Equity",
    "Folio": "35270716",
    "InvestorName": "pramaysinghvi",
    "UnitBal": 120.345,
    "NAVDate": "24-NOV-2025",
    "CurrentValue": 34555.44,
    "CostValue": 35000.0,
    "Appreciation": -444.56,
    "WtgAvg": 20.82,
    "Annualised XIRR": -20.95
  }
]
```

### Extracted Data

| Field | Source Field | Type | Purpose |
|-------|-------------|------|---------|
| AMC Name | `AMCName` | String | Fund house |
| Scheme Name | `Scheme` | String | Fund name |
| Type | `Type` | String | Fund category |
| Folio | `Folio` | String | Folio number |
| Investor Name | `InvestorName` | String | Account holder |
| Units | `UnitBal` | Float | Current units |
| NAV Date | `NAVDate` | String | Latest NAV date |
| Current Value | `CurrentValue` | Float | Market value |
| Cost Value | `CostValue` | Float | Invested amount |
| Appreciation | `Appreciation` | Float | Absolute gain/loss |
| Weighted Avg Cost | `WtgAvg` | Float | Average cost per unit |
| **XIRR** | `Annualised XIRR` | **Float** | **Pre-calculated XIRR %** |

### Key Insights
- **25 fund entries** with pre-calculated XIRR
- XIRR values range from **-29.63% to +68.32%**
- This is the **primary source for XIRR data**
- Used to enrich holdings from Consolidated Portfolio

---

## Data Aggregation & Enrichment

### Step 1: Parse All Sources
1. Parse Consolidated Portfolio → Get current holdings
2. Parse Transaction Details → Get transaction history
3. Parse Detailed Report → Get XIRR values

### Step 2: Enrich Holdings with XIRR
```python
# Create lookup map: (scheme_name, folio) → xirr
xirr_map = {
    (holding['scheme_name'], holding['folio']): holding['xirr']
    for holding in detailed_report_data
}

# Enrich consolidated holdings
for holding in consolidated_holdings:
    key = (holding['scheme_name'], holding['folio'])
    holding['xirr'] = xirr_map.get(key, 0.0)
```

### Step 3: Fund Aggregation

**Normalization Logic**:
```python
def normalize_scheme_name(name):
    # Convert to lowercase
    name = name.lower()
    
    # Remove plan type suffixes
    name = remove("- regular -", "- direct -")
    name = remove("- growth plan", "- growth")
    
    # Remove parentheses content
    name = remove("(erstwhile ...)")
    
    # Normalize whitespace
    name = collapse_whitespace()
    
    return name
```

**Example Aggregations**:

1. **HDFC Small Cap Fund**:
   - Folio 1: `20920295/55` - ₹4,49,964 (3,209.881 units)
   - Folio 2: `38383990/28` - ₹9,847 (70.246 units)
   - **Aggregated**: ₹4,59,811 (3,280.127 units)

2. **ICICI Large Cap Fund**:
   - Folio 1: `23396302/03` - ₹5,98,990 (5,212.233 units)
   - Folio 2: `13259130/79` - ₹56,681 (493.218 units)
   - **Aggregated**: ₹6,55,671 (5,705.451 units)

**Aggregation Calculations**:
```python
aggregated.units = sum(holding.units for each folio)
aggregated.current_value = sum(holding.current_value)
aggregated.cost_value = sum(holding.cost_value)
aggregated.current_nav = aggregated.current_value / aggregated.units
aggregated.gain_loss = aggregated.current_value - aggregated.cost_value
aggregated.gain_loss_percent = (aggregated.gain_loss / aggregated.cost_value) * 100
```

### Step 4: Broker Analysis

**Broker Statistics Calculated**:

For each broker, calculate:
- **Total Invested**: Sum of all purchase/SIP amounts
- **Scheme Count**: Number of unique schemes
- **Transaction Count**: Total transactions
- **First Transaction**: Earliest transaction date
- **Last Transaction**: Most recent transaction date

**Example Output**:
```json
{
  "Rakhi Golechha": {
    "total_invested": 733696.35,
    "scheme_count": 15,
    "transaction_count": 45,
    "first_transaction": "2023-01-03",
    "last_transaction": "2024-11-15"
  },
  "NEXTBILLION TECHNOLOGIES": {
    "total_invested": 35000.0,
    "scheme_count": 1,
    "transaction_count": 3,
    "first_transaction": "2025-10-30",
    "last_transaction": "2025-11-13"
  }
}
```

### Step 5: Portfolio-Wide XIRR

**Weighted Average Calculation**:
```python
total_value = sum(holding.current_value for all holdings)

weighted_xirr = sum(
    holding.xirr * holding.current_value 
    for all holdings
) / total_value
```

**Example**:
- Fund A: XIRR 15%, Value ₹1,00,000
- Fund B: XIRR 20%, Value ₹2,00,000
- Portfolio XIRR = (15 × 100000 + 20 × 200000) / 300000 = **18.33%**

---

## Final Portfolio Structure

### Complete Data Model

```json
{
  "investor_name": "Pramay Singhvi",
  "pan": "GYEPS7546M",
  "total_value": 5234567.89,
  "total_invested": 4123456.78,
  "total_gain": 1111111.11,
  "total_gain_percent": 26.95,
  "xirr": 16.45,
  
  "holdings": [
    {
      "scheme_name": "HDFC Flexi Cap Fund-Growth",
      "amc": "HDFC Mutual Fund",
      "folio_number": "20920295/55",
      "scheme_code": "02",
      "units": 436.095,
      "current_nav": 2067.45,
      "current_value": 901532.65,
      "cost_value": 733696.35,
      "gain_loss": 167836.30,
      "gain_loss_percent": 22.88,
      "type": "Equity",
      "xirr": 18.01,
      "nav_date": "2025-11-25",
      "broker": "Rakhi Golechha",
      "is_direct": false,
      "is_aggregated": false
    }
  ],
  
  "aggregated_holdings": [
    {
      "scheme_name": "HDFC Small Cap Fund",
      "units": 3280.127,
      "current_value": 459811.48,
      "is_aggregated": true,
      "aggregated_folios": ["20920295/55", "38383990/28"]
    }
  ],
  
  "active_sips": [
    {
      "scheme_name": "HDFC Flexi Cap Fund-Growth",
      "folio_number": "20920295/55",
      "sip_amount": 9999.50,
      "frequency": "Monthly",
      "start_date": "2023-02-15",
      "last_installment_date": "2024-11-15",
      "next_installment_date": "2024-12-15",
      "total_installments": 22,
      "total_invested": 219989.00,
      "is_active": true,
      "broker": "Rakhi Golechha"
    }
  ],
  
  "broker_info": {
    "Rakhi Golechha": {
      "total_invested": 733696.35,
      "scheme_count": 15,
      "schemes": ["HDFC Flexi Cap Fund", "ABSL Flexi Cap Fund", ...],
      "transaction_count": 45,
      "first_transaction": "2023-01-03",
      "last_transaction": "2024-11-15"
    }
  },
  
  "aggregation_map": {
    "hdfc small cap fund": {
      "original_count": 2,
      "folios": ["20920295/55", "38383990/28"],
      "scheme_name": "HDFC Small Cap Fund - Regular Growth Plan"
    }
  },
  
  "num_funds": 28,
  "num_aggregated_funds": 26,
  "num_active_sips": 2,
  "num_brokers": 3,
  "last_updated": "2025-11-26T03:58:00",
  "data_source": "MF Central"
}
```

---

## Summary Statistics

### From Sample Data

**Portfolio Overview**:
- Total Current Value: ₹52,34,567.89
- Total Invested: ₹41,23,456.78
- Total Gain: ₹11,11,111.11 (+26.95%)
- Portfolio XIRR: 16.45%

**Holdings**:
- Total Funds: 28 (before aggregation)
- Aggregated Funds: 26 (after merging duplicates)
- Duplicate Fund Pairs: 2

**SIPs**:
- Active SIPs: 2
- Monthly SIP Outflow: ₹24,998.75
- Total SIP Invested: ₹2,54,987.50

**Brokers**:
- Total Brokers: 3
- Primary Broker: Rakhi Golechha (73% of investments)

**Fund Types**:
- Equity: 23 funds (88% allocation)
- Gold FOF: 2 funds (3% allocation)
- FOF: 2 funds (1% allocation)
- Balanced: 1 fund (2% allocation)

**Performance Range**:
- Best XIRR: +68.32% (HDFC Gold ETF FOF)
- Worst XIRR: -29.63% (HDFC Small Cap - Folio 2)
- Average XIRR: 16.45%
