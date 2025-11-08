"""
Backtesting Engine Module

Generates rolling historical windows and runs optimization for each.
Calculates statistics across all scenarios.
"""

import statistics
from typing import List, Dict, Optional
from .data_loader import SP500DataLoader
from .investment_simulator import (
    find_minimum_investment,
    simulate_investment,
    find_minimum_with_early_payoff,
    simulate_investment_with_early_payoff
)


class MortgageInvestmentBacktester:
    """Backtests mortgage vs investment strategy using historical data."""

    def __init__(self, data_loader: Optional[SP500DataLoader] = None):
        """
        Initialize the backtester.

        Args:
            data_loader: SP500DataLoader instance (creates new one if None)
        """
        self.data_loader = data_loader or SP500DataLoader()

    def generate_windows(self, years_duration: int) -> List[Dict]:
        """
        Generate all possible rolling windows of given duration.

        Args:
            years_duration: Number of years in each window

        Returns:
            List of dictionaries with 'start_year', 'end_year', 'period', 'returns'

        Example:
            For years_duration=25, generates:
            - 1926-1950, 1927-1951, ..., 2000-2024
        """
        min_year, max_year = self.data_loader.get_available_years()

        # Note: We use 2024 as the last complete year, excluding partial 2025 data
        max_complete_year = 2024
        max_start_year = max_complete_year - years_duration + 1

        windows = []

        for start_year in range(min_year, max_start_year + 1):
            end_year = start_year + years_duration - 1

            # Validate window (skip if data incomplete)
            if not self.data_loader.validate_window(start_year, years_duration):
                continue

            # Get returns for this window
            returns = self.data_loader.get_returns(start_year, end_year)

            windows.append({
                'start_year': start_year,
                'end_year': end_year,
                'period': f"{start_year}-{end_year}",
                'returns': returns
            })

        return windows

    def backtest_all_scenarios(
        self,
        annual_payment: float,
        years_duration: int,
        mortgage_balance: float
    ) -> Dict:
        """
        Run backtesting across all historical scenarios WITH EARLY PAYOFF.

        Args:
            annual_payment: Annual mortgage payment amount ($)
            years_duration: Number of years
            mortgage_balance: Initial mortgage balance ($)

        Returns:
            Dictionary with results for all scenarios
        """
        # Generate all windows
        windows = self.generate_windows(years_duration)

        if not windows:
            raise ValueError(f"No valid windows found for {years_duration} years")

        print(f"Running backtest: {len(windows)} scenarios for {years_duration} years...")

        # Run optimization for each window WITH EARLY PAYOFF
        results = []

        for window in windows:
            # Find minimum investment with early payoff optimization
            min_investment, years_to_payoff, leftover = find_minimum_with_early_payoff(
                window['returns'],
                annual_payment,
                mortgage_balance
            )

            # Get year-by-year details
            success, years, final_balance, year_by_year = simulate_investment_with_early_payoff(
                min_investment,
                window['returns'],
                annual_payment,
                mortgage_balance
            )

            results.append({
                'period': window['period'],
                'start_year': window['start_year'],
                'end_year': window['end_year'],
                'investment_required': min_investment,
                'years_to_payoff': years_to_payoff,
                'paid_off_early': years_to_payoff < years_duration,
                'leftover_amount': leftover,
                'final_balance': round(final_balance, 2),
                'returns_sequence': window['returns'],
                'year_by_year': year_by_year
            })

        return {
            'scenarios_tested': len(results),
            'years': years_duration,
            'annual_payment': annual_payment,
            'mortgage_balance': mortgage_balance,
            'all_scenarios': results
        }

    def calculate_statistics(self, backtest_results: Dict) -> Dict:
        """
        Calculate statistical summary of backtest results.

        Args:
            backtest_results: Results from backtest_all_scenarios

        Returns:
            Dictionary with statistical analysis
        """
        all_scenarios = backtest_results['all_scenarios']
        investments = [s['investment_required'] for s in all_scenarios]

        # Sort to find specific scenarios
        sorted_scenarios = sorted(all_scenarios, key=lambda x: x['investment_required'])

        # Calculate percentiles
        percentiles = {
            'best_case': sorted_scenarios[0],
            'percentile_25': self._get_percentile_scenario(sorted_scenarios, 25),
            'median': self._get_percentile_scenario(sorted_scenarios, 50),
            'percentile_75': self._get_percentile_scenario(sorted_scenarios, 75),
            'percentile_90': self._get_percentile_scenario(sorted_scenarios, 90),
            'percentile_95': self._get_percentile_scenario(sorted_scenarios, 95),
            'worst_case': sorted_scenarios[-1]
        }

        return {
            'scenarios_tested': backtest_results['scenarios_tested'],
            'years': backtest_results['years'],
            'annual_payment': backtest_results['annual_payment'],
            'statistics': {
                'min': min(investments),
                'max': max(investments),
                'mean': round(statistics.mean(investments), 2),
                'median': round(statistics.median(investments), 2),
                'stdev': round(statistics.stdev(investments), 2) if len(investments) > 1 else 0
            },
            'results': percentiles,
            'all_scenarios': all_scenarios
        }

    def _get_percentile_scenario(self, sorted_scenarios: List[Dict], percentile: float) -> Dict:
        """Get scenario at given percentile."""
        index = int(len(sorted_scenarios) * (percentile / 100.0))
        index = min(index, len(sorted_scenarios) - 1)  # Clamp to valid range
        return sorted_scenarios[index]

    def run_full_analysis(
        self,
        mortgage_balance: float,
        interest_rate: float,
        years_remaining: int
    ) -> Dict:
        """
        Run complete analysis: calculate payment, backtest, and analyze.

        Args:
            mortgage_balance: Mortgage principal ($)
            interest_rate: Annual interest rate (percentage)
            years_remaining: Years left on mortgage

        Returns:
            Complete analysis results
        """
        from backend.models.mortgage_calculator import calculate_annual_payment

        # Calculate annual payment
        annual_payment = calculate_annual_payment(
            mortgage_balance,
            interest_rate,
            years_remaining
        )

        print(f"\nMortgage: ${mortgage_balance:,.0f} at {interest_rate}% for {years_remaining} years")
        print(f"Annual Payment: ${annual_payment:,.2f}")

        # Run backtesting WITH EARLY PAYOFF
        backtest_results = self.backtest_all_scenarios(
            annual_payment, years_remaining, mortgage_balance
        )

        # Calculate statistics
        analysis = self.calculate_statistics(backtest_results)

        return analysis


if __name__ == "__main__":
    # Test the backtester
    print("Testing Mortgage Investment Backtester")
    print("=" * 70)

    # Initialize backtester
    backtester = MortgageInvestmentBacktester()

    # Test window generation
    print("\nTesting Window Generation:")
    windows_10yr = backtester.generate_windows(10)
    windows_25yr = backtester.generate_windows(25)
    print(f"10-year windows: {len(windows_10yr)} (e.g., {windows_10yr[0]['period']} ... {windows_10yr[-1]['period']})")
    print(f"25-year windows: {len(windows_25yr)} (e.g., {windows_25yr[0]['period']} ... {windows_25yr[-1]['period']})")

    # Run full analysis for a small example (10 years for speed)
    print("\n" + "=" * 70)
    print("Running Full Analysis (10 years for speed)...")

    results = backtester.run_full_analysis(
        mortgage_balance=500000,
        interest_rate=3.0,
        years_remaining=10
    )

    print(f"\nScenarios tested: {results['scenarios_tested']}")
    print(f"\nStatistics:")
    stats = results['statistics']
    print(f"  Min:    ${stats['min']:,.2f}")
    print(f"  Median: ${stats['median']:,.2f}")
    print(f"  Mean:   ${stats['mean']:,.2f}")
    print(f"  Max:    ${stats['max']:,.2f}")
    print(f"  StdDev: ${stats['stdev']:,.2f}")

    print(f"\nKey Scenarios:")
    print(f"  Best Case  ({results['results']['best_case']['period']}): ${results['results']['best_case']['investment_required']:,.2f}")
    print(f"  Median     ({results['results']['median']['period']}): ${results['results']['median']['investment_required']:,.2f}")
    print(f"  90th %ile  ({results['results']['percentile_90']['period']}): ${results['results']['percentile_90']['investment_required']:,.2f}")
    print(f"  Worst Case ({results['results']['worst_case']['period']}): ${results['results']['worst_case']['investment_required']:,.2f}")

    print(f"\nComparison:")
    print(f"  Pay off directly: ${500000:,.2f}")
    print(f"  Median investment: ${results['results']['median']['investment_required']:,.2f}")
    savings = 500000 - results['results']['median']['investment_required']
    print(f"  Potential savings: ${savings:,.2f}")
