"""Test that mortgage payment drops after payoff."""

import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment

# Setup
loader = SP500DataLoader()
returns = loader.get_returns(1949, 1998)  # 50 years

portfolio = 5_000_000
living_expenses = 170_000
mortgage_balance = 500_000
mortgage_rate = 3.0
mortgage_years = 25

mortgage_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, mortgage_years)

print("Test: Mortgage Payment Drops After 25 Years")
print("=" * 70)
print(f"Portfolio: ${portfolio:,.0f}")
print(f"Living Expenses: ${living_expenses:,.0f}/year")
print(f"Mortgage Payment: ${mortgage_payment:,.2f}/year")
print(f"Mortgage Years: {mortgage_years}")
print(f"Projection Years: {len(returns)}")
print("=" * 70)

# Simulate Keep Invested (with mortgage payoff logic)
balance = portfolio

for year_idx, ret in enumerate(returns, start=1):
    # Withdrawal changes after mortgage is paid off
    if year_idx <= mortgage_years:
        withdrawal = living_expenses + mortgage_payment
    else:
        withdrawal = living_expenses

    balance -= withdrawal
    balance *= (1 + ret / 100.0)

    if year_idx == 1 or year_idx == 25 or year_idx == 26 or year_idx == 50:
        print(f"Year {year_idx}: Withdraw ${withdrawal:,.0f} → Balance: ${balance/1_000_000:.1f}M")

print("\n" + "=" * 70)
print(f"Final Balance (1949-1998): ${balance/1_000_000:.1f}M")
print("=" * 70)

print("\nExpected behavior:")
print("  - Years 1-25: Withdraw $200K ($170K + $30K mortgage)")
print("  - Years 26-50: Withdraw $170K (mortgage paid off)")
print("  - Should have MORE money than withdrawing $200K all 50 years")
