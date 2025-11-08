"""
Optimal Capital Allocation Algorithm

Two-phase binary search to find minimum capital allocation:
- Phase 1: Binary search on total capital
- Phase 2: Golden section search on stock/cash split

Based on:
- Bengen (1994): Historical backtesting methodology
- Pfau & Kitces (2014): Dynamic withdrawal strategies
- Ruin theory: Minimum capital for survival guarantee
"""

from typing import List, Tuple, Dict
import math


def simulate_smart_withdrawal(
    initial_stock: float,
    initial_cash: float,
    returns_sequence: List[float],
    annual_payment: float,
    initial_mortgage_balance: float,
    protected_base: float = 100000
) -> Dict:
    """
    Simulate smart withdrawal strategy.

    Withdrawal policy:
    - Market DOWN: Use cash (never sell stocks at a loss)
    - Market UP: Use stocks if above base, else cash
    """
    stock_balance = initial_stock
    cash_balance = initial_cash
    remaining_mortgage = initial_mortgage_balance

    year_by_year = []

    for year, stock_return in enumerate(returns_sequence, start=1):
        # Smart withdrawal logic
        if stock_return < 0:
            # Market DOWN: Use cash
            if cash_balance >= annual_payment:
                withdrawal_source = "cash (market down)"
                cash_balance -= annual_payment
            else:
                withdrawal_source = "stocks (forced, no cash)"
                stock_balance -= annual_payment
        else:
            # Market UP: Use stocks if above base
            if stock_balance > protected_base:
                withdrawal_source = "stocks (market up, above base)"
                stock_balance -= annual_payment
            elif cash_balance >= annual_payment:
                withdrawal_source = "cash (protect base)"
                cash_balance -= annual_payment
            else:
                withdrawal_source = "stocks (forced, no cash)"
                stock_balance -= annual_payment

        # Apply returns
        stock_balance *= (1 + stock_return / 100.0)
        cash_balance *= 1.037  # Cash earns 3.7%
        remaining_mortgage -= annual_payment

        total_balance = stock_balance + cash_balance

        year_by_year.append({
            'year': year,
            'return': stock_return,
            'stock_balance': round(stock_balance, 2),
            'cash_balance': round(cash_balance, 2),
            'total_balance': round(total_balance, 2),
            'remaining_mortgage': round(remaining_mortgage, 2),
            'withdrawal_source': withdrawal_source
        })

        # Check for early payoff
        if total_balance >= remaining_mortgage:
            leftover = total_balance - remaining_mortgage
            return {
                'success': True,
                'years_to_payoff': year,
                'leftover': leftover,
                'year_by_year': year_by_year
            }

        # Check for failure
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


class OptimalAllocator:
    """
    Find minimum capital allocation using two-phase binary search.
    """

    def __init__(
        self,
        returns_sequence: List[float],
        annual_payment: float,
        mortgage_balance: float,
        protected_base: float = 100000
    ):
        self.returns = returns_sequence
        self.payment = annual_payment
        self.mortgage = mortgage_balance
        self.base = protected_base

    def find_best_split(
        self,
        total_capital: float,
        precision: float = 0.01
    ) -> Tuple[bool, float, float, Dict]:
        """
        Phase 2: For given total capital, find optimal stock/cash split.

        Uses golden section search on the split ratio.

        Args:
            total_capital: Total capital available
            precision: Precision for ratio (0.01 = 1%)

        Returns:
            (success, optimal_stock, optimal_cash, result)
        """
        phi = (1 + math.sqrt(5)) / 2  # Golden ratio ≈ 1.618

        # Search bounds: [0, 1] representing stock ratio
        a, b = 0.0, 1.0
        c = b - (b - a) / phi
        d = a + (b - a) / phi

        best_result = None
        best_ratio = 0.5

        iterations = 0
        max_iterations = 50  # Safety limit

        while abs(b - a) > precision and iterations < max_iterations:
            iterations += 1

            # Evaluate both points
            stock_c = total_capital * c
            cash_c = total_capital * (1 - c)
            result_c = simulate_smart_withdrawal(
                stock_c, cash_c, self.returns, self.payment, self.mortgage, self.base
            )

            stock_d = total_capital * d
            cash_d = total_capital * (1 - d)
            result_d = simulate_smart_withdrawal(
                stock_d, cash_d, self.returns, self.payment, self.mortgage, self.base
            )

            # Selection criteria: prefer successful, then faster payoff
            def score(result):
                if not result['success']:
                    return -1000  # Large penalty for failure
                return -result['years_to_payoff']  # Negative so lower years = higher score

            score_c = score(result_c)
            score_d = score(result_d)

            if score_c > score_d:
                # c is better, narrow to [a, d]
                b = d
                d = c
                c = b - (b - a) / phi
                best_result = result_c
                best_ratio = c
            else:
                # d is better, narrow to [c, b]
                a = c
                c = d
                d = a + (b - a) / phi
                best_result = result_d
                best_ratio = d

        # Calculate final allocation
        optimal_stock = total_capital * best_ratio
        optimal_cash = total_capital * (1 - best_ratio)

        if best_result and best_result['success']:
            return True, optimal_stock, optimal_cash, best_result
        else:
            return False, optimal_stock, optimal_cash, best_result

    def find_minimum(
        self,
        tolerance: float = 1000,
        max_capital: float = None
    ) -> Tuple[float, float, Dict]:
        """
        Phase 1: Binary search on total capital to find minimum.

        Args:
            tolerance: Dollar precision (default $1K)
            max_capital: Maximum to search (default = mortgage balance)

        Returns:
            (optimal_stock, optimal_cash, result)
        """
        if max_capital is None:
            max_capital = self.mortgage

        low = 0
        high = max_capital

        optimal_stock = 0
        optimal_cash = 0
        optimal_result = None

        iterations = 0
        max_iterations = 50  # Safety limit

        while high - low > tolerance and iterations < max_iterations:
            iterations += 1
            mid = (low + high) / 2

            # Phase 2: Find best split for this total capital
            success, stock, cash, result = self.find_best_split(mid)

            if success:
                # Can succeed with this capital, try less
                optimal_stock = stock
                optimal_cash = cash
                optimal_result = result
                high = mid
            else:
                # Need more capital
                low = mid

        # If we never found a success, search up to max
        if optimal_result is None or not optimal_result.get('success'):
            # Try the maximum capital
            success, stock, cash, result = self.find_best_split(max_capital)
            if success:
                optimal_stock = stock
                optimal_cash = cash
                optimal_result = result

        return optimal_stock, optimal_cash, optimal_result

    def search_range(
        self,
        capital_range: List[float],
        progress_callback=None
    ) -> List[Dict]:
        """
        Test a range of capital levels and return success rates.

        Used for generating capital vs. success probability curves.

        Args:
            capital_range: List of capital levels to test
            progress_callback: Optional callback(current, total)

        Returns:
            List of {capital, success, stock, cash, years_to_payoff}
        """
        results = []

        for i, capital in enumerate(capital_range):
            if progress_callback:
                progress_callback(i + 1, len(capital_range))

            success, stock, cash, result = self.find_best_split(capital)

            results.append({
                'capital': capital,
                'success': success,
                'stock': stock,
                'cash': cash,
                'stock_ratio': stock / capital if capital > 0 else 0,
                'years_to_payoff': result['years_to_payoff'] if success else None,
                'leftover': result.get('leftover', 0)
            })

        return results


def find_optimal_allocation(
    returns_sequence: List[float],
    annual_payment: float,
    mortgage_balance: float,
    protected_base: float = 100000,
    tolerance: float = 1000
) -> Tuple[float, float, Dict]:
    """
    Convenience function to find optimal allocation.

    Args:
        returns_sequence: Historical returns for the period
        annual_payment: Annual mortgage payment
        mortgage_balance: Initial mortgage balance
        protected_base: Minimum stock balance to protect
        tolerance: Dollar precision

    Returns:
        (optimal_stock, optimal_cash, simulation_result)
    """
    allocator = OptimalAllocator(
        returns_sequence, annual_payment, mortgage_balance, protected_base
    )
    return allocator.find_minimum(tolerance)
