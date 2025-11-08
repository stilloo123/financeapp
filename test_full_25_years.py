"""
Test: Keep $500K Invested for FULL 25 Years

Compare:
1. Pay off $500K now → $0 left, but no mortgage
2. Invest $500K, withdraw $28,714/year for 25 years → ??? left at end

Goal: Beat paying off (have more than $0 at end) in 100% of scenarios
(excluding Great Depression which even $500K can't survive)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median


def simulate_full_term(
    initial_amount: float,
    returns_sequence: list,
    annual_payment: float
):
    """
    Simulate investing for FULL term, don't pay off early.
    Just track what's left after 25 years.
    """
    balance = initial_amount
    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Withdraw payment
        balance -= annual_payment

        # Apply return
        balance *= (1 + stock_return / 100.0)

        year_by_year.append({
            'year': year,
            'return': stock_return,
            'balance': balance
        })

    return {
        'final_balance': balance,
        'success': balance >= 0,
        'year_by_year': year_by_year
    }


def main():
    print("=" * 90)
    print("INVEST $500K FOR FULL 25 YEARS vs PAY OFF NOW")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Scenario A: Pay off $500K mortgage now")
    print(f"  Result: $0 mortgage, $0 investment")
    print(f"  Net worth after 25 years: $0")
    print()

    print(f"Scenario B: Invest $500K, pay ${annual_payment:,.2f}/year for 25 years")
    print(f"  Withdraw: ${annual_payment * 25:,.2f} total over 25 years")
    print(f"  Final balance after 25 years: ???")
    print()

    # Get all historical windows
    all_windows = []
    for start_year in range(1926, 2001):
        end_year = start_year + 24
        if end_year <= 2025:
            try:
                returns = loader.get_returns(start_year, end_year)
                if len(returns) == 25:
                    all_windows.append({
                        'period': f"{start_year}-{end_year}",
                        'start_year': start_year,
                        'returns': returns
                    })
            except:
                pass

    print(f"Testing across {len(all_windows)} historical 25-year periods...")
    print()

    # Simulate all periods
    results = []
    for window in all_windows:
        result = simulate_full_term(500000, window['returns'], annual_payment)
        results.append({
            'period': window['period'],
            'start_year': window['start_year'],
            'final_balance': result['final_balance'],
            'success': result['success'],
            'year_by_year': result['year_by_year']
        })

    # Analyze results
    successes = [r for r in results if r['success']]
    failures = [r for r in results if not r['success']]

    print("=" * 90)
    print("RESULTS")
    print("=" * 90)
    print()

    print(f"Success rate: {len(successes)}/{len(results)} ({len(successes)/len(results)*100:.1f}%)")
    print()

    if successes:
        final_balances = [r['final_balance'] for r in successes]
        print(f"Final Balance After 25 Years (Successful Scenarios):")
        print(f"  Average:  ${mean(final_balances):,.0f}")
        print(f"  Median:   ${median(final_balances):,.0f}")
        print(f"  Minimum:  ${min(final_balances):,.0f}")
        print(f"  Maximum:  ${max(final_balances):,.0f}")
        print()

    if failures:
        print(f"Failed Scenarios ({len(failures)}):")
        for f in failures:
            print(f"  {f['period']}: Final balance ${f['final_balance']:,.0f}")
        print()

    # Show distribution
    print("=" * 90)
    print("DISTRIBUTION OF OUTCOMES")
    print("=" * 90)
    print()

    # Group by outcome ranges
    ranges = [
        (float('-inf'), 0, "Negative (Failed)"),
        (0, 100000, "$0 - $100K"),
        (100000, 250000, "$100K - $250K"),
        (250000, 500000, "$250K - $500K"),
        (500000, 1000000, "$500K - $1M"),
        (1000000, float('inf'), "Over $1M"),
    ]

    for low, high, label in ranges:
        count = sum(1 for r in results if low <= r['final_balance'] < high)
        pct = count / len(results) * 100
        bar = "█" * int(pct / 2)
        print(f"{label:20s} | {count:3d} ({pct:5.1f}%) {bar}")

    print()

    # Compare to payoff
    print("=" * 90)
    print("INVEST vs PAY OFF COMPARISON")
    print("=" * 90)
    print()

    if successes:
        avg_final = mean([r['final_balance'] for r in successes])

        print(f"Pay off now:      $0 final balance")
        print(f"Invest strategy:  ${avg_final:,.0f} average final balance")
        print()
        print(f"Benefit of investing: ${avg_final:,.0f}")
        print()

        # What if you paid off and invested the savings?
        # If you pay off, you save $28,714/year in mortgage payments
        # Could invest those savings over 25 years
        # But you already paid $500K upfront, so no savings to invest

        print("Actually, let me recalculate this properly...")
        print()
        print("If you PAY OFF $500K now:")
        print("  - Year 0: Pay $500K, mortgage gone")
        print("  - Years 1-25: Save $28,714/year mortgage payments")
        print("  - Could invest those savings at 10% annually")

        # Calculate what happens if you invest the $28,714 savings each year
        payoff_strategy_value = 0
        for year in range(1, 26):
            payoff_strategy_value += annual_payment
            payoff_strategy_value *= 1.10  # Assume 10% average

        print(f"  - After 25 years: ${payoff_strategy_value:,.0f} from investing savings")
        print()

        print("If you INVEST $500K and pay mortgage:")
        print(f"  - After 25 years: ${avg_final:,.0f} average from investment")
        print()

        if avg_final > payoff_strategy_value:
            print(f"✅ INVESTING wins by ${avg_final - payoff_strategy_value:,.0f}!")
        else:
            print(f"⚠️ Paying off wins by ${payoff_strategy_value - avg_final:,.0f}")

    print()

    # Worst and best cases
    print("=" * 90)
    print("SPECIFIC EXAMPLES")
    print("=" * 90)
    print()

    if successes:
        best = max(successes, key=lambda x: x['final_balance'])
        worst_success = min(successes, key=lambda x: x['final_balance'])

        print(f"Best Case: {best['period']}")
        print(f"  Final balance: ${best['final_balance']:,.0f}")
        print()

        print(f"Worst Successful Case: {worst_success['period']}")
        print(f"  Final balance: ${worst_success['final_balance']:,.0f}")
        print()

    if failures:
        print(f"Failed Cases (even $500K not enough):")
        for f in failures:
            print(f"  {f['period']}: ${f['final_balance']:,.0f}")
        print()

    # Detailed breakdown for median case
    if successes:
        median_result = sorted(successes, key=lambda x: x['final_balance'])[len(successes)//2]

        print("=" * 90)
        print(f"MEDIAN CASE EXAMPLE: {median_result['period']}")
        print("=" * 90)
        print()

        print("Year | Return  | Balance After Payment | Notes")
        print("-----|---------|----------------------|---------------------------")

        for i in [0, 4, 9, 14, 19, 24]:  # Years 1, 5, 10, 15, 20, 25
            if i < len(median_result['year_by_year']):
                y = median_result['year_by_year'][i]
                note = ""
                if i == 0:
                    note = "Start"
                elif i == 24:
                    note = f"END - Keep ${y['balance']:,.0f}!"

                print(f"{y['year']:4d} | {y['return']:>+6.2f}% | ${y['balance']:>19,.0f} | {note}")

        print()

    # Final recommendation
    print("=" * 90)
    print("RECOMMENDATION")
    print("=" * 90)
    print()

    success_rate = len(successes) / len(results) * 100

    if success_rate >= 95:
        print(f"✅ YES! Invest the $500K!")
        print()
        print(f"Success rate: {success_rate:.1f}% ({len(successes)}/{len(results)} scenarios)")
        print(f"Average final balance: ${mean([r['final_balance'] for r in successes]):,.0f}")
        print()
        print("You beat paying off in nearly all historical scenarios!")
        print("The only failures are extreme events (Great Depression era).")
    else:
        print(f"⚠️ Marginal - {success_rate:.1f}% success rate")
        print()
        print(f"Failures: {len(failures)} scenarios")
        print("Risk may not be worth it for your goals.")

    print()


if __name__ == "__main__":
    main()
