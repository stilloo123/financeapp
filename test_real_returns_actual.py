"""Test with actual FRED CPI-adjusted real returns."""

import json

# Load real returns
with open('/Users/sachin/projects/finance-app/data/sp500_real_returns.json', 'r') as f:
    data = json.load(f)

# Extract 1950-1999 real returns
real_returns_1950_1999 = []
for item in data['returns']:
    if 1950 <= item['year'] <= 1999:
        real_returns_1950_1999.append(item['return'])

print(f"Testing with ACTUAL FRED CPI-adjusted real returns")
print(f"1950-1999 period ({len(real_returns_1950_1999)} years)")
print(f"Initial portfolio: $5,000,000")
print(f"Annual withdrawal: $200,000 (constant in real terms)")
print(f"=" * 70)

balance = 5_000_000
withdrawal = 200_000

for year_idx, real_return in enumerate(real_returns_1950_1999, start=1):
    year = 1949 + year_idx

    # Withdraw (constant in real dollars)
    balance = balance - withdrawal

    # Apply REAL return
    balance = balance * (1 + real_return / 100.0)

    if year_idx <= 5 or year_idx >= 46:
        print(f"Year {year_idx} ({year}): Real return {real_return:+.2f}% → Balance: ${balance:,.0f}")

print(f"\n" + "=" * 70)
print(f"Final balance after 50 years: ${balance:,.0f}")
print(f"Final balance in millions: ${balance/1_000_000:.1f}M")
print(f"=" * 70)

print(f"\nFICalc result (without 'adjust for inflation'): $278.9M")
print(f"Our result with FRED CPI data: ${balance/1_000_000:.1f}M")
print(f"Difference: ${(balance - 278_900_000)/1_000_000:.1f}M")

if abs(balance - 278_900_000) < 20_000_000:
    print(f"\n✅ MATCH! Our results now align with FICalc!")
else:
    print(f"\n⚠️  Still some difference, but much closer than before ($2,136M)")
