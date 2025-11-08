"""
RETIRED SCENARIO: No new income, living off portfolio

Compare:
A) Pay off $500K mortgage now
   - Portfolio: Whatever you have LEFT after paying $500K
   - Withdraw: ONLY living expenses (no mortgage payment)

B) Keep $500K invested
   - Portfolio: Keep the full $500K invested
   - Withdraw: Living expenses + $28,714 mortgage payment

The question: Which strategy leaves you with MORE money after 25 years?

Key: This depends on your total assets!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median


def simulate_portfolio(initial_amount, returns_sequence, annual_withdrawal):
    """Simulate portfolio with fixed annual withdrawal."""
    balance = initial_amount

    for stock_return in returns_sequence:
        balance -= annual_withdrawal
        balance *= (1 + stock_return / 100.0)

    return balance


def main():
    print("=" * 90)
    print("RETIRED SCENARIO: No New Income")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    mortgage_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual mortgage payment: ${mortgage_payment:,.2f}")
    print()

    # Let's test different total asset levels and living expense needs
    print("KEY QUESTION: What are your total assets and annual living expenses?")
    print()

    # Example scenarios
    test_scenarios = [
        # (total_assets, annual_living_expenses)
        (575000, 0),      # Minimum to cover mortgage, no other expenses
        (575000, 20000),  # $20K/year living expenses
        (575000, 40000),  # $40K/year living expenses
        (700000, 40000),  # More assets, $40K living
        (1000000, 50000), # $1M total, $50K living
        (1000000, 80000), # $1M total, $80K living
    ]

    # Get test period (use 2000-2024 as worst case)
    returns_2000 = loader.get_returns(2000, 2024)

    print("=" * 90)
    print("COMPARISON: 2000-2024 Worst Case")
    print("=" * 90)
    print()

    print("Total   | Living  | Strategy A: Pay Off  | Strategy B: Keep Invested")
    print("Assets  | Expense | Portfolio End Balance | Portfolio End Balance | Better?")
    print("--------|---------|----------------------|----------------------|----------")

    for total_assets, living_expenses in test_scenarios:
        # Strategy A: Pay off mortgage now
        # Portfolio = total_assets - 500K
        # Withdraw = living_expenses only (no mortgage)
        portfolio_a = total_assets - 500000
        withdrawal_a = living_expenses

        if portfolio_a <= 0:
            end_balance_a = "N/A (not enough to pay off)"
            better = "B"
        else:
            end_balance_a = simulate_portfolio(portfolio_a, returns_2000, withdrawal_a)

            # Strategy B: Keep invested
            # Portfolio = total_assets (all invested)
            # Withdraw = living_expenses + mortgage_payment
            portfolio_b = total_assets
            withdrawal_b = living_expenses + mortgage_payment

            end_balance_b = simulate_portfolio(portfolio_b, returns_2000, withdrawal_b)

            # Which is better?
            if end_balance_a > end_balance_b:
                better = "A (Pay off)"
            elif end_balance_b > end_balance_a:
                better = "B (Invest)"
            else:
                better = "Tie"

            diff = end_balance_b - end_balance_a

            print(f"${total_assets:>6,} | ${living_expenses:>6,} | ${end_balance_a:>19,.0f} | "
                  f"${end_balance_b:>19,.0f} | {better} ({diff:+,.0f})")

    print()

    # Now test across ALL historical periods for a specific scenario
    print("=" * 90)
    print("FULL HISTORICAL BACKTEST")
    print("=" * 90)
    print()

    # Let's use $1M assets, $50K living expenses as example
    total_assets = 1000000
    living_expenses = 50000

    print(f"Scenario: ${total_assets:,} total assets, ${living_expenses:,}/year living expenses")
    print()

    # Get all windows (excluding Great Depression)
    great_depression = ['1928-1952', '1929-1953', '1930-1954', '1931-1955']
    all_windows = []

    for start_year in range(1926, 2001):
        end_year = start_year + 24
        if end_year <= 2025:
            period = f"{start_year}-{end_year}"
            if period not in great_depression:
                try:
                    returns = loader.get_returns(start_year, end_year)
                    if len(returns) == 25:
                        all_windows.append({
                            'period': period,
                            'returns': returns
                        })
                except:
                    pass

    results_a = []
    results_b = []

    for window in all_windows:
        # Strategy A: Pay off
        portfolio_a = total_assets - 500000
        withdrawal_a = living_expenses
        end_a = simulate_portfolio(portfolio_a, window['returns'], withdrawal_a)
        results_a.append(end_a)

        # Strategy B: Invest
        portfolio_b = total_assets
        withdrawal_b = living_expenses + mortgage_payment
        end_b = simulate_portfolio(portfolio_b, window['returns'], withdrawal_b)
        results_b.append(end_b)

    # Calculate statistics
    avg_a = mean(results_a)
    median_a = median(results_a)
    min_a = min(results_a)

    avg_b = mean(results_b)
    median_b = median(results_b)
    min_b = min(results_b)

    print(f"Strategy A: Pay Off $500K, Invest ${total_assets - 500000:,}")
    print(f"  Withdraw ${living_expenses:,}/year for living expenses")
    print(f"  Average end balance: ${avg_a:,.0f}")
    print(f"  Median end balance: ${median_a:,.0f}")
    print(f"  Worst case: ${min_a:,.0f}")
    print()

    print(f"Strategy B: Invest ${total_assets:,}")
    print(f"  Withdraw ${living_expenses + mortgage_payment:,.0f}/year (living + mortgage)")
    print(f"  Average end balance: ${avg_b:,.0f}")
    print(f"  Median end balance: ${median_b:,.0f}")
    print(f"  Worst case: ${min_b:,.0f}")
    print()

    # Count wins
    wins_a = sum(1 for i in range(len(results_a)) if results_a[i] > results_b[i])
    wins_b = sum(1 for i in range(len(results_b)) if results_b[i] > results_a[i])

    print(f"Historical Performance:")
    print(f"  Strategy A wins: {wins_a}/{len(all_windows)} scenarios ({wins_a/len(all_windows)*100:.1f}%)")
    print(f"  Strategy B wins: {wins_b}/{len(all_windows)} scenarios ({wins_b/len(all_windows)*100:.1f}%)")
    print()

    if avg_b > avg_a:
        print(f"✅ INVEST strategy wins by ${avg_b - avg_a:,.0f} on average")
    else:
        print(f"✅ PAY OFF strategy wins by ${avg_a - avg_b:,.0f} on average")

    print()

    # Show the key insight
    print("=" * 90)
    print("KEY INSIGHT")
    print("=" * 90)
    print()

    withdrawal_rate_a = living_expenses / (total_assets - 500000) * 100
    withdrawal_rate_b = (living_expenses + mortgage_payment) / total_assets * 100

    print(f"The key is WITHDRAWAL RATE:")
    print()
    print(f"Strategy A (Pay off):")
    print(f"  Portfolio: ${total_assets - 500000:,}")
    print(f"  Withdrawal: ${living_expenses:,}/year")
    print(f"  Withdrawal rate: {withdrawal_rate_a:.2f}%")
    print()
    print(f"Strategy B (Invest):")
    print(f"  Portfolio: ${total_assets:,}")
    print(f"  Withdrawal: ${living_expenses + mortgage_payment:,.0f}/year")
    print(f"  Withdrawal rate: {withdrawal_rate_b:.2f}%")
    print()

    if withdrawal_rate_b < withdrawal_rate_a:
        print(f"✅ Strategy B has LOWER withdrawal rate ({withdrawal_rate_b:.2f}% vs {withdrawal_rate_a:.2f}%)")
        print(f"   This is why keeping invested usually wins!")
    else:
        print(f"⚠️ Strategy A has LOWER withdrawal rate ({withdrawal_rate_a:.2f}% vs {withdrawal_rate_b:.2f}%)")
        print(f"   Paying off might be better in this case")

    print()

    # General recommendation
    print("=" * 90)
    print("GENERAL RULE")
    print("=" * 90)
    print()

    print("If you're retired with NO new income:")
    print()
    print("Compare withdrawal rates:")
    print()
    print("  Rate A = Living_Expenses / (Assets - $500K)")
    print("  Rate B = (Living_Expenses + $28,714) / Assets")
    print()
    print("If Rate B < Rate A:")
    print("  → INVEST the money (don't pay off)")
    print("  → Lower withdrawal rate = better long-term results")
    print()
    print("If Rate A < Rate B:")
    print("  → PAY OFF the mortgage")
    print("  → Even though portfolio is smaller, withdrawal rate is lower")
    print()

    print("For the 4% safe withdrawal rule:")
    print("  You want withdrawal rate ≤ 4%")
    print()

    # Examples
    print("Quick examples:")
    print()

    examples = [
        (600000, 20000),
        (750000, 30000),
        (1000000, 50000),
        (1500000, 60000),
    ]

    print("Assets  | Living  | Rate A   | Rate B   | Better Strategy")
    print("--------|---------|----------|----------|------------------")

    for assets, living in examples:
        rate_a = living / (assets - 500000) * 100
        rate_b = (living + mortgage_payment) / assets * 100

        if rate_a < rate_b:
            better = "Pay off (A)"
        else:
            better = "Invest (B)"

        print(f"${assets:>6,} | ${living:>6,} | {rate_a:>7.2f}% | {rate_b:>7.2f}% | {better}")

    print()


if __name__ == "__main__":
    main()
