"""Service to fetch current treasury yields from FRED API."""

import os
import requests
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TreasuryYieldFetcher:
    """Fetches current treasury yields from FRED (Federal Reserve Economic Data)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize fetcher.

        Get a free API key from: https://fred.stlouisfed.org/docs/api/api_key.html
        API key can be set in .env file as FRED_API_KEY
        """
        # Try to get API key from: parameter > env variable > fallback
        self.api_key = api_key or os.getenv('FRED_API_KEY') or "demo"
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

    def get_30_year_yield(self) -> float:
        """
        Get the most recent 30-year treasury yield.

        Returns:
            float: Current 30-year treasury yield as a percentage (e.g., 4.5 for 4.5%)
        """
        try:
            # DGS30 = 30-Year Treasury Constant Maturity Rate
            params = {
                'series_id': 'DGS30',
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',  # Most recent first
                'limit': 10  # Get last 10 observations (some may be null on weekends)
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Find the most recent non-null observation
            for observation in data.get('observations', []):
                value = observation.get('value')
                if value and value != '.':  # '.' means missing data
                    return float(value)

            # Fallback if API fails or no data
            print("Warning: Could not fetch 30-year treasury yield, using default 4.0%")
            return 4.0

        except Exception as e:
            print(f"Error fetching treasury yield: {e}")
            print("Using default 4.0%")
            return 4.0

    def get_10_year_yield(self) -> float:
        """
        Get the most recent 10-year treasury yield.

        Returns:
            float: Current 10-year treasury yield as a percentage
        """
        try:
            # DGS10 = 10-Year Treasury Constant Maturity Rate
            params = {
                'series_id': 'DGS10',
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 10
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            for observation in data.get('observations', []):
                value = observation.get('value')
                if value and value != '.':
                    return float(value)

            return 3.5  # Fallback

        except Exception as e:
            print(f"Error fetching 10-year treasury yield: {e}")
            return 3.5


# Singleton instance
_treasury_fetcher = None

def get_treasury_fetcher(api_key: Optional[str] = None) -> TreasuryYieldFetcher:
    """Get or create treasury fetcher instance."""
    global _treasury_fetcher
    if _treasury_fetcher is None:
        _treasury_fetcher = TreasuryYieldFetcher(api_key)
    return _treasury_fetcher


def get_current_bond_return() -> float:
    """
    Get current bond return estimate based on 30-year treasury yield.

    This is a convenience function used throughout the app.

    Returns:
        float: Current bond return as a percentage
    """
    fetcher = get_treasury_fetcher()
    return fetcher.get_30_year_yield()
