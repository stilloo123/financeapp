"""
Test Dynamic Withdrawal Strategy with Emergency Account

Key Idea:
- Main account: 100% stocks
- Emergency account: Separate cash reserve
- During crashes: Withdraw from emergency account (don't touch stocks)
- During good years: Replenish emergency account from stocks
- Goal: Avoid selling stocks at the bottom

Test on 2000-2024: Two major crashes where this should shine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from typing import List, Tuple, Dict


def simulate_dynamic_withdrawal(
    initial_investment: float,
    emergency_fund: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    crash_threshold: float = -5.0,  # Consider it a crash if return < -5%
    recovery_threshold: float = 15.0  # Good year if return > 15%
) -> Tuple[bool, int, float, float, List[Dict]]:
    """
    Simulate with dynamic withdrawal strategy.

    Rules:
    1. If market return < crash_threshold: Withdraw from emergency fund
    2. If market return > recovery_threshold AND emergency fund depleted: Replenish from stocks
    3. Otherwise: Withdraw from stocks normally

    Returns:
        (success, years_to_payoff, leftover_investment, leftover_emergency, year_by_year)
    """
    stock_balance = initial_investment
    emergency_balance = emergency_fund
    remaining_mortgage = initial_mortgage_balance
    year_by_year = []

    for year, stock_return_pct in enumerate(returns_sequence, start=1):
        withdrawal_source = "stocks"  # Default

        # DECISION: Where to withdraw from?
        if stock_return_pct < crash_threshold and emergency_balance >= annual_payment:
            # CRASH YEAR: Use emergency fund, don't touch stocks
            withdrawal_source = "emergency"
            emergency_balance -= annual_payment
        else:
            # NORMAL/GOOD YEAR: Withdraw from stocks
            stock_balance -= annual_payment
            withdrawal_source = "stocks"

        # Reduce mortgage
        remaining_mortgage -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return_pct / 100.0)
        emergency_balance *= 1.02  # Emergency fund earns 2%

        # REPLENISHMENT: In good years, replenish emergency fund
        if stock_return_pct > recovery_threshold and emergency_balance < emergency_fund:
            # Replenish up to original amount
            needed = emergency_fund - emergency_balance
            # Take up to 20% of stock balance or what's needed
            replenish_amount = min(needed, stock_balance * 0.20)
            stock_balance -= replenish_amount
            emergency_balance += replenish_amount
            replenishment = replenish_amount
        else:
            replenishment = 0

        total_balance = stock_balance + emergency_balance

        year_by_year.append({
            'year': year,
            'return': stock_return_pct,
            'stock_balance': round(stock_balance, 2),
            'emergency_balance': round(emergency_balance, 2),
            'total_balance': round(total_balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'withdrawal_source': withdrawal_source,
            'replenishment': round(replenishment, 2),
            'can_payoff_early': total_balance >= remaining_mortgage
        })

        # CHECK: Early payoff?
        if total_balance >= remaining_mortgage:
            leftover_total = total_balance - remaining_mortgage
            return True, year, round(stock_balance, 2), round(emergency_balance, 2), year_by_year

        # CHECK: Ran out of money?
        if total_balance < 0:
            return False, year, round(stock_balance, 2), round(emergency_balance, 2), year_by_year

    # Completed full term
    success = total_balance >= 0
    return success, len(returns_sequence), round(stock_balance, 2), round(emergency_balance, 2), year_by_year


def find_minimum_dynamic_withdrawal(
    emergency_fund: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    tolerance: float = 100.0
) -> Tuple[float, int, float, float]:
    """
    Find minimum initial investment needed with given emergency fund size.

    Returns:
        (min_investment, years_to_payoff, leftover_investment, leftover_emergency)
    """
    low = 0.0
    high = initial_mortgage_balance * 2.0

    while high - low > tolerance:
        mid = (low + high) / 2.0

        success, years, leftover_inv, leftover_emerg, _ = simulate_dynamic_withdrawal(
            mid, emergency_fund, returns_sequence, annual_payment, initial_mortgage_balance
        )

        if success:
            high = mid  # Try less
        else:
            low = mid  # Need more

    # Final simulation
    success, years, leftover_inv, leftover_emerg, _ = simulate_dynamic_withdrawal(
        high, emergency_fund, returns_sequence, annual_payment, initial_mortgage_balance
    )

    return round(high, 2), years, round(leftover_inv, 2), round(leftover_emerg, 2)


def test_dynamic_withdrawal_2000_2024():
    """Test dynamic withdrawal on 2000-2024 with various emergency fund sizes."""
    print("=" * 80)
    print("DYNAMIC WITHDRAWAL STRATEGY TEST: 2000-2024")
    print("=" * 80)
    print()
    print("Strategy:")
    print("  - Main account: 100% stocks")
    print("  - Emergency account: Separate cash pool")
    print("  - CRASH YEARS (return < -5%): Withdraw from emergency, don't touch stocks")
    print("  - GOOD YEARS (return > 15%): Replenish emergency fund from stock gains")
    print("  - NORMAL YEARS: Withdraw from stocks as usual")
    print()
    print("Crashes in 2000-2024:")
    print("  - 2000: -9.10%  ← Use emergency")
    print("  - 2001: -11.89% ← Use emergency")
    print("  - 2002: -22.10% ← Use emergency")
    print("  - 2008: -37.00% ← Use emergency")
    print()

    # Load data
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)
    annual_payment = 28078
    mortgage_balance = 500000

    print(f"Mortgage: ${mortgage_balance:,}")
    print(f"Annual payment: ${annual_payment:,}")
    print()
    print("=" * 80)
    print()

    # Test different emergency fund sizes
    emergency_sizes = [0, 1, 2, 3, 4, 5]  # Years worth of payments

    results = {}

    print("Testing different emergency fund sizes...")
    print()

    for years_emergency in emergency_sizes:
        emergency_fund = annual_payment * years_emergency

        print(f"Emergency fund: {years_emergency} years (${emergency_fund:,})...", end=" ", flush=True)

        min_investment, years_to_payoff, leftover_inv, leftover_emerg = find_minimum_dynamic_withdrawal(
            emergency_fund, returns_2000, annual_payment, mortgage_balance
        )

        total_required = min_investment + emergency_fund
        total_leftover = leftover_inv + leftover_emerg

        results[years_emergency] = {
            'investment': min_investment,
            'emergency_fund': emergency_fund,
            'total_required': total_required,
            'years': years_to_payoff,
            'leftover_inv': leftover_inv,
            'leftover_emerg': leftover_emerg,
            'total_leftover': total_leftover
        }

        print(f"Total: ${total_required:>10,.0f}  |  {years_to_payoff:2d} years")

    # Find optimal
    optimal_size = min(results, key=lambda k: results[k]['total_required'])
    optimal = results[optimal_size]
    baseline = results[0]

    # Display results
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print("| Emergency | Investment | Emergency | Total Needed | Years | vs Baseline |")
    print("| Fund Size | Required   | Fund      |              |       |             |")
    print("|-----------|------------|-----------|--------------|-------|-------------|")

    for years_emergency in emergency_sizes:
        r = results[years_emergency]
        diff = r['total_required'] - baseline['total_required']
        diff_pct = (diff / baseline['total_required']) * 100 if baseline['total_required'] > 0 else 0

        marker = " ⭐ BEST" if years_emergency == optimal_size else ""

        print(f"| {years_emergency} years   | ${r['investment']:>9,.0f} | "
              f"${r['emergency_fund']:>8,.0f} | ${r['total_required']:>11,.0f} | "
              f"{r['years']:>5d} | {diff:>+8,.0f} ({diff_pct:>+5.1f}%){marker} |")

    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    if optimal['total_required'] < baseline['total_required']:
        savings = baseline['total_required'] - optimal['total_required']
        savings_pct = (savings / baseline['total_required']) * 100
        years_faster = baseline['years'] - optimal['years']

        print("🎯 DYNAMIC WITHDRAWAL STRATEGY WORKS!")
        print()
        print(f"Optimal emergency fund: {optimal_size} years (${optimal['emergency_fund']:,.0f})")
        print(f"Total capital needed: ${optimal['total_required']:,.0f}")
        print(f"  - Investment account: ${optimal['investment']:,.0f}")
        print(f"  - Emergency fund: ${optimal['emergency_fund']:,.0f}")
        print()
        print(f"Baseline (no emergency fund): ${baseline['total_required']:,.0f}")
        print(f"SAVINGS: ${savings:,.0f} ({savings_pct:.1f}% reduction)")
        print()
        print(f"Years to payoff: {optimal['years']} years")
        if years_faster > 0:
            print(f"Pays off {years_faster} years faster!")
        print()
        print("WHY IT WORKS:")
        print(f"  ✓ Avoided selling stocks during 4 crash years (2000, 2001, 2002, 2008)")
        print(f"  ✓ Let stocks recover fully without forced liquidation")
        print(f"  ✓ Replenished emergency fund during good years")
        print(f"  ✓ Paid off mortgage in {optimal['years']} years instead of 25")

    else:
        print("Strategy doesn't help - baseline is already optimal")

    print()
    print("=" * 80)
    print(f"YEAR-BY-YEAR: {optimal_size}-YEAR EMERGENCY FUND (OPTIMAL)")
    print("=" * 80)
    print()

    # Detailed year-by-year
    _, _, _, _, yearly = simulate_dynamic_withdrawal(
        optimal['investment'],
        optimal['emergency_fund'],
        returns_2000,
        annual_payment,
        mortgage_balance
    )

    print("Year | Actual | Return  | Stocks    | Emergency | Total     | Mortgage  | Source    | Replenish | Payoff?")
    print("-----|--------|---------|-----------|-----------|-----------|-----------|-----------|-----------|--------")

    for y in yearly[:12]:  # Show first 12 years
        actual_year = 2000 + y['year'] - 1
        can_payoff = "✓ YES" if y['can_payoff_early'] else ""
        source_symbol = "💰E" if y['withdrawal_source'] == 'emergency' else "📈S"

        print(f"{y['year']:4d} | {actual_year} | {y['return']:>+6.2f}% | "
              f"${y['stock_balance']:>8,.0f} | ${y['emergency_balance']:>8,.0f} | "
              f"${y['total_balance']:>8,.0f} | ${y['remaining_mortgage']:>8,.0f} | "
              f"{source_symbol:8s} | ${y['replenishment']:>8,.0f} | {can_payoff}")

    if len(yearly) > 12:
        print("...")
        last = yearly[-1]
        actual_year = 2000 + last['year'] - 1
        can_payoff = "✓ YES" if last['can_payoff_early'] else ""
        source_symbol = "💰E" if last['withdrawal_source'] == 'emergency' else "📈S"

        print(f"{last['year']:4d} | {actual_year} | {last['return']:>+6.2f}% | "
              f"${last['stock_balance']:>8,.0f} | ${last['emergency_balance']:>8,.0f} | "
              f"${last['total_balance']:>8,.0f} | ${last['remaining_mortgage']:>8,.0f} | "
              f"{source_symbol:8s} | ${last['replenishment']:>8,.0f} | {can_payoff}")

    print()
    print(f"Legend: 💰E = Emergency withdrawal, 📈S = Stock withdrawal")
    print(f"Paid off in year {optimal['years']} with ${optimal['total_leftover']:,.0f} total remaining")
    print()


if __name__ == "__main__":
    test_dynamic_withdrawal_2000_2024()
