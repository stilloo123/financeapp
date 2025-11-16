"""
Test to exactly replicate FICalc's scenario and find the discrepancy.
"""

import json
import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader

# Load real returns
loader = SP500DataLoader()

# Get all 50-year windows from 1948-2024
min_year = 1948
max_year = 2024
window_size = 50

print("Testing ALL 50-year windows from 1948-2024")
print(f"Initial: $5,000,000")
print(f"Withdrawal: $200,000/year")
print(f"Allocation: 100% stocks (real returns)")
print("=" * 80)

successes = 0
failures = 0
all_results = []

for start_year in range(min_year, max_year - window_size + 2):
    end_year = start_year + window_size - 1

    # Check if we have data for this full window
    try:
        returns = loader.get_returns(start_year, end_year)
    except:
        continue

    if len(returns) != window_size:
        continue

    # Run simulation
    balance = 5_000_000
    withdrawal = 200_000
    ran_out = False
    ran_out_year = None

    for year_idx, annual_return in enumerate(returns, start=1):
        # Withdraw at beginning of year
        balance -= withdrawal

        # Apply return
        balance *= (1 + annual_return / 100.0)

        # Check if ran out
        if balance < 0 and not ran_out:
            ran_out = True
            ran_out_year = year_idx

    # Record result
    if balance >= 0:
        successes += 1
        all_results.append({
            'period': f'{start_year}-{end_year}',
            'success': True,
            'final_balance': balance
        })
    else:
        failures += 1
        all_results.append({
            'period': f'{start_year}-{end_year}',
            'success': False,
            'final_balance': balance,
            'ran_out_year': ran_out_year
        })

total = successes + failures
success_rate = (successes / total * 100) if total > 0 else 0

print(f"\nResults:")
print(f"Total windows tested: {total}")
print(f"Successes: {successes}")
print(f"Failures: {failures}")
print(f"Success Rate: {success_rate:.1f}%")

print(f"\n" + "=" * 80)
print(f"FICalc (1948-2024, 50 years): 100%")
print(f"Our test: {success_rate:.1f}%")
print(f"=" * 80)

if failures > 0:
    print(f"\nFailed periods:")
    for result in all_results:
        if not result['success']:
            print(f"  {result['period']}: Ran out in year {result['ran_out_year']}")

# Show worst performing periods
all_results.sort(key=lambda x: x['final_balance'])
print(f"\nWorst 5 periods:")
for i, result in enumerate(all_results[:5]):
    status = "✓" if result['success'] else "✗"
    print(f"  {status} {result['period']}: ${result['final_balance']/1_000_000:.1f}M")

print(f"\nBest 5 periods:")
for i, result in enumerate(all_results[-5:][::-1]):
    print(f"  ✓ {result['period']}: ${result['final_balance']/1_000_000:.1f}M")
