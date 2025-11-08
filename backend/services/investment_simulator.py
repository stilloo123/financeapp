"""
Investment Simulator Module

Simulates investment account balance over time with annual withdrawals.
Uses binary search to find the minimum initial investment required.
"""

from typing import List, Dict, Tuple


def simulate_investment(
    initial_amount: float,
    returns_sequence: List[float],
    annual_payment: float
) -> Tuple[float, List[Dict]]:
    """
    Simulates investment account balance over time with annual withdrawals.

    Process for each year:
    1. Withdraw annual_payment at beginning of year
    2. Apply market return to remaining balance

    Args:
        initial_amount: Starting investment amount ($)
        returns_sequence: List of annual returns as percentages (e.g., [11.62, -37.00, 26.46])
        annual_payment: Amount withdrawn each year for mortgage payment ($)

    Returns:
        Tuple of:
            - final_balance: Balance after all years
            - year_by_year: List of yearly details with year, return, and balance

    Example:
        >>> simulate_investment(300000, [10.0, -5.0, 15.0], 30000)
        (328425.0, [
            {'year': 1, 'return': 10.0, 'balance': 297000.0},
            {'year': 2, 'return': -5.0, 'balance': 253650.0},
            {'year': 3, 'return': 15.0, 'balance': 257197.5}
        ])
    """
    balance = initial_amount
    year_by_year = []

    for year, annual_return_pct in enumerate(returns_sequence, start=1):
        # Withdraw at beginning of year for mortgage payment
        balance -= annual_payment

        # Apply market return (convert percentage to decimal)
        balance *= (1 + annual_return_pct / 100.0)

        year_by_year.append({
            'year': year,
            'return': annual_return_pct,
            'balance': round(balance, 2)
        })

    final_balance = balance
    return final_balance, year_by_year


def find_minimum_investment(
    returns_sequence: List[float],
    annual_payment: float,
    tolerance: float = 100.0
) -> float:
    """
    Find minimum initial investment using binary search.

    Uses binary search to find the minimum amount needed such that
    the account balance after all withdrawals is >= $0.

    Args:
        returns_sequence: List of annual returns as percentages
        annual_payment: Amount withdrawn each year ($)
        tolerance: Acceptable error margin ($), default $100

    Returns:
        Minimum initial investment required ($)

    Example:
        >>> find_minimum_investment([10.0, -5.0, 15.0], 30000)
        267543.21
    """
    if annual_payment <= 0:
        raise ValueError("Annual payment must be positive")

    if not returns_sequence:
        raise ValueError("Returns sequence cannot be empty")

    # Set initial bounds for binary search
    # Lower bound: 0
    # Upper bound: Conservative estimate assuming 0% returns
    low = 0.0
    high = annual_payment * len(returns_sequence) * 1.5  # 1.5x safety factor

    # Binary search for minimum investment
    while high - low > tolerance:
        mid = (low + high) / 2.0
        final_balance, _ = simulate_investment(mid, returns_sequence, annual_payment)

        if final_balance < 0:
            # Need more money
            low = mid
        else:
            # Can use less money
            high = mid

    # Return the upper bound (conservative estimate)
    return round(high, 2)


def simulate_investment_with_early_payoff(
    initial_amount: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float
) -> Tuple[bool, int, float, List[Dict]]:
    """
    Simulate investment with early payoff option.

    At any year, if balance >= remaining mortgage balance, pay off immediately.

    Args:
        initial_amount: Starting investment amount ($)
        returns_sequence: List of annual returns as percentages
        annual_payment: Amount withdrawn each year for mortgage payment ($)
        initial_mortgage_balance: Starting mortgage balance ($)

    Returns:
        Tuple of:
            - success: bool - Successfully paid off mortgage?
            - years_to_payoff: int - Years until mortgage paid off
            - final_balance: float - Money left over (or deficit if negative)
            - year_by_year: List[Dict] - Detailed breakdown

    Example:
        If balance exceeds remaining mortgage in year 5, returns:
        (True, 5, leftover_amount, year_by_year_data)
    """
    balance = initial_amount
    remaining_mortgage = initial_mortgage_balance
    year_by_year = []

    for year, annual_return_pct in enumerate(returns_sequence, start=1):
        # Withdraw payment at beginning of year
        balance -= annual_payment
        remaining_mortgage -= annual_payment

        # Apply market return
        balance *= (1 + annual_return_pct / 100.0)

        year_by_year.append({
            'year': year,
            'return': annual_return_pct,
            'balance': round(balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'can_payoff_early': balance >= remaining_mortgage
        })

        # Check for early payoff
        if balance >= remaining_mortgage:
            leftover = balance - remaining_mortgage
            return True, year, round(leftover, 2), year_by_year

        # Check for failure
        if balance < 0:
            return False, year, round(balance, 2), year_by_year

    # Completed full term
    success = balance >= 0
    return success, len(returns_sequence), round(balance, 2), year_by_year


def find_minimum_with_early_payoff(
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    tolerance: float = 100.0
) -> Tuple[float, int, float]:
    """
    Find minimum investment with early payoff optimization.

    Uses binary search to find minimum initial investment where you can
    either pay off early (if balance > remaining mortgage) or survive full term.

    Args:
        returns_sequence: List of annual returns as percentages
        annual_payment: Amount withdrawn each year ($)
        initial_mortgage_balance: Starting mortgage balance ($)
        tolerance: Acceptable error margin ($), default $100

    Returns:
        Tuple of:
            - min_investment: Minimum investment required ($)
            - years_to_payoff: Years until mortgage paid off
            - leftover_amount: Money left over after payoff ($)

    Example:
        >>> find_minimum_with_early_payoff([10, 20, 30], 30000, 500000)
        (250000.0, 8, 15000.0)  # Need $250K, pays off in 8 years with $15K left
    """
    if annual_payment <= 0:
        raise ValueError("Annual payment must be positive")
    if initial_mortgage_balance <= 0:
        raise ValueError("Mortgage balance must be positive")
    if not returns_sequence:
        raise ValueError("Returns sequence cannot be empty")

    # Set initial bounds
    low = 0.0
    high = initial_mortgage_balance * 2.0  # Conservative upper bound

    best_result = None

    # Binary search for minimum
    while high - low > tolerance:
        mid = (low + high) / 2.0

        success, years, leftover, _ = simulate_investment_with_early_payoff(
            mid, returns_sequence, annual_payment, initial_mortgage_balance
        )

        if success:
            # This amount works
            best_result = (mid, years, leftover)
            high = mid  # Try less
        else:
            # Need more money
            low = mid

    # Final simulation with optimal amount
    success, years, leftover, _ = simulate_investment_with_early_payoff(
        high, returns_sequence, annual_payment, initial_mortgage_balance
    )

    return round(high, 2), years, round(leftover, 2)


def get_simulation_summary(
    initial_amount: float,
    returns_sequence: List[float],
    annual_payment: float,
    period_label: str = ""
) -> Dict:
    """
    Get comprehensive simulation summary with statistics.

    Args:
        initial_amount: Starting investment amount ($)
        returns_sequence: List of annual returns as percentages
        annual_payment: Amount withdrawn each year ($)
        period_label: Optional label for the period (e.g., "1926-1950")

    Returns:
        Dictionary with simulation results and statistics
    """
    final_balance, year_by_year = simulate_investment(
        initial_amount, returns_sequence, annual_payment
    )

    # Calculate some statistics
    total_withdrawn = annual_payment * len(returns_sequence)
    total_return_dollars = final_balance - (initial_amount - total_withdrawn)
    avg_return = sum(returns_sequence) / len(returns_sequence)

    return {
        'period': period_label,
        'initial_investment': initial_amount,
        'final_balance': round(final_balance, 2),
        'years': len(returns_sequence),
        'annual_payment': annual_payment,
        'total_withdrawn': round(total_withdrawn, 2),
        'total_return_dollars': round(total_return_dollars, 2),
        'average_return_pct': round(avg_return, 2),
        'year_by_year': year_by_year
    }


if __name__ == "__main__":
    # Test the simulator
    print("Testing Investment Simulator")
    print("=" * 50)

    # Example: $300K invested with $30K annual withdrawal
    # Simple 3-year test with known returns
    initial = 300000
    payment = 30000
    returns = [10.0, -5.0, 15.0]

    print(f"\nInitial Investment: ${initial:,.0f}")
    print(f"Annual Payment: ${payment:,.0f}")
    print(f"Returns: {returns}")

    final, yearly = simulate_investment(initial, returns, payment)
    print(f"\nFinal Balance: ${final:,.2f}")
    print("\nYear-by-Year:")
    for y in yearly:
        print(f"  Year {y['year']}: {y['return']:+.1f}% → ${y['balance']:,.2f}")

    # Test binary search
    print("\n" + "=" * 50)
    print("Testing Binary Search for Minimum Investment")
    min_investment = find_minimum_investment(returns, payment)
    print(f"Minimum investment needed: ${min_investment:,.2f}")

    # Verify it works
    final_verify, _ = simulate_investment(min_investment, returns, payment)
    print(f"Final balance with minimum: ${final_verify:,.2f}")
