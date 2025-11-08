"""
Detailed trace of protected base strategy
Show EXACTLY what happens each year with full calculation steps
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


def trace_first_10_years():
    """Show detailed calculations for first 10 years."""

    # Setup
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    # Initial
    stock_balance = 350000
    cash_balance = 100000
    remaining_mortgage = mortgage_balance
    protected_base = 100000

    print("=" * 100)
    print("DETAILED TRACE: Protected Base Strategy 2000-2024")
    print("=" * 100)
    print()
    print(f"Starting Allocation:")
    print(f"  Stocks: ${stock_balance:,}")
    print(f"  Cash:   ${cash_balance:,}")
    print(f"  Protected Base: ${protected_base:,}")
    print(f"  Annual Payment: ${annual_payment:,.2f}")
    print()
    print("=" * 100)
    print()

    for year in range(1, 11):
        actual_year = 2000 + year - 1
        stock_return = returns_2000[year - 1]

        print(f"YEAR {year} ({actual_year}):")
        print(f"  Market Return: {stock_return:+.2f}%")
        print(f"  Start of Year:")
        print(f"    Stocks: ${stock_balance:,.2f}")
        print(f"    Cash:   ${cash_balance:,.2f}")
        print(f"    Total:  ${stock_balance + cash_balance:,.2f}")
        print(f"    Remaining Mortgage: ${remaining_mortgage:,.2f}")
        print()

        # DECISION LOGIC
        print(f"  Decision Logic:")
        near_finish = remaining_mortgage <= stock_balance
        above_base = stock_balance > protected_base
        has_cash = cash_balance >= annual_payment

        print(f"    - Near finish (mortgage <= stocks)? {near_finish}")
        print(f"    - Stocks above base ($100K)? {above_base} (stocks: ${stock_balance:,.0f})")
        print(f"    - Has cash for payment? {has_cash} (cash: ${cash_balance:,.0f})")

        # Determine source
        if near_finish:
            source = "STOCKS (near finish)"
            stock_balance -= annual_payment
            print(f"    → Withdraw from STOCKS (near finish line)")
        elif above_base:
            source = "STOCKS (above base)"
            stock_balance -= annual_payment
            print(f"    → Withdraw from STOCKS (above protected base)")
        elif has_cash:
            source = "CASH (protect base)"
            cash_balance -= annual_payment
            print(f"    → Withdraw from CASH (protect base)")
        else:
            source = "STOCKS (forced, no cash)"
            stock_balance -= annual_payment
            print(f"    → Withdraw from STOCKS (FORCED - no cash left)")

        print()
        print(f"  After Withdrawal:")
        print(f"    Stocks: ${stock_balance:,.2f}")
        print(f"    Cash:   ${cash_balance:,.2f}")
        print()

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037
        remaining_mortgage -= annual_payment

        print(f"  After Returns Applied:")
        print(f"    Stocks: ${stock_balance:,.2f} (after {stock_return:+.2f}%)")
        print(f"    Cash:   ${cash_balance:,.2f} (after +3.7%)")
        print(f"    Total:  ${stock_balance + cash_balance:,.2f}")
        print(f"    Remaining Mortgage: ${remaining_mortgage:,.2f}")
        print()

        # Analysis
        if stock_return < 0 and source.startswith("STOCKS"):
            print(f"  ⚠️  WARNING: Market was DOWN {stock_return}% but withdrew from STOCKS!")
            print(f"       This violates the 'use cash in down markets' principle")

        if stock_balance < protected_base:
            print(f"  ⚠️  WARNING: Stocks (${stock_balance:,.0f}) BELOW protected base (${protected_base:,})")

        print()
        print("=" * 100)
        print()


if __name__ == "__main__":
    trace_first_10_years()
