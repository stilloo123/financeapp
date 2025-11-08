"""
Test different stock/cash splits within $300K
to see if the specific $240K/$60K allocation matters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from typing import List, Dict


def simulate_smart_withdrawal(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    protected_base: float = 100000
) -> Dict:
    """Smart withdrawal simulation."""
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    for year, stock_return in enumerate(returns_sequence, start=1):
        if stock_return < 0:
            if cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment
        else:
            if stock_balance > protected_base:
                stock_balance -= annual_payment
            elif cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment

        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037
        remaining_mortgage -= annual_payment

        total_balance = stock_balance + cash_balance

        if total_balance >= remaining_mortgage:
            return {'success': True, 'years': year, 'leftover': total_balance - remaining_mortgage}
        if total_balance < 0:
            return {'success': False, 'years': year, 'leftover': total_balance}

    return {'success': total_balance >= 0, 'years': len(returns_sequence),
            'leftover': total_balance - remaining_mortgage if total_balance > remaining_mortgage else total_balance}


def main():
    print("=" * 90)
    print("TEST: Different Stock/Cash Splits Within $300K")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    # Get all windows
    all_windows = []
    for start_year in range(1926, 2001):
        end_year = start_year + 24
        if end_year <= 2025:
            try:
                returns = loader.get_returns(start_year, end_year)
                if len(returns) == 25:
                    all_windows.append({
                        'period': f"{start_year}-{end_year}",
                        'returns': returns
                    })
            except:
                pass

    print(f"Testing across {len(all_windows)} historical periods")
    print()

    # Test different splits of $300K
    splits = [
        (300000, 0),      # 100% stocks, 0% cash
        (270000, 30000),  # 90% stocks, 10% cash
        (240000, 60000),  # 80% stocks, 20% cash
        (210000, 90000),  # 70% stocks, 30% cash
        (180000, 120000), # 60% stocks, 40% cash
        (150000, 150000), # 50% stocks, 50% cash
    ]

    print("Stock   | Cash    | Success | Avg Years | Avg Leftover | Notes")
    print("--------|---------|---------|-----------|--------------|------------------")

    results_by_split = []

    for stocks, cash in splits:
        successes = []
        failures = 0

        for window in all_windows:
            result = simulate_smart_withdrawal(
                stocks, cash, window['returns'], annual_payment, mortgage_balance
            )

            if result['success']:
                successes.append(result)
            else:
                failures += 1

        success_rate = len(successes) / len(all_windows) * 100

        if successes:
            avg_years = sum(r['years'] for r in successes) / len(successes)
            avg_leftover = sum(r['leftover'] for r in successes) / len(successes)
        else:
            avg_years = 0
            avg_leftover = 0

        results_by_split.append({
            'stocks': stocks,
            'cash': cash,
            'success_rate': success_rate,
            'successes': len(successes),
            'failures': failures,
            'avg_years': avg_years,
            'avg_leftover': avg_leftover
        })

        notes = ""
        if success_rate >= 70:
            notes = "✅ Good"
        elif success_rate >= 60:
            notes = "⚠️ Moderate"
        else:
            notes = "❌ Poor"

        print(f"${stocks:>6,} | ${cash:>6,} | {success_rate:6.1f}% | {avg_years:9.1f} | ${avg_leftover:>11,.0f} | {notes}")

    print()

    # Find best split
    best = max(results_by_split, key=lambda x: (x['success_rate'], -x['avg_years']))

    print("=" * 90)
    print("ANALYSIS")
    print("=" * 90)
    print()

    print(f"Best split within $300K:")
    print(f"  Stocks: ${best['stocks']:,}")
    print(f"  Cash:   ${best['cash']:,}")
    print(f"  Success rate: {best['success_rate']:.1f}%")
    print(f"  Average years: {best['avg_years']:.1f}")
    print(f"  Average leftover: ${best['avg_leftover']:,.0f}")
    print()

    # Compare to our recommendation
    our_rec = [r for r in results_by_split if r['stocks'] == 240000][0]
    print(f"Our recommendation ($240K stocks + $60K cash):")
    print(f"  Success rate: {our_rec['success_rate']:.1f}%")
    print(f"  Average years: {our_rec['avg_years']:.1f}")
    print(f"  Average leftover: ${our_rec['avg_leftover']:,.0f}")
    print()

    if best['stocks'] == our_rec['stocks']:
        print("✅ Our recommendation IS the optimal split!")
    else:
        diff = best['success_rate'] - our_rec['success_rate']
        print(f"⚠️ Best split is {best['stocks']/300000*100:.0f}% stocks vs our {our_rec['stocks']/300000*100:.0f}%")
        print(f"   Difference: {diff:+.1f}% success rate")

    print()

    # Test if we can use LESS than $300K
    print("=" * 90)
    print("CAN WE USE LESS THAN $300K?")
    print("=" * 90)
    print()

    test_amounts = [250000, 275000, 300000, 325000]

    print("Total   | Best Stock% | Success | Avg Years | With $200K reserve")
    print("--------|-------------|---------|-----------|--------------------")

    for total in test_amounts:
        # Test different splits for this total
        best_success = 0
        best_split = None

        for pct in range(60, 101, 10):  # 60% to 100% stocks
            stocks = total * pct / 100
            cash = total - stocks

            successes = []
            for window in all_windows:
                result = simulate_smart_withdrawal(
                    stocks, cash, window['returns'], annual_payment, mortgage_balance
                )
                if result['success']:
                    successes.append(result)

            success_rate = len(successes) / len(all_windows) * 100

            if success_rate > best_success:
                best_success = success_rate
                best_split = {
                    'stocks': stocks,
                    'cash': cash,
                    'success_rate': success_rate,
                    'avg_years': sum(r['years'] for r in successes) / len(successes) if successes else 0
                }

        reserve = 500000 - total
        print(f"${total:>6,} | {best_split['stocks']/total*100:>10.0f}% | {best_split['success_rate']:6.1f}% | "
              f"{best_split['avg_years']:9.1f} | ${reserve:,} @ 1%")

    print()
    print("NOTE: When initial deployment succeeds, you keep the entire reserve!")
    print("      When it fails, you deploy reserve (use all $500K)")
    print()


if __name__ == "__main__":
    main()
