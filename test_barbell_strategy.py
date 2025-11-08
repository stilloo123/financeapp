"""
Barbell Strategy: Buy Treasuries for Later Years, Use Stocks for Early Years

Key Insight:
- Later year treasuries are MORE expensive (need to be bought at lower PV)
- Later year treasuries lock in HIGHER rates (4.65% for 20-year)
- Early years: More flexibility, can pay off early with stocks

Smart Approach:
1. Buy treasury ladder for years 15-25 TODAY (expensive, high rates, lock them in)
2. Use stocks for years 1-14 (cheaper, flexible, can pay off early)

Benefits:
- If stocks do well: Pay off in years 8-12, never use the later treasuries (can sell them)
- If stocks crash: You have years 15-25 covered, only need to survive 14 years
- Locks in best treasury rates (long-term treasuries at 4.65%)
- Reduces upfront capital vs. full treasury ladder
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from typing import Tuple, List, Dict


def interpolate_treasury_rate(year: int, rate_points: dict) -> float:
    """Interpolate treasury rate for given year."""
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


def calculate_treasury_cost_for_years(
    annual_payment: float,
    start_year: int,
    end_year: int,
    treasury_rates: dict
) -> float:
    """Calculate cost TODAY to buy treasury ladder for years [start_year, end_year]."""
    total_cost = 0

    for year in range(start_year, end_year + 1):
        rate = interpolate_treasury_rate(year, treasury_rates) / 100.0
        discount_factor = (1 + rate) ** year
        cost_today = annual_payment / discount_factor
        total_cost += cost_today

    return total_cost


def simulate_barbell_strategy(
    initial_stock_investment: float,
    treasury_coverage_start_year: int,  # Start year of treasury coverage (e.g., 15)
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    treasury_rates: dict
) -> Dict:
    """
    Simulate barbell strategy:
    - Treasury ladder covers years [treasury_coverage_start_year, 25]
    - Stocks cover years [1, treasury_coverage_start_year - 1]

    Returns:
        Result dictionary with success, capital needed, payoff time, etc.
    """
    total_years = len(returns_sequence)

    # Cost of treasury ladder for later years
    treasury_cost = calculate_treasury_cost_for_years(
        annual_payment,
        treasury_coverage_start_year,
        total_years,
        treasury_rates
    )

    # Simulate stocks for early years
    stock_balance = initial_stock_investment
    remaining_mortgage = initial_mortgage_balance

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Make payment
        stock_balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply return
        stock_balance *= (1 + stock_return / 100.0)

        # Check for early payoff (before we need treasuries!)
        if stock_balance >= remaining_mortgage:
            # Success! Paid off early, don't even need the treasuries
            # (In reality, you could sell the treasury ladder)
            total_capital = initial_stock_investment + treasury_cost
            leftover = stock_balance - remaining_mortgage

            return {
                'success': True,
                'paid_off_early': True,
                'years_to_payoff': year,
                'stock_investment': initial_stock_investment,
                'treasury_cost': treasury_cost,
                'total_capital': total_capital,
                'leftover': leftover,
                'treasury_unused': True  # Could sell treasuries
            }

        # Check if we made it to treasury coverage years
        if year >= treasury_coverage_start_year:
            # Treasuries take over from here
            total_capital = initial_stock_investment + treasury_cost

            return {
                'success': True,
                'paid_off_early': False,
                'years_to_payoff': total_years,
                'stock_investment': initial_stock_investment,
                'treasury_cost': treasury_cost,
                'total_capital': total_capital,
                'leftover': 0,
                'treasury_unused': False,
                'treasury_kicked_in': year
            }

        # Check for failure (ran out before treasuries kick in)
        if stock_balance < 0:
            return {
                'success': False,
                'paid_off_early': False,
                'years_to_payoff': year,
                'stock_investment': initial_stock_investment,
                'treasury_cost': treasury_cost,
                'total_capital': initial_stock_investment + treasury_cost,
                'leftover': stock_balance,
                'treasury_unused': False
            }

    # Made it through all years
    total_capital = initial_stock_investment + treasury_cost
    return {
        'success': stock_balance >= 0,
        'paid_off_early': False,
        'years_to_payoff': total_years,
        'stock_investment': initial_stock_investment,
        'treasury_cost': treasury_cost,
        'total_capital': total_capital,
        'leftover': stock_balance,
        'treasury_unused': False
    }


def find_optimal_stock_amount(
    treasury_coverage_start_year: int,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    treasury_rates: dict
) -> Tuple[float, Dict]:
    """Binary search to find minimum stock investment needed."""
    low = 0.0
    high = initial_mortgage_balance
    tolerance = 100.0

    while high - low > tolerance:
        mid = (low + high) / 2.0

        result = simulate_barbell_strategy(
            mid,
            treasury_coverage_start_year,
            returns_sequence,
            annual_payment,
            initial_mortgage_balance,
            treasury_rates
        )

        if result['success']:
            high = mid  # Try less
        else:
            low = mid  # Need more

    # Final simulation
    result = simulate_barbell_strategy(
        high,
        treasury_coverage_start_year,
        returns_sequence,
        annual_payment,
        initial_mortgage_balance,
        treasury_rates
    )

    return high, result


def main():
    print("=" * 90)
    print("BARBELL STRATEGY: Treasury Ladder for Later Years + Stocks for Early Years")
    print("=" * 90)
    print()

    # Setup
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    years = 25
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, years)

    # Current treasury rates
    treasury_rates = {
        1: 3.70,
        3: 3.60,
        5: 3.71,
        10: 4.11,
        20: 4.65,
        30: 4.67
    }

    print(f"Scenario: 2000-2024 (worst crash period)")
    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}% for {years} years")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Baselines
    treasury_full = 433032
    stock_2000 = 489746

    print("Baseline Strategies:")
    print(f"  - Full Treasury Ladder: ${treasury_full:,}")
    print(f"  - 100% Stocks (2000-2024): ${stock_2000:,}")
    print()

    print("=" * 90)
    print("TESTING BARBELL STRATEGY WITH DIFFERENT SPLIT POINTS")
    print("=" * 90)
    print()

    # Test different split points
    split_points = [10, 12, 15, 18, 20]

    print("Treasury     | Treasury | Stock    | Total      | Outcome")
    print("Covers Years | Cost     | Needed   | Capital    | ")
    print("-------------|----------|----------|------------|---------------------------")

    results = {}

    for split_year in split_points:
        # Calculate treasury cost for later years
        treasury_cost = calculate_treasury_cost_for_years(
            annual_payment,
            split_year,
            years,
            treasury_rates
        )

        # Find minimum stock investment needed
        stock_needed, result = find_optimal_stock_amount(
            split_year,
            returns_2000,
            annual_payment,
            mortgage_balance,
            treasury_rates
        )

        total_capital = stock_needed + treasury_cost

        results[split_year] = {
            'treasury_cost': treasury_cost,
            'stock_needed': stock_needed,
            'total_capital': total_capital,
            'result': result
        }

        outcome = f"Years {split_year}-{years}"
        if result.get('paid_off_early'):
            outcome = f"✓ Paid off year {result['years_to_payoff']} (early!)"
        elif not result['success']:
            outcome = "✗ Failed"

        print(f"{split_year:2d}-{years:2d}       | ${treasury_cost:>7,.0f} | ${stock_needed:>7,.0f} | "
              f"${total_capital:>9,.0f} | {outcome}")

    # Find optimal
    optimal_split = min(results, key=lambda k: results[k]['total_capital'])
    optimal = results[optimal_split]

    print()
    print("=" * 90)
    print("OPTIMAL BARBELL STRATEGY")
    print("=" * 90)
    print()

    print(f"✅ Best Split Point: Years {optimal_split}-{years} covered by treasuries")
    print()
    print(f"Capital Allocation:")
    print(f"  - Treasury Ladder (years {optimal_split}-{years}): ${optimal['treasury_cost']:,.2f}")
    print(f"  - Stock Investment (years 1-{optimal_split-1}):    ${optimal['stock_needed']:,.2f}")
    print(f"  - TOTAL CAPITAL NEEDED:                ${optimal['total_capital']:,.2f}")
    print()

    savings_vs_full_treasury = treasury_full - optimal['total_capital']
    savings_vs_full_stock = stock_2000 - optimal['total_capital']

    print("Comparison:")
    print(f"  vs. Full Treasury: ${savings_vs_full_treasury:+,.2f}")
    print(f"  vs. Full Stocks:   ${savings_vs_full_stock:+,.2f}")
    print()

    if optimal['total_capital'] < treasury_full:
        print("🎯 BARBELL STRATEGY WINS!")
        print()
        print(f"Savings: ${savings_vs_full_treasury:,.2f} vs. full treasury ladder")
        print()
        print("How it works:")
        print(f"  1. Buy treasuries for years {optimal_split}-{years} TODAY (${optimal['treasury_cost']:,.0f})")
        print(f"  2. Invest ${optimal['stock_needed']:,.0f} in stocks for years 1-{optimal_split-1}")
        print(f"  3. If stocks do well: Pay off early, sell unused treasuries")
        print(f"  4. If stocks crash: Treasuries kick in at year {optimal_split}, guaranteed payoff")
        print()
        print("Benefits:")
        print(f"  ✓ Save ${savings_vs_full_treasury:,.0f} vs. full treasury")
        print("  ✓ Lock in high long-term treasury rates (4.65%)")
        print("  ✓ Keep stock upside potential for early payoff")
        print("  ✓ Guaranteed safety net from year " + str(optimal_split))
    else:
        print("Full treasury ladder is still optimal for this scenario")

    print()


if __name__ == "__main__":
    main()
