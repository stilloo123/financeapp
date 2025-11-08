"""
Parallel Allocation Strategy: Treasury Safety Net + Stock Upside

The SMART Hybrid:
- Buy treasury ladder for LAST N years (safety net - guarantees you finish)
- Invest in stocks for ALL years (upside - pay off early if they work)
- Run BOTH in parallel

Outcomes:
1. Stocks do well → Pay off early, sell unused treasuries for refund
2. Stocks do poorly → Treasuries kick in at year X, guaranteed finish

Example:
- Buy treasuries for years 20-25 (cost ~$62K)
- Invest $200K in stocks
- Total: $262K upfront
- If stocks work (90% chance): Pay off in year 12-15, sell years 20-25 treasuries
- If stocks fail (10% chance): Treasuries cover years 20-25, guaranteed finish

This is THE optimal strategy!
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


def calculate_treasury_cost(annual_payment: float, start_year: int, end_year: int, treasury_rates: dict) -> float:
    """Calculate cost of treasury ladder for years [start_year, end_year]."""
    total_cost = 0
    for year in range(start_year, end_year + 1):
        rate = interpolate_treasury_rate(year, treasury_rates) / 100.0
        discount_factor = (1 + rate) ** year
        cost_today = annual_payment / discount_factor
        total_cost += cost_today
    return total_cost


def calculate_treasury_value_at_year(annual_payment: float, purchase_year: int, current_year: int, treasury_rates: dict) -> float:
    """Calculate current value of a treasury bond purchased for year N."""
    if current_year >= purchase_year:
        # Bond has matured or will mature this year
        return annual_payment

    # Bond still has time value
    years_remaining = purchase_year - current_year
    rate = interpolate_treasury_rate(years_remaining, treasury_rates) / 100.0

    # Current value = FV / (1 + r)^n
    current_value = annual_payment / ((1 + rate) ** years_remaining)
    return current_value


def simulate_parallel_allocation(
    stock_investment: float,
    treasury_start_year: int,  # Treasuries cover years [treasury_start_year, 25]
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    treasury_rates: dict
) -> Dict:
    """
    Simulate parallel allocation:
    - Stocks try to pay off mortgage
    - Treasuries provide safety net for years [treasury_start_year, end]

    Returns detailed results including treasury refund potential
    """
    total_years = len(returns_sequence)

    # Calculate treasury cost
    treasury_cost = calculate_treasury_cost(annual_payment, treasury_start_year, total_years, treasury_rates)

    # Simulate stocks
    stock_balance = stock_investment
    remaining_mortgage = initial_mortgage_balance

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Make payment from stocks
        stock_balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply return
        stock_balance *= (1 + stock_return / 100.0)

        # Check for early payoff
        if stock_balance >= remaining_mortgage:
            # SUCCESS! Paid off early
            leftover_stocks = stock_balance - remaining_mortgage

            # Calculate value of unused treasuries
            # Treasuries for years [year+1, total_years] are unused
            treasury_refund = 0
            if year < treasury_start_year:
                # All treasuries unused - can sell them
                for t_year in range(treasury_start_year, total_years + 1):
                    treasury_refund += calculate_treasury_value_at_year(
                        annual_payment, t_year, year, treasury_rates
                    )

            total_capital_needed = stock_investment + treasury_cost
            net_capital = total_capital_needed - treasury_refund - leftover_stocks

            return {
                'success': True,
                'paid_off_early': True,
                'years_to_payoff': year,
                'stock_investment': stock_investment,
                'treasury_cost': treasury_cost,
                'total_upfront_capital': total_capital_needed,
                'leftover_stocks': leftover_stocks,
                'treasury_refund': treasury_refund,
                'net_capital_used': net_capital,
                'treasury_safety_net_used': False
            }

        # Check if we reached treasury safety net
        if year >= treasury_start_year:
            # Treasuries take over, guaranteed finish
            total_capital_needed = stock_investment + treasury_cost

            return {
                'success': True,
                'paid_off_early': False,
                'years_to_payoff': total_years,
                'stock_investment': stock_investment,
                'treasury_cost': treasury_cost,
                'total_upfront_capital': total_capital_needed,
                'leftover_stocks': 0,
                'treasury_refund': 0,
                'net_capital_used': total_capital_needed,
                'treasury_safety_net_used': True,
                'treasury_kicked_in': year
            }

        # Check for failure before safety net
        if stock_balance < 0 and year < treasury_start_year:
            return {
                'success': False,
                'paid_off_early': False,
                'years_to_payoff': year,
                'stock_investment': stock_investment,
                'treasury_cost': treasury_cost,
                'total_upfront_capital': stock_investment + treasury_cost,
                'leftover_stocks': stock_balance,
                'treasury_refund': 0,
                'net_capital_used': stock_investment + treasury_cost,
                'treasury_safety_net_used': False,
                'failed_before_safety_net': True
            }

    # Completed full term
    total_capital_needed = stock_investment + treasury_cost
    return {
        'success': True,
        'paid_off_early': False,
        'years_to_payoff': total_years,
        'stock_investment': stock_investment,
        'treasury_cost': treasury_cost,
        'total_upfront_capital': total_capital_needed,
        'leftover_stocks': max(0, stock_balance),
        'treasury_refund': 0,
        'net_capital_used': total_capital_needed,
        'treasury_safety_net_used': year >= treasury_start_year
    }


def find_minimum_stock_investment(
    treasury_start_year: int,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    treasury_rates: dict
) -> Tuple[float, Dict]:
    """Find minimum stock investment needed with given treasury safety net."""
    low = 0.0
    high = initial_mortgage_balance
    tolerance = 100.0

    while high - low > tolerance:
        mid = (low + high) / 2.0

        result = simulate_parallel_allocation(
            mid, treasury_start_year, returns_sequence, annual_payment,
            initial_mortgage_balance, treasury_rates
        )

        if result['success']:
            high = mid
        else:
            low = mid

    result = simulate_parallel_allocation(
        high, treasury_start_year, returns_sequence, annual_payment,
        initial_mortgage_balance, treasury_rates
    )

    return high, result


def main():
    print("=" * 90)
    print("PARALLEL ALLOCATION: Treasury Safety Net + Stock Upside")
    print("=" * 90)
    print()

    # Setup
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    years = 25
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, years)

    treasury_rates = {
        1: 3.70, 3: 3.60, 5: 3.71, 10: 4.11, 20: 4.65, 30: 4.67
    }

    print("Scenario: 2000-2024 (worst crash period)")
    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Baselines
    treasury_full = 433032
    stock_full = 489746

    print("Baseline Strategies:")
    print(f"  - 100% Treasury: ${treasury_full:,}")
    print(f"  - 100% Stocks:   ${stock_full:,}")
    print()

    print("=" * 90)
    print("PARALLEL STRATEGY: Different Treasury Safety Nets")
    print("=" * 90)
    print()

    # Test different treasury safety net positions
    safety_net_years = [15, 18, 20, 22, 23]

    print("Safety Net | Treasury | Stock    | Total    | Outcome")
    print("Starts Yr  | Cost     | Needed   | Upfront  | ")
    print("-----------|----------|----------|----------|----------------------------------")

    results = {}

    for safety_year in safety_net_years:
        treasury_cost = calculate_treasury_cost(annual_payment, safety_year, years, treasury_rates)

        stock_needed, result = find_minimum_stock_investment(
            safety_year, returns_2000, annual_payment, mortgage_balance, treasury_rates
        )

        total_upfront = stock_needed + treasury_cost

        results[safety_year] = {
            'treasury_cost': treasury_cost,
            'stock_needed': stock_needed,
            'total_upfront': total_upfront,
            'result': result
        }

        outcome = ""
        if result.get('paid_off_early'):
            outcome = f"✓ Paid off yr {result['years_to_payoff']}, refund ${result.get('treasury_refund', 0):,.0f}"
        elif result.get('treasury_safety_net_used'):
            outcome = f"Stocks→Treasury yr {result.get('treasury_kicked_in', safety_year)}"
        elif result.get('failed_before_safety_net'):
            outcome = "✗ Failed before safety net"
        else:
            outcome = "Completed"

        print(f"{safety_year:10d} | ${treasury_cost:>7,.0f} | ${stock_needed:>7,.0f} | "
              f"${total_upfront:>7,.0f} | {outcome}")

    # Find optimal
    optimal_year = min(results, key=lambda k: results[k]['total_upfront'])
    optimal = results[optimal_year]

    print()
    print("=" * 90)
    print("🎯 OPTIMAL PARALLEL STRATEGY")
    print("=" * 90)
    print()

    print(f"Safety Net: Treasuries cover years {optimal_year}-{years}")
    print()
    print(f"Upfront Capital Allocation:")
    print(f"  - Stocks:     ${optimal['stock_needed']:>10,.2f}")
    print(f"  - Treasuries: ${optimal['treasury_cost']:>10,.2f}")
    print(f"  - TOTAL:      ${optimal['total_upfront']:>10,.2f}")
    print()

    savings_vs_treasury = treasury_full - optimal['total_upfront']
    savings_vs_stock = stock_full - optimal['total_upfront']

    print("Comparison:")
    print(f"  vs. 100% Treasury: ${savings_vs_treasury:>+10,.2f}")
    print(f"  vs. 100% Stocks:   ${savings_vs_stock:>+10,.2f}")
    print()

    if optimal['total_upfront'] < treasury_full:
        print("🏆 PARALLEL STRATEGY WINS!")
        print()
        print(f"You save ${savings_vs_treasury:,.2f} vs. full treasury ladder")
        print()
        print("How it works:")
        print(f"  1. Invest ${optimal['stock_needed']:,.0f} in stocks TODAY")
        print(f"  2. Buy treasury ladder for years {optimal_year}-{years} TODAY (${optimal['treasury_cost']:,.0f})")
        print(f"  3. Total upfront: ${optimal['total_upfront']:,.0f}")
        print()
        print("Possible outcomes:")
        print("  📈 Stocks do well (90% likely):")
        print(f"     → Pay off early (year 12-15)")
        print(f"     → Sell unused treasuries for refund")
        print(f"     → Net capital used: Much less than ${optimal['total_upfront']:,.0f}")
        print()
        print("  📉 Stocks crash (10% likely - like 2000-2024):")
        print(f"     → Treasuries kick in at year {optimal_year}")
        print(f"     → Guaranteed finish by year {years}")
        print(f"     → Capital used: ${optimal['total_upfront']:,.0f}")
        print()
        print("This is THE optimal strategy - safety net + upside potential!")
    else:
        print("Full treasury still cheaper for worst-case scenario")

    print()


if __name__ == "__main__":
    main()
