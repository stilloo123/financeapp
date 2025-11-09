"""
Script to convert nominal S&P 500 returns to real (inflation-adjusted) returns using FRED CPI data.
"""

import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, '/Users/sachin/projects/finance-app')

from backend.services.cpi_data_loader import CPIDataLoader


def convert_to_real_returns():
    """Convert nominal returns to real returns using actual CPI data."""

    # Step 1: Load nominal returns
    nominal_file = '/Users/sachin/projects/finance-app/data/sp500_returns.json'
    print("Loading nominal S&P 500 returns...")
    with open(nominal_file, 'r') as f:
        nominal_data = json.load(f)

    # Step 2: Fetch CPI data from FRED
    print("\nFetching CPI data from FRED API...")
    print("(Make sure FRED_API_KEY environment variable is set)")

    try:
        cpi_loader = CPIDataLoader()
        inflation_data = cpi_loader.fetch_cpi_data(start_year=1926, end_year=2025)

        # Save CPI data for future offline use
        cpi_loader.save_to_file('/Users/sachin/projects/finance-app/data/cpi_data.json')

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo use this script, get a FRED API key:")
        print("1. Go to https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Sign up (free)")
        print("3. Set environment variable: export FRED_API_KEY='your_key_here'")
        return

    # Step 3: Convert nominal to real returns
    print("\nConverting nominal returns to real returns...")

    real_returns = []
    missing_years = []

    for item in nominal_data['returns']:
        year = item['year']
        nominal_return = item['return']

        if year in inflation_data:
            inflation = inflation_data[year]
            # Fisher equation approximation: real = nominal - inflation
            real_return = nominal_return - inflation
            real_returns.append({
                'year': year,
                'nominal_return': nominal_return,
                'inflation': inflation,
                'real_return': round(real_return, 2)
            })
        else:
            missing_years.append(year)
            print(f"⚠️  No CPI data for {year}, skipping...")

    if missing_years:
        print(f"\n⚠️  Missing CPI data for {len(missing_years)} years: {missing_years}")

    # Step 4: Save real returns
    output_data = {
        'metadata': {
            'source': 'NYU Stern (nominal returns) + FRED CPI (inflation adjustment)',
            'description': 'Real (inflation-adjusted) S&P 500 returns',
            'period': f"{min(r['year'] for r in real_returns)}-{max(r['year'] for r in real_returns)}",
            'calculation': 'Real return = Nominal return - CPI inflation rate',
            'note': 'Returns are in percentage points (e.g., 10.5 means 10.5%)'
        },
        'returns': [
            {
                'year': r['year'],
                'return': r['real_return']  # For compatibility with existing code
            }
            for r in real_returns
        ],
        'detailed_returns': real_returns  # Keep detailed breakdown for reference
    }

    output_file = '/Users/sachin/projects/finance-app/data/sp500_real_returns.json'
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Saved real returns to {output_file}")

    # Step 5: Show comparison
    print("\n" + "=" * 80)
    print("COMPARISON: Nominal vs Real Returns")
    print("=" * 80)

    sample_years = [1950, 1974, 1980, 2000, 2008, 2020]
    print(f"{'Year':<8} {'Nominal':<12} {'Inflation':<12} {'Real':<12}")
    print("-" * 80)

    for r in real_returns:
        if r['year'] in sample_years:
            print(f"{r['year']:<8} {r['nominal_return']:>+10.2f}% {r['inflation']:>+10.2f}% {r['real_return']:>+10.2f}%")

    # Calculate averages
    print("\n" + "=" * 80)
    print("AVERAGES BY PERIOD")
    print("=" * 80)

    periods = [
        (1950, 1999),
        (2000, 2024),
        (1926, 2024)
    ]

    for start_year, end_year in periods:
        period_returns = [r for r in real_returns if start_year <= r['year'] <= end_year]
        if period_returns:
            avg_nominal = sum(r['nominal_return'] for r in period_returns) / len(period_returns)
            avg_inflation = sum(r['inflation'] for r in period_returns) / len(period_returns)
            avg_real = sum(r['real_return'] for r in period_returns) / len(period_returns)

            print(f"\n{start_year}-{end_year}:")
            print(f"  Nominal:   {avg_nominal:+.2f}%")
            print(f"  Inflation: {avg_inflation:+.2f}%")
            print(f"  Real:      {avg_real:+.2f}%")

    print("\n" + "=" * 80)
    print("✓ Conversion complete!")
    print("=" * 80)

    print(f"\nNext steps:")
    print(f"1. Update your code to use '{output_file}' instead of nominal returns")
    print(f"2. Your simulations will now match FICalc's results")


if __name__ == "__main__":
    convert_to_real_returns()
