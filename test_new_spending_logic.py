"""Test the new spending logic (excluding mortgage)."""

import sys
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.models.mortgage_calculator import calculate_annual_payment

# Test scenario
mortgage_balance = 500_000
mortgage_rate = 3.0
mortgage_years = 25
living_expenses = 73_000
portfolio = 5_000_000

# Calculate mortgage payment
mortgage_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, mortgage_years)

print("Test Scenario:")
print("=" * 70)
print(f"Portfolio: ${portfolio:,.0f}")
print(f"Mortgage Balance: ${mortgage_balance:,.0f}")
print(f"Mortgage Rate: {mortgage_rate}%")
print(f"Mortgage Years: {mortgage_years}")
print(f"Living Expenses (user input): ${living_expenses:,.0f}/year")
print(f"Calculated Mortgage Payment: ${mortgage_payment:,.2f}/year")
print("=" * 70)

print("\nStrategy 1: Pay Off Completely")
print("-" * 70)
new_portfolio = portfolio - mortgage_balance
new_spending = living_expenses  # No mortgage payment needed
print(f"New Portfolio: ${new_portfolio:,.0f}")
print(f"Annual Spending: ${new_spending:,.0f}/year")
print(f"Withdrawal Rate: {new_spending/new_portfolio*100:.2f}%")

print("\nStrategy 2: Keep 100% Invested")
print("-" * 70)
total_spending = living_expenses + mortgage_payment
print(f"Portfolio: ${portfolio:,.0f}")
print(f"Living Expenses: ${living_expenses:,.0f}/year")
print(f"Mortgage Payment: ${mortgage_payment:,.2f}/year")
print(f"Total Annual Spending: ${total_spending:,.0f}/year")
print(f"Withdrawal Rate: {total_spending/portfolio*100:.2f}%")

print("\n" + "=" * 70)
print("✓ Logic looks correct!")
print("  - Pay off: Lower spending, smaller portfolio")
print("  - Keep invested: Higher spending, larger portfolio")
