"""
Historical Optimizer

Comprehensive backtesting using optimal allocation algorithm across
all historical 25-year rolling windows.

Generates:
- Percentile analysis (capital requirements at different difficulty levels)
- Success rate curves (capital vs. success probability)
- Optimal stock/cash splits by scenario
"""

from typing import List, Dict, Tuple
from statistics import mean, median, stdev
import math

from .optimal_allocator import OptimalAllocator
from .data_loader import SP500DataLoader


class HistoricalOptimizer:
    """
    Run optimal allocation across all historical periods.
    """

    def __init__(
        self,
        annual_payment: float,
        mortgage_balance: float,
        protected_base: float = 100000
    ):
        self.payment = annual_payment
        self.mortgage = mortgage_balance
        self.base = protected_base
        self.data_loader = SP500DataLoader()

    def get_all_windows(self, window_size: int = 25) -> List[Dict]:
        """
        Get all rolling windows of specified size.

        Returns:
            List of {period, start_year, end_year, returns}
        """
        windows = []

        for start_year in range(1926, 2001):  # 1926-2000
            end_year = start_year + window_size - 1
            if end_year <= 2025:
                try:
                    returns = self.data_loader.get_returns(start_year, end_year)
                    if len(returns) == window_size:
                        windows.append({
                            'period': f"{start_year}-{end_year}",
                            'start_year': start_year,
                            'end_year': end_year,
                            'returns': returns
                        })
                except Exception as e:
                    print(f"Skipping {start_year}-{end_year}: {e}")

        return windows

    def optimize_all_periods(
        self,
        tolerance: float = 1000,
        progress_callback=None
    ) -> List[Dict]:
        """
        Find optimal allocation for each historical period.

        Returns:
            List of results with period, capital, stock, cash, years, etc.
        """
        windows = self.get_all_windows()
        results = []

        for i, window in enumerate(windows):
            if progress_callback:
                progress_callback(i + 1, len(windows), window['period'])

            allocator = OptimalAllocator(
                window['returns'],
                self.payment,
                self.mortgage,
                self.base
            )

            stock, cash, sim_result = allocator.find_minimum(tolerance)

            results.append({
                'period': window['period'],
                'start_year': window['start_year'],
                'end_year': window['end_year'],
                'total_capital': stock + cash,
                'stock': stock,
                'cash': cash,
                'stock_ratio': stock / (stock + cash) if (stock + cash) > 0 else 0,
                'success': sim_result.get('success', False) if sim_result else False,
                'years_to_payoff': sim_result.get('years_to_payoff') if sim_result else None,
                'leftover': sim_result.get('leftover', 0) if sim_result else 0
            })

        return results

    def percentile_analysis(
        self,
        percentiles: List[int] = [10, 25, 50, 75, 90, 95],
        tolerance: float = 1000
    ) -> Dict:
        """
        Calculate capital requirements at different percentiles.

        Args:
            percentiles: List of percentiles to calculate (e.g., [10, 50, 90])
            tolerance: Dollar precision

        Returns:
            {
                'percentiles': {10: {...}, 50: {...}, 90: {...}},
                'all_results': [...],
                'statistics': {...}
            }
        """
        print(f"Optimizing all historical periods (tolerance=${tolerance:,.0f})...")
        all_results = self.optimize_all_periods(
            tolerance,
            progress_callback=lambda c, t, p: print(f"  Progress: {c}/{t} - {p}")
        )

        # Sort by total capital required
        sorted_results = sorted(all_results, key=lambda x: x['total_capital'])

        # Calculate percentiles
        percentile_results = {}
        n = len(sorted_results)

        for p in percentiles:
            index = int((p / 100.0) * n)
            if index >= n:
                index = n - 1

            percentile_results[p] = sorted_results[index]

        # Calculate statistics
        capitals = [r['total_capital'] for r in all_results]
        stocks = [r['stock'] for r in all_results]
        cash = [r['cash'] for r in all_results]
        years = [r['years_to_payoff'] for r in all_results if r['years_to_payoff']]

        statistics = {
            'count': len(all_results),
            'capital': {
                'mean': mean(capitals),
                'median': median(capitals),
                'std': stdev(capitals) if len(capitals) > 1 else 0,
                'min': min(capitals),
                'max': max(capitals)
            },
            'stock': {
                'mean': mean(stocks),
                'median': median(stocks)
            },
            'cash': {
                'mean': mean(cash),
                'median': median(cash)
            },
            'years_to_payoff': {
                'mean': mean(years) if years else 0,
                'median': median(years) if years else 0,
                'min': min(years) if years else 0,
                'max': max(years) if years else 0
            }
        }

        return {
            'percentiles': percentile_results,
            'all_results': all_results,
            'statistics': statistics
        }

    def success_curve(
        self,
        capital_range: List[float],
        sample_periods: List[str] = None
    ) -> Dict:
        """
        Generate capital vs. success rate curve.

        For each capital level, determines what % of historical periods succeed.

        Args:
            capital_range: List of capital levels to test
            sample_periods: Optional list of periods to test (default: all)

        Returns:
            {
                'curve': [{capital, success_rate, avg_years}, ...],
                'periods_tested': int
            }
        """
        windows = self.get_all_windows()

        if sample_periods:
            windows = [w for w in windows if w['period'] in sample_periods]

        print(f"Generating success curve across {len(windows)} periods...")

        curve = []

        for i, capital in enumerate(capital_range):
            print(f"  Testing capital ${capital:,.0f} ({i+1}/{len(capital_range)})...")

            successes = 0
            years_list = []

            for window in windows:
                allocator = OptimalAllocator(
                    window['returns'],
                    self.payment,
                    self.mortgage,
                    self.base
                )

                # Find best split for this capital
                success, stock, cash, result = allocator.find_best_split(capital)

                if success:
                    successes += 1
                    years_list.append(result['years_to_payoff'])

            success_rate = (successes / len(windows)) * 100
            avg_years = mean(years_list) if years_list else 0

            curve.append({
                'capital': capital,
                'success_rate': success_rate,
                'successes': successes,
                'failures': len(windows) - successes,
                'avg_years': avg_years
            })

        return {
            'curve': curve,
            'periods_tested': len(windows)
        }

    def find_for_success_rate(
        self,
        target_success_rate: float,
        tolerance: float = 1000,
        max_iterations: int = 20
    ) -> Dict:
        """
        Find minimum capital needed for target success rate.

        Args:
            target_success_rate: Target % (e.g., 90.0 for 90%)
            tolerance: Dollar precision
            max_iterations: Max binary search iterations

        Returns:
            {
                'capital': float,
                'success_rate': float,
                'stock': float,
                'cash': float
            }
        """
        windows = self.get_all_windows()

        def test_capital(capital: float) -> float:
            """Test capital and return success rate."""
            successes = 0

            for window in windows:
                allocator = OptimalAllocator(
                    window['returns'],
                    self.payment,
                    self.mortgage,
                    self.base
                )
                success, _, _, _ = allocator.find_best_split(capital)
                if success:
                    successes += 1

            return (successes / len(windows)) * 100

        # Binary search on capital
        low = 0
        high = self.mortgage

        iterations = 0
        while high - low > tolerance and iterations < max_iterations:
            iterations += 1
            mid = (low + high) / 2

            rate = test_capital(mid)
            print(f"  Iteration {iterations}: ${mid:,.0f} → {rate:.1f}% success")

            if rate >= target_success_rate:
                # Can achieve target, try less capital
                high = mid
            else:
                # Need more capital
                low = mid

        # Final capital
        final_capital = high
        final_rate = test_capital(final_capital)

        # Get optimal split for this capital (using first period as representative)
        allocator = OptimalAllocator(
            windows[0]['returns'],
            self.payment,
            self.mortgage,
            self.base
        )
        _, stock, cash, _ = allocator.find_best_split(final_capital)

        return {
            'capital': final_capital,
            'success_rate': final_rate,
            'stock': stock,
            'cash': cash,
            'stock_ratio': stock / final_capital if final_capital > 0 else 0,
            'iterations': iterations
        }
