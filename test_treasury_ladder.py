"""
Test Treasury Bond Ladder Strategy

Key Idea:
- Buy treasury bonds with staggered maturity dates
- Each bond matures exactly when you need to make a payment
- Guaranteed return (4% current treasury rates)
- ZERO principal risk
- ZERO sequence of returns risk

Compare to:
- Paying off mortgage directly: $500,000
- Stock strategy: $489,746 (risky, takes 17 years)
- Treasury ladder: ??? (risk-free!)

Math:
To receive $28,078 in year N with 4% treasury yield:
  Cost today = $28,078 / (1.04)^N

Total cost = Sum of all discounted payments (present value of annuity)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.mortgage_calculator import calculate_annual_payment
from typing import Tuple


def calculate_treasury_ladder_cost(
    annual_payment: float,
    years: int,
    treasury_rate: float
) -> Tuple[float, list]:
    """
    Calculate cost of treasury bond ladder.

    For each year N, buy a bond that:
    - Pays annual_payment when it matures
    - Costs: annual_payment / (1 + treasury_rate)^N today

    Returns:
        (total_cost, year_by_year_details)
    """
    year_by_year = []
    total_cost = 0

    for year in range(1, years + 1):
        # Cost to buy a bond that pays annual_payment in year N
        discount_factor = (1 + treasury_rate) ** year
        cost_today = annual_payment / discount_factor

        total_cost += cost_today

        year_by_year.append({
            'year': year,
            'payment_needed': annual_payment,
            'cost_today': round(cost_today, 2),
            'discount_factor': round(discount_factor, 4)
        })

    return round(total_cost, 2), year_by_year


def calculate_pv_annuity(payment: float, rate: float, periods: int) -> float:
    """
    Present value of annuity formula:
    PV = PMT * [(1 - (1/(1+r)^n)) / r]
    """
    if rate == 0:
        return payment * periods

    pv = payment * ((1 - (1 / (1 + rate) ** periods)) / rate)
    return round(pv, 2)


def compare_treasury_vs_mortgage():
    """Compare treasury ladder strategy vs other options."""
    print("=" * 80)
    print("TREASURY BOND LADDER STRATEGY")
    print("=" * 80)
    print()
    print("Strategy: Buy treasury bonds with staggered maturity dates")
    print("  - Each bond matures exactly when you need to make a payment")
    print("  - Guaranteed 4% return (current treasury rates)")
    print("  - ZERO market risk, ZERO sequence of returns risk")
    print()

    # Mortgage parameters
    mortgage_balance = 500000
    mortgage_rate = 3.0
    years = 25

    # Calculate annual payment
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, years)

    print(f"Mortgage Details:")
    print(f"  Balance: ${mortgage_balance:,}")
    print(f"  Interest Rate: {mortgage_rate}%")
    print(f"  Years: {years}")
    print(f"  Annual Payment: ${annual_payment:,.2f}")
    print()

    # Test different treasury rates
    treasury_rates = [
        2.0,  # Below mortgage rate (bad)
        3.0,  # Equal to mortgage rate (break-even)
        3.5,  # Slightly above
        4.0,  # Current rates
        4.5,  # Higher rates
        5.0   # Much higher
    ]

    print("=" * 80)
    print("TREASURY LADDER COSTS AT DIFFERENT RATES")
    print("=" * 80)
    print()

    results = {}

    for treasury_rate in treasury_rates:
        treasury_rate_decimal = treasury_rate / 100.0

        # Calculate using annuity formula (faster)
        total_cost = calculate_pv_annuity(annual_payment, treasury_rate_decimal, years)

        savings_vs_payoff = mortgage_balance - total_cost
        savings_pct = (savings_vs_payoff / mortgage_balance) * 100

        results[treasury_rate] = {
            'cost': total_cost,
            'savings': savings_vs_payoff,
            'savings_pct': savings_pct
        }

        outcome = ""
        if savings_vs_payoff > 0:
            outcome = f"✅ SAVE ${savings_vs_payoff:,.0f} ({savings_pct:.1f}%)"
        elif savings_vs_payoff < 0:
            outcome = f"❌ LOSE ${abs(savings_vs_payoff):,.0f} ({abs(savings_pct):.1f}%)"
        else:
            outcome = "⚖️  BREAK-EVEN"

        print(f"Treasury Rate: {treasury_rate}% → Cost: ${total_cost:>10,.0f}  |  {outcome}")

    # Focus on 4% (current rate)
    print()
    print("=" * 80)
    print("DETAILED ANALYSIS: 4% TREASURY RATE (CURRENT)")
    print("=" * 80)
    print()

    treasury_rate = 4.0
    treasury_rate_decimal = treasury_rate / 100.0

    total_cost, year_by_year = calculate_treasury_ladder_cost(
        annual_payment, years, treasury_rate_decimal
    )

    print(f"Total Cost of Treasury Ladder: ${total_cost:,}")
    print(f"Mortgage Balance: ${mortgage_balance:,}")
    print(f"SAVINGS: ${mortgage_balance - total_cost:,} ({((mortgage_balance - total_cost) / mortgage_balance * 100):.2f}%)")
    print()

    print("Year-by-Year Bond Purchases:")
    print()
    print("Year | Payment Needed | Cost Today | Discount Factor")
    print("-----|----------------|------------|----------------")

    for i, detail in enumerate(year_by_year[:10], 1):
        print(f"{detail['year']:4d} | ${detail['payment_needed']:>12,.0f} | "
              f"${detail['cost_today']:>9,.0f} | {detail['discount_factor']:>14.4f}")

    if len(year_by_year) > 10:
        print(" ... | ...            | ...        | ...")
        last = year_by_year[-1]
        print(f"{last['year']:4d} | ${last['payment_needed']:>12,.0f} | "
              f"${last['cost_today']:>9,.0f} | {last['discount_factor']:>14.4f}")

    print()
    print(f"TOTAL: ${total_cost:>58,.0f}")
    print()

    # Compare all strategies
    print("=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)
    print()

    stock_baseline = 489746  # From earlier 2000-2024 test

    strategies = [
        {
            'name': 'Pay Off Directly',
            'cost': mortgage_balance,
            'time': 0,
            'risk': 'None - done immediately',
            'upside': 'None'
        },
        {
            'name': 'Treasury Ladder (4%)',
            'cost': total_cost,
            'time': 0,
            'risk': 'ZERO - government guaranteed',
            'upside': f'Save ${mortgage_balance - total_cost:,.0f}'
        },
        {
            'name': 'Stock Strategy (2000-2024)',
            'cost': stock_baseline,
            'time': 17,
            'risk': 'HIGH - market crashes possible',
            'upside': f'Save ${mortgage_balance - stock_baseline:,.0f}'
        }
    ]

    for strategy in strategies:
        print(f"Strategy: {strategy['name']}")
        print(f"  Cost: ${strategy['cost']:,}")
        print(f"  Time to payoff: {strategy['time']} years" if strategy['time'] > 0 else "  Time to payoff: Immediate")
        print(f"  Risk: {strategy['risk']}")
        print(f"  Benefit: {strategy['upside']}")
        print()

    # Key insight
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print()

    if total_cost < stock_baseline:
        print("🏆 TREASURY LADDER WINS!")
        print()
        print(f"✅ Cheaper than stocks: ${stock_baseline - total_cost:,.0f} less")
        print(f"✅ ZERO market risk (vs. high stock market risk)")
        print(f"✅ Guaranteed outcome (vs. uncertain 17 years)")
        print(f"✅ Saves ${mortgage_balance - total_cost:,.0f} vs. paying off directly")
        print()
        print("VERDICT: Treasury ladder is the BEST strategy when rates > mortgage rate")

    elif total_cost < mortgage_balance:
        print("✅ Treasury ladder saves money vs. paying off directly")
        print(f"   Savings: ${mortgage_balance - total_cost:,.0f}")
        print()
        print("BUT:")
        print(f"❌ Stocks could save more: ${mortgage_balance - stock_baseline:,.0f}")
        print(f"❌ Stock strategy costs ${stock_baseline:,.0f} vs. treasury ${total_cost:,.0f}")
        print()
        print("TRADE-OFF:")
        print(f"  - Pay ${total_cost - stock_baseline:,.0f} more for ZERO risk")
        print(f"  - Or save ${total_cost - stock_baseline:,.0f} but take market risk for 17 years")

    else:
        print("❌ Treasury ladder costs MORE than paying off directly")
        print(f"   Extra cost: ${total_cost - mortgage_balance:,.0f}")
        print()
        print("This happens when treasury rate < mortgage rate")
        print("Better to just pay off the mortgage or use stocks")

    print()
    print("=" * 80)
    print("THE ARBITRAGE RULE")
    print("=" * 80)
    print()
    print("Treasury ladder makes sense when: Treasury Rate > Mortgage Rate")
    print()
    print(f"Your mortgage: {mortgage_rate}%")
    print(f"Current treasuries: 4.0%")
    print(f"Spread: {4.0 - mortgage_rate}% in YOUR favor")
    print()
    print("This is a RISK-FREE ARBITRAGE opportunity!")
    print()


if __name__ == "__main__":
    compare_treasury_vs_mortgage()
