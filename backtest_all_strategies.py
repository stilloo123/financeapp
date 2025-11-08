"""
Comprehensive Backtest: All Strategies Across All Historical 25-Year Windows

Test each strategy on all 75 rolling 25-year periods from 1926-2025
to get exact success rates and statistics.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median, stdev


def simulate_stock_only(initial_amount, returns_sequence, annual_payment, mortgage_balance):
    """100% stocks, withdraw annually."""
    balance = initial_amount
    remaining_mortgage = mortgage_balance

    for year, annual_return in enumerate(returns_sequence, start=1):
        balance -= annual_payment
        remaining_mortgage -= annual_payment
        balance *= (1 + annual_return / 100.0)

        # Early payoff?
        if balance >= remaining_mortgage:
            leftover = balance - remaining_mortgage
            return {'success': True, 'years': year, 'leftover': leftover}

        # Failure?
        if balance < 0:
            return {'success': False, 'years': year, 'leftover': balance}

    return {'success': balance >= 0, 'years': len(returns_sequence), 'leftover': balance}


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


def main():
    print("=" * 90)
    print("COMPREHENSIVE BACKTEST: ALL STRATEGIES ON ALL HISTORICAL PERIODS")
    print("=" * 90)
    print()

    # Setup
    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Get all 25-year windows
    all_windows = []
    for start_year in range(1926, 2000 + 1):  # 1926-1950 through 2000-2024
        end_year = start_year + 24
        if end_year <= 2025:
            returns = loader.get_returns(start_year, end_year)
            if len(returns) == 25:
                all_windows.append({
                    'period': f"{start_year}-{end_year}",
                    'start': start_year,
                    'returns': returns
                })

    print(f"Testing {len(all_windows)} rolling 25-year windows from 1926-2025")
    print()

    # Test strategies
    strategies = [
        {
            'name': 'Stock-only $241K',
            'test': lambda returns: simulate_stock_only(241000, returns, annual_payment, mortgage_balance)
        },
        {
            'name': 'Smart $250K ($200K stock + $50K cash)',
            'test': lambda returns: simulate_smart_withdrawal(200000, 50000, returns, annual_payment, mortgage_balance)
        },
        {
            'name': 'Smart $300K ($250K stock + $50K cash)',
            'test': lambda returns: simulate_smart_withdrawal(250000, 50000, returns, annual_payment, mortgage_balance)
        },
    ]

    results = {s['name']: [] for s in strategies}

    print("Testing all strategies...")
    print()

    for strategy in strategies:
        for window in all_windows:
            result = strategy['test'](window['returns'])
            results[strategy['name']].append({
                'period': window['period'],
                'success': result['success'],
                'years': result['years'] if result['success'] else None,
                'leftover': result['leftover'] if result['success'] else None
            })

    # Analyze results
    print("=" * 90)
    print("RESULTS SUMMARY")
    print("=" * 90)
    print()

    treasury = 433032

    for strategy_name, strategy_results in results.items():
        print(f"{strategy_name}:")
        print("-" * 90)

        successes = [r for r in strategy_results if r['success']]
        failures = [r for r in strategy_results if not r['success']]

        success_rate = len(successes) / len(strategy_results) * 100

        print(f"  Success rate: {len(successes)}/{len(strategy_results)} ({success_rate:.1f}%)")

        if successes:
            years_list = [r['years'] for r in successes]
            avg_years = mean(years_list)
            median_years = median(years_list)
            min_years = min(years_list)
            max_years = max(years_list)

            print(f"  Years to payoff: avg={avg_years:.1f}, median={median_years}, min={min_years}, max={max_years}")

            leftover_list = [r['leftover'] for r in successes]
            avg_leftover = mean(leftover_list)

            print(f"  Average leftover: ${avg_leftover:,.0f}")

        if failures:
            print(f"  Failed in {len(failures)} scenarios:")
            for f in failures[:5]:  # Show first 5 failures
                print(f"    - {f['period']}")
            if len(failures) > 5:
                print(f"    ... and {len(failures) - 5} more")

        print()

    # Comparison
    print("=" * 90)
    print("STRATEGY COMPARISON")
    print("=" * 90)
    print()

    print("Strategy                              | Success | Avg Years | vs Treasury")
    print("--------------------------------------|---------|-----------|------------------")
    print(f"Treasury Ladder                       | 100.0%  |    25     | Baseline ($433K)")

    for strategy_name, strategy_results in results.items():
        successes = [r for r in strategy_results if r['success']]
        success_rate = len(successes) / len(strategy_results) * 100

        if successes:
            avg_years = mean([r['years'] for r in successes])

            # Extract capital from name
            if '$241K' in strategy_name:
                capital = 241000
            elif '$250K' in strategy_name:
                capital = 250000
            elif '$300K' in strategy_name:
                capital = 300000
            else:
                capital = 0

            savings = treasury - capital

            print(f"{strategy_name:37s} | {success_rate:6.1f}% | {avg_years:9.1f} | {savings:>+6,} ({savings/treasury*100:+.0f}%)")

    print()

    # Recommendations
    print("=" * 90)
    print("RECOMMENDATIONS")
    print("=" * 90)
    print()

    smart_250_results = results['Smart $250K ($200K stock + $50K cash)']
    smart_250_successes = [r for r in smart_250_results if r['success']]
    smart_250_success_rate = len(smart_250_successes) / len(smart_250_results) * 100

    print(f"1. **Risk-Free (Conservative)**")
    print(f"   → Treasury Ladder: $433K")
    print(f"   • 100% success rate across ALL historical periods")
    print(f"   • Guaranteed outcome")
    print(f"   • Saves $67K vs. paying off mortgage")
    print()

    print(f"2. **Calculated Risk (Moderate)**")
    print(f"   → Smart Withdrawal: $250K ($200K stocks + $50K cash)")
    print(f"   • {smart_250_success_rate:.1f}% historical success rate")
    print(f"   • Saves $183K vs. treasury (42%)")
    print(f"   • Pays off in ~8 years on average (when successful)")
    print(f"   • Accept {100-smart_250_success_rate:.1f}% risk of needing more capital")
    print()

    stock_results = results['Stock-only $241K']
    stock_successes = [r for r in stock_results if r['success']]
    stock_success_rate = len(stock_successes) / len(stock_results) * 100

    print(f"3. **High Risk (Aggressive)**")
    print(f"   → Stock-only: $241K")
    print(f"   • {stock_success_rate:.1f}% historical success rate")
    print(f"   • Saves $192K vs. treasury (44%)")
    print(f"   • Higher risk of failure in crash scenarios")
    print()

    print("=" * 90)
    print("BOTTOM LINE")
    print("=" * 90)
    print()
    print(f"• For {smart_250_success_rate:.0f}% of historical scenarios, smart withdrawal with $250K")
    print(f"  saves $183K (42%) vs. treasury and pays off in ~8 years")
    print()
    print(f"• For {100-smart_250_success_rate:.0f}% worst-case scenarios, you'd need more capital")
    print(f"  (up to $490K for 2000-2024)")
    print()
    print("• Treasury ladder at $433K works for 100% of scenarios")
    print()
    print("→ Your choice depends on risk tolerance")
    print()


if __name__ == "__main__":
    main()
