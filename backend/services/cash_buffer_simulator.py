"""
Cash Buffer Investment Simulator

Implements a "bucket strategy" with a cash buffer to reduce sequence of returns risk.
"""

from typing import List, Dict, Tuple


def simulate_with_cash_buffer(
    initial_amount: float,
    returns_sequence: List[float],
    annual_payment: float,
    cash_buffer_years: int = 3
) -> Tuple[float, List[Dict]]:
    """
    Simulate investment with cash buffer strategy.

    Strategy:
    - Keep cash_buffer_years of payments in cash
    - Rest in stocks
    - Each year: withdraw from cash
    - Replenish cash from stocks only in positive return years
    - In negative years, use cash buffer to avoid selling at losses

    Args:
        initial_amount: Starting investment ($)
        returns_sequence: Annual returns (%)
        annual_payment: Annual withdrawal ($)
        cash_buffer_years: Years of payments to keep in cash (default 3)

    Returns:
        (final_balance, year_by_year_details)
    """
    # Initial allocation
    cash_buffer_target = annual_payment * cash_buffer_years
    cash_balance = min(cash_buffer_target, initial_amount)
    stock_balance = initial_amount - cash_balance

    year_by_year = []

    for year, annual_return_pct in enumerate(returns_sequence, start=1):
        # Withdraw from cash at beginning of year
        cash_balance -= annual_payment

        # Apply return to stocks
        stock_balance *= (1 + annual_return_pct / 100.0)

        # Replenishment logic
        if cash_balance < annual_payment:  # Cash running low
            # Must sell stocks
            if annual_return_pct >= 0:
                # Positive year - replenish to full buffer
                replenish_amount = min(cash_buffer_target - cash_balance, stock_balance)
            else:
                # Negative year - only take what we need for next payment
                replenish_amount = min(annual_payment - cash_balance, stock_balance)

            stock_balance -= replenish_amount
            cash_balance += replenish_amount
        elif cash_balance < cash_buffer_target and annual_return_pct > 10:
            # Good year and buffer not full - top it up
            replenish_amount = min(cash_buffer_target - cash_balance, stock_balance * 0.2)
            stock_balance -= replenish_amount
            cash_balance += replenish_amount

        total_balance = cash_balance + stock_balance

        year_by_year.append({
            'year': year,
            'return': annual_return_pct,
            'stock_balance': round(stock_balance, 2),
            'cash_balance': round(cash_balance, 2),
            'total_balance': round(total_balance, 2)
        })

    final_balance = cash_balance + stock_balance
    return final_balance, year_by_year


def find_minimum_with_buffer(
    returns_sequence: List[float],
    annual_payment: float,
    cash_buffer_years: int = 3,
    tolerance: float = 100.0
) -> float:
    """Find minimum investment with cash buffer strategy."""
    low = 0.0
    high = annual_payment * len(returns_sequence) * 1.5

    while high - low > tolerance:
        mid = (low + high) / 2.0
        final_balance, _ = simulate_with_cash_buffer(
            mid, returns_sequence, annual_payment, cash_buffer_years
        )

        if final_balance < 0:
            low = mid
        else:
            high = mid

    return round(high, 2)


if __name__ == "__main__":
    # Test with 2000-2024 (the brutal two-crash period)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from backend.services.data_loader import SP500DataLoader
    from backend.services.investment_simulator import find_minimum_investment

    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)
    annual_payment = 28078

    print("=" * 70)
    print("Cash Buffer Strategy Test - 2000-2024 Period")
    print("=" * 70)
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Test with no buffer (current implementation)
    min_no_buffer = find_minimum_investment(returns_2000, annual_payment)
    print(f"NO BUFFER (100% stocks):")
    print(f"  Minimum investment: ${min_no_buffer:,.2f}")
    print()

    # Test with 2-year buffer
    min_2yr_buffer = find_minimum_with_buffer(returns_2000, annual_payment, 2)
    print(f"2-YEAR CASH BUFFER:")
    print(f"  Minimum investment: ${min_2yr_buffer:,.2f}")
    print(f"  Savings vs no buffer: ${min_no_buffer - min_2yr_buffer:,.2f}")
    print()

    # Test with 3-year buffer
    min_3yr_buffer = find_minimum_with_buffer(returns_2000, annual_payment, 3)
    print(f"3-YEAR CASH BUFFER:")
    print(f"  Minimum investment: ${min_3yr_buffer:,.2f}")
    print(f"  Savings vs no buffer: ${min_no_buffer - min_3yr_buffer:,.2f}")
    print()

    # Show year-by-year for 3-year buffer
    final, yearly = simulate_with_cash_buffer(min_3yr_buffer, returns_2000, annual_payment, 3)
    print("Year-by-year (first 10 years with 3-year buffer):")
    for i in range(10):
        y = yearly[i]
        actual_year = 2000 + i
        print(f"  {actual_year}: Return {y['return']:+.2f}% | Stocks: ${y['stock_balance']:>10,.0f} | Cash: ${y['cash_balance']:>10,.0f} | Total: ${y['total_balance']:>10,.0f}")
