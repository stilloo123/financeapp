"""
Test Optimal Algorithm with 1% Cash Rate

Compare:
- Cash at 3.7% (current): Positive carry (+0.7% vs 3.0% mortgage)
- Cash at 1.0% (test): Negative carry (-2.0% vs 3.0% mortgage)

This will show if the cash-heavy strategy was driven by the positive carry.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from typing import List, Dict


def simulate_smart_withdrawal_custom_cash_rate(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    cash_rate: float = 3.7,  # Cash return rate
    protected_base: float = 100000
) -> Dict:
    """
    Simulate smart withdrawal with custom cash rate.
    """
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Smart withdrawal logic
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
        cash_balance *= (1 + cash_rate / 100.0)  # Use custom cash rate
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

        # Check for early payoff
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


def find_optimal_with_cash_rate(returns_sequence, annual_payment, mortgage_balance, cash_rate):
    """
    Find optimal allocation for given cash rate using binary search.
    """
    import math

    def find_best_split(total_capital, cash_rate):
        """Golden section search on stock/cash split."""
        phi = (1 + math.sqrt(5)) / 2

        a, b = 0.0, 1.0
        c = b - (b - a) / phi
        d = a + (b - a) / phi

        best_result = None
        best_ratio = 0.5

        for _ in range(30):  # Max iterations
            if abs(b - a) < 0.01:
                break

            stock_c = total_capital * c
            cash_c = total_capital * (1 - c)
            result_c = simulate_smart_withdrawal_custom_cash_rate(
                stock_c, cash_c, returns_sequence, annual_payment, mortgage_balance, cash_rate
            )

            stock_d = total_capital * d
            cash_d = total_capital * (1 - d)
            result_d = simulate_smart_withdrawal_custom_cash_rate(
                stock_d, cash_d, returns_sequence, annual_payment, mortgage_balance, cash_rate
            )

            def score(result):
                if not result['success']:
                    return -1000
                return -result['years_to_payoff']

            if score(result_c) > score(result_d):
                b = d
                d = c
                c = b - (b - a) / phi
                best_result = result_c
                best_ratio = c
            else:
                a = c
                c = d
                d = a + (b - a) / phi
                best_result = result_d
                best_ratio = d

        optimal_stock = total_capital * best_ratio
        optimal_cash = total_capital * (1 - best_ratio)

        return best_result and best_result['success'], optimal_stock, optimal_cash, best_result

    # Binary search on total capital
    low, high = 0, mortgage_balance
    optimal_stock, optimal_cash, optimal_result = 0, 0, None

    for _ in range(20):  # Max iterations
        if high - low < 5000:  # $5K tolerance
            break

        mid = (low + high) / 2
        success, stock, cash, result = find_best_split(mid, cash_rate)

        if success:
            optimal_stock = stock
            optimal_cash = cash
            optimal_result = result
            high = mid
        else:
            low = mid

    return optimal_stock, optimal_cash, optimal_result


def main():
    print("=" * 90)
    print("OPTIMAL ALGORITHM: Cash Rate Sensitivity Test")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()
    print("Testing on 2000-2024 (worst historical period)")
    print()

    # Test different cash rates
    cash_rates = [
        (1.0, "Negative carry (-2.0% vs mortgage)"),
        (2.0, "Negative carry (-1.0% vs mortgage)"),
        (3.0, "Break-even (0.0% vs mortgage)"),
        (3.7, "Positive carry (+0.7% vs mortgage)"),
        (4.0, "Positive carry (+1.0% vs mortgage)"),
    ]

    print("=" * 90)
    print("FINDING OPTIMAL ALLOCATIONS")
    print("=" * 90)
    print()

    results = []

    for cash_rate, description in cash_rates:
        print(f"Cash rate: {cash_rate}% - {description}")
        print("  Optimizing...")

        stock, cash, result = find_optimal_with_cash_rate(
            returns_2000, annual_payment, mortgage_balance, cash_rate
        )

        total = stock + cash

        if result and result.get('success'):
            print(f"  ✅ Optimal: ${stock:,.0f} stocks + ${cash:,.0f} cash = ${total:,.0f}")
            print(f"     Stock ratio: {stock/total*100:.1f}%")
            print(f"     Pays off in: {result['years_to_payoff']} years")
        else:
            print(f"  ❌ Failed to find solution")

        print()

        results.append({
            'cash_rate': cash_rate,
            'description': description,
            'total': total,
            'stock': stock,
            'cash': cash,
            'stock_ratio': stock / total * 100 if total > 0 else 0,
            'success': result and result.get('success', False),
            'years': result['years_to_payoff'] if result and result.get('success') else None
        })

    # Summary
    print("=" * 90)
    print("SUMMARY: Cash Rate Impact on Optimal Allocation")
    print("=" * 90)
    print()

    print("Cash | vs Mort | Total   | Stock   | Cash    | Stock% | Years | Insight")
    print("Rate | Spread  | Capital | Alloc   | Alloc   | Ratio  |       |")
    print("-----|---------|---------|---------|---------|--------|-------|------------------")

    for r in results:
        spread = r['cash_rate'] - mortgage_rate
        insight = ""
        if r['stock_ratio'] < 20:
            insight = "Cash-heavy"
        elif r['stock_ratio'] < 50:
            insight = "Balanced"
        elif r['stock_ratio'] < 80:
            insight = "Stock-heavy"
        else:
            insight = "Stock-dominant"

        print(f"{r['cash_rate']:4.1f}% | {spread:+6.1f}% | ${r['total']:>6,.0f} | "
              f"${r['stock']:>6,.0f} | ${r['cash']:>6,.0f} | {r['stock_ratio']:5.1f}% | "
              f"{r['years']:5d} | {insight}")

    print()

    # Key insights
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    print()

    result_1pct = [r for r in results if r['cash_rate'] == 1.0][0]
    result_37pct = [r for r in results if r['cash_rate'] == 3.7][0]

    print(f"At 1.0% cash (negative carry -2.0%):")
    print(f"  Optimal: ${result_1pct['stock']:,.0f} stocks + ${result_1pct['cash']:,.0f} cash")
    print(f"  Stock ratio: {result_1pct['stock_ratio']:.1f}%")
    print()

    print(f"At 3.7% cash (positive carry +0.7%):")
    print(f"  Optimal: ${result_37pct['stock']:,.0f} stocks + ${result_37pct['cash']:,.0f} cash")
    print(f"  Stock ratio: {result_37pct['stock_ratio']:.1f}%")
    print()

    if result_1pct['stock_ratio'] > result_37pct['stock_ratio']:
        print("✅ CONFIRMED: Negative carry → More stocks needed")
        print("✅ CONFIRMED: Positive carry → More cash optimal")
    else:
        print("❓ Unexpected result - needs investigation")

    print()

    # Capital efficiency
    print("Capital Efficiency vs Cash Rate:")
    print()
    min_capital = min(r['total'] for r in results if r['success'])
    max_capital = max(r['total'] for r in results if r['success'])

    print(f"  Minimum capital: ${min_capital:,.0f} (at {[r['cash_rate'] for r in results if r['total'] == min_capital][0]}% cash)")
    print(f"  Maximum capital: ${max_capital:,.0f} (at {[r['cash_rate'] for r in results if r['total'] == max_capital][0]}% cash)")
    print(f"  Difference: ${max_capital - min_capital:,.0f} ({(max_capital - min_capital)/min_capital*100:.1f}%)")
    print()

    treasury = 433032
    print(f"Treasury ladder: ${treasury:,}")
    print()
    print("Cash rate impact:")
    for r in results:
        savings = treasury - r['total']
        print(f"  {r['cash_rate']:.1f}%: ${r['total']:>6,.0f} → {savings:>+6,.0f} vs treasury ({savings/treasury*100:>+5.1f}%)")

    print()


if __name__ == "__main__":
    main()
