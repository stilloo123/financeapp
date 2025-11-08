"""
Test Early Payoff Optimization
Verify improvement on 1927-1951 period (90th percentile)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.services.investment_simulator import (
    find_minimum_investment,
    find_minimum_with_early_payoff,
    simulate_investment_with_early_payoff
)

print("=" * 70)
print("EARLY PAYOFF OPTIMIZATION - VERIFICATION TEST")
print("=" * 70)
print()

# Load data
loader = SP500DataLoader()
returns_1927 = loader.get_returns(1927, 1951)
mortgage_balance = 500000
annual_payment = 28078

print("Testing 1927-1951 Period (90th percentile - was $430K)")
print(f"Mortgage: ${mortgage_balance:,}")
print(f"Annual payment: ${annual_payment:,}")
print(f"Average return: {sum(returns_1927) / len(returns_1927):.2f}%")
print()

# Old approach (no early payoff)
print("OLD APPROACH (No Early Payoff):")
print("-" * 70)
old_min = find_minimum_investment(returns_1927, annual_payment)
print(f"Minimum investment: ${old_min:,.2f}")
print(f"Optimization: Survive full 25 years")
print()

# New approach (with early payoff)
print("NEW APPROACH (With Early Payoff):")
print("-" * 70)
new_min, years_to_payoff, leftover = find_minimum_with_early_payoff(
    returns_1927, annual_payment, mortgage_balance
)
print(f"Minimum investment: ${new_min:,.2f}")
print(f"Years to payoff: {years_to_payoff} years")
print(f"Leftover amount: ${leftover:,.2f}")
print()

# Calculate improvement
improvement = old_min - new_min
improvement_pct = (improvement / old_min) * 100

print("=" * 70)
print("RESULTS")
print("=" * 70)
print(f"Old (no early payoff): ${old_min:,.2f}")
print(f"New (with early payoff): ${new_min:,.2f}")
print(f"IMPROVEMENT: ${improvement:,.2f} ({improvement_pct:.1f}% reduction)")
print()

# Show year-by-year what happens
print("=" * 70)
print("YEAR-BY-YEAR SIMULATION (with minimum investment)")
print("=" * 70)

success, years, final, yearly = simulate_investment_with_early_payoff(
    new_min, returns_1927, annual_payment, mortgage_balance
)

for i, y in enumerate(yearly):
    actual_year = 1927 + i
    can_payoff = "✓ CAN PAY OFF!" if y['can_payoff_early'] else ""
    print(f"{actual_year} (Yr {y['year']:2d}): Return {y['return']:+7.2f}%  "
          f"Balance: ${y['balance']:>12,.0f}  "
          f"Mortgage: ${y['remaining_mortgage']:>12,.0f}  {can_payoff}")

print()
print(f"Success: {success}")
print(f"Paid off in year: {years}")
print(f"Leftover: ${final:,.2f}")
