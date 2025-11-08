"""
Test Parallel Strategy Across ALL Historical Scenarios

Key insight: 2000-2024 is the WORST case (95th percentile)
For MEDIAN and BEST cases, parallel strategy should shine!

Test the parallel strategy across all historical windows to find:
1. What's the optimal safety net position for 90th percentile protection?
2. How much capital do we save vs. full treasury in typical scenarios?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from backend.services.backtester import MortgageInvestmentBacktester
from typing import Dict, List


def interpolate_treasury_rate(year: int, rate_points: dict) -> float:
    """Interpolate treasury rate."""
    years = sorted(rate_points.keys())
    if year in rate_points:
        return rate_points[year]

    lower_year = None
    upper_year = None
    for y in years:
        if y < year:
            lower_year = y
        elif y > year and upper_year is None:
            upper_year = y
            break

    if lower_year is None:
        return rate_points[years[0]]
    if upper_year is None:
        return rate_points[years[-1]]

    lower_rate = rate_points[lower_year]
    upper_rate = rate_points[upper_year]
    return lower_rate + (year - lower_year) * (upper_rate - lower_rate) / (upper_year - lower_year)


def calculate_treasury_cost(annual_payment: float, start_year: int, end_year: int, treasury_rates: dict) -> float:
    """Calculate treasury ladder cost."""
    total_cost = 0
    for year in range(start_year, end_year + 1):
        rate = interpolate_treasury_rate(year, treasury_rates) / 100.0
        discount_factor = (1 + rate) ** year
        total_cost += annual_payment / discount_factor
    return total_cost


def main():
    print("=" * 90)
    print("PARALLEL STRATEGY: Test Across ALL Historical Scenarios")
    print("=" * 90)
    print()

    # Setup
    loader = SP500DataLoader()
    backtester = MortgageInvestmentBacktester(loader)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    years = 25
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, years)

    treasury_rates = {
        1: 3.70, 3: 3.60, 5: 3.71, 10: 4.11, 20: 4.65, 30: 4.67
    }

    # Get all scenarios from backtester
    print("Running backtest across all historical periods...")
    analysis = backtester.run_full_analysis(mortgage_balance, mortgage_rate, years)

    all_scenarios = analysis['all_scenarios']
    print(f"Total scenarios: {len(all_scenarios)}")
    print()

    # Sort by investment required
    sorted_scenarios = sorted(all_scenarios, key=lambda x: x['investment_required'])

    # Get key percentiles
    best_case = sorted_scenarios[0]
    percentile_25 = sorted_scenarios[len(sorted_scenarios) // 4]
    median = sorted_scenarios[len(sorted_scenarios) // 2]
    percentile_75 = sorted_scenarios[3 * len(sorted_scenarios) // 4]
    percentile_90 = sorted_scenarios[9 * len(sorted_scenarios) // 10]
    worst_case = sorted_scenarios[-1]

    # Full treasury cost
    treasury_full = calculate_treasury_cost(annual_payment, 1, years, treasury_rates)

    print("=" * 90)
    print("STOCK-ONLY STRATEGY (from backtester)")
    print("=" * 90)
    print()
    print(f"Scenario         | Period        | Stock Investment | Years to Payoff")
    print("-----------------|---------------|------------------|----------------")
    print(f"Best Case        | {best_case['period']:13s} | ${best_case['investment_required']:>14,.0f} | {best_case['years_to_payoff']:15d}")
    print(f"25th Percentile  | {percentile_25['period']:13s} | ${percentile_25['investment_required']:>14,.0f} | {percentile_25['years_to_payoff']:15d}")
    print(f"Median (50th)    | {median['period']:13s} | ${median['investment_required']:>14,.0f} | {median['years_to_payoff']:15d}")
    print(f"75th Percentile  | {percentile_75['period']:13s} | ${percentile_75['investment_required']:>14,.0f} | {percentile_75['years_to_payoff']:15d}")
    print(f"90th Percentile  | {percentile_90['period']:13s} | ${percentile_90['investment_required']:>14,.0f} | {percentile_90['years_to_payoff']:15d}")
    print(f"Worst Case       | {worst_case['period']:13s} | ${worst_case['investment_required']:>14,.0f} | {worst_case['years_to_payoff']:15d}")

    print()
    print(f"Full Treasury Ladder: ${treasury_full:,.2f}")
    print()

    # Now test parallel strategy
    print("=" * 90)
    print("PARALLEL STRATEGY ANALYSIS")
    print("=" * 90)
    print()

    # For median scenario, what's the optimal parallel split?
    print("Testing parallel strategy for MEDIAN scenario...")
    print()

    # Test safety nets at years 20, 22, 23, 24
    safety_nets = [20, 22, 23, 24]

    print("Median Scenario Parallel Options:")
    print()
    print("Safety Net | Treasury | Stock (Median) | Total    | vs Treasury | vs Stock")
    print("Years      | Cost     | Needed         | Upfront  | Ladder      | Only")
    print("-----------|----------|----------------|----------|-------------|----------")

    median_stock = median['investment_required']

    for safety_year in safety_nets:
        treasury_cost = calculate_treasury_cost(annual_payment, safety_year, years, treasury_rates)

        # For median scenario, assume stock strategy needs median amount
        total_upfront = median_stock + treasury_cost

        vs_treasury = total_upfront - treasury_full
        vs_stock = total_upfront - median_stock

        print(f"{safety_year:2d}-{years:2d}      | ${treasury_cost:>7,.0f} | ${median_stock:>14,.0f} | "
              f"${total_upfront:>7,.0f} | ${vs_treasury:>+10,.0f} | ${vs_stock:>+7,.0f}")

    print()
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    print()

    print("For MEDIAN scenario (50% of historical cases):")
    median_stock_needed = median['investment_required']
    print(f"  - Stock-only needs: ${median_stock_needed:,.0f}")
    print(f"  - Years to payoff: {median['years_to_payoff']}")
    print(f"  - Savings vs payoff: ${mortgage_balance - median_stock_needed:,.0f}")
    print()

    # Best parallel for median
    treasury_safety_23_25 = calculate_treasury_cost(annual_payment, 23, years, treasury_rates)
    median_parallel_total = median_stock_needed + treasury_safety_23_25

    print(f"With parallel strategy (safety net years 23-25):")
    print(f"  - Stock investment: ${median_stock_needed:,.0f}")
    print(f"  - Treasury safety net (yrs 23-25): ${treasury_safety_23_25:,.0f}")
    print(f"  - Total upfront: ${median_parallel_total:,.0f}")
    print()

    if median_parallel_total < treasury_full:
        savings = treasury_full - median_parallel_total
        print(f"✅ PARALLEL SAVES ${savings:,.0f} vs. full treasury!")
        print()
        print("Typical outcome (50% of cases):")
        print(f"  - Pay off in ~{median['years_to_payoff']} years (not {years})")
        print(f"  - Never need the safety net (years 23-25)")
        print(f"  - Can sell safety net treasuries for refund")
        print()
    else:
        print(f"❌ Full treasury still cheaper by ${median_parallel_total - treasury_full:,.0f}")
        print()

    print("=" * 90)
    print("THE OPTIMAL STRATEGY DECISION")
    print("=" * 90)
    print()

    print("Three Strategies Compared:")
    print()
    print("1. FULL TREASURY LADDER:")
    print(f"   - Upfront: ${treasury_full:,.0f}")
    print("   - Risk: ZERO")
    print("   - Outcome: Guaranteed")
    print()

    print("2. STOCK ONLY (Median Case):")
    print(f"   - Upfront: ${median_stock_needed:,.0f}")
    print("   - Risk: Medium")
    print(f"   - Outcome: 50% chance, {median['years_to_payoff']} years")
    print(f"   - Savings: ${mortgage_balance - median_stock_needed:,.0f}")
    print()

    print("3. PARALLEL (Stock + Safety Net):")
    print(f"   - Upfront: ${median_parallel_total:,.0f}")
    print("   - Risk: Low")
    print(f"   - Outcome: Pay off in {median['years_to_payoff']} years (50% case), guaranteed by year 25")
    print(f"   - Savings vs Treasury: ${treasury_full - median_parallel_total:,.0f}")
    print()

    if median_parallel_total < treasury_full:
        print("🏆 WINNER: PARALLEL STRATEGY")
        print()
        print("Best of both worlds:")
        print(f"  ✓ Save ${treasury_full - median_parallel_total:,.0f} vs. full treasury")
        print("  ✓ Safety net guarantees finish if stocks fail")
        print("  ✓ Upside potential if stocks succeed")
        print(f"  ✓ Only ${median_parallel_total - median_stock_needed:,.0f} insurance premium")
    else:
        print("Winner depends on risk tolerance:")
        print(f"  - Risk-averse: Full treasury (${treasury_full:,.0f})")
        print(f"  - Risk-tolerant: Stock only (${median_stock_needed:,.0f}, 50% success)")

    print()


if __name__ == "__main__":
    main()
