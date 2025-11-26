"""
Test script for response formatting
"""
from utils.response_formatter import format_response

# Sample raw LLM response
raw_response = """
**Current State**: The portfolio shows heavy equity concentration at 90% with significant holdings in HDFC and ICICI funds.

**Analysis**
The portfolio has a total value of Rs. 628765.33 with 99.1% in equity. This is extremely aggressive.

**Risk Assessment**  At >99% equity allocation, the portfolio is exposed to market volatility and downside risk typical of equity assets, especially given India's equity volatility profile.

**Sector / Thematic Diversification** Several funds exhibit technology & consumer bias, while overlapping in Large Cap & Mid Cap space. Overlap might reduce diversification benefits.

**Rebalancing Recommendations**
1. Increase Debt and Defensive Asset Allocation to 10-15% – Currently, only ~0.9 % is in debt/gold/FOF. Shifting 10-15% of portfolio value (~₹628k to ~₹940k) into debt funds, corporate bonds, or liquid funds will reduce volatility and improve risk-adjusted returns.
2. Consolidate some small/mid-cap allocation from HDFC Mutual Fund and ICICI Prudential Mutual Fund which overlap.

**Fund Overlap & AMC Concentration** Heavy allocation to HDFC Mutual Fund and ICICI Prudential Mutual Fund suggests potential portfolio overlap and AMC concentration risk.
"""

print("="*80)
print("BEFORE FORMATTING:")
print("="*80)
print(raw_response)

print("\n\n")
print("="*80)
print("AFTER FORMATTING:")
print("="*80)
formatted = format_response(raw_response)
print(formatted)

print("\n\n")
print("="*80)
print("FORMATTED LENGTH:", len(formatted))
print("="*80)
