"""
Backtest: Staged Deployment Strategy

Compare:
1. $500K all-stocks upfront
2. $300K initial + $200K reserve (earning 1% in money market)
   - Add from reserve only if needed
   - Reserve compounds at 1% while waiting

This shows the real expected value of the staged approach.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from typing import List, Dict


def simulate_all_stocks(
    initial_amount: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float
) -> Dict:
    """Simple all-stocks strategy."""
    balance = initial_amount
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        balance -= annual_payment
        remaining_mortgage -= annual_payment
        balance *= (1 + stock_return / 100.0)

        year_by_year.append({
            'year': year,
            'balance': balance,
            'remaining_mortgage': remaining_mortgage
        })

        # Early payoff?
        if balance >= remaining_mortgage:
            leftover = balance - remaining_mortgage
            return {
                'success': True,
                'years_to_payoff': year,
                'leftover': leftover,
                'capital_deployed': initial_amount,
                'year_by_year': year_by_year
            }

        # Failure?
        if balance < 0:
            return {
                'success': False,
                'years_to_payoff': year,
                'leftover': balance,
                'capital_deployed': initial_amount,
                'year_by_year': year_by_year
            }

    return {
        'success': balance >= 0,
        'years_to_payoff': len(returns_sequence),
        'leftover': balance,
        'capital_deployed': initial_amount,
        'year_by_year': year_by_year
    }


def simulate_smart_withdrawal(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    protected_base: float = 100000
) -> Dict:
    """Smart withdrawal with stock/cash allocation."""
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Smart withdrawal logic
        if stock_return < 0:
            # Market DOWN: Use cash
            if cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment
        else:
            # Market UP: Use stocks if above base
            if stock_balance > protected_base:
                stock_balance -= annual_payment
            elif cash_balance >= annual_payment:
                cash_balance -= annual_payment
            else:
                stock_balance -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037  # Cash earns 3.7%
        remaining_mortgage -= annual_payment

        total_balance = stock_balance + cash_balance

        year_by_year.append({
            'year': year,
            'stock_balance': stock_balance,
            'cash_balance': cash_balance,
            'total_balance': total_balance,
            'remaining_mortgage': remaining_mortgage
        })

        # Early payoff?
        if total_balance >= remaining_mortgage:
            leftover = total_balance - remaining_mortgage
            return {
                'success': True,
                'years_to_payoff': year,
                'leftover': leftover,
                'year_by_year': year_by_year
            }

        # Failure?
        if total_balance < 0:
            return {
                'success': False,
                'years_to_payoff': year,
                'leftover': total_balance,
                'year_by_year': year_by_year
            }

    return {
        'success': total_balance >= 0,
        'years_to_payoff': len(returns_sequence),
        'leftover': total_balance,
        'year_by_year': year_by_year
    }


def simulate_staged_deployment(
    initial_deployed: float,
    initial_deployed_stocks: float,
    initial_deployed_cash: float,
    reserve: float,
    reserve_rate: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float
) -> Dict:
    """
    Staged deployment strategy:
    - Start with $300K deployed ($240K stocks + $60K cash)
    - Keep $200K in reserve earning reserve_rate
    - Add from reserve only if needed
    """
    # Run initial deployment
    result = simulate_smart_withdrawal(
        initial_deployed_stocks,
        initial_deployed_cash,
        returns_sequence,
        annual_payment,
        initial_mortgage_balance
    )

    # Reserve compounds while waiting
    reserve_balance = reserve

    if result['success']:
        # Didn't need reserve!
        years = result['years_to_payoff']
        # Reserve grew at reserve_rate for those years
        final_reserve = reserve * ((1 + reserve_rate / 100.0) ** years)

        total_leftover = result['leftover'] + final_reserve
        total_deployed = initial_deployed  # Only used initial

        return {
            'success': True,
            'years_to_payoff': years,
            'leftover': total_leftover,
            'initial_deployment': initial_deployed,
            'reserve_used': 0,
            'reserve_leftover': final_reserve,
            'total_capital_deployed': total_deployed,
            'needed_reserve': False
        }
    else:
        # Failed - would need to deploy reserve
        # This is a simplified model - in reality you'd add incrementally
        # For now, let's say we deploy all $500K from the start if initial fails

        # Re-simulate with full $500K
        full_result = simulate_all_stocks(
            500000,
            returns_sequence,
            annual_payment,
            initial_mortgage_balance
        )

        return {
            'success': full_result['success'],
            'years_to_payoff': full_result['years_to_payoff'],
            'leftover': full_result['leftover'],
            'initial_deployment': initial_deployed,
            'reserve_used': reserve,
            'reserve_leftover': 0,
            'total_capital_deployed': 500000,
            'needed_reserve': True
        }


def main():
    print("=" * 90)
    print("STAGED DEPLOYMENT BACKTEST")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    print(f"Mortgage: ${mortgage_balance:,} at {mortgage_rate}%")
    print(f"Annual Payment: ${annual_payment:,.2f}")
    print()

    # Get all historical windows
    all_windows = []
    for start_year in range(1926, 2001):
        end_year = start_year + 24
        if end_year <= 2025:
            try:
                returns = loader.get_returns(start_year, end_year)
                if len(returns) == 25:
                    all_windows.append({
                        'period': f"{start_year}-{end_year}",
                        'start_year': start_year,
                        'returns': returns
                    })
            except:
                pass

    print(f"Testing across {len(all_windows)} historical 25-year periods")
    print()

    # Test strategies
    print("=" * 90)
    print("STRATEGY COMPARISON")
    print("=" * 90)
    print()

    results_500k = []
    results_staged = []

    for window in all_windows:
        # Strategy 1: $500K all-stocks upfront
        result_500k = simulate_all_stocks(
            500000, window['returns'], annual_payment, mortgage_balance
        )
        results_500k.append({
            'period': window['period'],
            **result_500k
        })

        # Strategy 2: Staged deployment
        result_staged = simulate_staged_deployment(
            initial_deployed=300000,
            initial_deployed_stocks=240000,
            initial_deployed_cash=60000,
            reserve=200000,
            reserve_rate=1.0,  # Conservative 1% on reserve
            returns_sequence=window['returns'],
            annual_payment=annual_payment,
            initial_mortgage_balance=mortgage_balance
        )
        results_staged.append({
            'period': window['period'],
            **result_staged
        })

    # Calculate statistics
    from statistics import mean, median

    # $500K all-stocks
    leftover_500k = [r['leftover'] for r in results_500k if r['success']]
    years_500k = [r['years_to_payoff'] for r in results_500k if r['success']]
    success_500k = sum(1 for r in results_500k if r['success'])

    # Staged deployment
    leftover_staged = [r['leftover'] for r in results_staged if r['success']]
    years_staged = [r['years_to_payoff'] for r in results_staged if r['success']]
    success_staged = sum(1 for r in results_staged if r['success'])
    needed_reserve = sum(1 for r in results_staged if r.get('needed_reserve', False))

    print("Strategy 1: $500K All-Stocks Upfront")
    print(f"  Success rate: {success_500k}/{len(results_500k)} ({success_500k/len(results_500k)*100:.1f}%)")
    if leftover_500k:
        print(f"  Average leftover: ${mean(leftover_500k):,.0f}")
        print(f"  Median leftover: ${median(leftover_500k):,.0f}")
        print(f"  Average years to payoff: {mean(years_500k):.1f}")
        print(f"  Median years to payoff: {median(years_500k):.0f}")
    print()

    print("Strategy 2: Staged Deployment ($300K initial + $200K reserve at 1%)")
    print(f"  Success rate: {success_staged}/{len(results_staged)} ({success_staged/len(results_staged)*100:.1f}%)")
    if leftover_staged:
        print(f"  Average leftover: ${mean(leftover_staged):,.0f}")
        print(f"  Median leftover: ${median(leftover_staged):,.0f}")
        print(f"  Average years to payoff: {mean(years_staged):.1f}")
        print(f"  Median years to payoff: {median(years_staged):.0f}")
    print(f"  Needed to tap reserve: {needed_reserve}/{len(results_staged)} ({needed_reserve/len(results_staged)*100:.1f}%)")
    print()

    # Key comparison
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    print()

    # Calculate expected value
    # Staged: 70% don't need reserve, 30% do
    reserve_not_needed = [r for r in results_staged if not r.get('needed_reserve', False)]
    reserve_needed = [r for r in results_staged if r.get('needed_reserve', False)]

    if reserve_not_needed:
        avg_leftover_no_reserve = mean([r['leftover'] for r in reserve_not_needed if r['success']])
        print(f"When reserve NOT needed ({len(reserve_not_needed)} scenarios):")
        print(f"  Average total leftover: ${avg_leftover_no_reserve:,.0f}")
        print(f"  (This includes $200K reserve that grew at 1%)")
        print()

    if reserve_needed:
        avg_leftover_with_reserve = mean([r['leftover'] for r in reserve_needed if r['success']])
        print(f"When reserve WAS needed ({len(reserve_needed)} scenarios):")
        print(f"  Average leftover: ${avg_leftover_with_reserve:,.0f}")
        print(f"  (Used all $500K)")
        print()

    # Expected value calculation
    pct_no_reserve = len(reserve_not_needed) / len(results_staged) * 100
    pct_with_reserve = len(reserve_needed) / len(results_staged) * 100

    print(f"Expected Value Analysis:")
    print(f"  {pct_no_reserve:.1f}% scenarios: Keep ~$200K+ extra (didn't need reserve)")
    print(f"  {pct_with_reserve:.1f}% scenarios: Use all $500K (same as upfront strategy)")
    print()

    if leftover_500k and leftover_staged:
        diff = mean(leftover_staged) - mean(leftover_500k)
        print(f"Average leftover difference: ${diff:,.0f}")
        if diff > 0:
            print(f"  ✅ Staged deployment wins by ${diff:,.0f} on average!")
        else:
            print(f"  ❌ $500K upfront wins by ${abs(diff):,.0f} on average")

    print()

    # Show some specific examples
    print("=" * 90)
    print("SPECIFIC EXAMPLES")
    print("=" * 90)
    print()

    # Best case for staged
    best_staged = max([r for r in results_staged if r['success']],
                     key=lambda x: x['leftover'])
    print(f"Best case for staged deployment: {best_staged['period']}")
    print(f"  Leftover: ${best_staged['leftover']:,.0f}")
    print(f"  Years: {best_staged['years_to_payoff']}")
    print(f"  Needed reserve: {'Yes' if best_staged.get('needed_reserve') else 'No'}")
    print()

    # Worst case where reserve was needed
    worst_needed_reserve = [r for r in results_staged if r.get('needed_reserve', False) and r['success']]
    if worst_needed_reserve:
        worst = min(worst_needed_reserve, key=lambda x: x['leftover'])
        print(f"Worst case that needed reserve: {worst['period']}")
        print(f"  Leftover: ${worst['leftover']:,.0f}")
        print(f"  Years: {worst['years_to_payoff']}")
        print()

    # Compare 2000-2024
    staged_2000 = [r for r in results_staged if r['period'] == '2000-2024'][0]
    stock_2000 = [r for r in results_500k if r['period'] == '2000-2024'][0]

    print(f"2000-2024 (worst case) comparison:")
    print(f"  $500K upfront: {stock_2000['years_to_payoff']} years, ${stock_2000['leftover']:,.0f} leftover")
    print(f"  Staged: {staged_2000['years_to_payoff']} years, ${staged_2000['leftover']:,.0f} leftover")
    print(f"  Needed reserve: {'Yes' if staged_2000.get('needed_reserve') else 'No'}")
    print()

    # Final recommendation
    print("=" * 90)
    print("RECOMMENDATION")
    print("=" * 90)
    print()

    print(f"With {pct_no_reserve:.0f}% chance of NOT needing the $200K reserve:")
    print()
    print(f"Expected outcome with STAGED approach:")
    if reserve_not_needed and reserve_needed:
        expected = (len(reserve_not_needed) / len(results_staged) * avg_leftover_no_reserve +
                   len(reserve_needed) / len(results_staged) * avg_leftover_with_reserve)
        print(f"  Expected leftover: ${expected:,.0f}")
        print()

        upfront_expected = mean(leftover_500k) if leftover_500k else 0
        print(f"Expected outcome with $500K UPFRONT:")
        print(f"  Expected leftover: ${upfront_expected:,.0f}")
        print()

        if expected > upfront_expected:
            benefit = expected - upfront_expected
            print(f"✅ STAGED deployment wins by ${benefit:,.0f} expected value!")
            print()
            print("Recommendation: Start with $300K ($240K stocks + $60K cash)")
            print("                Keep $200K in 1% money market as backup")
        else:
            print(f"❌ $500K upfront is better by ${upfront_expected - expected:,.0f}")
            print()
            print("Recommendation: Just invest all $500K in stocks upfront")

    print()


if __name__ == "__main__":
    main()
