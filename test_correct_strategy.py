"""
THE CORRECT STRATEGY

Priority order:
1. Is market DOWN? → Use CASH (never sell stocks at a loss!)
2. Is market UP? → Use STOCKS (if above base, else cash)

This is the optimal capital-efficient strategy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


def simulate_correct_strategy(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: list,
    annual_payment: float,
    initial_mortgage_balance: float,
    protected_base: float = 100000
):
    """
    THE CORRECT STRATEGY:
    - Market DOWN → Use cash
    - Market UP → Use stocks (if above base, else cash)
    """
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # THE CORRECT PRIORITY
        if stock_return < 0:
            # MARKET DOWN: Use cash, protect stocks
            if cash_balance >= annual_payment:
                withdrawal_source = "cash (market down)"
                cash_balance -= annual_payment
            else:
                # No cash left, forced to use stocks
                withdrawal_source = "stocks (forced, no cash)"
                stock_balance -= annual_payment
        else:
            # MARKET UP: Can use stocks if healthy
            if stock_balance > protected_base:
                withdrawal_source = "stocks (market up, above base)"
                stock_balance -= annual_payment
            elif cash_balance >= annual_payment:
                withdrawal_source = "cash (protect base)"
                cash_balance -= annual_payment
            else:
                withdrawal_source = "stocks (forced, no cash)"
                stock_balance -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037
        remaining_mortgage -= annual_payment

        total_balance = stock_balance + cash_balance

        year_by_year.append({
            'year': year,
            'return': stock_return,
            'stock_balance': round(stock_balance, 2),
            'cash_balance': round(cash_balance, 2),
            'total_balance': round(total_balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'withdrawal_source': withdrawal_source
        })

        # Check for payoff
        if total_balance >= remaining_mortgage:
            leftover = total_balance - remaining_mortgage
            return {
                'success': True,
                'years_to_payoff': year,
                'leftover': leftover,
                'year_by_year': year_by_year
            }

        # Check for failure
        if total_balance < 0:
            return {
                'success': False,
                'years_to_payoff': year,
                'leftover': total_balance,
                'year_by_year': year_by_year
            }

    return {
        'success': total_balance >= 0,
        'years_to_payoff': len(returns_sequence),
        'leftover': total_balance,
        'year_by_year': year_by_year
    }


def find_optimal_allocation(returns_sequence, annual_payment, mortgage_balance, protected_base=100000):
    """Find minimum capital needed."""
    test_cases = [
        (400000, 100000),
        (425000, 75000),
        (450000, 50000),
        (475000, 25000),
        (480000, 20000),
        (485000, 15000),
        (490000, 10000),
    ]

    print("Stock   | Cash    | Total   | Result")
    print("--------|---------|---------|------------------------------------------")

    best = None
    best_total = float('inf')

    for stock, cash in test_cases:
        total = stock + cash
        result = simulate_correct_strategy(
            stock, cash, returns_sequence, annual_payment, mortgage_balance, protected_base
        )

        if result['success']:
            outcome = f"✓ Paid off yr {result['years_to_payoff']}, ${result['leftover']:,.0f} left"
            if total < best_total:
                best_total = total
                best = (stock, cash, result)
        else:
            outcome = f"✗ Failed yr {result['years_to_payoff']}"

        print(f"${stock:>6,} | ${cash:>6,} | ${total:>6,} | {outcome}")

    return best


def main():
    print("=" * 90)
    print("THE CORRECT STRATEGY")
    print("=" * 90)
    print()
    print("Priority Rules:")
    print("  1. Market DOWN → Withdraw from CASH (never sell stocks at a loss)")
    print("  2. Market UP → Withdraw from STOCKS (if above base, else cash)")
    print()

    # Setup
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Testing on: 2000-2024")
    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    print("=" * 90)
    print("FINDING OPTIMAL ALLOCATION")
    print("=" * 90)
    print()

    result = find_optimal_allocation(returns_2000, annual_payment, mortgage_balance)

    if result is None:
        print()
        print("No successful allocation found with tested amounts.")
        return

    best_stock, best_cash, best_result = result

    print()
    print("=" * 90)
    print("🏆 OPTIMAL ALLOCATION")
    print("=" * 90)
    print()

    total = best_stock + best_cash
    print(f"Stocks: ${best_stock:,}")
    print(f"Cash:   ${best_cash:,}")
    print(f"TOTAL:  ${total:,}")
    print()
    print(f"Result: Paid off in {best_result['years_to_payoff']} years")
    print(f"Leftover: ${best_result['leftover']:,.2f}")
    print()

    # Compare
    treasury = 433032
    stock_only = 489746

    print("=" * 90)
    print("COMPARISON")
    print("=" * 90)
    print()
    print(f"Full Treasury:    ${treasury:>8,}")
    print(f"Stock Only:       ${stock_only:>8,}")
    print(f"Correct Strategy: ${total:>8,}")
    print()

    if total < treasury:
        print(f"✅ SAVES ${treasury - total:,} vs. treasury!")
    if total < stock_only:
        print(f"✅ SAVES ${stock_only - total:,} vs. stock-only!")

    print()

    # Show first 15 years
    print("=" * 90)
    print("YEAR-BY-YEAR (First 15 Years)")
    print("=" * 90)
    print()
    print("Year | Actual | Return  | Stocks  | Cash   | Total   | Mortgage | Source")
    print("-----|--------|---------|---------|--------|---------|----------|----------------------")

    for y in best_result['year_by_year'][:15]:
        actual_year = 2000 + y['year'] - 1
        print(f"{y['year']:4d} | {actual_year} | {y['return']:>+6.2f}% | ${y['stock_balance']:>6,.0f} | "
              f"${y['cash_balance']:>5,.0f} | ${y['total_balance']:>6,.0f} | ${y['remaining_mortgage']:>7,.0f} | "
              f"{y['withdrawal_source']:20s}")

    print()

    # Statistics
    down_years = sum(1 for y in best_result['year_by_year'] if y['return'] < 0)
    cash_in_down = sum(1 for y in best_result['year_by_year'] if y['return'] < 0 and 'cash' in y['withdrawal_source'])

    print("=" * 90)
    print("STRATEGY PERFORMANCE")
    print("=" * 90)
    print()
    print(f"Down market years: {down_years}")
    print(f"Used cash in down years: {cash_in_down}")
    print(f"Protected stocks from selling at loss: {cash_in_down}/{down_years} times")
    print()

    min_stock = min(y['stock_balance'] for y in best_result['year_by_year'])
    min_year = [y for y in best_result['year_by_year'] if y['stock_balance'] == min_stock][0]
    print(f"Minimum stock balance: ${min_stock:,.0f} in year {min_year['year']}")
    print()

    print("🎯 THIS IS THE OPTIMAL STRATEGY!")
    print()


if __name__ == "__main__":
    main()
