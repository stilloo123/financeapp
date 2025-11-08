"""
Test: $5M Portfolio, $200K/year spending (including $28.7K mortgage)

Living expenses = $200K - $28,714 = $171,286/year

Compare:
A) Pay off mortgage: $4.5M portfolio, withdraw $171,286/year
B) Keep invested: $5M portfolio, withdraw $200K/year
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from statistics import mean, median


def simulate_portfolio(initial_amount, returns_sequence, annual_withdrawal):
    """Simulate portfolio with fixed annual withdrawal."""
    balance = initial_amount
    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        balance -= annual_withdrawal
        balance *= (1 + stock_return / 100.0)

        year_by_year.append({
            'year': year,
            'balance': balance
        })

    return {
        'final_balance': balance,
        'year_by_year': year_by_year
    }


def main():
    print("=" * 90)
    print("$5M PORTFOLIO TEST: $200K/year total spending")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    mortgage_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    total_assets = 5000000
    total_spending = 200000
    living_expenses = total_spending - mortgage_payment

    print(f"Your situation:")
    print(f"  Total assets: ${total_assets:,}")
    print(f"  Total spending: ${total_spending:,}/year")
    print(f"  Mortgage payment: ${mortgage_payment:,.2f}/year")
    print(f"  Living expenses: ${living_expenses:,.2f}/year")
    print()

    # Calculate withdrawal rates
    rate_a = living_expenses / (total_assets - 500000) * 100
    rate_b = total_spending / total_assets * 100

    print("=" * 90)
    print("WITHDRAWAL RATE COMPARISON")
    print("=" * 90)
    print()

    print(f"Strategy A: Pay Off $500K Mortgage")
    print(f"  Portfolio: ${total_assets - 500000:,}")
    print(f"  Annual withdrawal: ${living_expenses:,.2f}")
    print(f"  Withdrawal rate: {rate_a:.2f}%")
    print()

    print(f"Strategy B: Keep Invested")
    print(f"  Portfolio: ${total_assets:,}")
    print(f"  Annual withdrawal: ${total_spending:,.2f}")
    print(f"  Withdrawal rate: {rate_b:.2f}%")
    print()

    if rate_a < rate_b:
        print(f"⚠️ Strategy A has LOWER withdrawal rate ({rate_a:.2f}% vs {rate_b:.2f}%)")
        print(f"   Paying off might be better!")
    else:
        print(f"✅ Strategy B has LOWER withdrawal rate ({rate_b:.2f}% vs {rate_a:.2f}%)")
        print(f"   Keeping invested is better!")

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

    # Test both strategies
    results_a = []
    results_b = []

    for window in all_windows:
        # Strategy A: Pay off
        result_a = simulate_portfolio(total_assets - 500000, window['returns'], living_expenses)
        results_a.append(result_a['final_balance'])

        # Strategy B: Keep invested
        result_b = simulate_portfolio(total_assets, window['returns'], total_spending)
        results_b.append(result_b['final_balance'])

    # Calculate statistics
    avg_a = mean(results_a)
    median_a = median(results_a)
    min_a = min(results_a)
    max_a = max(results_a)

    avg_b = mean(results_b)
    median_b = median(results_b)
    min_b = min(results_b)
    max_b = max(results_b)

    # Count successes (positive balance)
    success_a = sum(1 for r in results_a if r >= 0)
    success_b = sum(1 for r in results_b if r >= 0)

    print("=" * 90)
    print("HISTORICAL BACKTEST RESULTS (25 years)")
    print("=" * 90)
    print()

    print(f"Strategy A: Pay Off Mortgage")
    print(f"  Success rate: {success_a}/{len(results_a)} ({success_a/len(results_a)*100:.1f}%)")
    print(f"  Average final balance: ${avg_a:,.0f}")
    print(f"  Median final balance: ${median_a:,.0f}")
    print(f"  Minimum: ${min_a:,.0f}")
    print(f"  Maximum: ${max_a:,.0f}")
    print()

    print(f"Strategy B: Keep Invested")
    print(f"  Success rate: {success_b}/{len(results_b)} ({success_b/len(results_b)*100:.1f}%)")
    print(f"  Average final balance: ${avg_b:,.0f}")
    print(f"  Median final balance: ${median_b:,.0f}")
    print(f"  Minimum: ${min_b:,.0f}")
    print(f"  Maximum: ${max_b:,.0f}")
    print()

    # Compare
    wins_a = sum(1 for i in range(len(results_a)) if results_a[i] > results_b[i])
    wins_b = sum(1 for i in range(len(results_b)) if results_b[i] > results_a[i])

    print("=" * 90)
    print("HEAD-TO-HEAD COMPARISON")
    print("=" * 90)
    print()

    print(f"Strategy A wins: {wins_a}/{len(all_windows)} scenarios ({wins_a/len(all_windows)*100:.1f}%)")
    print(f"Strategy B wins: {wins_b}/{len(all_windows)} scenarios ({wins_b/len(all_windows)*100:.1f}%)")
    print()

    if avg_a > avg_b:
        diff = avg_a - avg_b
        print(f"✅ PAY OFF wins by ${diff:,.0f} on average")
        print()
        print(f"After 25 years:")
        print(f"  Pay off: ${avg_a:,.0f} average")
        print(f"  Invest: ${avg_b:,.0f} average")
    else:
        diff = avg_b - avg_a
        print(f"✅ INVEST wins by ${diff:,.0f} on average")
        print()
        print(f"After 25 years:")
        print(f"  Invest: ${avg_b:,.0f} average")
        print(f"  Pay off: ${avg_a:,.0f} average")

    print()

    # Test on 2000-2024 specifically
    returns_2000 = loader.get_returns(2000, 2024)

    result_a_2000 = simulate_portfolio(total_assets - 500000, returns_2000, living_expenses)
    result_b_2000 = simulate_portfolio(total_assets, returns_2000, total_spending)

    print("=" * 90)
    print("2000-2024 WORST CASE")
    print("=" * 90)
    print()

    print(f"Strategy A (Pay off): ${result_a_2000['final_balance']:,.0f}")
    print(f"Strategy B (Invest): ${result_b_2000['final_balance']:,.0f}")
    print()

    if result_a_2000['final_balance'] > result_b_2000['final_balance']:
        diff = result_a_2000['final_balance'] - result_b_2000['final_balance']
        print(f"✅ Pay off wins by ${diff:,.0f} in worst case")
    else:
        diff = result_b_2000['final_balance'] - result_a_2000['final_balance']
        print(f"✅ Invest wins by ${diff:,.0f} in worst case")

    print()

    # Show year-by-year for 2000-2024
    print("Year-by-year comparison (2000-2024):")
    print()
    print("Year | Pay Off Balance | Invest Balance | Difference")
    print("-----|-----------------|----------------|------------")

    for i in [0, 4, 9, 14, 19, 24]:  # Sample years
        if i < len(result_a_2000['year_by_year']):
            bal_a = result_a_2000['year_by_year'][i]['balance']
            bal_b = result_b_2000['year_by_year'][i]['balance']
            diff = bal_a - bal_b

            print(f"{i+1:4d} | ${bal_a:>14,.0f} | ${bal_b:>14,.0f} | ${diff:>+11,.0f}")

    print()

    # Final recommendation
    print("=" * 90)
    print("RECOMMENDATION FOR YOUR SITUATION")
    print("=" * 90)
    print()

    print(f"With ${total_assets:,} assets and ${total_spending:,}/year spending:")
    print()

    # Compare both withdrawal rates and average outcomes
    if rate_a < rate_b and avg_a > avg_b:
        print(f"✅ CLEAR WINNER: Pay Off the Mortgage")
        print()
        print(f"Reasons:")
        print(f"  • Lower withdrawal rate ({rate_a:.2f}% vs {rate_b:.2f}%)")
        print(f"  • Better average outcome (${avg_a:,.0f} vs ${avg_b:,.0f})")
        print(f"  • Wins {wins_a/len(all_windows)*100:.0f}% of historical scenarios")
        print()
        print(f"Benefits:")
        print(f"  • Eliminate mortgage payment of ${mortgage_payment:,.2f}/year")
        print(f"  • Reduce annual spending from ${total_spending:,.0f} to ${living_expenses:,.0f}")
        print(f"  • Portfolio lasts longer with lower withdrawal rate")
        print(f"  • Peace of mind being debt-free")
    elif rate_b < rate_a and avg_b > avg_a:
        print(f"✅ CLEAR WINNER: Keep the Money Invested")
        print()
        print(f"Reasons:")
        print(f"  • Lower withdrawal rate ({rate_b:.2f}% vs {rate_a:.2f}%)")
        print(f"  • Better average outcome (${avg_b:,.0f} vs ${avg_a:,.0f})")
        print(f"  • Wins {wins_b/len(all_windows)*100:.0f}% of historical scenarios")
    else:
        print(f"⚠️ MIXED RESULTS - Close call")
        print()
        print(f"  Withdrawal rates: {rate_a:.2f}% (pay off) vs {rate_b:.2f}% (invest)")
        print(f"  Average outcomes: ${avg_a:,.0f} (pay off) vs ${avg_b:,.0f} (invest)")
        print()
        print(f"Both strategies are viable. Choose based on personal preference:")
        print(f"  • Pay off: Peace of mind, debt-free")
        print(f"  • Invest: Mathematical slight edge")

    print()

    # Show the impact of the $500K
    print("=" * 90)
    print("THE $500K IMPACT")
    print("=" * 90)
    print()

    pct_of_portfolio = 500000 / total_assets * 100
    print(f"$500K is {pct_of_portfolio:.1f}% of your ${total_assets:,} portfolio")
    print()

    mortgage_pct_of_spending = mortgage_payment / total_spending * 100
    print(f"Mortgage payment (${mortgage_payment:,.0f}) is {mortgage_pct_of_spending:.1f}% of your total spending")
    print()

    print("With a large portfolio, the mortgage becomes less significant:")
    print(f"  • Paying it off only reduces withdrawal by {mortgage_pct_of_spending:.1f}%")
    print(f"  • But it reduces your portfolio by {pct_of_portfolio:.1f}%")
    print(f"  • The trade-off becomes close!")

    print()


if __name__ == "__main__":
    main()
