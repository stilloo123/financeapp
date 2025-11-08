"""Test simulation logic to debug negative outcomes."""

def simulate_portfolio_old(initial: float, returns: list[float], annual_withdrawal: float) -> float:
    """Current simulation - withdraws FIRST."""
    balance = initial

    for stock_return in returns:
        balance -= annual_withdrawal
        balance *= (1 + stock_return / 100.0)

    return balance

def simulate_portfolio_new(initial: float, returns: list[float], annual_withdrawal: float) -> float:
    """New simulation - applies return FIRST."""
    balance = initial

    for stock_return in returns:
        balance *= (1 + stock_return / 100.0)
        balance -= annual_withdrawal

    return balance


# Test with user's scenario
initial_pay_off = 4_500_000  # $4.5M after paying $500k mortgage
annual_withdrawal_pay_off = 171_600  # $200k - $28.4k mortgage payment

initial_keep = 5_000_000  # $5M
annual_withdrawal_keep = 200_000  # $200k including mortgage

# Test with average 10% returns for 25 years
avg_returns = [10.0] * 25

print("=" * 60)
print("SCENARIO: Average 10% Returns for 25 Years")
print("=" * 60)

print("\nPay Off Completely:")
print(f"  Starting Portfolio: ${initial_pay_off:,.0f}")
print(f"  Annual Withdrawal: ${annual_withdrawal_pay_off:,.0f}")
print(f"  Withdrawal Rate: {annual_withdrawal_pay_off/initial_pay_off*100:.2f}%")

result_old = simulate_portfolio_old(initial_pay_off, avg_returns, annual_withdrawal_pay_off)
result_new = simulate_portfolio_new(initial_pay_off, avg_returns, annual_withdrawal_pay_off)

print(f"  OLD Logic (withdraw first): ${result_old:,.0f}")
print(f"  NEW Logic (return first): ${result_new:,.0f}")

print("\nKeep Invested:")
print(f"  Starting Portfolio: ${initial_keep:,.0f}")
print(f"  Annual Withdrawal: ${annual_withdrawal_keep:,.0f}")
print(f"  Withdrawal Rate: {annual_withdrawal_keep/initial_keep*100:.2f}%")

result_old_keep = simulate_portfolio_old(initial_keep, avg_returns, annual_withdrawal_keep)
result_new_keep = simulate_portfolio_new(initial_keep, avg_returns, annual_withdrawal_keep)

print(f"  OLD Logic (withdraw first): ${result_old_keep:,.0f}")
print(f"  NEW Logic (return first): ${result_new_keep:,.0f}")

# Test with a bad period (2000-2024 which includes 2008 crash)
print("\n" + "=" * 60)
print("SCENARIO: Realistic Historical Returns (including crashes)")
print("=" * 60)

# Simulate some bad years
bad_returns = [-10, -12, -22, 28, 10, 5, 16, -37, 26, 15, 2, 16, 32, 14, 1, 12, 22, -4, 31, 19, 1, 29, -18, 31, 27]  # Approximation

print(f"\nReturns used: {len(bad_returns)} years")
print(f"Average return: {sum(bad_returns)/len(bad_returns):.2f}%")

result_old_bad = simulate_portfolio_old(initial_pay_off, bad_returns, annual_withdrawal_pay_off)
result_new_bad = simulate_portfolio_new(initial_pay_off, bad_returns, annual_withdrawal_pay_off)

print("\nPay Off Completely (with realistic returns):")
print(f"  OLD Logic: ${result_old_bad:,.0f}")
print(f"  NEW Logic: ${result_new_bad:,.0f}")

result_old_keep_bad = simulate_portfolio_old(initial_keep, bad_returns, annual_withdrawal_keep)
result_new_keep_bad = simulate_portfolio_new(initial_keep, bad_returns, annual_withdrawal_keep)

print("\nKeep Invested (with realistic returns):")
print(f"  OLD Logic: ${result_old_keep_bad:,.0f}")
print(f"  NEW Logic: ${result_new_keep_bad:,.0f}")

# Test year-by-year to see what's happening
print("\n" + "=" * 60)
print("DETAILED YEAR-BY-YEAR (Pay Off Completely, OLD logic)")
print("=" * 60)

balance = initial_pay_off
for year, stock_return in enumerate(bad_returns[:5], 1):  # Just first 5 years
    balance_before = balance
    balance -= annual_withdrawal_pay_off
    balance_after_withdrawal = balance
    balance *= (1 + stock_return / 100.0)
    balance_after_return = balance

    print(f"Year {year}:")
    print(f"  Start: ${balance_before:,.0f}")
    print(f"  After withdrawal: ${balance_after_withdrawal:,.0f}")
    print(f"  Return: {stock_return:+.2f}%")
    print(f"  End: ${balance_after_return:,.0f}")
