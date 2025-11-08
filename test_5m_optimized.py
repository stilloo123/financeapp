"""
$5M Portfolio with OPTIMIZED $500K mortgage allocation

Compare:
A) Pay off mortgage: $4.5M portfolio, withdraw $171K/year
B) Keep $500K with OPTIMAL allocation for mortgage, $4.5M for living

Test different splits of $500K to find the best allocation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median


def simulate_smart_mortgage_account(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: list,
    annual_payment: float,
    cash_rate: float = 0.037
):
    """Simulate the $500K mortgage account with smart withdrawals."""
    stock_balance = initial_stock
    cash_balance = initial_cash

    for stock_return in returns_sequence:
        # Smart withdrawal logic
        if stock_return < 0:
            # Market down: use cash first
            if cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment
        else:
            # Market up: use stocks
            if stock_balance > 0:
                stock_balance -= annual_payment
            else:
                cash_balance -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= (1 + cash_rate)

    return stock_balance + cash_balance


def simulate_living_account(
    initial_amount: float,
    returns_sequence: list,
    annual_withdrawal: float
):
    """Simulate the main living expenses account."""
    balance = initial_amount

    for stock_return in returns_sequence:
        balance -= annual_withdrawal
        balance *= (1 + stock_return / 100.0)

    return balance


def main():
    print("=" * 90)
    print("$5M PORTFOLIO WITH OPTIMIZED $500K MORTGAGE ALLOCATION")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    total_assets = 5000000
    living_expenses = 171286  # $200K - $28.7K mortgage

    print(f"Your situation:")
    print(f"  Total assets: ${total_assets:,}")
    print(f"  Living expenses: ${living_expenses:,}/year")
    print(f"  Mortgage payment: ${annual_payment:,.2f}/year")
    print()

    # Get all windows (excluding Great Depression)
    great_depression = ['1928-1952', '1929-1953', '1930-1954', '1931-1955']
    all_windows = []

    for start_year in range(1926, 2001):
        end_year = start_year + 24
        if end_year <= 2025:
            period = f"{start_year}-{end_year}"
            if period not in great_depression:
                try:
                    returns = loader.get_returns(start_year, end_year)
                    if len(returns) == 25:
                        all_windows.append({
                            'period': period,
                            'returns': returns
                        })
                except:
                    pass

    print(f"Testing across {len(all_windows)} historical periods...")
    print()

    # Step 1: Find optimal allocation for $500K mortgage piece
    print("=" * 90)
    print("STEP 1: TEST DIFFERENT SPLITS OF $500K FOR MORTGAGE")
    print("=" * 90)
    print()

    test_splits = [
        (500000, 0),       # 100% stocks
        (450000, 50000),   # 90% stocks, 10% cash
        (400000, 100000),  # 80% stocks, 20% cash
        (350000, 150000),  # 70% stocks, 30% cash
        (300000, 200000),  # 60% stocks, 40% cash
        (250000, 250000),  # 50% stocks, 50% cash
    ]

    print("Stocks  | Cash    | Success | Avg Leftover | Notes")
    print("--------|---------|---------|--------------|------------------")

    best_split = None
    best_leftover = -float('inf')

    for stocks, cash in test_splits:
        leftovers = []
        successes = 0

        for window in all_windows:
            final = simulate_smart_mortgage_account(
                stocks, cash, window['returns'], annual_payment
            )
            leftovers.append(final)
            if final >= 0:
                successes += 1

        success_rate = successes / len(all_windows) * 100
        avg_leftover = mean(leftovers)

        notes = "✅" if success_rate == 100 else ""

        print(f"${stocks:>6,} | ${cash:>6,} | {success_rate:>6.1f}% | ${avg_leftover:>11,.0f} | {notes}")

        if success_rate == 100 and avg_leftover > best_leftover:
            best_leftover = avg_leftover
            best_split = (stocks, cash)

    print()

    if best_split:
        optimal_stock, optimal_cash = best_split
        print(f"Optimal allocation for $500K:")
        print(f"  Stocks: ${optimal_stock:,} ({optimal_stock/500000*100:.0f}%)")
        print(f"  Cash:   ${optimal_cash:,} ({optimal_cash/500000*100:.0f}%)")
        print(f"  Average leftover: ${best_leftover:,.0f}")
    else:
        # Just pick the one with highest leftover even if not 100%
        optimal_stock, optimal_cash = test_splits[0]
        print(f"Using 100% stocks allocation (best available)")

    print()

    # Step 2: Simulate both strategies with optimal allocation
    print("=" * 90)
    print("STEP 2: FULL PORTFOLIO SIMULATION")
    print("=" * 90)
    print()

    results_a = []  # Pay off mortgage
    results_b = []  # Keep invested with optimal allocation
    mortgage_leftover = []  # What's left in mortgage account

    for window in all_windows:
        # Strategy A: Pay off mortgage
        # $4.5M invested, withdraw $171K/year for living
        final_a = simulate_living_account(4500000, window['returns'], living_expenses)
        results_a.append(final_a)

        # Strategy B: Keep $500K optimized for mortgage
        # $4.5M for living expenses
        living_final = simulate_living_account(4500000, window['returns'], living_expenses)

        # $500K optimized for mortgage payments
        mortgage_final = simulate_smart_mortgage_account(
            optimal_stock, optimal_cash, window['returns'], annual_payment
        )

        total_final_b = living_final + mortgage_final
        results_b.append(total_final_b)
        mortgage_leftover.append(mortgage_final)

    # Calculate statistics
    avg_a = mean(results_a)
    median_a = median(results_a)
    min_a = min(results_a)

    avg_b = mean(results_b)
    median_b = median(results_b)
    min_b = min(results_b)

    avg_mortgage_leftover = mean(mortgage_leftover)

    print("Strategy A: Pay Off Mortgage")
    print(f"  Portfolio: $4.5M (all for living)")
    print(f"  Withdraw: ${living_expenses:,}/year")
    print(f"  Average final: ${avg_a:,.0f}")
    print(f"  Median final: ${median_a:,.0f}")
    print(f"  Minimum: ${min_a:,.0f}")
    print()

    print("Strategy B: Keep $500K Optimized for Mortgage")
    print(f"  Living portfolio: $4.5M → withdraw ${living_expenses:,}/year")
    print(f"  Mortgage account: ${optimal_stock:,} stocks + ${optimal_cash:,} cash")
    print(f"  Mortgage account leftover: ${avg_mortgage_leftover:,.0f} average")
    print(f"  Total average final: ${avg_b:,.0f}")
    print(f"  Total median final: ${median_b:,.0f}")
    print(f"  Total minimum: ${min_b:,.0f}")
    print()

    # Compare
    wins_a = sum(1 for i in range(len(results_a)) if results_a[i] > results_b[i])
    wins_b = sum(1 for i in range(len(results_b)) if results_b[i] > results_a[i])

    print("=" * 90)
    print("RESULTS")
    print("=" * 90)
    print()

    print(f"Strategy A wins: {wins_a}/{len(all_windows)} scenarios ({wins_a/len(all_windows)*100:.1f}%)")
    print(f"Strategy B wins: {wins_b}/{len(all_windows)} scenarios ({wins_b/len(all_windows)*100:.1f}%)")
    print()

    if avg_b > avg_a:
        diff = avg_b - avg_a
        print(f"✅ KEEP INVESTED wins by ${diff:,.0f} on average")
        print()
        print(f"Breakdown:")
        print(f"  Living account ends at: ${avg_a:,.0f} (same for both)")
        print(f"  Mortgage account leftover: ${avg_mortgage_leftover:,.0f}")
        print(f"  Total benefit of keeping invested: ${diff:,.0f}")
    else:
        diff = avg_a - avg_b
        print(f"✅ PAY OFF wins by ${diff:,.0f} on average")

    print()

    # Show the benefit more clearly
    print("=" * 90)
    print("THE BENEFIT BREAKDOWN")
    print("=" * 90)
    print()

    print(f"If you pay off mortgage:")
    print(f"  You spend: $500,000 today")
    print(f"  You get: $0 back (mortgage is paid)")
    print(f"  Net 'cost': $500,000")
    print()

    print(f"If you keep $500K invested optimally:")
    print(f"  You keep: $500,000 working for you")
    print(f"  You pay: ${annual_payment:,.2f}/year for 25 years")
    print(f"  Total paid: ${annual_payment * 25:,.2f}")
    print(f"  Final leftover: ${avg_mortgage_leftover:,.0f} average")
    print()

    net_benefit = avg_mortgage_leftover
    print(f"✅ Net benefit: You end up with ${net_benefit:,.0f} from the mortgage account!")
    print()

    # 2000-2024 test
    returns_2000 = loader.get_returns(2000, 2024)

    final_a_2000 = simulate_living_account(4500000, returns_2000, living_expenses)
    living_2000 = simulate_living_account(4500000, returns_2000, living_expenses)
    mortgage_2000 = simulate_smart_mortgage_account(
        optimal_stock, optimal_cash, returns_2000, annual_payment
    )
    final_b_2000 = living_2000 + mortgage_2000

    print("=" * 90)
    print("2000-2024 WORST CASE")
    print("=" * 90)
    print()

    print(f"Strategy A (Pay off): ${final_a_2000:,.0f}")
    print(f"Strategy B (Keep invested):")
    print(f"  Living account: ${living_2000:,.0f}")
    print(f"  Mortgage account: ${mortgage_2000:,.0f}")
    print(f"  Total: ${final_b_2000:,.0f}")
    print()

    if final_b_2000 > final_a_2000:
        print(f"✅ Keep invested wins by ${final_b_2000 - final_a_2000:,.0f} even in worst case!")
    else:
        print(f"⚠️ Pay off wins by ${final_a_2000 - final_b_2000:,.0f} in worst case")

    print()

    # Final recommendation
    print("=" * 90)
    print("FINAL RECOMMENDATION")
    print("=" * 90)
    print()

    print(f"For your $5M portfolio with $200K/year spending:")
    print()

    if wins_b > wins_a * 2 and avg_mortgage_leftover > 0:
        print(f"✅ KEEP THE $500K INVESTED")
        print()
        print(f"Allocation for mortgage account:")
        print(f"  • ${optimal_stock:,} in S&P 500 stocks ({optimal_stock/500000*100:.0f}%)")
        print(f"  • ${optimal_cash:,} in high-yield savings ({optimal_cash/500000*100:.0f}%)")
        print()
        print(f"Benefits:")
        print(f"  • Wins {wins_b/len(all_windows)*100:.0f}% of historical scenarios")
        print(f"  • Average ${avg_mortgage_leftover:,.0f} leftover after 25 years")
        print(f"  • Better expected outcome by ${diff:,.0f}")
        print()
        print(f"How it works:")
        print(f"  • Down years: Withdraw ${annual_payment:,.2f} from cash (protect stocks)")
        print(f"  • Up years: Withdraw ${annual_payment:,.2f} from stocks (let them grow)")
    else:
        print(f"⚠️ Results are close - choose based on preference")

    print()


if __name__ == "__main__":
    main()
