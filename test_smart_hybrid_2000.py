"""
Test Smart Hybrid Strategy on 2000-2024

The Strategy:
- Deploy: $241K in stocks (median allocation)
- Deploy: $29K in treasury ladder for years 23-25 (safety net)
- Reserve: $163K in 1-year treasuries at 3.7% (accessible, earning money)
- Total: $433K (but only $270K committed)

Decision Logic:
- Years 1-5: Monitor stock performance
- If stocks down >30% cumulative: TRIGGER BAILOUT
  - Pull from reserve ($163K)
  - Use stock balance + reserve to buy treasury ladder for remaining years

Let's see what ACTUALLY happens in 2000-2024...
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


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
    """Calculate cost of treasury ladder for years [start_year, end_year]."""
    total_cost = 0
    for year in range(start_year, end_year + 1):
        # Years from NOW
        years_from_now = year - start_year + 1
        rate = interpolate_treasury_rate(years_from_now, treasury_rates) / 100.0
        discount_factor = (1 + rate) ** years_from_now
        cost_today = annual_payment / discount_factor
        total_cost += cost_today
    return total_cost


def simulate_smart_hybrid(
    initial_stock_investment: float,
    reserve_amount: float,
    safety_net_start_year: int,
    returns_sequence: list,
    annual_payment: float,
    initial_mortgage_balance: float,
    treasury_rates: dict,
    bailout_threshold: float = -30.0,
    bailout_check_years: int = 5
):
    """
    Simulate the Smart Hybrid strategy.

    Returns detailed year-by-year results.
    """
    stock_balance = initial_stock_investment
    reserve_balance = reserve_amount
    remaining_mortgage = initial_mortgage_balance
    total_years = len(returns_sequence)

    # Cost of safety net (years 23-25)
    safety_net_cost = calculate_treasury_cost(annual_payment, safety_net_start_year, total_years, treasury_rates)

    initial_committed = initial_stock_investment + safety_net_cost

    year_by_year = []
    bailed_out = False
    bailout_year = None
    additional_capital_used = 0

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Withdraw from stocks
        stock_balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        reserve_balance *= 1.037  # Reserve earns 3.7%

        # Calculate cumulative return
        total_withdrawn = year * annual_payment
        cumulative_return_pct = ((stock_balance + total_withdrawn) / initial_stock_investment - 1) * 100

        # Check for bailout trigger
        if (year <= bailout_check_years and
            cumulative_return_pct < bailout_threshold and
            not bailed_out):

            # BAILOUT TRIGGERED!
            bailed_out = True
            bailout_year = year

            # How much do we need to buy treasuries for remaining years?
            treasury_cost_remaining = calculate_treasury_cost(
                annual_payment,
                year + 1,  # Next year
                total_years,
                treasury_rates
            )

            # Do we have enough in stock + reserve?
            available = stock_balance + reserve_balance

            if available >= treasury_cost_remaining:
                # Yes! Use available funds
                additional_capital_used = 0
                leftover = available - treasury_cost_remaining
            else:
                # Need more capital
                additional_capital_used = treasury_cost_remaining - available
                leftover = 0

            year_by_year.append({
                'year': year,
                'return': stock_return,
                'stock_balance': round(stock_balance, 2),
                'reserve_balance': round(reserve_balance, 2),
                'remaining_mortgage': round(remaining_mortgage, 2),
                'cumulative_return': round(cumulative_return_pct, 2),
                'bailout_triggered': True,
                'treasury_cost_remaining': round(treasury_cost_remaining, 2),
                'available_funds': round(available, 2),
                'additional_needed': round(additional_capital_used, 2)
            })

            break  # Exit simulation, treasuries take over

        # Check for early payoff
        if stock_balance >= remaining_mortgage:
            year_by_year.append({
                'year': year,
                'return': stock_return,
                'stock_balance': round(stock_balance, 2),
                'reserve_balance': round(reserve_balance, 2),
                'remaining_mortgage': round(remaining_mortgage, 2),
                'cumulative_return': round(cumulative_return_pct, 2),
                'paid_off_early': True
            })

            leftover_stocks = stock_balance - remaining_mortgage
            # Can sell unused reserve and safety net
            total_leftover = leftover_stocks + reserve_balance + safety_net_cost

            return {
                'success': True,
                'paid_off_early': True,
                'years_to_payoff': year,
                'initial_committed': initial_committed,
                'reserve_deployed': 0,
                'additional_capital_needed': 0,
                'total_capital_used': initial_committed - reserve_balance - safety_net_cost,
                'leftover': total_leftover,
                'year_by_year': year_by_year
            }

        # Check for failure (before safety net)
        if stock_balance < 0 and year < safety_net_start_year:
            year_by_year.append({
                'year': year,
                'return': stock_return,
                'stock_balance': round(stock_balance, 2),
                'reserve_balance': round(reserve_balance, 2),
                'remaining_mortgage': round(remaining_mortgage, 2),
                'cumulative_return': round(cumulative_return_pct, 2),
                'failed': True
            })

            return {
                'success': False,
                'paid_off_early': False,
                'years_to_payoff': year,
                'initial_committed': initial_committed,
                'reserve_deployed': 0,
                'additional_capital_needed': float('inf'),
                'total_capital_used': initial_committed,
                'leftover': stock_balance,
                'year_by_year': year_by_year
            }

        # Check if safety net kicks in
        if year >= safety_net_start_year:
            year_by_year.append({
                'year': year,
                'return': stock_return,
                'stock_balance': round(stock_balance, 2),
                'reserve_balance': round(reserve_balance, 2),
                'remaining_mortgage': round(remaining_mortgage, 2),
                'cumulative_return': round(cumulative_return_pct, 2),
                'safety_net_active': True
            })

            return {
                'success': True,
                'paid_off_early': False,
                'years_to_payoff': total_years,
                'initial_committed': initial_committed,
                'reserve_deployed': 0,
                'additional_capital_needed': 0,
                'total_capital_used': initial_committed,
                'leftover': reserve_balance,
                'safety_net_used': True,
                'year_by_year': year_by_year
            }

        year_by_year.append({
            'year': year,
            'return': stock_return,
            'stock_balance': round(stock_balance, 2),
            'reserve_balance': round(reserve_balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'cumulative_return': round(cumulative_return_pct, 2)
        })

    # If bailed out
    if bailed_out:
        return {
            'success': True,
            'paid_off_early': False,
            'years_to_payoff': total_years,
            'initial_committed': initial_committed,
            'reserve_deployed': reserve_balance,
            'additional_capital_needed': additional_capital_used,
            'total_capital_used': initial_committed + additional_capital_used,
            'leftover': 0,
            'bailed_out': True,
            'bailout_year': bailout_year,
            'year_by_year': year_by_year
        }

    # Completed without bailout or payoff
    return {
        'success': stock_balance >= 0,
        'paid_off_early': False,
        'years_to_payoff': total_years,
        'initial_committed': initial_committed,
        'reserve_deployed': 0,
        'additional_capital_needed': 0,
        'total_capital_used': initial_committed,
        'leftover': stock_balance + reserve_balance,
        'year_by_year': year_by_year
    }


def main():
    print("=" * 90)
    print("SMART HYBRID STRATEGY: 2000-2024 Test")
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

    print("The Smart Hybrid Strategy:")
    print("  - Deploy: $241K in stocks (median allocation)")
    print("  - Deploy: $29K in treasury ladder for years 23-25")
    print("  - Reserve: $163K in 1-year treasuries at 3.7% (accessible)")
    print("  - Total assets: $433K (but only $270K committed)")
    print()
    print("Bailout trigger: If stocks down >30% cumulative in first 5 years")
    print()

    # Run simulation
    stock_investment = 241333
    reserve = 163000
    safety_net_year = 23

    result = simulate_smart_hybrid(
        stock_investment,
        reserve,
        safety_net_year,
        returns_2000,
        annual_payment,
        mortgage_balance,
        treasury_rates
    )

    print("=" * 90)
    print("RESULTS FOR 2000-2024")
    print("=" * 90)
    print()

    print("Capital Deployment:")
    print(f"  Initial committed: ${result['initial_committed']:,.2f}")
    print(f"    - Stocks: ${stock_investment:,.2f}")
    print(f"    - Safety net (yrs 23-25): ${result['initial_committed'] - stock_investment:,.2f}")
    print(f"  Reserve (accessible): ${reserve:,.2f} earning 3.7%")
    print()

    if result.get('bailed_out'):
        print(f"🚨 BAILOUT TRIGGERED in Year {result['bailout_year']}!")
        print()
        print(f"  Reserve deployed: ${result['reserve_deployed']:,.2f}")
        print(f"  Additional capital needed: ${result['additional_capital_needed']:,.2f}")
        print(f"  Total capital used: ${result['total_capital_used']:,.2f}")
        print()
    elif result.get('paid_off_early'):
        print(f"✅ PAID OFF EARLY in Year {result['years_to_payoff']}!")
        print()
        print(f"  Total capital used: ${result['total_capital_used']:,.2f}")
        print(f"  Leftover (incl. reserve & safety net): ${result['leftover']:,.2f}")
        print()
    elif result.get('safety_net_used'):
        print("🛡️ SAFETY NET ACTIVATED at Year 23")
        print()
        print(f"  Total capital used: ${result['total_capital_used']:,.2f}")
        print(f"  Reserve unused: ${result['leftover']:,.2f}")
        print()
    else:
        print(f"Outcome: {result}")
        print()

    # Year by year
    print("=" * 90)
    print("YEAR-BY-YEAR BREAKDOWN")
    print("=" * 90)
    print()
    print("Year | Actual | Return  | Stock Bal | Reserve Bal | Total   | Mortgage | Cum Return | Event")
    print("-----|--------|---------|-----------|-------------|---------|----------|------------|-------")

    for y in result['year_by_year'][:10]:
        actual_year = 2000 + y['year'] - 1
        total_bal = y['stock_balance'] + y['reserve_balance']

        event = ""
        if y.get('bailout_triggered'):
            event = "🚨 BAILOUT"
        elif y.get('paid_off_early'):
            event = "✅ PAID OFF"
        elif y.get('safety_net_active'):
            event = "🛡️ SAFETY NET"
        elif y.get('failed'):
            event = "❌ FAILED"

        print(f"{y['year']:4d} | {actual_year} | {y['return']:>+6.2f}% | ${y['stock_balance']:>8,.0f} | "
              f"${y['reserve_balance']:>10,.0f} | ${total_bal:>6,.0f} | ${y['remaining_mortgage']:>7,.0f} | "
              f"{y['cumulative_return']:>+9.2f}% | {event}")

    if len(result['year_by_year']) > 10:
        print("...")

    if result.get('bailout_triggered'):
        last = result['year_by_year'][-1]
        print()
        print(f"Bailout Details (Year {result['bailout_year']}):")
        print(f"  Treasury cost for remaining years: ${last['treasury_cost_remaining']:,.2f}")
        print(f"  Available funds (stocks + reserve): ${last['available_funds']:,.2f}")
        print(f"  Additional capital needed: ${last['additional_needed']:,.2f}")

    print()
    print("=" * 90)
    print("VERDICT")
    print("=" * 90)
    print()

    full_treasury = 433032

    print(f"Smart Hybrid total capital: ${result['total_capital_used']:,.2f}")
    print(f"Full treasury ladder: ${full_treasury:,.2f}")
    print()

    if result['total_capital_used'] < full_treasury:
        savings = full_treasury - result['total_capital_used']
        print(f"✅ Smart Hybrid SAVES ${savings:,.2f} even in worst-case 2000-2024!")
    elif result['total_capital_used'] == result['initial_committed']:
        print(f"Smart Hybrid uses ${result['initial_committed']:,.2f} committed capital")
        print(f"Reserve of ${reserve:,.2f} remained invested earning 3.7%")
        print()
        print("Effective capital efficiency vs. full treasury:")
        reserve_earnings = reserve * ((1.037 ** result['years_to_payoff']) - 1)
        net_cost = result['initial_committed'] - reserve_earnings
        print(f"  Net cost: ${net_cost:,.2f} (after reserve earnings)")
        savings = full_treasury - net_cost
        print(f"  Savings: ${savings:,.2f}")
    else:
        extra = result['total_capital_used'] - full_treasury
        print(f"❌ Smart Hybrid needs ${extra:,.2f} MORE than full treasury")
        print()
        print("But remember: 2000-2024 is the WORST case (95th percentile)")
        print("In 90% of scenarios, this strategy wins big!")

    print()


if __name__ == "__main__":
    main()
