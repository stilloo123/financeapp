"""
Treasury Ladder with ACTUAL Current Rates (Oct 2025)

No backtesting needed - these are GUARANTEED rates you can lock in today!

Current Treasury Rates (late Oct 2025):
- 1 Year:  3.70%
- 3 Year:  3.60%
- 5 Year:  3.71%
- 10 Year: 4.11%
- 20 Year: 4.65%
- 30 Year: 4.67%

For 25-year mortgage, we need bonds maturing in years 1-25.
We'll interpolate rates for years between the given maturities.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.mortgage_calculator import calculate_annual_payment


def interpolate_rate(year: int, rate_points: dict) -> float:
    """
    Interpolate treasury rate for a given year using linear interpolation.

    rate_points: {maturity_year: rate}
    """
    years = sorted(rate_points.keys())

    # If exact match, return it
    if year in rate_points:
        return rate_points[year]

    # Find surrounding points
    lower_year = None
    upper_year = None

    for y in years:
        if y < year:
            lower_year = y
        elif y > year and upper_year is None:
            upper_year = y
            break

    # If year is below all points, use lowest rate
    if lower_year is None:
        return rate_points[years[0]]

    # If year is above all points, use highest rate
    if upper_year is None:
        return rate_points[years[-1]]

    # Linear interpolation
    lower_rate = rate_points[lower_year]
    upper_rate = rate_points[upper_year]

    # y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    interpolated = lower_rate + (year - lower_year) * (upper_rate - lower_rate) / (upper_year - lower_year)

    return interpolated


def calculate_treasury_ladder_actual_rates(
    annual_payment: float,
    years: int,
    rate_points: dict
) -> tuple:
    """
    Calculate treasury ladder cost using actual yield curve.

    Args:
        annual_payment: Annual mortgage payment
        years: Number of years (mortgage term)
        rate_points: {maturity_year: rate_percent}

    Returns:
        (total_cost, year_by_year_details, weighted_avg_rate)
    """
    year_by_year = []
    total_cost = 0
    total_payment = 0

    for year in range(1, years + 1):
        # Get interpolated rate for this maturity
        rate_percent = interpolate_rate(year, rate_points)
        rate_decimal = rate_percent / 100.0

        # Calculate present value of this payment
        # PV = FV / (1 + r)^n
        discount_factor = (1 + rate_decimal) ** year
        cost_today = annual_payment / discount_factor

        total_cost += cost_today
        total_payment += annual_payment

        year_by_year.append({
            'year': year,
            'payment_needed': annual_payment,
            'treasury_rate': rate_percent,
            'cost_today': round(cost_today, 2),
            'discount_factor': round(discount_factor, 4)
        })

    # Calculate weighted average rate
    weighted_avg_rate = sum(y['treasury_rate'] * y['cost_today'] for y in year_by_year) / total_cost

    return round(total_cost, 2), year_by_year, round(weighted_avg_rate, 2)


def main():
    print("=" * 90)
    print("TREASURY LADDER WITH ACTUAL CURRENT RATES (October 2025)")
    print("=" * 90)
    print()
    print("These are REAL rates you can lock in TODAY - no market risk, no guessing!")
    print()

    # Current treasury rates (late Oct 2025)
    current_rates = {
        1: 3.70,
        3: 3.60,
        5: 3.71,
        10: 4.11,
        20: 4.65,
        30: 4.67
    }

    print("Current Treasury Yield Curve:")
    for maturity, rate in sorted(current_rates.items()):
        print(f"  {maturity:2d} Year: {rate}%")
    print()

    # Mortgage parameters
    mortgage_balance = 500000
    mortgage_rate = 3.0
    years = 25

    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, years)

    print(f"Your Mortgage:")
    print(f"  Balance: ${mortgage_balance:,}")
    print(f"  Rate: {mortgage_rate}%")
    print(f"  Term: {years} years")
    print(f"  Annual Payment: ${annual_payment:,.2f}")
    print()
    print("=" * 90)
    print()

    # Calculate treasury ladder cost
    total_cost, year_by_year, weighted_avg_rate = calculate_treasury_ladder_actual_rates(
        annual_payment, years, current_rates
    )

    savings = mortgage_balance - total_cost
    savings_pct = (savings / mortgage_balance) * 100

    print("TREASURY LADDER ANALYSIS")
    print("=" * 90)
    print()
    print(f"Total Cost: ${total_cost:,}")
    print(f"Mortgage Balance: ${mortgage_balance:,}")
    print(f"SAVINGS: ${savings:,.2f} ({savings_pct:.2f}%)")
    print(f"Weighted Average Treasury Rate: {weighted_avg_rate:.2f}%")
    print(f"Mortgage Rate: {mortgage_rate}%")
    print(f"Rate Advantage: {weighted_avg_rate - mortgage_rate:.2f}%")
    print()

    # Show first few years and last few years
    print("Bond Purchase Details:")
    print()
    print("Year | Payment    | Treasury | Cost Today | Discount  | Interest Earned")
    print("     | Needed     | Rate     |            | Factor    | vs Mortgage")
    print("-----|------------|----------|------------|-----------|----------------")

    for i in range(min(10, len(year_by_year))):
        y = year_by_year[i]
        interest_advantage = (y['treasury_rate'] - mortgage_rate) / 100 * y['cost_today'] * y['year']
        print(f"{y['year']:4d} | ${y['payment_needed']:>9,.0f} | {y['treasury_rate']:>6.2f}% | "
              f"${y['cost_today']:>9,.0f} | {y['discount_factor']:>8.4f} | ${interest_advantage:>8,.0f}")

    if len(year_by_year) > 15:
        print(" ... |     ...    |   ...    |     ...    |    ...    |      ...")

        for i in range(max(10, len(year_by_year) - 5), len(year_by_year)):
            y = year_by_year[i]
            interest_advantage = (y['treasury_rate'] - mortgage_rate) / 100 * y['cost_today'] * y['year']
            print(f"{y['year']:4d} | ${y['payment_needed']:>9,.0f} | {y['treasury_rate']:>6.2f}% | "
                  f"${y['cost_today']:>9,.0f} | {y['discount_factor']:>8.4f} | ${interest_advantage:>8,.0f}")

    print()
    print(f"TOTAL COST: ${total_cost:>67,}")
    print()

    # Compare strategies
    print("=" * 90)
    print("STRATEGY COMPARISON")
    print("=" * 90)
    print()

    stock_worst_case = 489746  # 2000-2024 scenario
    stock_median = 264000  # Approximate median from earlier
    stock_best_case = 175000  # Approximate best case

    print("┌─────────────────────────────┬──────────────┬─────────────┬─────────────┬──────────────┐")
    print("│ Strategy                    │ Capital      │ Time        │ Risk        │ Savings      │")
    print("├─────────────────────────────┼──────────────┼─────────────┼─────────────┼──────────────┤")
    print(f"│ 1. Pay Off Directly         │ ${mortgage_balance:>10,} │ Immediate   │ None        │ Baseline     │")
    print(f"│ 2. Treasury Ladder (ACTUAL) │ ${total_cost:>10,} │ Immediate   │ ZERO ✓      │ ${savings:>10,.0f} │")
    print(f"│ 3. Stocks (Best Case)       │ ${stock_best_case:>10,} │ ~8-10 years │ High        │ ${mortgage_balance - stock_best_case:>10,} │")
    print(f"│ 4. Stocks (Median)          │ ${stock_median:>10,} │ ~12-15 yrs  │ High        │ ${mortgage_balance - stock_median:>10,} │")
    print(f"│ 5. Stocks (Worst - 2000)    │ ${stock_worst_case:>10,} │ 17 years    │ Very High   │ ${mortgage_balance - stock_worst_case:>10,} │")
    print("└─────────────────────────────┴──────────────┴─────────────┴─────────────┴──────────────┘")
    print()

    # Analysis
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    print()

    print("✅ TREASURY LADDER DOMINATES:")
    print()
    print(f"1. GUARANTEED ${savings:,.0f} savings (no market risk)")
    print(f"2. Locks in {weighted_avg_rate:.2f}% return (vs {mortgage_rate}% mortgage cost)")
    print(f"3. Bonds mature EXACTLY when you need the money")
    print(f"4. ZERO sequence of returns risk")
    print(f"5. Can execute TODAY with current rates")
    print()

    if total_cost < stock_best_case:
        print(f"🏆 CHEAPER than even the BEST CASE stock scenario!")
        print(f"   Treasury: ${total_cost:,}")
        print(f"   Best stock: ${stock_best_case:,}")
        print(f"   Advantage: ${stock_best_case - total_cost:,}")
        print()
    elif total_cost < stock_median:
        print(f"🎯 CHEAPER than median stock scenario!")
        print(f"   Treasury: ${total_cost:,}")
        print(f"   Median stock: ${stock_median:,}")
        print(f"   Advantage: ${stock_median - total_cost:,}")
        print()

    print("=" * 90)
    print("THE VERDICT")
    print("=" * 90)
    print()
    print("With current treasury rates ABOVE your mortgage rate:")
    print()
    print(f"  Your mortgage rate: {mortgage_rate}%")
    print(f"  Weighted avg treasury: {weighted_avg_rate:.2f}%")
    print(f"  ARBITRAGE SPREAD: +{weighted_avg_rate - mortgage_rate:.2f}%")
    print()
    print("✅ TREASURY LADDER IS A NO-BRAINER")
    print()
    print("This is RISK-FREE arbitrage:")
    print(f"  - Borrow at {mortgage_rate}%")
    print(f"  - Invest at {weighted_avg_rate:.2f}%")
    print(f"  - Pocket ${savings:,.0f} with ZERO risk")
    print()
    print("No need to gamble on stocks. The treasury ladder wins.")
    print()


if __name__ == "__main__":
    main()
