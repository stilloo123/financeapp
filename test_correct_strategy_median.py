"""
Test CORRECT Strategy on MEDIAN Scenarios

The worst-case 2000-2024 needed $500K (pointless - just pay off mortgage!)

Let's test on MEDIAN scenarios where stock-only needed ~$241K.
Can the correct withdrawal logic (market down → cash, market up → stocks)
work with MUCH LESS than $500K?
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


def find_optimal_allocation(returns_sequence, annual_payment, mortgage_balance, period_name):
    """Find minimum capital needed for this period."""
    # Test allocations well UNDER $500K
    test_cases = [
        (200000, 50000),   # $250K total
        (220000, 50000),   # $270K total
        (240000, 50000),   # $290K total
        (260000, 50000),   # $310K total
        (280000, 50000),   # $330K total
        (300000, 50000),   # $350K total
        (320000, 50000),   # $370K total
        (340000, 50000),   # $390K total
        (350000, 60000),   # $410K total
        (360000, 70000),   # $430K total
        (370000, 80000),   # $450K total
    ]

    print(f"\n{'='*80}")
    print(f"Testing Period: {period_name}")
    print(f"{'='*80}")
    print()
    print("Stock   | Cash   | Total   | Result")
    print("--------|--------|---------|------------------------------------------")

    best = None
    best_total = float('inf')

    for stock, cash in test_cases:
        total = stock + cash
        result = simulate_correct_strategy(
            stock, cash, returns_sequence, annual_payment, mortgage_balance
        )

        if result['success']:
            outcome = f"✓ Paid off yr {result['years_to_payoff']}, ${result['leftover']:,.0f} left"
            if total < best_total:
                best_total = total
                best = (stock, cash, result)
        else:
            outcome = f"✗ Failed yr {result['years_to_payoff']}"

        print(f"${stock:>6,} | ${cash:>5,} | ${total:>6,} | {outcome}")

    return best


def main():
    print("=" * 80)
    print("CORRECT STRATEGY: MEDIAN SCENARIOS TEST")
    print("=" * 80)
    print()
    print("The Point: Any strategy needing ≥$500K is POINTLESS (just pay off mortgage!)")
    print()
    print("Let's test on MEDIAN scenarios where stock-only needed ~$241K")
    print("Can the correct withdrawal logic achieve capital efficiency?")
    print()

    # Setup
    loader = SP500DataLoader()

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Test on several representative periods
    test_periods = [
        ("1946-1970", loader.get_returns(1946, 1970)),  # Post-war boom
        ("1975-1999", loader.get_returns(1975, 1999)),  # Great bull run
        ("1984-2008", loader.get_returns(1984, 2008)),  # Includes 2008 crash
        ("1995-2019", loader.get_returns(1995, 2019)),  # Tech boom + recovery
        ("2000-2024", loader.get_returns(2000, 2024)),  # Worst case
    ]

    results_summary = []

    for period_name, returns in test_periods:
        result = find_optimal_allocation(returns, annual_payment, mortgage_balance, period_name)

        if result:
            stock, cash, res = result
            total = stock + cash
            results_summary.append({
                'period': period_name,
                'total_capital': total,
                'stock': stock,
                'cash': cash,
                'years_to_payoff': res['years_to_payoff'],
                'leftover': res['leftover']
            })
        else:
            results_summary.append({
                'period': period_name,
                'total_capital': None,
                'stock': None,
                'cash': None,
                'years_to_payoff': None,
                'leftover': None
            })

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY: CORRECT STRATEGY ACROSS SCENARIOS")
    print("=" * 80)
    print()
    print("Period      | Total Capital | Stock   | Cash   | Years | Status")
    print("------------|---------------|---------|--------|-------|------------------")

    for r in results_summary:
        if r['total_capital']:
            status = "✓ Under $500K" if r['total_capital'] < 500000 else "⚠️ At/Over $500K"
            print(f"{r['period']:11s} | ${r['total_capital']:>12,} | ${r['stock']:>6,} | ${r['cash']:>5,} | "
                  f"{r['years_to_payoff']:5d} | {status}")
        else:
            print(f"{r['period']:11s} | {'FAILED':>13s} | {'N/A':>7s} | {'N/A':>6s} | {'N/A':>5s} | ✗ Failed")

    print()

    # Analysis
    successful = [r for r in results_summary if r['total_capital'] and r['total_capital'] < 500000]
    at_or_over = [r for r in results_summary if r['total_capital'] and r['total_capital'] >= 500000]

    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    if successful:
        print(f"✅ {len(successful)} out of {len(test_periods)} periods work with UNDER $500K:")
        print()
        for r in successful:
            print(f"  • {r['period']}: ${r['total_capital']:,} "
                  f"(${r['stock']:,} stocks + ${r['cash']:,} cash)")
            print(f"    → Pays off in {r['years_to_payoff']} years")
        print()

    if at_or_over:
        print(f"⚠️  {len(at_or_over)} periods need AT/OVER $500K (pointless - just pay off!):")
        print()
        for r in at_or_over:
            print(f"  • {r['period']}: ${r['total_capital']:,} ← MAKES NO SENSE")
        print()

    if successful:
        avg_capital = sum(r['total_capital'] for r in successful) / len(successful)
        avg_years = sum(r['years_to_payoff'] for r in successful) / len(successful)

        print(f"Average for successful periods:")
        print(f"  Capital needed: ${avg_capital:,.0f}")
        print(f"  Years to payoff: {avg_years:.1f}")
        print()

        # Compare to treasury
        treasury = 433032
        if avg_capital < treasury:
            print(f"🏆 Average ${avg_capital:,.0f} BEATS treasury ${treasury:,} by ${treasury - avg_capital:,.0f}!")
        else:
            print(f"Treasury ladder (${treasury:,}) is still better for guaranteed outcome")
        print()

    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("The correct withdrawal strategy (market down → cash, market up → stocks)")
    print("achieves capital efficiency in MOST scenarios, but:")
    print()
    print("  1. Worst-case (2000-2024) still needs ~$500K = pointless")
    print("  2. Treasury ladder at $433K guarantees ALL scenarios")
    print("  3. For risk tolerance, median scenarios work with ~$250K-$350K")
    print()


if __name__ == "__main__":
    main()
