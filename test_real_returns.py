"""Test with REAL returns (inflation-adjusted) like FICalc."""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

# Load data
loader = SP500DataLoader()
nominal_returns_1950_1999 = loader.get_returns(1950, 1999)

print(f"Testing 1950-1999 with REAL returns (FICalc style)")
print(f"Initial portfolio: $5,000,000")
print(f"Annual withdrawal: $200,000 (constant in real dollars)")
print(f"Returns: Nominal returns - ~3.5% inflation = Real returns")
print(f"=" * 70)

# Convert nominal returns to real returns (subtract inflation)
# Historical inflation 1950-1999 averaged around 3.5-4%
inflation_rate = 3.7  # Approximate average

real_returns = [nom_return - inflation_rate for nom_return in nominal_returns_1950_1999]

balance = 5_000_000
withdrawal = 200_000  # Stays constant in real (inflation-adjusted) dollars

for year_idx, real_return in enumerate(real_returns, start=1):
    year = 1949 + year_idx
    nom_return = nominal_returns_1950_1999[year_idx - 1]

    # Withdraw (constant in real dollars)
    balance = balance - withdrawal

    # Apply REAL return
    balance = balance * (1 + real_return / 100.0)

    if year_idx <= 5 or year_idx >= 46:
        print(f"Year {year_idx} ({year}): Nom {nom_return:+.1f}% → Real {real_return:+.1f}% → Balance: ${balance:,.0f}")

print(f"\n" + "=" * 70)
print(f"Final balance after 50 years: ${balance:,.0f}")
print(f"Final balance in millions: ${balance/1_000_000:.1f}M")
print(f"=" * 70)

# Try different inflation rates to match FICalc
print(f"\n\nTrying to match FICalc's $279M result:")
print(f"=" * 70)

for inf_rate in [3.5, 3.7, 4.0, 4.5, 5.0]:
    balance = 5_000_000
    withdrawal = 200_000

    real_rets = [nom - inf_rate for nom in nominal_returns_1950_1999]

    for real_ret in real_rets:
        balance = (balance - withdrawal) * (1 + real_ret / 100.0)

    print(f"Inflation {inf_rate}% → Real returns → Final: ${balance/1_000_000:.1f}M")
