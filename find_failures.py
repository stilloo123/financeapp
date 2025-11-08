"""
Find which scenarios failed with staged deployment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_loader import SP500DataLoader
from backend.models.mortgage_calculator import calculate_annual_payment


def simulate_all_stocks(initial_amount, returns_sequence, annual_payment, mortgage_balance):
    """Simple all-stocks simulation."""
    balance = initial_amount
    remaining_mortgage = mortgage_balance

    for year, stock_return in enumerate(returns_sequence, start=1):
        balance -= annual_payment
        remaining_mortgage -= annual_payment
        balance *= (1 + stock_return / 100.0)

        if balance >= remaining_mortgage:
            return {'success': True, 'years': year, 'leftover': balance - remaining_mortgage}
        if balance < 0:
            return {'success': False, 'years': year, 'leftover': balance}

    return {'success': balance >= 0, 'years': len(returns_sequence), 'leftover': balance}


loader = SP500DataLoader()
mortgage_balance = 500000
mortgage_rate = 3.0
annual_payment = calculate_annual_payment(mortgage_balance, mortgage_rate, 25)

failures = []

for start_year in range(1926, 2001):
    end_year = start_year + 24
    if end_year <= 2025:
        try:
            returns = loader.get_returns(start_year, end_year)
            if len(returns) == 25:
                result = simulate_all_stocks(500000, returns, annual_payment, mortgage_balance)
                if not result['success']:
                    failures.append({
                        'period': f"{start_year}-{end_year}",
                        'result': result
                    })
        except:
            pass

print("Periods that FAIL even with $500K all-stocks:")
print()
for f in failures:
    print(f"  {f['period']}: Failed in year {f['result']['years']}, shortfall ${abs(f['result']['leftover']):,.0f}")

print()
print(f"Total failures: {len(failures)} out of 75 scenarios")
