"""
Mortgage Calculator Module

Calculates mortgage payments using standard amortization formulas.
"""


def calculate_annual_payment(principal: float, annual_rate: float, years: int) -> float:
    """
    Calculate annual mortgage payment using amortization formula.

    Formula: PMT = P × [r(1+r)^n] / [(1+r)^n - 1]

    Args:
        principal: Mortgage balance ($)
        annual_rate: Annual interest rate (as percentage, e.g., 3.0 for 3%)
        years: Number of years remaining

    Returns:
        Annual payment amount ($)

    Example:
        >>> calculate_annual_payment(500000, 3.0, 25)
        35693.26
    """
    if principal <= 0:
        raise ValueError("Principal must be positive")
    if annual_rate < 0:
        raise ValueError("Interest rate cannot be negative")
    if years <= 0:
        raise ValueError("Years must be positive")

    # Convert percentage to decimal
    r = annual_rate / 100.0

    # Handle edge case: 0% interest
    if r == 0:
        return principal / years

    # Apply amortization formula
    numerator = r * ((1 + r) ** years)
    denominator = ((1 + r) ** years) - 1

    annual_payment = principal * (numerator / denominator)

    return round(annual_payment, 2)


def calculate_total_paid(principal: float, annual_rate: float, years: int) -> dict:
    """
    Calculate total amount to be paid over the life of the mortgage.

    Args:
        principal: Mortgage balance ($)
        annual_rate: Annual interest rate (as percentage)
        years: Number of years remaining

    Returns:
        Dictionary with:
            - annual_payment: Annual payment amount
            - total_paid: Total amount paid over life of loan
            - total_interest: Total interest paid

    Example:
        >>> calculate_total_paid(500000, 3.0, 25)
        {
            'annual_payment': 35693.26,
            'total_paid': 892331.50,
            'total_interest': 392331.50
        }
    """
    annual_payment = calculate_annual_payment(principal, annual_rate, years)
    total_paid = annual_payment * years
    total_interest = total_paid - principal

    return {
        'annual_payment': annual_payment,
        'total_paid': round(total_paid, 2),
        'total_interest': round(total_interest, 2)
    }


def get_mortgage_summary(principal: float, annual_rate: float, years: int) -> dict:
    """
    Get comprehensive mortgage summary.

    Args:
        principal: Mortgage balance ($)
        annual_rate: Annual interest rate (as percentage)
        years: Number of years remaining

    Returns:
        Dictionary with complete mortgage details
    """
    payment_info = calculate_total_paid(principal, annual_rate, years)

    return {
        'balance': principal,
        'rate': annual_rate,
        'years': years,
        'annual_payment': payment_info['annual_payment'],
        'total_to_pay': payment_info['total_paid'],
        'total_interest': payment_info['total_interest']
    }


if __name__ == "__main__":
    # Test the calculator
    print("Testing Mortgage Calculator")
    print("=" * 50)

    # Example: $500K at 3% for 25 years
    principal = 500000
    rate = 3.0
    years = 25

    summary = get_mortgage_summary(principal, rate, years)

    print(f"\nMortgage: ${principal:,.0f} at {rate}% for {years} years")
    print(f"Annual Payment: ${summary['annual_payment']:,.2f}")
    print(f"Total to Pay: ${summary['total_to_pay']:,.2f}")
    print(f"Total Interest: ${summary['total_interest']:,.2f}")
