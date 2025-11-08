"""
Test Cash Buffer Strategy WITH Early Payoff Optimization
Focus on 2000-2024 period (two early crashes)

Hypothesis: Buffer should help now because:
- Survive 2000-2002 crash with cash (no stock selling)
- Survive 2008 crash with cash
- Catch 2009-2019 bull run
- Pay off in year 12-15 instead of 17
- Cash drag only for 12-15 years, not 25!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from typing import List, Tuple


def simulate_with_buffer_and_early_payoff(
    initial_investment: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    buffer_years: int
) -> Tuple[bool, int, float, List[dict]]:
    """
    Simulate with both cash buffer AND early payoff optimization.

    Returns:
        (success, years_to_payoff, leftover_amount, year_by_year)
    """
    if buffer_years == 0:
        # No buffer - use pure stock strategy with early payoff
        from backend.services.investment_simulator import simulate_investment_with_early_payoff
        return simulate_investment_with_early_payoff(
            initial_investment, returns_sequence, annual_payment, initial_mortgage_balance
        )

    # Initial allocation
    cash_target = annual_payment * buffer_years
    cash_balance = min(cash_target, initial_investment)
    stock_balance = initial_investment - cash_balance
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year_idx, stock_return_pct in enumerate(returns_sequence, start=1):
        # Withdraw from cash at start of year
        cash_balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply returns
        cash_balance *= 1.02  # Cash earns 2%
        stock_balance *= (1 + stock_return_pct / 100.0)

        # Replenishment logic
        if cash_balance < annual_payment:
            # CRITICAL: Must replenish (less than 1 year left)
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance)
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return_pct > 10 and cash_balance < cash_target:
            # Good year: Top up buffer
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance * 0.3)
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return_pct > 0 and cash_balance < cash_target * 0.7:
            # Positive year and buffer low: Partial replenish
            needed = (cash_target * 0.8) - cash_balance
            transfer = min(needed, stock_balance * 0.2)
            stock_balance -= transfer
            cash_balance += transfer

        total_balance = cash_balance + stock_balance

        year_by_year.append({
            'year': year_idx,
            'return': stock_return_pct,
            'balance': round(total_balance, 2),
            'cash': round(cash_balance, 2),
            'stocks': round(stock_balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'can_payoff_early': total_balance >= remaining_mortgage
        })

        # CHECK: Early payoff?
        if total_balance >= remaining_mortgage:
            leftover = total_balance - remaining_mortgage
            return True, year_idx, round(leftover, 2), year_by_year

        # CHECK: Ran out of money?
        if total_balance < 0:
            return False, year_idx, round(total_balance, 2), year_by_year

    # Completed full term
    success = total_balance >= 0
    return success, len(returns_sequence), round(total_balance, 2), year_by_year


def find_minimum_with_buffer_and_early_payoff(
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    buffer_years: int,
    tolerance: float = 100.0
) -> Tuple[float, int, float]:
    """
    Find minimum investment with given buffer size AND early payoff.

    Returns:
        (min_investment, years_to_payoff, leftover_amount)
    """
    low = 0.0
    high = initial_mortgage_balance * 2.0

    while high - low > tolerance:
        mid = (low + high) / 2.0

        success, years, leftover, _ = simulate_with_buffer_and_early_payoff(
            mid, returns_sequence, annual_payment, initial_mortgage_balance, buffer_years
        )

        if success:
            high = mid  # Try less
        else:
            low = mid  # Need more

    # Final simulation
    success, years, leftover, _ = simulate_with_buffer_and_early_payoff(
        high, returns_sequence, annual_payment, initial_mortgage_balance, buffer_years
    )

    return round(high, 2), years, round(leftover, 2)


def test_2000_2024_with_buffers():
    """Test 2000-2024 period with different buffer sizes."""
    print("=" * 70)
    print("CASH BUFFER + EARLY PAYOFF TEST: 2000-2024 PERIOD")
    print("=" * 70)
    print()
    print("This period had TWO major crashes:")
    print("  - 2000-2002: Dot-com crash (-9%, -12%, -22%)")
    print("  - 2008: Financial crisis (-37%)")
    print()
    print("Hypothesis: Cash buffer should help avoid forced selling in crashes,")
    print("            then capitalize on recoveries to pay off early.")
    print()

    # Load data
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)
    annual_payment = 28078
    mortgage_balance = 500000

    print(f"Mortgage: ${mortgage_balance:,}")
    print(f"Annual payment: ${annual_payment:,}")
    print(f"Testing buffer sizes: 0-5 years")
    print()
    print("=" * 70)
    print()

    # Test each buffer size
    results = {}

    for buffer_years in range(0, 6):
        print(f"Testing {buffer_years}-year buffer...", end=" ", flush=True)

        min_investment, years_to_payoff, leftover = find_minimum_with_buffer_and_early_payoff(
            returns_2000, annual_payment, mortgage_balance, buffer_years
        )

        results[buffer_years] = {
            'investment': min_investment,
            'years': years_to_payoff,
            'leftover': leftover
        }

        print(f"${min_investment:>10,.0f}  |  {years_to_payoff:2d} years  |  ${leftover:>8,.0f} left")

    # Find optimal
    optimal_buffer = min(results, key=lambda k: results[k]['investment'])
    optimal_result = results[optimal_buffer]
    baseline_result = results[0]

    # Display results table
    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print()
    print("| Buffer | Investment Req | Years to Payoff | Leftover | vs No Buffer |")
    print("|--------|----------------|-----------------|----------|--------------|")

    for buffer_years in range(0, 6):
        r = results[buffer_years]
        diff = r['investment'] - baseline_result['investment']
        diff_pct = (diff / baseline_result['investment']) * 100

        marker = " ⭐ BEST" if buffer_years == optimal_buffer else ""

        print(f"| {buffer_years} year | ${r['investment']:>12,.0f} | "
              f"{r['years']:>15d} | ${r['leftover']:>7,.0f} | "
              f"{diff:>+8,.0f} ({diff_pct:>+5.1f}%){marker} |")

    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()

    if optimal_result['investment'] < baseline_result['investment']:
        savings = baseline_result['investment'] - optimal_result['investment']
        savings_pct = (savings / baseline_result['investment']) * 100
        years_faster = baseline_result['years'] - optimal_result['years']

        print("✅ BUFFER STRATEGY WORKS WITH EARLY PAYOFF!")
        print()
        print(f"Optimal buffer size: {optimal_buffer} years")
        print(f"Required investment: ${optimal_result['investment']:,.0f}")
        print(f"Baseline (no buffer): ${baseline_result['investment']:,.0f}")
        print(f"SAVINGS: ${savings:,.0f} ({savings_pct:.1f}% reduction)")
        print()
        print(f"Years to payoff with buffer: {optimal_result['years']} years")
        print(f"Years to payoff without buffer: {baseline_result['years']} years")
        if years_faster > 0:
            print(f"PAYS OFF {years_faster} YEARS FASTER with buffer!")
        print()
        print("WHY IT WORKS:")
        print("  - Buffer prevented forced selling during 2000-2002 crash")
        print("  - Buffer prevented forced selling during 2008 crash")
        print("  - Stocks caught the full 2003-2007 recovery")
        print("  - Stocks caught the full 2009-2019 bull run")
        print(f"  - Paid off early in year {optimal_result['years']} (not full 25 years)")
        print(f"  - Cash drag only for {optimal_result['years']} years, not 25!")
        print()
        print("🎉 RECOMMENDATION: Include cash buffer optimization in full implementation")

    else:
        print("❌ BUFFER STILL DOESN'T HELP (even with early payoff)")
        print()
        print(f"Best buffer: {optimal_buffer} years")
        print(f"Investment needed: ${optimal_result['investment']:,.0f}")
        print(f"Baseline (no buffer): ${baseline_result['investment']:,.0f}")
        print()
        print("The cash opportunity cost still exceeds the crash-avoidance benefit.")
        print("Stick with 100% stocks strategy.")

    print()

    # Show detailed year-by-year for optimal buffer
    print("=" * 70)
    print(f"YEAR-BY-YEAR DETAILS: {optimal_buffer}-YEAR BUFFER (OPTIMAL)")
    print("=" * 70)
    print()

    _, _, _, yearly = simulate_with_buffer_and_early_payoff(
        optimal_result['investment'],
        returns_2000,
        annual_payment,
        mortgage_balance,
        optimal_buffer
    )

    print("Year | Actual | Return  | Total Balance | Cash    | Stocks  | Mortgage | Can Payoff?")
    print("-----|--------|---------|---------------|---------|---------|----------|------------")

    for y in yearly[:10]:  # Show first 10 years
        actual_year = 2000 + y['year'] - 1
        can_payoff = "✓ YES" if y['can_payoff_early'] else ""

        print(f"{y['year']:4d} | {actual_year} | {y['return']:>+6.2f}% | "
              f"${y['balance']:>12,.0f} | ${y['cash']:>6,.0f} | "
              f"${y['stocks']:>6,.0f} | ${y['remaining_mortgage']:>7,.0f} | {can_payoff}")

    if len(yearly) > 10:
        print("...")
        last_year = yearly[-1]
        actual_year = 2000 + last_year['year'] - 1
        can_payoff = "✓ YES" if last_year['can_payoff_early'] else ""

        print(f"{last_year['year']:4d} | {actual_year} | {last_year['return']:>+6.2f}% | "
              f"${last_year['balance']:>12,.0f} | ${last_year['cash']:>6,.0f} | "
              f"${last_year['stocks']:>6,.0f} | ${last_year['remaining_mortgage']:>7,.0f} | {can_payoff}")

    print()
    print(f"Mortgage paid off in year {optimal_result['years']} with ${optimal_result['leftover']:,.0f} remaining")
    print()


if __name__ == "__main__":
    test_2000_2024_with_buffers()
