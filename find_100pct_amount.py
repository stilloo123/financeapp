"""
Find minimum amount for 100% success (excluding Great Depression)

Great Depression periods to exclude:
- 1928-1952
- 1929-1953
- 1930-1954
- 1931-1955

Must succeed in 2000-2024 and all other modern periods.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


def simulate_full_term(initial_amount, returns_sequence, annual_payment):
    """Simulate for full 25 years."""
    balance = initial_amount

    for stock_return in returns_sequence:
        balance -= annual_payment
        balance *= (1 + stock_return / 100.0)

    return balance


def main():
    print("=" * 90)
    print("FIND MINIMUM FOR 100% SUCCESS (Excluding Great Depression)")
    print("=" * 90)
    print()

    loader = SP500DataLoader()
    mortgage_balance = 500000
    mortgage_rate = 3.0
    annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

    # Get all windows EXCEPT Great Depression
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

    print(f"Testing {len(all_windows)} periods (excluding {len(great_depression)} Great Depression)")
    print()

    # Test different amounts
    amounts = list(range(500000, 750001, 25000))  # $500K to $750K in $25K steps

    print("Amount  | Success | Failures | Worst Period | Worst Balance")
    print("--------|---------|----------|--------------|---------------")

    best_amount = None

    for amount in amounts:
        failures = []
        worst_balance = float('inf')
        worst_period = None

        for window in all_windows:
            final_balance = simulate_full_term(amount, window['returns'], annual_payment)

            if final_balance < 0:
                failures.append(window['period'])

            if final_balance < worst_balance:
                worst_balance = final_balance
                worst_period = window['period']

        success_rate = (len(all_windows) - len(failures)) / len(all_windows) * 100

        if len(failures) == 0 and best_amount is None:
            best_amount = amount

        status = "✅" if len(failures) == 0 else ""

        print(f"${amount:>6,} | {len(all_windows)-len(failures):>7}/{len(all_windows)} | {len(failures):>8} | "
              f"{worst_period:12s} | ${worst_balance:>12,.0f} {status}")

    print()

    if best_amount:
        print("=" * 90)
        print("MINIMUM AMOUNT FOR 100% SUCCESS (Excluding Great Depression)")
        print("=" * 90)
        print()
        print(f"Amount needed: ${best_amount:,}")
        print()

        # Test this amount on 2000-2024
        returns_2000 = loader.get_returns(2000, 2024)
        balance_2000 = simulate_full_term(best_amount, returns_2000, annual_payment)

        print(f"2000-2024 test:")
        print(f"  Starting amount: ${best_amount:,}")
        print(f"  Final balance: ${balance_2000:,.0f}")
        print()

        # Compare to $500K
        diff = best_amount - 500000
        print(f"vs. Paying off $500K now:")
        print(f"  Additional capital needed: ${diff:,} ({diff/500000*100:.1f}%)")
        print()

        # Calculate average final balance
        balances = []
        for window in all_windows:
            final = simulate_full_term(best_amount, window['returns'], annual_payment)
            balances.append(final)

        avg_final = sum(balances) / len(balances)
        median_final = sorted(balances)[len(balances)//2]

        print(f"Expected outcomes with ${best_amount:,}:")
        print(f"  Average final balance: ${avg_final:,.0f}")
        print(f"  Median final balance: ${median_final:,.0f}")
        print()

        print(f"Return on ${best_amount:,}:")
        print(f"  Invested: ${best_amount:,}")
        print(f"  Average return: ${avg_final:,.0f}")
        print(f"  Net gain: ${avg_final - best_amount:,.0f}")
        print(f"  Multiple: {avg_final / best_amount:.2f}x")
    else:
        print()
        print("❌ Could not find 100% success amount in tested range")
        print("   Try amounts > $750K")

    print()


if __name__ == "__main__":
    main()
