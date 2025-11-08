"""
Bond Data Loader Module

Loads and manages historical bond return data from Damodaran's dataset.
"""

import json
import os
from typing import List, Dict


class BondDataLoader:
    """Loads and provides access to historical bond returns."""

    def __init__(self, data_file_path: str = None):
        """
        Initialize the bond data loader.

        Args:
            data_file_path: Path to bond_returns.json file
        """
        if data_file_path is None:
            # Default path relative to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_file_path = os.path.join(project_root, 'data', 'bond_returns.json')

        self.data_file_path = data_file_path
        self.data = None
        self.returns_by_year = {}
        self.load_data()

    def load_data(self) -> None:
        """Load bond returns from JSON file."""
        try:
            with open(self.data_file_path, 'r') as f:
                self.data = json.load(f)

            # Create a dictionary for easy lookup by year
            self.returns_by_year = {
                item['year']: item['return'] * 100  # Convert to percentage
                for item in self.data['returns']
            }

            print(f"✓ Loaded {len(self.returns_by_year)} years of bond data ({min(self.returns_by_year.keys())}-{max(self.returns_by_year.keys())})")

        except FileNotFoundError:
            raise FileNotFoundError(f"Bond data file not found: {self.data_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in bond data file: {self.data_file_path}")

    def get_returns(self, start_year: int, end_year: int) -> List[float]:
        """
        Get returns for a specific year range.

        Args:
            start_year: Starting year (inclusive)
            end_year: Ending year (inclusive)

        Returns:
            List of annual returns as percentages

        Example:
            >>> loader.get_returns(2000, 2002)
            [21.48, 3.70, 15.12]
        """
        if start_year > end_year:
            raise ValueError(f"Start year ({start_year}) must be <= end year ({end_year})")

        returns = []
        for year in range(start_year, end_year + 1):
            if year not in self.returns_by_year:
                raise ValueError(f"No bond data available for year {year}")
            returns.append(self.returns_by_year[year])

        return returns

    def get_available_years(self) -> tuple:
        """
        Get the range of available years.

        Returns:
            Tuple of (min_year, max_year)
        """
        years = list(self.returns_by_year.keys())
        return (min(years), max(years))

    def get_metadata(self) -> Dict:
        """Get metadata about the dataset."""
        return self.data.get('metadata', {})

    def validate_window(self, start_year: int, years_duration: int) -> bool:
        """
        Check if a window of given duration starting at start_year is valid.

        Args:
            start_year: Starting year
            years_duration: Duration in years

        Returns:
            True if window is valid (all years have data), False otherwise
        """
        end_year = start_year + years_duration - 1
        min_year, max_year = self.get_available_years()

        return (start_year >= min_year and
                end_year <= max_year and
                all(year in self.returns_by_year for year in range(start_year, end_year + 1)))


if __name__ == "__main__":
    # Test the bond data loader
    print("Testing Bond Data Loader")
    print("=" * 50)

    loader = BondDataLoader()

    # Get metadata
    metadata = loader.get_metadata()
    print(f"\nData Source: {metadata.get('source', 'Unknown')}")
    print(f"Bond Type: {metadata.get('bond_type', 'Unknown')}")
    print(f"Period: {metadata.get('period', 'Unknown')}")

    # Get available years
    min_year, max_year = loader.get_available_years()
    print(f"\nAvailable Years: {min_year} - {max_year}")
    print(f"Total Years: {max_year - min_year + 1}")

    # Test getting specific returns
    print("\n" + "=" * 50)
    print("Testing Return Extraction")
    print("\n2000-2002 (Dot-com era):")
    returns_2000s = loader.get_returns(2000, 2002)
    for i, ret in enumerate(returns_2000s, start=2000):
        print(f"  {i}: {ret:+.2f}%")

    print("\n2008-2009 (Financial Crisis):")
    returns_2008 = loader.get_returns(2008, 2009)
    for i, ret in enumerate(returns_2008, start=2008):
        print(f"  {i}: {ret:+.2f}%")

    print("\n2022 (Rate Hikes):")
    returns_2022 = loader.get_returns(2022, 2022)
    for i, ret in enumerate(returns_2022, start=2022):
        print(f"  {i}: {ret:+.2f}%")

    # Test window validation
    print("\n" + "=" * 50)
    print("Testing Window Validation")
    print(f"Can create 25-year window starting 2000? {loader.validate_window(2000, 25)}")
    print(f"Can create 30-year window starting 2000? {loader.validate_window(2000, 30)}")
    print(f"Can create 25-year window starting 1920? {loader.validate_window(1920, 25)}")
