"""Test simulation with inflation-adjusted spending (like FICalc)."""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

# Load data
loader = SP500DataLoader()
returns_1950_1999 = loader.get_returns(1950, 1999)

print(f"Testing 1950-1999 with INFLATION-ADJUSTED spending (like FICalc)")
print(f"Initial portfolio: $5,000,000")
print(f"Initial withdrawal: $200,000 (grows with inflation)")
print(f"Inflation rate: 3.5% per year (approximate historical average)")
print(f"=" * 70)

balance = 5_000_000
withdrawal = 200_000
inflation_rate = 3.5  # Historical average inflation ~3-3.5%

total_withdrawn = 0

for year_idx, annual_return in enumerate(returns_1950_1999, start=1):
    year = 1949 + year_idx

    # Adjust withdrawal for inflation (starting year 2)
    if year_idx > 1:
        withdrawal = withdrawal * (1 + inflation_rate / 100.0)

    # Withdraw at beginning of year
    balance = balance - withdrawal
    total_withdrawn += withdrawal

    # Apply return
    balance = balance * (1 + annual_return / 100.0)

    if year_idx <= 5 or year_idx >= 46:
        print(f"Year {year_idx} ({year}): Withdraw ${withdrawal:,.0f} → "
              f"Return {annual_return:+.2f}% → Balance: ${balance:,.0f}")

print(f"\n" + "=" * 70)
print(f"Final balance after 50 years: ${balance:,.0f}")
print(f"Final balance in millions: ${balance/1_000_000:.1f}M")
print(f"Total withdrawn (nominal): ${total_withdrawn:,.0f}")
print(f"Final withdrawal amount: ${withdrawal:,.0f}/year")
print(f"=" * 70)

# Try with different inflation rates
print(f"\n\nTrying different inflation rates:")
print(f"=" * 70)

for inflation in [3.0, 3.5, 4.0]:
    balance = 5_000_000
    withdrawal = 200_000

    for year_idx, annual_return in enumerate(returns_1950_1999, start=1):
        if year_idx > 1:
            withdrawal = withdrawal * (1 + inflation / 100.0)
        balance = (balance - withdrawal) * (1 + annual_return / 100.0)

    print(f"Inflation {inflation}%: Final balance = ${balance/1_000_000:.1f}M")
