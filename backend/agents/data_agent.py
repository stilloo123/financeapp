"""Data Agent - Load historical S&P 500 and bond data."""

from typing import Dict, Any
from .base_agent import BaseAgent
from backend.services.data_loader import SP500DataLoader
from backend.services.bond_data_loader import BondDataLoader


class DataAgent(BaseAgent):
    """Agent responsible for loading historical data."""

    def __init__(self):
        super().__init__("data")
        self.sp500_loader = SP500DataLoader()
        self.bond_loader = BondDataLoader()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Load historical data."""
        self.log_info("Loading historical S&P 500 and bond data")

        # Get projection years from context
        projection_years = context.get('projection_years', 25)

        # Get all windows of the required length
        windows = self._load_windows(projection_years)

        self.log_info(f"Loaded {len(windows)} historical {projection_years}-year periods (stocks + bonds)")

        return {
            "historical_windows": windows,
            "num_periods": len(windows)
        }

    def _load_windows(self, years: int):
        """Load and filter historical windows with both stock and bond returns."""
        windows = []

        # Start from 1928 (earliest bond data), end when we can't get a full window
        latest_start = 2025 - years

        for start_year in range(1928, latest_start + 1):
            end_year = start_year + years - 1
            period = f"{start_year}-{end_year}"
            try:
                stock_returns = self.sp500_loader.get_returns(start_year, end_year)
                bond_returns = self.bond_loader.get_returns(start_year, end_year)

                if len(stock_returns) == years and len(bond_returns) == years:
                    windows.append({
                        'period': period,
                        'start_year': start_year,
                        'end_year': end_year,
                        'returns': stock_returns,  # Keep 'returns' for backward compatibility (S&P 500)
                        'stock_returns': stock_returns,
                        'bond_returns': bond_returns
                    })
            except Exception as e:
                # Skip windows where data is not available
                pass

        return windows
