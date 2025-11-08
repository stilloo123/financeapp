"""
Test $150K stocks + $150K cash on 2000-2024

Can this equal split survive the worst historical case?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


def simulate_smart_withdrawal(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: list,
    annual_payment: float,
    initial_mortgage_balance: float,
    protected_base: float = 100000
):
    """Smart withdrawal: market down → cash, market up → stocks."""
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # CORRECT PRIORITY
        if stock_return < 0:
            # Market DOWN: Use cash
            if cash_balance >= annual_payment:
                withdrawal_source = "cash (market down)"
                cash_balance -= annual_payment
            else:
                withdrawal_source = "stocks (forced, no cash)"
                stock_balance -= annual_payment
        else:
            # Market UP: Use stocks if above base
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
            'actual_year': 2000 + year - 1,
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
    print("=" * 90)
    print("TEST: $150K Stocks + $150K Cash on 2000-2024")
    print("=" * 90)
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
    print("Testing 2000-2024 (worst historical period)")
    print("Allocation: $150K stocks + $150K cash = $300K total")
    print()

    # Run simulation
    result = simulate_smart_withdrawal(
        150000, 150000, returns_2000, annual_payment, mortgage_balance
    )

    print("=" * 90)
    print("RESULT")
    print("=" * 90)
    print()

    if result['success']:
        print(f"✅ SUCCESS!")
        print(f"  Paid off in: {result['years_to_payoff']} years")
        print(f"  Leftover: ${result['leftover']:,.2f}")
    else:
        print(f"❌ FAILED in year {result['years_to_payoff']}")
        print(f"  Final balance: ${result['leftover']:,.2f}")

    print()
    print("=" * 90)
    print("YEAR-BY-YEAR BREAKDOWN")
    print("=" * 90)
    print()
    print("Year | Actual | Return  | Stocks  | Cash    | Total   | Mortgage | Source")
    print("-----|--------|---------|---------|---------|---------|----------|-------------------------")

    for y in result['year_by_year']:
        marker = ""
        if y['total_balance'] < 0:
            marker = " ❌ FAILED"
        elif y['total_balance'] >= y['remaining_mortgage']:
            marker = " ✅ CAN PAY OFF"
        elif y['stock_balance'] < 100000 and 'protect base' in y['withdrawal_source']:
            marker = " ⚠️ BELOW BASE"

        print(f"{y['year']:4d} | {y['actual_year']} | {y['return']:>+6.2f}% | ${y['stock_balance']:>6,.0f} | "
              f"${y['cash_balance']:>6,.0f} | ${y['total_balance']:>6,.0f} | ${y['remaining_mortgage']:>7,.0f} | "
              f"{y['withdrawal_source']:23s}{marker}")

    print()

    # Analysis
    print("=" * 90)
    print("ANALYSIS")
    print("=" * 90)
    print()

    # Find critical moments
    cash_withdrawals = sum(1 for y in result['year_by_year'] if 'cash' in y['withdrawal_source'])
    stock_withdrawals = sum(1 for y in result['year_by_year'] if 'stocks' in y['withdrawal_source'])

    down_years = [y for y in result['year_by_year'] if y['return'] < 0]
    cash_in_down = [y for y in down_years if 'cash' in y['withdrawal_source']]

    print(f"Cash withdrawals: {cash_withdrawals} years")
    print(f"Stock withdrawals: {stock_withdrawals} years")
    print()
    print(f"Down market years: {len(down_years)}")
    print(f"Used cash in down years: {len(cash_in_down)}/{len(down_years)}")
    print()

    if down_years:
        print("Down market years detail:")
        for y in down_years:
            protection = "✓ Protected" if 'cash' in y['withdrawal_source'] else "✗ Sold stocks"
            print(f"  Year {y['year']} ({y['actual_year']}): {y['return']:+.2f}% - {protection}")
        print()

    # Find minimum balances
    min_stock = min(y['stock_balance'] for y in result['year_by_year'])
    min_stock_year = [y for y in result['year_by_year'] if y['stock_balance'] == min_stock][0]

    min_cash = min(y['cash_balance'] for y in result['year_by_year'])
    min_cash_year = [y for y in result['year_by_year'] if y['cash_balance'] == min_cash][0]

    print(f"Minimum stock balance: ${min_stock:,.0f} in year {min_stock_year['year']} ({min_stock_year['actual_year']})")
    print(f"Minimum cash balance: ${min_cash:,.0f} in year {min_cash_year['year']} ({min_cash_year['actual_year']})")
    print()

    if result['success']:
        print("=" * 90)
        print("✅ CONCLUSION")
        print("=" * 90)
        print()
        print(f"YES! $300K ($150K stocks + $150K cash) CAN survive 2000-2024!")
        print(f"  • Pays off in {result['years_to_payoff']} years")
        print(f"  • Leftover: ${result['leftover']:,.2f}")
        print()
        print("This works because:")
        print("  1. Large cash buffer ($150K) protected during crashes")
        print(f"  2. Successfully used cash in {len(cash_in_down)}/{len(down_years)} down years")
        print("  3. Stocks recovered and compounded during up years")
    else:
        print("=" * 90)
        print("❌ CONCLUSION")
        print("=" * 90)
        print()
        print(f"NO. $300K ($150K stocks + $150K cash) FAILS in 2000-2024")
        print(f"  • Failed in year {result['years_to_payoff']}")
        print(f"  • Shortfall: ${abs(result['leftover']):,.2f}")
        print()
        print("Why it failed:")
        if min_cash < 0:
            print(f"  • Cash ran out in year {min_cash_year['year']} ({min_cash_year['actual_year']})")
        if min_stock < 0:
            print(f"  • Stocks went negative in year {min_stock_year['year']} ({min_stock_year['actual_year']})")
        print(f"  • Initial stock allocation ($150K) was too low for this period")
        print(f"  • Cash buffer ($150K) was good but not enough given stock performance")

    print()


if __name__ == "__main__":
    main()
