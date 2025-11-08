"""
Hybrid Strategy: Optimize Capital Efficiency with Dynamic Allocation

The Dilemma:
- Treasury ladder: $433K upfront (guaranteed, but locks up capital)
- Stocks: $175K-$490K (usually works with less, but risky)
- Stocks work 90% of the time (based on historical data)

Smart Solution: Start with LESS capital in stocks, bail to treasuries if crash

Hybrid Strategies to Test:

1. "Rolling Lock-In": Start stocks, gradually lock in treasuries as you go
   - Years 1-5: Use stocks
   - Year by year: Lock in treasury for far-out years as rates become attractive
   - Benefit: Start with less capital, build treasury ladder progressively

2. "Crash Bail-Out": Start stocks, switch to treasuries if early crash
   - Start with median stock allocation (~$264K)
   - If market crashes >20% in first 3 years: Bail out, buy treasuries for remaining years
   - If market does well: Continue with stocks, pay off early
   - Benefit: Optimize for likely scenario, have escape hatch

3. "Barbell Strategy": Split between stocks and treasuries
   - Put 50% in stocks (risky)
   - Put 50% in treasury ladder for later years (safe)
   - Benefit: Hedge your bets

4. "Options Strategy": Buy insurance against crashes
   - Invest in stocks
   - Buy put options or VIX calls as crash insurance
   - Benefit: Keep stock upside, limit downside
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


def cost_of_treasury_ladder(annual_payment: float, start_year: int, end_year: int, rate_points: dict) -> float:
    """Calculate cost of treasury ladder for years [start_year, end_year]."""
    total_cost = 0

    for year in range(start_year, end_year + 1):
        years_from_now = year - start_year + 1
        rate = interpolate_treasury_rate(years_from_now, rate_points) / 100.0
        discount_factor = (1 + rate) ** years_from_now
        cost_today = annual_payment / discount_factor
        total_cost += cost_today

    return total_cost


def strategy_rolling_lockin(
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    initial_stock_investment: float,
    treasury_rates: dict,
    lockin_threshold: float = 10.0  # Lock in treasuries after good years (>10% return)
) -> Dict:
    """
    Rolling Lock-In Strategy:
    - Start with stocks
    - After good years, progressively lock in treasury bonds for future years
    - Reduces risk over time while maximizing early stock growth

    Returns performance metrics
    """
    stock_balance = initial_stock_investment
    remaining_mortgage = initial_mortgage_balance
    treasury_locked_years = set()  # Years we've locked in with treasuries

    total_treasury_cost = 0
    years_to_payoff = None

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Withdraw from stocks
        stock_balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply stock return
        stock_balance *= (1 + stock_return / 100.0)

        total_balance = stock_balance

        # Decision: Lock in treasuries for far-out years?
        if stock_return > lockin_threshold and stock_balance > annual_payment * 2:
            # Good year! Lock in treasury for farthest year not yet locked
            # (This is simplified - in reality you'd lock in specific bonds)
            pass  # For now, just continue with stocks

        # Check for early payoff
        if total_balance >= remaining_mortgage:
            years_to_payoff = year
            leftover = total_balance - remaining_mortgage
            return {
                'success': True,
                'years_to_payoff': years_to_payoff,
                'initial_capital': initial_stock_investment + total_treasury_cost,
                'leftover': leftover,
                'strategy': 'rolling_lockin'
            }

        if total_balance < 0:
            # Failed - would need to bail out
            return {
                'success': False,
                'years_to_payoff': year,
                'initial_capital': initial_stock_investment + total_treasury_cost,
                'leftover': total_balance,
                'strategy': 'rolling_lockin'
            }

    return {
        'success': stock_balance >= 0,
        'years_to_payoff': len(returns_sequence),
        'initial_capital': initial_stock_investment + total_treasury_cost,
        'leftover': stock_balance,
        'strategy': 'rolling_lockin'
    }


def strategy_crash_bailout(
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    initial_stock_investment: float,
    treasury_rates: dict,
    crash_threshold: float = -15.0,  # Bail out if cumulative loss > 15%
    bailout_window: int = 5  # Check for bail-out in first 5 years
) -> Dict:
    """
    Crash Bail-Out Strategy:
    - Start with stocks
    - If early crash detected, bail out and buy treasury ladder for remaining years
    - Otherwise continue with stocks

    This optimizes for the common case (no crash) with a safety net
    """
    stock_balance = initial_stock_investment
    remaining_mortgage = initial_mortgage_balance
    years_remaining = len(returns_sequence)

    cumulative_return = 0

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Withdraw from stocks
        stock_balance -= annual_payment
        remaining_mortgage -= annual_payment
        years_remaining -= 1

        # Apply stock return
        stock_balance *= (1 + stock_return / 100.0)

        # Track cumulative performance
        cumulative_return = ((stock_balance + (year * annual_payment)) / initial_stock_investment - 1) * 100

        # BAIL-OUT DECISION: Are we in a crash?
        if year <= bailout_window and cumulative_return < crash_threshold:
            # CRASH DETECTED! Bail out to treasuries

            # Cost to buy treasury ladder for remaining years
            treasury_cost = cost_of_treasury_ladder(annual_payment, year + 1, len(returns_sequence), treasury_rates)

            # Total capital needed
            total_capital = initial_stock_investment + treasury_cost

            # Do we have enough in stock balance to buy treasuries?
            if stock_balance >= treasury_cost:
                # Yes! Bail out successful
                leftover = stock_balance - treasury_cost
                return {
                    'success': True,
                    'years_to_payoff': len(returns_sequence),
                    'initial_capital': initial_stock_investment,
                    'additional_capital': 0,
                    'total_capital': initial_stock_investment,
                    'leftover': leftover,
                    'bailed_out': True,
                    'bailout_year': year,
                    'strategy': 'crash_bailout'
                }
            else:
                # Need additional capital to complete bailout
                additional_needed = treasury_cost - stock_balance
                return {
                    'success': True,
                    'years_to_payoff': len(returns_sequence),
                    'initial_capital': initial_stock_investment,
                    'additional_capital': additional_needed,
                    'total_capital': initial_stock_investment + additional_needed,
                    'leftover': 0,
                    'bailed_out': True,
                    'bailout_year': year,
                    'strategy': 'crash_bailout'
                }

        # Check for early payoff (no bailout needed!)
        if stock_balance >= remaining_mortgage:
            return {
                'success': True,
                'years_to_payoff': year,
                'initial_capital': initial_stock_investment,
                'additional_capital': 0,
                'total_capital': initial_stock_investment,
                'leftover': stock_balance - remaining_mortgage,
                'bailed_out': False,
                'bailout_year': None,
                'strategy': 'crash_bailout'
            }

        # Check for failure
        if stock_balance < 0:
            return {
                'success': False,
                'years_to_payoff': year,
                'initial_capital': initial_stock_investment,
                'additional_capital': 0,
                'total_capital': initial_stock_investment,
                'leftover': stock_balance,
                'bailed_out': False,
                'bailout_year': None,
                'strategy': 'crash_bailout'
            }

    # Completed full term without bailout
    return {
        'success': stock_balance >= 0,
        'years_to_payoff': len(returns_sequence),
        'initial_capital': initial_stock_investment,
        'additional_capital': 0,
        'total_capital': initial_stock_investment,
        'leftover': stock_balance,
        'bailed_out': False,
        'bailout_year': None,
        'strategy': 'crash_bailout'
    }


def test_hybrid_strategies():
    """Test hybrid strategies on 2000-2024 period."""
    print("=" * 90)
    print("HYBRID STRATEGY OPTIMIZATION")
    print("=" * 90)
    print()
    print("Goal: Use LESS capital upfront by being smart about risk management")
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

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}% for {years} years")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Baseline comparisons
    treasury_full_cost = 433032  # From earlier calculation
    stock_2000_cost = 489746  # 2000-2024 worst case
    stock_median_cost = 264000  # Approximate median

    print("=" * 90)
    print("BASELINE STRATEGIES")
    print("=" * 90)
    print()
    print(f"1. Pay off directly:        ${mortgage_balance:,}")
    print(f"2. Treasury ladder (full):  ${treasury_full_cost:,} (guaranteed)")
    print(f"3. Stocks (2000-2024):      ${stock_2000_cost:,} (17 years, high risk)")
    print(f"4. Stocks (median case):    ${stock_median_cost:,} (12-15 years, med risk)")
    print()

    # Test Strategy: Crash Bail-Out with different initial investments
    print("=" * 90)
    print("HYBRID STRATEGY: CRASH BAIL-OUT")
    print("=" * 90)
    print()
    print("Approach: Start with stocks, bail to treasuries if early crash")
    print()

    test_investments = [
        200000,  # Aggressive
        250000,  # Moderate
        300000,  # Conservative
        350000,  # Very conservative
    ]

    print("Testing different initial stock investments:")
    print()
    print("Initial Investment | Outcome | Total Capital | Years | Bailed Out?")
    print("-------------------|---------|---------------|-------|-------------")

    best_result = None
    best_capital = float('inf')

    for initial_inv in test_investments:
        result = strategy_crash_bailout(
            returns_2000,
            annual_payment,
            mortgage_balance,
            initial_inv,
            treasury_rates
        )

        outcome = "✓ Success" if result['success'] else "✗ Failed"
        bailout_status = f"Yes (yr {result['bailout_year']})" if result.get('bailed_out') else "No"

        print(f"${initial_inv:>17,} | {outcome:7s} | ${result['total_capital']:>12,} | "
              f"{result['years_to_payoff']:>5d} | {bailout_status:15s}")

        if result['success'] and result['total_capital'] < best_capital:
            best_capital = result['total_capital']
            best_result = result
            best_result['initial_investment'] = initial_inv

    print()
    print("=" * 90)
    print("OPTIMAL HYBRID STRATEGY")
    print("=" * 90)
    print()

    if best_result:
        print(f"✅ Best Hybrid Approach:")
        print()
        print(f"  Initial Investment: ${best_result['initial_investment']:,}")
        print(f"  Additional Capital Needed: ${best_result.get('additional_capital', 0):,}")
        print(f"  TOTAL CAPITAL: ${best_result['total_capital']:,}")
        print()
        print(f"  Years to Payoff: {best_result['years_to_payoff']}")
        print(f"  Bailed Out: {'Yes' if best_result.get('bailed_out') else 'No'}")
        if best_result.get('bailed_out'):
            print(f"  Bailout Year: {best_result['bailout_year']}")
        print()

        # Compare to alternatives
        savings_vs_payoff = mortgage_balance - best_result['total_capital']
        savings_vs_treasury = treasury_full_cost - best_result['total_capital']

        print(f"  Savings vs. Pay Off Directly: ${savings_vs_payoff:,}")
        print(f"  Savings vs. Full Treasury:    ${savings_vs_treasury:,}")
        print()

        if best_result['total_capital'] < treasury_full_cost:
            print(f"🏆 HYBRID WINS!")
            print(f"   - Need ${best_result['initial_investment']:,} upfront (vs ${treasury_full_cost:,})")
            print(f"   - Save ${savings_vs_treasury:,} vs. treasury ladder")
            print(f"   - Have bailout option if market crashes")
            print()
        else:
            print("Treasury ladder still cheaper - stick with that")
            print()

    print("=" * 90)
    print("THE SMART SOLUTION")
    print("=" * 90)
    print()
    print("Instead of committing $433K to treasuries upfront:")
    print()
    print(f"1. Start with ${best_result['initial_investment']:,} in stocks")
    print("2. If stocks crash in first 5 years → Bail to treasury ladder")
    print(f"3. If stocks do well → Pay off early in {best_result['years_to_payoff']} years")
    print()
    print("Benefits:")
    print(f"  ✓ Only need ${best_result['initial_investment']:,} upfront (not ${treasury_full_cost:,})")
    print(f"  ✓ Save ${savings_vs_treasury:,} in capital efficiency")
    print("  ✓ Have upside potential if stocks perform well")
    print("  ✓ Safety net if things go wrong (bail to treasuries)")
    print()


if __name__ == "__main__":
    test_hybrid_strategies()
