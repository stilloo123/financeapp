"""
CPI Data Loader - Fetches historical inflation data from FRED API
"""

import requests
import json
from typing import Dict, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CPIDataLoader:
    """Loads historical CPI data from FRED API."""

    def __init__(self, api_key: str = None):
        """
        Initialize CPI data loader.

        Args:
            api_key: FRED API key (or set FRED_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        if not self.api_key:
            raise ValueError("FRED API key required. Set FRED_API_KEY environment variable or pass api_key parameter.")

        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.cpi_series_id = "CPIAUCSL"  # Consumer Price Index for All Urban Consumers

        self.cpi_by_year = {}
        self.inflation_by_year = {}

    def fetch_cpi_data(self, start_year: int = 1926, end_year: int = 2025) -> Dict[int, float]:
        """
        Fetch annual CPI data from FRED.

        Args:
            start_year: Start year (default 1926 to match S&P data)
            end_year: End year (default 2025)

        Returns:
            Dictionary mapping year to annual inflation rate (%)
        """
        params = {
            'series_id': self.cpi_series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': f'{start_year}-01-01',
            'observation_end': f'{end_year}-12-31',
            'frequency': 'a',  # Annual frequency
            'units': 'pc1'  # Percent change from year ago
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'observations' not in data:
                raise ValueError(f"Invalid response from FRED API: {data}")

            # Parse observations
            for obs in data['observations']:
                year = int(obs['date'][:4])
                value = obs['value']

                # Skip missing values (marked as '.')
                if value != '.':
                    self.inflation_by_year[year] = float(value)

            print(f"✓ Loaded CPI data for {len(self.inflation_by_year)} years ({min(self.inflation_by_year.keys())}-{max(self.inflation_by_year.keys())})")

            return self.inflation_by_year

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch CPI data from FRED: {e}")

    def get_inflation_rate(self, year: int) -> float:
        """
        Get inflation rate for a specific year.

        Args:
            year: Year to get inflation for

        Returns:
            Inflation rate as percentage (e.g., 3.5 for 3.5%)
        """
        if not self.inflation_by_year:
            raise ValueError("CPI data not loaded. Call fetch_cpi_data() first.")

        if year not in self.inflation_by_year:
            raise ValueError(f"No CPI data available for year {year}")

        return self.inflation_by_year[year]

    def calculate_real_return(self, nominal_return: float, year: int) -> float:
        """
        Calculate real (inflation-adjusted) return.

        Args:
            nominal_return: Nominal return (%)
            year: Year for inflation lookup

        Returns:
            Real return (%)
        """
        inflation = self.get_inflation_rate(year)
        # Fisher equation: (1 + nominal) / (1 + inflation) - 1
        # Approximation: nominal - inflation (close enough for small values)
        real_return = nominal_return - inflation
        return real_return

    def save_to_file(self, filepath: str):
        """Save CPI data to JSON file for offline use."""
        data = {
            'metadata': {
                'source': 'FRED API (Federal Reserve Bank of St. Louis)',
                'series': self.cpi_series_id,
                'description': 'Annual inflation rates (CPI-U, percent change from year ago)',
                'period': f"{min(self.inflation_by_year.keys())}-{max(self.inflation_by_year.keys())}"
            },
            'inflation_rates': [
                {'year': year, 'inflation_rate': rate}
                for year, rate in sorted(self.inflation_by_year.items())
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved CPI data to {filepath}")

    @staticmethod
    def load_from_file(filepath: str) -> Dict[int, float]:
        """Load CPI data from JSON file (for offline use)."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        inflation_by_year = {
            item['year']: item['inflation_rate']
            for item in data['inflation_rates']
        }

        print(f"✓ Loaded CPI data from file: {len(inflation_by_year)} years")
        return inflation_by_year


if __name__ == "__main__":
    # Test the CPI loader
    print("CPI Data Loader Test")
    print("=" * 70)

    # You need to set FRED_API_KEY environment variable or pass it here
    # Get your free API key from: https://fred.stlouisfed.org/docs/api/api_key.html

    try:
        loader = CPIDataLoader()

        # Fetch data from FRED
        print("\nFetching CPI data from FRED API...")
        inflation_data = loader.fetch_cpi_data(start_year=1926, end_year=2025)

        # Show some examples
        print("\n" + "=" * 70)
        print("Sample Inflation Rates:")
        print("=" * 70)

        sample_years = [1950, 1974, 1980, 2008, 2020, 2023]
        for year in sample_years:
            if year in inflation_data:
                print(f"{year}: {inflation_data[year]:+.2f}%")

        # Calculate average for different periods
        print("\n" + "=" * 70)
        print("Average Inflation by Period:")
        print("=" * 70)

        periods = [
            (1950, 1999, "1950-1999 (for comparison with S&P)"),
            (2000, 2024, "2000-2024 (Recent era)"),
            (1926, 2024, "1926-2024 (Full dataset)")
        ]

        for start, end, label in periods:
            rates = [inflation_data[y] for y in range(start, end + 1) if y in inflation_data]
            if rates:
                avg = sum(rates) / len(rates)
                print(f"{label}: {avg:.2f}%")

        # Save to file for offline use
        output_file = '/Users/sachin/projects/finance-app/data/cpi_data.json'
        loader.save_to_file(output_file)

        print("\n" + "=" * 70)
        print("✓ CPI data ready to use!")
        print("=" * 70)

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo use this script:")
        print("1. Get a free API key from https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Set environment variable: export FRED_API_KEY='your_key_here'")
        print("3. Or pass it directly: CPIDataLoader(api_key='your_key_here')")
