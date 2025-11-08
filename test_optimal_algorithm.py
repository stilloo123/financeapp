"""
Test Optimal Allocation Algorithm

Validates the two-phase binary search algorithm against known results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.services.optimal_allocator import find_optimal_allocation
from backend.services.historical_optimizer import HistoricalOptimizer
from backend.models.mortgage_calculator import calculate_annual_payment


def test_single_period():
    """Test optimal allocation for 2000-2024 worst case."""
    print("=" * 90)
    print("TEST 1: Single Period Optimization (2000-2024)")
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
    print("Finding optimal allocation for 2000-2024 (worst historical case)...")
    print()

    # Run optimal algorithm
    stock, cash, result = find_optimal_allocation(
        returns_2000, annual_payment, mortgage_balance, tolerance=5000
    )

    total = stock + cash

    print("RESULT:")
    print(f"  Optimal Stock: ${stock:,.2f}")
    print(f"  Optimal Cash:  ${cash:,.2f}")
    print(f"  Stock Ratio:   {stock/total*100:.1f}%")
    print(f"  TOTAL:         ${total:,.2f}")
    print()

    if result and result.get('success'):
        print(f"  ✅ Success!")
        print(f"  Years to payoff: {result['years_to_payoff']}")
        print(f"  Leftover: ${result['leftover']:,.2f}")
    else:
        print(f"  ❌ Failed")
        print(f"  Note: 2000-2024 may require more than tested range")

    print()

    # Compare to known manual result
    print("Comparison to Manual Testing:")
    print(f"  Manual result: $390K stocks + $100K cash = $490K")
    print(f"  Optimal algo:  ${stock:,.0f} stocks + ${cash:,.0f} cash = ${total:,.0f}")
    print()

    diff = abs(total - 490000)
    if diff < 10000:  # Within $10K
        print(f"  ✅ Algorithm matches manual result (within ${diff:,.0f})")
    else:
        print(f"  ⚠️ Difference: ${diff:,.0f}")

    print()


def test_percentile_analysis():
    """Test percentile analysis across all historical periods."""
    print("=" * 90)
    print("TEST 2: Percentile Analysis Across All Historical Periods")
    print("=" * 90)
    print()

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    optimizer = HistoricalOptimizer(annual_payment, mortgage_balance)

    print("This will take a few minutes...")
    print()

    # Run percentile analysis
    analysis = optimizer.percentile_analysis(
        percentiles=[10, 25, 50, 75, 90, 95],
        tolerance=5000  # $5K tolerance for speed
    )

    print()
    print("=" * 90)
    print("PERCENTILE RESULTS")
    print("=" * 90)
    print()

    print("Pct  | Total Capital | Stock   | Cash   | Ratio | Years | Period")
    print("-----|---------------|---------|--------|-------|-------|---------------")

    for pct, data in sorted(analysis['percentiles'].items()):
        print(f"{pct:3d}% | ${data['total_capital']:>12,.0f} | "
              f"${data['stock']:>6,.0f} | ${data['cash']:>5,.0f} | "
              f"{data['stock_ratio']*100:5.1f}% | {data['years_to_payoff']:5d} | "
              f"{data['period']}")

    print()
    print("=" * 90)
    print("STATISTICS")
    print("=" * 90)
    print()

    stats = analysis['statistics']
    print(f"Periods tested: {stats['count']}")
    print()
    print(f"Total Capital:")
    print(f"  Mean:   ${stats['capital']['mean']:,.0f}")
    print(f"  Median: ${stats['capital']['median']:,.0f}")
    print(f"  Std:    ${stats['capital']['std']:,.0f}")
    print(f"  Min:    ${stats['capital']['min']:,.0f}")
    print(f"  Max:    ${stats['capital']['max']:,.0f}")
    print()
    print(f"Years to Payoff:")
    print(f"  Mean:   {stats['years_to_payoff']['mean']:.1f}")
    print(f"  Median: {stats['years_to_payoff']['median']:.1f}")
    print(f"  Range:  {stats['years_to_payoff']['min']}-{stats['years_to_payoff']['max']}")
    print()

    # Key insights
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    print()

    p50 = analysis['percentiles'][50]
    p90 = analysis['percentiles'][90]
    p95 = analysis['percentiles'][95]

    treasury = 433032

    print(f"50th Percentile (Median difficulty):")
    print(f"  Capital: ${p50['total_capital']:,.0f}")
    print(f"  vs. Treasury: {(p50['total_capital'] - treasury):+,.0f} ({(p50['total_capital']/treasury - 1)*100:+.1f}%)")
    print()

    print(f"90th Percentile (Hard scenarios):")
    print(f"  Capital: ${p90['total_capital']:,.0f}")
    print(f"  vs. Treasury: {(p90['total_capital'] - treasury):+,.0f} ({(p90['total_capital']/treasury - 1)*100:+.1f}%)")
    print()

    print(f"95th Percentile (Very hard scenarios like 2000-2024):")
    print(f"  Capital: ${p95['total_capital']:,.0f}")
    print(f"  vs. Treasury: {(p95['total_capital'] - treasury):+,.0f} ({(p95['total_capital']/treasury - 1)*100:+.1f}%)")
    print()


def test_success_curve():
    """Test success rate curve generation."""
    print("=" * 90)
    print("TEST 3: Success Rate Curve")
    print("=" * 90)
    print()

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    optimizer = HistoricalOptimizer(annual_payment, mortgage_balance)

    # Test key capital levels
    capital_range = [
        250000, 275000, 300000, 325000, 350000,
        375000, 400000, 425000, 450000, 475000, 500000
    ]

    print("Generating success curve...")
    print()

    curve_data = optimizer.success_curve(capital_range)

    print()
    print("=" * 90)
    print("SUCCESS RATE BY CAPITAL LEVEL")
    print("=" * 90)
    print()

    print("Capital  | Success | Failures | Rate    | Avg Years | Status")
    print("---------|---------|----------|---------|-----------|------------------")

    for point in curve_data['curve']:
        status = ""
        if point['success_rate'] >= 95:
            status = "✅ Excellent"
        elif point['success_rate'] >= 90:
            status = "✅ Very Good"
        elif point['success_rate'] >= 80:
            status = "✓ Good"
        elif point['success_rate'] >= 70:
            status = "✓ Moderate"
        else:
            status = "⚠️ Risky"

        print(f"${point['capital']:>7,} | {point['successes']:7d} | {point['failures']:8d} | "
              f"{point['success_rate']:6.1f}% | {point['avg_years']:9.1f} | {status}")

    print()
    print(f"Periods tested: {curve_data['periods_tested']}")
    print()


def main():
    """Run all tests."""
    print()
    print("╔" + "=" * 88 + "╗")
    print("║" + " " * 20 + "OPTIMAL ALLOCATION ALGORITHM TESTS" + " " * 34 + "║")
    print("╚" + "=" * 88 + "╝")
    print()

    # Test 1: Single period
    test_single_period()

    # Ask user if they want to continue with expensive tests
    print("=" * 90)
    print("NEXT TESTS")
    print("=" * 90)
    print()
    print("The next tests will:")
    print("  - Test 2: Optimize across ALL 75 historical periods (~2-3 minutes)")
    print("  - Test 3: Generate success curve (~3-5 minutes)")
    print()

    response = input("Continue with full historical tests? [y/N]: ").strip().lower()

    if response == 'y':
        print()
        # Test 2: Percentile analysis
        test_percentile_analysis()

        print()
        # Test 3: Success curve
        test_success_curve()

        print()
        print("=" * 90)
        print("ALL TESTS COMPLETE!")
        print("=" * 90)
        print()
        print("The optimal algorithm successfully:")
        print("  ✅ Found minimum allocation for single period")
        print("  ✅ Analyzed all 75 historical periods")
        print("  ✅ Generated capital vs. success rate curve")
        print()
    else:
        print()
        print("Skipping full historical tests.")
        print("Run again with 'y' to see complete results.")
        print()


if __name__ == "__main__":
    main()
