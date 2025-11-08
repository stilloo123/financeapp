"""
Quick Test: Cash Buffer Strategy
Test 2000-2024 period with buffer sizes 0-5 years to validate hypothesis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.services.investment_simulator import find_minimum_investment
from typing import List, Tuple


def simulate_with_cash_buffer(
    initial_investment: float,
    returns_sequence: List[float],
    annual_payment: float,
    buffer_years: int
) -> float:
    """
    Simulate investment with cash buffer.

    Returns final balance (negative if ran out of money)
    """
    if buffer_years == 0:
        # Special case: 100% stocks (use existing simulator)
        from backend.services.investment_simulator import simulate_investment
        final_balance, _ = simulate_investment(initial_investment, returns_sequence, annual_payment)
        return final_balance

    # Initial allocation
    cash_target = annual_payment * buffer_years
    cash_balance = min(cash_target, initial_investment)
    stock_balance = initial_investment - cash_balance

    for year_idx, stock_return_pct in enumerate(returns_sequence):
        # Start of year: Withdraw from cash
        cash_balance -= annual_payment

        # Cash earns 2% (money market / short-term bonds)
        cash_balance *= 1.02

        # Stocks earn market return
        stock_balance *= (1 + stock_return_pct / 100.0)

        # Replenishment logic
        if cash_balance < annual_payment:
            # CRITICAL: Must replenish (less than 1 year left)
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance)
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return_pct > 10 and cash_balance < cash_target:
            # Good year: Opportunistically top up buffer
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance * 0.3)  # Max 30% of stocks
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return_pct > 0 and cash_balance < cash_target * 0.7:
            # Positive year and buffer getting low: Partial replenish
            needed = (cash_target * 0.8) - cash_balance
            transfer = min(needed, stock_balance * 0.2)
            stock_balance -= transfer
            cash_balance += transfer
        # If negative return: Don't touch stocks unless critical (handled above)

        total_balance = cash_balance + stock_balance

        if total_balance < 0:
            # Ran out of money
            return -1

    final_balance = cash_balance + stock_balance
    return final_balance


def find_minimum_with_buffer(
    returns_sequence: List[float],
    annual_payment: float,
    buffer_years: int,
    tolerance: float = 100.0
) -> float:
    """Find minimum investment with given buffer size."""
    low = 0.0
    high = annual_payment * len(returns_sequence) * 1.5

    while high - low > tolerance:
        mid = (low + high) / 2.0
        final_balance = simulate_with_cash_buffer(
            mid, returns_sequence, annual_payment, buffer_years
        )

        if final_balance < 0:
            low = mid  # Need more
        else:
            high = mid  # Can use less

    return round(high, 2)


def test_buffer_strategy():
    """Test cash buffer strategy on 2000-2024 period."""
    print("=" * 70)
    print("CASH BUFFER STRATEGY - QUICK TEST")
    print("=" * 70)
    print()
    print("Testing 2000-2024 period (dot-com crash + 2008 financial crisis)")
    print("Annual payment: $28,078")
    print("Cash earns: 2%")
    print("Stocks earn: Historical S&P 500 returns")
    print()

    # Load data
    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)
    annual_payment = 28078

    # Test each buffer size
    results = {}

    print("Testing buffer sizes 0-5 years...")
    print()

    for buffer_years in range(0, 6):
        print(f"Testing {buffer_years}-year buffer...", end=" ", flush=True)
        min_investment = find_minimum_with_buffer(
            returns_2000, annual_payment, buffer_years
        )
        results[buffer_years] = min_investment
        print(f"${min_investment:,.2f}")

    # Find optimal
    optimal_buffer = min(results, key=results.get)
    optimal_investment = results[optimal_buffer]
    baseline_investment = results[0]

    # Display results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print("| Buffer Size | Min Investment | vs Baseline | vs 0-Year |")
    print("|-------------|----------------|-------------|-----------|")

    for buffer_years in range(0, 6):
        investment = results[buffer_years]
        diff_from_baseline = investment - baseline_investment
        diff_pct = (diff_from_baseline / baseline_investment) * 100

        is_optimal = "⭐ OPTIMAL" if buffer_years == optimal_buffer else ""
        marker = "  (baseline)" if buffer_years == 0 else f"{diff_from_baseline:+,.0f}"

        print(f"| {buffer_years} years      | ${investment:>10,.0f} | {marker:>11} | {diff_pct:>+6.1f}%  | {is_optimal}")

    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()

    if optimal_investment < baseline_investment:
        savings = baseline_investment - optimal_investment
        savings_pct = (savings / baseline_investment) * 100
        print(f"✅ BUFFER STRATEGY WORKS!")
        print()
        print(f"Optimal buffer: {optimal_buffer} years")
        print(f"Required investment: ${optimal_investment:,.2f}")
        print(f"Baseline (no buffer): ${baseline_investment:,.2f}")
        print(f"SAVINGS: ${savings:,.2f} ({savings_pct:.1f}% reduction)")
        print()
        print("RECOMMENDATION: Proceed with full implementation")
    else:
        increase = optimal_investment - baseline_investment
        increase_pct = (increase / baseline_investment) * 100
        print(f"❌ BUFFER STRATEGY DOES NOT HELP")
        print()
        print(f"Best buffer: {optimal_buffer} years")
        print(f"Required investment: ${optimal_investment:,.2f}")
        print(f"Baseline (no buffer): ${baseline_investment:,.2f}")
        print(f"INCREASE: ${increase:,.2f} ({increase_pct:.1f}% more needed)")
        print()
        print("RECOMMENDATION: Do NOT implement buffer strategy")

    print()

    return results, optimal_buffer, optimal_investment


if __name__ == "__main__":
    test_buffer_strategy()
