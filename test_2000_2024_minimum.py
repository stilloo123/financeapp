"""
Find the MINIMUM allocation for 2000-2024 worst case

We know:
- $450K ($370K stocks + $80K cash) = FAILS
- $500K ($400K stocks + $100K cash) = SUCCESS (but pointless!)

What's the minimum? And is it under $500K?
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


def main():
    print("=" * 80)
    print("2000-2024 WORST CASE: FIND MINIMUM")
    print("=" * 80)
    print()

    # Setup
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()
    print("Testing 2000-2024 (worst historical case)")
    print()

    # Test finer granularity around the failure point
    test_cases = [
        # Around $450K-$500K
        (370000, 80000),   # $450K - we know this fails
        (375000, 85000),   # $460K
        (380000, 90000),   # $470K
        (385000, 95000),   # $480K
        (390000, 100000),  # $490K
        (395000, 105000),  # $500K
        (400000, 100000),  # $500K (different mix)

        # Also test if more cash helps
        (350000, 100000),  # $450K with more cash
        (360000, 100000),  # $460K
        (370000, 100000),  # $470K
        (380000, 100000),  # $480K
    ]

    print("Stock   | Cash    | Total   | Result")
    print("--------|---------|---------|------------------------------------------")

    min_success = None
    min_total = float('inf')

    for stock, cash in sorted(test_cases, key=lambda x: x[0] + x[1]):
        total = stock + cash
        result = simulate_correct_strategy(
            stock, cash, returns_2000, annual_payment, mortgage_balance
        )

        if result['success']:
            outcome = f"✓ Paid off yr {result['years_to_payoff']}, ${result['leftover']:,.0f} left"
            if total < min_total:
                min_total = total
                min_success = (stock, cash, result)

            # Highlight if under $500K
            if total < 500000:
                outcome = "✅ " + outcome + " ← UNDER $500K!"
        else:
            outcome = f"✗ Failed yr {result['years_to_payoff']}"

        print(f"${stock:>6,} | ${cash:>6,} | ${total:>6,} | {outcome}")

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print()

    if min_success:
        stock, cash, result = min_success
        total = stock + cash

        print(f"Minimum for 2000-2024: ${total:,}")
        print(f"  Stocks: ${stock:,}")
        print(f"  Cash:   ${cash:,}")
        print(f"  Pays off in: {result['years_to_payoff']} years")
        print()

        treasury = 433032

        if total < 500000:
            print(f"✅ SUCCESS: Under $500K!")
            print()
            if total < treasury:
                print(f"🏆 BEATS treasury ${treasury:,} by ${treasury - total:,}")
            else:
                print(f"⚠️  More than treasury ${treasury:,} by ${total - treasury:,}")
        else:
            print(f"❌ FAILS YOUR TEST: Needs $500K or more")
            print()
            print("As you said: 'if we had 500K we will just pay it off now right'")
            print()
            print("This means for 2000-2024 worst case:")
            print("  • Stock strategy is NOT viable")
            print("  • Treasury ladder ($433K) is the better option")
        print()

        # Show the critical years
        print("=" * 80)
        print("CRITICAL YEARS (First 10)")
        print("=" * 80)
        print()
        print("Year | Actual | Return  | Stocks  | Cash   | Total   | Source")
        print("-----|--------|---------|---------|--------|---------|----------------------")

        for y in result['year_by_year'][:10]:
            actual_year = 2000 + y['year'] - 1
            print(f"{y['year']:4d} | {actual_year} | {y['return']:>+6.2f}% | ${y['stock_balance']:>6,.0f} | "
                  f"${y['cash_balance']:>5,.0f} | ${y['total_balance']:>6,.0f} | "
                  f"{y['withdrawal_source']:20s}")
    else:
        print("❌ NO SUCCESSFUL ALLOCATION FOUND")
        print()
        print("Even $500K+ doesn't work with tested allocations.")
        print("2000-2024 is EXTREMELY difficult for stock-based strategies.")

    print()


if __name__ == "__main__":
    main()
