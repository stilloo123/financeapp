"""
Fetch bond return data from Aswath Damodaran's dataset and cache it locally.

This script downloads historical bond returns (including coupon payments)
and saves them to data/bond_returns.json for use in simulations.
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

# Damodaran's historical returns URL
DAMODARAN_URL = "https://www.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls"

def fetch_damodaran_bond_data():
    """Fetch bond return data from Damodaran's dataset."""
    print(f"Fetching data from {DAMODARAN_URL}...")

    try:
        # Download the Excel file
        response = requests.get(DAMODARAN_URL, timeout=30)
        response.raise_for_status()

        # Save temporarily
        temp_file = '/tmp/damodaran_returns.xls'
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        # Read the "Returns by year" sheet
        xls = pd.ExcelFile(temp_file)
        print(f"\nSheets found: {xls.sheet_names}")

        # Try "T. Bond yield & return" sheet first (specific to bonds)
        target_sheet = None
        for sheet_name in xls.sheet_names:
            if 'bond' in sheet_name.lower() and ('return' in sheet_name.lower() or 'yield' in sheet_name.lower()):
                target_sheet = sheet_name
                break

        # If not found, try "Returns by year"
        if target_sheet is None:
            for sheet_name in xls.sheet_names:
                if 'return' in sheet_name.lower() and 'year' in sheet_name.lower():
                    target_sheet = sheet_name
                    break

        if target_sheet is None:
            print("ERROR: Could not find bond returns sheet")
            return None

        print(f"\nUsing sheet: {target_sheet}")

        # Try different header rows in this sheet
        df = None
        for header_row in range(0, 10):
            try:
                test_df = pd.read_excel(temp_file, sheet_name=target_sheet, header=header_row)
                print(f"\n  Header row {header_row}:")
                print(f"    Columns: {test_df.columns.tolist()[:5]}")  # Show first 5 columns
                print(f"    First values: {test_df.iloc[0].tolist()[:5] if len(test_df) > 0 else 'Empty'}")

                # Check if we found actual data - look for year column with numeric years
                for col in test_df.columns:
                    if 'year' in str(col).lower():
                        print(f"    Found year column: {col}")
                        # Check if first few values are years (1900-2030)
                        try:
                            first_vals = test_df[col].dropna().head(5)
                            print(f"    First year values: {first_vals.tolist()}")
                            years_valid = []
                            for v in first_vals:
                                if pd.notna(v):
                                    try:
                                        year_int = int(float(v))
                                        years_valid.append(1900 <= year_int <= 2030)
                                    except:
                                        years_valid.append(False)

                            if years_valid and all(years_valid):
                                df = test_df
                                print(f"  ✓ Found data at row {header_row}")
                                break
                        except Exception as e:
                            print(f"    Error checking years: {e}")
                            continue
                if df is not None:
                    break
            except Exception as e:
                print(f"    Error reading header row {header_row}: {e}")
                continue

        if df is None:
            print("ERROR: Could not find data with year column")
            return None

        print("\nColumns found:")
        print(df.columns.tolist())
        print("\nFirst few rows:")
        print(df.head(10))

        # Find the year column and bond return column
        # Common column names: 'Year', 'US T. Bond', '10-year T.Bond', etc.
        year_col = None
        bond_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if 'year' in col_lower and year_col is None:
                year_col = col
            if ('bond' in col_lower or 't.bond' in col_lower) and 'bill' not in col_lower:
                if bond_col is None or 'baa' not in col_lower:  # Prefer government bonds
                    bond_col = col

        if year_col is None or bond_col is None:
            print(f"\nERROR: Could not find required columns")
            print(f"Year column: {year_col}")
            print(f"Bond column: {bond_col}")
            return None

        print(f"\nUsing columns:")
        print(f"  Year: {year_col}")
        print(f"  Bonds: {bond_col}")

        # Extract year and bond returns
        bond_data = []
        for _, row in df.iterrows():
            year = row[year_col]
            bond_return = row[bond_col]

            # Skip if not valid
            if pd.isna(year) or pd.isna(bond_return):
                continue

            # Convert to proper types
            try:
                year = int(year)
                bond_return = float(bond_return)

                # Skip if year is unreasonable
                if year < 1900 or year > 2030:
                    continue

                bond_data.append({
                    'year': year,
                    'return': round(bond_return, 2)
                })
            except (ValueError, TypeError):
                continue

        # Sort by year
        bond_data.sort(key=lambda x: x['year'])

        print(f"\n✓ Extracted {len(bond_data)} years of bond data")
        print(f"  Period: {bond_data[0]['year']}-{bond_data[-1]['year']}")

        return bond_data

    except Exception as e:
        print(f"ERROR fetching data: {e}")
        return None

def save_bond_data(bond_data):
    """Save bond data to JSON file."""
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'data')
    output_file = os.path.join(data_dir, 'bond_returns.json')

    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Prepare JSON structure
    json_data = {
        'metadata': {
            'source': 'Aswath Damodaran (NYU Stern)',
            'url': DAMODARAN_URL,
            'description': 'Historical U.S. Government Bond Total Returns (price + coupon)',
            'bond_type': '10-Year Treasury Bonds',
            'period': f"{bond_data[0]['year']}-{bond_data[-1]['year']}",
            'fetched_at': datetime.now().isoformat(),
            'note': 'Returns include both price changes and coupon income (total return)'
        },
        'returns': bond_data
    }

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"\n✓ Saved bond data to {output_file}")
    print(f"  {len(bond_data)} years of data")
    print(f"  {bond_data[0]['year']}-{bond_data[-1]['year']}")

    return output_file

if __name__ == '__main__':
    print("="*60)
    print("Fetching Bond Return Data from Damodaran")
    print("="*60)

    bond_data = fetch_damodaran_bond_data()

    if bond_data:
        output_file = save_bond_data(bond_data)
        print(f"\n✓ Bond data cached successfully!")
        print(f"\nSample data:")
        print(f"  1929: {[d for d in bond_data if d['year'] == 1929]}")
        print(f"  2008: {[d for d in bond_data if d['year'] == 2008]}")
        print(f"  2022: {[d for d in bond_data if d['year'] == 2022]}")
    else:
        print("\n✗ Failed to fetch bond data")
