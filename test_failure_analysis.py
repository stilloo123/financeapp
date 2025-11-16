"""
Detailed analysis of the failed periods to understand when they run out.
"""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

loader = SP500DataLoader()

# Analyze the worst period: 1969-2018
returns = loader.get_returns(1969, 2018)

print("Detailed year-by-year analysis: 1969-2018")
print("Initial: $5,000,000 | Withdrawal: $200,000")
print("=" * 80)

balance = 5_000_000
for year_idx, ret in enumerate(returns, start=1):
    year = 1968 + year_idx
    balance_before = balance
    balance -= 200_000
    balance_after_withdrawal = balance
    balance *= (1 + ret / 100.0)

    if year_idx <= 10 or year_idx >= 20 and year_idx <= 30 or year_idx >= 45:
        print(f"Year {year_idx} ({year}): ${balance_before/1_000_000:>6.2f}M → "
              f"Withdraw → ${balance_after_withdrawal/1_000_000:>6.2f}M → "
              f"{ret:>+6.2f}% → ${balance/1_000_000:>6.2f}M")
    elif year_idx == 19 or year_idx == 44:
        print("  ...")

    if balance < 0 and balance_before >= 0:
        print(f"\n*** RAN OUT in Year {year_idx} ({year}) ***")
        print(f"Balance before year {year_idx}: ${balance_before:,.0f}")
        print(f"After withdrawal: ${balance_after_withdrawal:,.0f}")
        print(f"Return for year: {ret:+.2f}%")
        print(f"Final balance: ${balance:,.0f}")
        break

print(f"\n" + "=" * 80)
print("Checking FICalc's exact setup...")
print("Maybe FICalc is using 25-year rolling windows, not 50-year?")
print("=" * 80)

# Test with 25-year windows
successes_25 = 0
failures_25 = 0

for start_year in range(1948, 2025 - 25 + 1):
    end_year = start_year + 25 - 1

    try:
        returns = loader.get_returns(start_year, end_year)
    except:
        continue

    if len(returns) != 25:
        continue

    balance = 5_000_000
    for ret in returns:
        balance -= 200_000
        balance *= (1 + ret / 100.0)

    if balance >= 0:
        successes_25 += 1
    else:
        failures_25 += 1

total_25 = successes_25 + failures_25
success_rate_25 = (successes_25 / total_25 * 100) if total_25 > 0 else 0

print(f"\n25-year periods:")
print(f"  Total windows: {total_25}")
print(f"  Success rate: {success_rate_25:.1f}%")

# Test with 30-year windows (more common retirement timeframe)
successes_30 = 0
failures_30 = 0

for start_year in range(1948, 2025 - 30 + 1):
    end_year = start_year + 30 - 1

    try:
        returns = loader.get_returns(start_year, end_year)
    except:
        continue

    if len(returns) != 30:
        continue

    balance = 5_000_000
    for ret in returns:
        balance -= 200_000
        balance *= (1 + ret / 100.0)

    if balance >= 0:
        successes_30 += 1
    else:
        failures_30 += 1

total_30 = successes_30 + failures_30
success_rate_30 = (successes_30 / total_30 * 100) if total_30 > 0 else 0

print(f"\n30-year periods:")
print(f"  Total windows: {total_30}")
print(f"  Success rate: {success_rate_30:.1f}%")

print(f"\n50-year periods:")
print(f"  Success rate: 82.1%")
