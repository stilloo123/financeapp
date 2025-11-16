"""Quick test to verify 1950-1999 simulation matches expected results."""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

# Load data
loader = SP500DataLoader()
returns_1950_1999 = loader.get_returns(1950, 1999)

print(f"Testing 1950-1999 simulation (50 years)")
print(f"Initial portfolio: $5,000,000")
print(f"Annual withdrawal: $200,000")
print(f"Allocation: 100% stocks")
print(f"=" * 60)

# Manual simulation
balance = 5_000_000
withdrawal = 200_000

print(f"\nYear 0: ${balance:,.0f}")

for year_idx, annual_return in enumerate(returns_1950_1999, start=1):
    year = 1949 + year_idx

    # Withdraw at beginning of year
    balance_after_withdrawal = balance - withdrawal

    # Apply return
    growth = balance_after_withdrawal * (annual_return / 100.0)
    balance = balance_after_withdrawal + growth

    if year_idx <= 5 or year_idx >= 46:  # Show first 5 and last 5 years
        print(f"Year {year_idx} ({year}): Withdraw ${withdrawal:,.0f} → ${balance_after_withdrawal:,.0f} → "
              f"Return {annual_return:+.2f}% → ${balance:,.0f}")

print(f"\n" + "=" * 60)
print(f"Final balance after 50 years: ${balance:,.0f}")
print(f"Final balance in millions: ${balance/1_000_000:.1f}M")
print(f"=" * 60)

# Calculate with FICalc-style method (end-of-year withdrawals)
print(f"\n\nTesting with END-of-year withdrawals (like FICalc):")
print(f"=" * 60)

balance_eoy = 5_000_000

for year_idx, annual_return in enumerate(returns_1950_1999, start=1):
    year = 1949 + year_idx

    # Apply return FIRST
    balance_eoy = balance_eoy * (1 + annual_return / 100.0)

    # Then withdraw at END of year
    balance_eoy = balance_eoy - withdrawal

    if year_idx <= 5 or year_idx >= 46:
        print(f"Year {year_idx} ({year}): Return {annual_return:+.2f}% → Withdraw ${withdrawal:,.0f} → ${balance_eoy:,.0f}")

print(f"\n" + "=" * 60)
print(f"Final balance (end-of-year withdrawals): ${balance_eoy:,.0f}")
print(f"Final balance in millions: ${balance_eoy/1_000_000:.1f}M")
print(f"=" * 60)
