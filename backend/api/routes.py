"""
API Routes Module

Defines REST API endpoints for the mortgage vs investment optimizer.
"""

from flask import Blueprint, request, jsonify
from backend.models.mortgage_calculator import get_mortgage_summary
from backend.services.backtester import MortgageInvestmentBacktester
from backend.services.data_loader import SP500DataLoader

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize data loader and backtester (loaded once at startup)
data_loader = SP500DataLoader()
backtester = MortgageInvestmentBacktester(data_loader)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON with status and data availability
    """
    min_year, max_year = data_loader.get_available_years()

    return jsonify({
        'status': 'ok',
        'data_loaded': True,
        'data_years': f"{min_year}-{max_year}"
    })


@api_bp.route('/data-info', methods=['GET'])
def data_info():
    """
    Get information about available historical data.

    Returns:
        JSON with data availability information
    """
    min_year, max_year = data_loader.get_available_years()
    metadata = data_loader.get_metadata()

    return jsonify({
        'years_available': f"{min_year}-{max_year}",
        'min_year': min_year,
        'max_year': max_year,
        'total_years': max_year - min_year + 1,
        'max_term_years': 2024 - min_year,  # Using 2024 as last complete year
        'source': metadata.get('source', 'Unknown'),
        'description': metadata.get('description', '')
    })


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Main calculation endpoint.

    Expected JSON body:
    {
        "mortgage_balance": 500000,
        "interest_rate": 3.0,
        "years_remaining": 25,
        "risk_tolerance": "conservative"  // "aggressive", "moderate", "conservative"
    }

    Returns:
        JSON with complete analysis results
    """
    try:
        # Parse request
        data = request.get_json()

        # Validate required fields
        required_fields = ['mortgage_balance', 'interest_rate', 'years_remaining']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Extract and validate parameters
        mortgage_balance = float(data['mortgage_balance'])
        interest_rate = float(data['interest_rate'])
        years_remaining = int(data['years_remaining'])
        risk_tolerance = data.get('risk_tolerance', 'conservative').lower()

        # Validation
        if mortgage_balance <= 0:
            return jsonify({'error': 'Mortgage balance must be positive'}), 400
        if interest_rate < 0:
            return jsonify({'error': 'Interest rate cannot be negative'}), 400
        if years_remaining <= 0 or years_remaining > 30:
            return jsonify({'error': 'Years remaining must be between 1 and 30'}), 400
        if risk_tolerance not in ['aggressive', 'moderate', 'conservative']:
            risk_tolerance = 'conservative'

        # Get mortgage details
        mortgage_details = get_mortgage_summary(
            mortgage_balance,
            interest_rate,
            years_remaining
        )

        # Run backtesting analysis
        analysis = backtester.run_full_analysis(
            mortgage_balance,
            interest_rate,
            years_remaining
        )

        # Map risk tolerance to percentile
        risk_map = {
            'aggressive': 'median',
            'moderate': 'percentile_75',
            'conservative': 'percentile_90'
        }
        selected_percentile = risk_map[risk_tolerance]
        recommended_scenario = analysis['results'][selected_percentile]

        # Calculate savings
        savings_vs_payoff = mortgage_balance - recommended_scenario['investment_required']

        # Build response with early payoff information
        response = {
            'mortgage_details': mortgage_details,
            'scenarios_tested': analysis['scenarios_tested'],
            'results': {
                'best_case': {
                    'investment_required': analysis['results']['best_case']['investment_required'],
                    'period': analysis['results']['best_case']['period'],
                    'years_to_payoff': analysis['results']['best_case']['years_to_payoff'],
                    'paid_off_early': analysis['results']['best_case']['paid_off_early'],
                    'leftover_amount': analysis['results']['best_case']['leftover_amount'],
                    'year_by_year': analysis['results']['best_case']['year_by_year']
                },
                'median': {
                    'investment_required': analysis['results']['median']['investment_required'],
                    'period': analysis['results']['median']['period'],
                    'years_to_payoff': analysis['results']['median']['years_to_payoff'],
                    'paid_off_early': analysis['results']['median']['paid_off_early'],
                    'leftover_amount': analysis['results']['median']['leftover_amount'],
                    'year_by_year': analysis['results']['median']['year_by_year']
                },
                'percentile_75': {
                    'investment_required': analysis['results']['percentile_75']['investment_required'],
                    'period': analysis['results']['percentile_75']['period'],
                    'years_to_payoff': analysis['results']['percentile_75']['years_to_payoff'],
                    'paid_off_early': analysis['results']['percentile_75']['paid_off_early'],
                    'leftover_amount': analysis['results']['percentile_75']['leftover_amount'],
                    'year_by_year': analysis['results']['percentile_75']['year_by_year']
                },
                'percentile_90': {
                    'investment_required': analysis['results']['percentile_90']['investment_required'],
                    'period': analysis['results']['percentile_90']['period'],
                    'years_to_payoff': analysis['results']['percentile_90']['years_to_payoff'],
                    'paid_off_early': analysis['results']['percentile_90']['paid_off_early'],
                    'leftover_amount': analysis['results']['percentile_90']['leftover_amount'],
                    'year_by_year': analysis['results']['percentile_90']['year_by_year']
                },
                'percentile_95': {
                    'investment_required': analysis['results']['percentile_95']['investment_required'],
                    'period': analysis['results']['percentile_95']['period'],
                    'years_to_payoff': analysis['results']['percentile_95']['years_to_payoff'],
                    'paid_off_early': analysis['results']['percentile_95']['paid_off_early'],
                    'leftover_amount': analysis['results']['percentile_95']['leftover_amount'],
                    'year_by_year': analysis['results']['percentile_95']['year_by_year']
                },
                'worst_case': {
                    'investment_required': analysis['results']['worst_case']['investment_required'],
                    'period': analysis['results']['worst_case']['period'],
                    'years_to_payoff': analysis['results']['worst_case']['years_to_payoff'],
                    'paid_off_early': analysis['results']['worst_case']['paid_off_early'],
                    'leftover_amount': analysis['results']['worst_case']['leftover_amount'],
                    'year_by_year': analysis['results']['worst_case']['year_by_year']
                }
            },
            'recommendation': {
                'amount': recommended_scenario['investment_required'],
                'risk_level': risk_tolerance,
                'percentile': selected_percentile,
                'period_example': recommended_scenario['period'],
                'years_to_payoff': recommended_scenario['years_to_payoff'],
                'paid_off_early': recommended_scenario['paid_off_early'],
                'leftover_amount': recommended_scenario['leftover_amount'],
                'success_rate': 0.50 if risk_tolerance == 'aggressive' else (0.75 if risk_tolerance == 'moderate' else 0.90),
                'savings_vs_payoff': round(savings_vs_payoff, 2)
            },
            'statistics': analysis['statistics'],
            'all_scenarios': [
                {
                    'period': s['period'],
                    'investment_required': s['investment_required'],
                    'years_to_payoff': s['years_to_payoff'],
                    'paid_off_early': s['paid_off_early'],
                    'leftover_amount': s['leftover_amount']
                }
                for s in analysis['all_scenarios']
            ]
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
