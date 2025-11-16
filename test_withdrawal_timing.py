"""
Test if withdrawal timing (beginning vs end of year) explains the difference.
"""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

loader = SP500DataLoader()

# Test the worst period: 1969-2018
returns = loader.get_returns(1969, 2018)

print("Testing 1969-2018 (worst period)")
print("Initial: $5,000,000")
print("Withdrawal: $200,000")
print("=" * 80)

# Method 1: Withdraw at BEGINNING of year (your current method)
print("\nMethod 1: Withdraw at BEGINNING of year")
balance_beginning = 5_000_000
for year_idx, ret in enumerate(returns, start=1):
    balance_beginning -= 200_000  # Withdraw first
    balance_beginning *= (1 + ret / 100.0)  # Then apply return

print(f"Final balance: ${balance_beginning/1_000_000:.1f}M")
print(f"Success: {'✓' if balance_beginning >= 0 else '✗'}")

# Method 2: Withdraw at END of year (FICalc might do this)
print("\nMethod 2: Withdraw at END of year")
balance_end = 5_000_000
for year_idx, ret in enumerate(returns, start=1):
    balance_end *= (1 + ret / 100.0)  # Apply return first
    balance_end -= 200_000  # Then withdraw

print(f"Final balance: ${balance_end/1_000_000:.1f}M")
print(f"Success: {'✓' if balance_end >= 0 else '✗'}")

print("\n" + "=" * 80)
print(f"Difference: ${(balance_end - balance_beginning)/1_000_000:.1f}M")

# Now test all periods with END-of-year withdrawals
print("\n" + "=" * 80)
print("Testing ALL periods with END-of-year withdrawals:")
print("=" * 80)

successes_end = 0
failures_end = 0

for start_year in range(1948, 2025 - 50 + 1):
    end_year = start_year + 50 - 1

    try:
        returns = loader.get_returns(start_year, end_year)
    except:
        continue

    if len(returns) != 50:
        continue

    balance = 5_000_000
    for ret in returns:
        balance *= (1 + ret / 100.0)  # Return first
        balance -= 200_000  # Withdraw second

    if balance >= 0:
        successes_end += 1
    else:
        failures_end += 1

total = successes_end + failures_end
success_rate_end = (successes_end / total * 100) if total > 0 else 0

print(f"Success rate (end-of-year): {success_rate_end:.1f}%")
print(f"Success rate (beginning-of-year): 82.1%")
print(f"FICalc: 100%")
