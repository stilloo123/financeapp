"""
Find Optimal Allocation: Balance between success rate and capital efficiency

Test different stock/cash allocations to find the sweet spot:
- High enough success rate (>80%?)
- Low enough capital requirement (<$400K to beat treasury)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median


def simulate_smart_withdrawal(initial_stock, initial_cash, returns_sequence, annual_payment, mortgage_balance, protected_base=100000):
    """Smart withdrawal: market down → cash, market up → stocks."""
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = mortgage_balance

    for year, stock_return in enumerate(returns_sequence, start=1):
        # CORRECT PRIORITY
        if stock_return < 0:
            # Market DOWN: Use cash
            if cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment
        else:
            # Market UP: Use stocks if above base
            if stock_balance > protected_base:
                stock_balance -= annual_payment
            elif cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037
        remaining_mortgage -= annual_payment

        total_balance = stock_balance + cash_balance

        # Early payoff?
        if total_balance >= remaining_mortgage:
            leftover = total_balance - remaining_mortgage
            return {'success': True, 'years': year, 'leftover': leftover}

        # Failure?
        if total_balance < 0:
            return {'success': False, 'years': year, 'leftover': total_balance}

    return {'success': total_balance >= 0, 'years': len(returns_sequence), 'leftover': total_balance}


def test_allocation(stock, cash, all_windows, annual_payment, mortgage_balance):
    """Test a specific allocation across all windows."""
    results = []
    for window in all_windows:
        result = simulate_smart_withdrawal(stock, cash, window['returns'], annual_payment, mortgage_balance)
        results.append({
            'period': window['period'],
            'success': result['success'],
            'years': result['years'] if result['success'] else None,
            'leftover': result['leftover'] if result['success'] else None
        })

    successes = [r for r in results if r['success']]
    success_rate = len(successes) / len(results) * 100

    if successes:
        avg_years = mean([r['years'] for r in successes])
        median_years = median([r['years'] for r in successes])
    else:
        avg_years = None
        median_years = None

    return {
        'stock': stock,
        'cash': cash,
        'total': stock + cash,
        'success_rate': success_rate,
        'avg_years': avg_years,
        'median_years': median_years,
        'successes': len(successes),
        'failures': len(results) - len(successes)
    }


def main():
    print("=" * 90)
    print("FIND OPTIMAL ALLOCATION: Balance Success Rate vs. Capital")
    print("=" * 90)
    print()

    # Setup
    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    # Get all 25-year windows
    all_windows = []
    for start_year in range(1926, 2000 + 1):
        end_year = start_year + 24
        if end_year <= 2025:
            returns = loader.get_returns(start_year, end_year)
            if len(returns) == 25:
                all_windows.append({
                    'period': f"{start_year}-{end_year}",
                    'start': start_year,
                    'returns': returns
                })

    print(f"Testing across {len(all_windows)} rolling 25-year windows")
    print()

    # Test various allocations
    test_cases = [
        # Lower end
        (200000, 50000),   # $250K - baseline
        (220000, 60000),   # $280K
        (240000, 60000),   # $300K

        # Mid range
        (250000, 70000),   # $320K
        (260000, 80000),   # $340K
        (270000, 80000),   # $350K
        (280000, 90000),   # $370K
        (290000, 90000),   # $380K
        (300000, 100000),  # $400K

        # Higher end
        (310000, 100000),  # $410K
        (320000, 100000),  # $420K
        (330000, 100000),  # $430K = treasury price
    ]

    print("Stock   | Cash    | Total   | Success | Avg Yrs | vs Treasury | Status")
    print("--------|---------|---------|---------|---------|-------------|------------------")

    treasury = 433032
    all_results = []

    for stock, cash in test_cases:
        result = test_allocation(stock, cash, all_windows, annual_payment, mortgage_balance)
        all_results.append(result)

        total = result['total']
        success_rate = result['success_rate']
        avg_years = result['avg_years'] if result['avg_years'] else 0
        savings = treasury - total

        # Status
        if success_rate >= 90:
            status = "✅ Excellent"
        elif success_rate >= 80:
            status = "✓ Very Good"
        elif success_rate >= 70:
            status = "✓ Good"
        elif success_rate >= 60:
            status = "⚠️ Moderate"
        else:
            status = "❌ Poor"

        print(f"${stock:>6,} | ${cash:>6,} | ${total:>6,} | {success_rate:6.1f}% | "
              f"{avg_years:7.1f} | {savings:>+6,} | {status}")

    print()

    # Find sweet spots
    print("=" * 90)
    print("SWEET SPOTS")
    print("=" * 90)
    print()

    # Best under $400K with >80% success
    under_400_good = [r for r in all_results if r['total'] < 400000 and r['success_rate'] >= 80]
    if under_400_good:
        best = max(under_400_good, key=lambda x: x['success_rate'])
        print("Best allocation UNDER $400K with ≥80% success:")
        print(f"  ${best['stock']:,} stocks + ${best['cash']:,} cash = ${best['total']:,}")
        print(f"  Success rate: {best['success_rate']:.1f}%")
        print(f"  Average payoff: {best['avg_years']:.1f} years")
        print(f"  Saves ${treasury - best['total']:,} vs. treasury ({(treasury - best['total'])/treasury*100:.0f}%)")
        print()

    # Best with >90% success
    excellent = [r for r in all_results if r['success_rate'] >= 90]
    if excellent:
        best = min(excellent, key=lambda x: x['total'])
        print("Minimum allocation for ≥90% success:")
        print(f"  ${best['stock']:,} stocks + ${best['cash']:,} cash = ${best['total']:,}")
        print(f"  Success rate: {best['success_rate']:.1f}%")
        print(f"  Average payoff: {best['avg_years']:.1f} years")
        if best['total'] < treasury:
            print(f"  Saves ${treasury - best['total']:,} vs. treasury ({(treasury - best['total'])/treasury*100:.0f}%)")
        else:
            print(f"  Costs ${best['total'] - treasury:,} MORE than treasury")
        print()

    # Best overall value (success rate * savings)
    for r in all_results:
        r['value_score'] = r['success_rate'] * (treasury - r['total']) / 100

    best_value = max(all_results, key=lambda x: x['value_score'])
    print("Best overall value (success rate × savings):")
    print(f"  ${best_value['stock']:,} stocks + ${best_value['cash']:,} cash = ${best_value['total']:,}")
    print(f"  Success rate: {best_value['success_rate']:.1f}%")
    print(f"  Average payoff: {best_value['avg_years']:.1f} years")
    print(f"  Saves ${treasury - best_value['total']:,} vs. treasury")
    print()

    # Recommendations
    print("=" * 90)
    print("RECOMMENDATION TIERS")
    print("=" * 90)
    print()

    print("TIER 1: Risk-Free (100% success)")
    print(f"  → Treasury Ladder: $433K")
    print(f"  • Guaranteed across all scenarios")
    print(f"  • Best for risk-averse investors")
    print()

    if excellent:
        best_excellent = min(excellent, key=lambda x: x['total'])
        print(f"TIER 2: Very High Success (≥90%)")
        print(f"  → Smart Withdrawal: ${best_excellent['total']:,} "
              f"(${best_excellent['stock']:,} stocks + ${best_excellent['cash']:,} cash)")
        print(f"  • {best_excellent['success_rate']:.1f}% historical success rate")
        print(f"  • Pays off in ~{best_excellent['avg_years']:.0f} years average")
        if best_excellent['total'] < treasury:
            savings = treasury - best_excellent['total']
            print(f"  • Saves ${savings:,} vs. treasury ({savings/treasury*100:.0f}%)")
        print()

    if under_400_good:
        best_under_400 = max(under_400_good, key=lambda x: x['success_rate'])
        print(f"TIER 3: Good Success + High Savings (≥80%, <$400K)")
        print(f"  → Smart Withdrawal: ${best_under_400['total']:,} "
              f"(${best_under_400['stock']:,} stocks + ${best_under_400['cash']:,} cash)")
        print(f"  • {best_under_400['success_rate']:.1f}% historical success rate")
        print(f"  • Pays off in ~{best_under_400['avg_years']:.0f} years average")
        savings = treasury - best_under_400['total']
        print(f"  • Saves ${savings:,} vs. treasury ({savings/treasury*100:.0f}%)")
        print(f"  • Best for moderate risk tolerance")
        print()

    print("=" * 90)


if __name__ == "__main__":
    main()
