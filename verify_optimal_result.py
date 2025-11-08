"""
Verify the optimal algorithm's surprising result:
$33K stocks + $377K cash = $410K for 2000-2024

Compare to manual result: $390K stocks + $100K cash = $490K
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment
from backend.services.optimal_allocator import simulate_smart_withdrawal


def main():
    print("=" * 90)
    print("VERIFY OPTIMAL ALGORITHM RESULT")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    returns_2000 = loader.get_returns(2000, 2024)

    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    # Test both allocations
    allocations = [
        ("Optimal Algorithm", 32862, 377295),
        ("Manual Grid Search", 390000, 100000),
    ]

    print("Testing both allocations on 2000-2024:")
    print()

    for name, stock, cash in allocations:
        total = stock + cash
        result = simulate_smart_withdrawal(
            stock, cash, returns_2000, annual_payment, mortgage_balance
        )

        print(f"{name}:")
        print(f"  Allocation: ${stock:,} stocks + ${cash:,} cash = ${total:,} total")
        print(f"  Stock ratio: {stock/total*100:.1f}%")

        if result['success']:
            print(f"  ✅ SUCCESS - Paid off in {result['years_to_payoff']} years")
            print(f"  Leftover: ${result['leftover']:,.2f}")
        else:
            print(f"  ❌ FAILED in year {result['years_to_payoff']}")
            print(f"  Shortfall: ${abs(result['leftover']):,.2f}")

        print()

        # Show year-by-year for first 10 years
        print(f"  First 10 years:")
        print(f"  Year | Return  | Stocks  | Cash    | Total   | Source")
        print(f"  -----|---------|---------|---------|---------|-------------------------")

        for y in result['year_by_year'][:10]:
            print(f"  {y['year']:4d} | {y['return']:>+6.2f}% | ${y['stock_balance']:>6,.0f} | "
                  f"${y['cash_balance']:>6,.0f} | ${y['total_balance']:>6,.0f} | "
                  f"{y['withdrawal_source'][:23]:23s}")

        print()
        print("-" * 90)
        print()

    # Analysis
    print("=" * 90)
    print("ANALYSIS: Why is Optimal Algorithm Better?")
    print("=" * 90)
    print()

    print("The key difference is the CASH STRATEGY:")
    print()
    print("Optimal Algorithm ($33K stocks, $377K cash):")
    print("  • Starts with HUGE cash buffer")
    print("  • Cash can fund ~13 years of payments ($377K / $28.7K)")
    print("  • Stocks barely matter - they're almost irrelevant")
    print("  • Strategy: Use cash for everything, let tiny stock position compound")
    print("  • Cash earns 3.7% which is ABOVE mortgage rate 3.0%!")
    print()

    print("Manual Grid Search ($390K stocks, $100K cash):")
    print("  • Starts with BIG stock position")
    print("  • Cash can fund ~3.5 years of payments")
    print("  • Relies on stocks recovering after crashes")
    print("  • Strategy: Protect stocks during crashes, use them in good years")
    print()

    print("=" * 90)
    print("THE SURPRISING TRUTH")
    print("=" * 90)
    print()

    print("Since CASH RATE (3.7%) > MORTGAGE RATE (3.0%):")
    print()
    print("  • Keeping money in cash MAKES MONEY (0.7% spread)")
    print("  • Cash compounds at 3.7% while mortgage costs 3.0%")
    print("  • This is basically a TREASURY-LIKE strategy!")
    print()

    print("The 'optimal' solution found:")
    print("  • Minimize risky stocks ($33K)")
    print("  • Maximize safe cash ($377K)")
    print("  • Total: $410K")
    print()

    treasury = 433032
    print(f"Compare to treasury ladder: ${treasury:,}")
    print(f"  Optimal algo saves: ${treasury - 410156:,} ({(treasury - 410156)/treasury*100:.1f}%)")
    print()

    print("This explains why:")
    print("  1. Algorithm found mostly-cash solution")
    print("  2. It beats treasury slightly ($23K less)")
    print("  3. It's much safer than $390K stocks + $100K cash")
    print()


if __name__ == "__main__":
    main()
