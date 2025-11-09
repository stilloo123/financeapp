"""Strategy Agent - Test multiple strategies."""

from typing import Dict, Any, List
from statistics import mean, median
import numpy as np
from .base_agent import BaseAgent
from backend.models.mortgage_calculator import calculate_annual_payment
from backend.services.treasury_data import get_current_bond_return


class StrategyAgent(BaseAgent):
    """Agent responsible for testing strategies."""

    def __init__(self):
        super().__init__("strategy")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test multiple strategies with both treasury and bond fund scenarios."""
        user_input = context['user_input']
        historical_windows = context['historical_windows']
        projection_years = context.get('projection_years', 25)
        mortgage_years = context.get('mortgage_years', 25)

        # Fetch current bond return from FRED API
        self.log_info("Fetching current 30-year treasury yield...")
        bond_return = get_current_bond_return()
        self.log_info(f"Using bond return: {bond_return:.2f}%")

        self.log_info(f"Testing strategies over {projection_years} years")

        strategies = []

        # Strategy 1: Pay off completely - Treasury Bonds
        self.log_info("Testing Strategy 1: Pay off completely - Treasury Bonds")
        strategy_1 = await self._test_payoff_completely(user_input, historical_windows, projection_years, mortgage_years, bond_return, bond_type="treasury")
        strategies.append(strategy_1)

        # Strategy 2: Pay off completely - Bond Fund
        self.log_info("Testing Strategy 2: Pay off completely - Bond Fund")
        strategy_2 = await self._test_payoff_completely(user_input, historical_windows, projection_years, mortgage_years, bond_return, bond_type="fund")
        strategies.append(strategy_2)

        # Strategy 3: Keep 100% invested - Treasury Bonds
        self.log_info("Testing Strategy 3: Keep 100% invested - Treasury Bonds")
        strategy_3 = await self._test_keep_invested(user_input, historical_windows, projection_years, mortgage_years, bond_return, bond_type="treasury")
        strategies.append(strategy_3)

        # Strategy 4: Keep 100% invested - Bond Fund
        self.log_info("Testing Strategy 4: Keep 100% invested - Bond Fund")
        strategy_4 = await self._test_keep_invested(user_input, historical_windows, projection_years, mortgage_years, bond_return, bond_type="fund")
        strategies.append(strategy_4)

        # Tag strategies by what they optimize for
        # Sort by median outcome to find highest money
        by_money = sorted(strategies, key=lambda s: s['median_outcome'], reverse=True)

        # For safety, prioritize:
        # 1. Success rate (higher is better)
        # 2. Min outcome (higher floor is safer)
        # 3. Lower median (more conservative = safer for retired folks)
        by_safety = sorted(strategies, key=lambda s: (
            s['success_rate'],           # Higher success rate
            s['min_outcome'],             # Higher worst-case floor
            -s['median_outcome']          # LOWER median = more conservative
        ), reverse=True)

        # Assign tags - with 4 strategies, rank all by median outcome
        for i, s in enumerate(strategies):
            s['tags'] = []
            s['rank'] = i + 1  # Rank 1-4 based on original order
            s['emoji'] = ''

        # Tag best money and best safety
        by_money[0]['tags'].append('Most Money')
        by_money[0]['emoji'] = '💰'

        by_safety[0]['tags'].append('Most Safety')
        if not by_safety[0]['emoji']:
            by_safety[0]['emoji'] = '🛡️'

        # If same strategy is both, give it gold medal
        if by_money[0] == by_safety[0]:
            by_money[0]['tags'] = ['Most Money', 'Most Safety']
            by_money[0]['emoji'] = '🥇'

        # Sort by median outcome (best first)
        strategies.sort(key=lambda s: s['median_outcome'], reverse=True)

        # Reassign ranks based on median outcome
        for i, s in enumerate(strategies):
            s['rank'] = i + 1

        # DEBUG LOGGING - Results Summary
        print(f"\n{'='*60}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*60}")
        for strategy in strategies:
            print(f"\n{strategy['emoji']} {strategy['name']} - {', '.join(strategy['tags'])}")
            print(f"   Median Outcome: ${strategy['median_outcome']:,.0f}")
            print(f"   Success Rate: {strategy['success_rate']*100:.1f}%")
            print(f"   P10 (worst 10%): ${strategy['p10_outcome']:,.0f}")
            print(f"   Min: ${strategy['min_outcome']:,.0f}")
        print(f"\n{'='*60}\n")

        self.log_info(f"Tested {len(strategies)} strategies")

        return {
            "strategies": strategies,
            "recommended": strategies[0],  # Highest ranked
            "bond_return_used": bond_return
        }

    async def _test_payoff_completely(self, user_input: Dict, windows: List, projection_years: int, mortgage_years: int, bond_return: float, bond_type: str = "treasury") -> Dict:
        """Test paying off mortgage completely."""
        is_retired = user_input['employment_status'] == 'retired'

        if is_retired:
            # After paying off mortgage, spending stays the same (no mortgage payment needed)
            # User's spending input already excludes mortgage
            new_spending = user_input['financial']['spending']

            mortgage_payment = calculate_annual_payment(
                user_input['mortgage']['balance'],
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            new_portfolio = user_input['financial']['portfolio'] - user_input['mortgage']['balance']

            # DEBUG LOGGING
            print(f"\n{'='*60}")
            print(f"DEBUG: Pay Off Completely Strategy")
            print(f"{'='*60}")
            print(f"Original Portfolio: ${user_input['financial']['portfolio']:,.0f}")
            print(f"Mortgage Balance: ${user_input['mortgage']['balance']:,.0f}")
            print(f"Mortgage Payment: ${mortgage_payment:,.2f}/year")
            print(f"Original Spending: ${user_input['financial']['spending']:,.0f}/year")
            print(f"New Portfolio: ${new_portfolio:,.0f}")
            print(f"New Spending: ${new_spending:,.2f}/year")
            print(f"Withdrawal Rate: {new_spending/new_portfolio*100:.2f}%")
            print(f"{'='*60}\n")

            results_final = []
            results_at_payoff = []
            period_details = []
            for window in windows:
                # Use either constant treasury rate or historical bond returns
                bond_data = bond_return if bond_type == "treasury" else window['bond_returns']
                # Enable annual rebalancing for bond fund option only
                should_rebalance = (bond_type == "fund")

                result = self._simulate_portfolio(
                    new_portfolio,
                    window['returns'],
                    new_spending,
                    mortgage_years,
                    user_input['financial']['stock_allocation_pct'],
                    bond_data,
                    rebalance_annually=should_rebalance
                )
                results_final.append(result['final'])
                results_at_payoff.append(result['at_mortgage_payoff'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'balance_at_payoff': result['at_mortgage_payoff'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        else:
            # Working scenario
            # After paying off, no mortgage payment needed
            # Investment grows without withdrawals
            new_portfolio = user_input['financial']['portfolio'] - user_input['mortgage']['balance']

            results_final = []
            results_at_payoff = []
            period_details = []
            for window in windows:
                # Use either constant treasury rate or historical bond returns
                bond_data = bond_return if bond_type == "treasury" else window['bond_returns']
                # Enable annual rebalancing for bond fund option only
                should_rebalance = (bond_type == "fund")

                result = self._simulate_portfolio_working(
                    new_portfolio,
                    window['returns'],
                    user_input['financial'].get('income', 0),
                    user_input['financial']['spending'],
                    mortgage_paid_off=True,
                    mortgage_years=mortgage_years,
                    income_years=user_input['financial'].get('income_years'),
                    stock_allocation_pct=user_input['financial']['stock_allocation_pct'],
                    bond_returns=bond_data,
                    rebalance_annually=should_rebalance
                )
                results_final.append(result['final'])
                results_at_payoff.append(result['at_mortgage_payoff'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'balance_at_payoff': result['at_mortgage_payoff'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        # Sort periods by outcome to find best/worst
        sorted_periods = sorted(period_details, key=lambda x: x['final_balance'])

        # Get worst 5 periods
        worst_periods_list = sorted_periods[:5]

        # Always include 2000-2025 period if it exists (includes dot-com crash & 2008 crisis)
        period_2000_2025 = next((p for p in period_details if p['start_year'] == 2000), None)
        if period_2000_2025 and period_2000_2025 not in worst_periods_list:
            worst_periods_list.append(period_2000_2025)
            # Re-sort by final_balance
            worst_periods_list = sorted(worst_periods_list, key=lambda x: x['final_balance'])

        # Calculate percentiles for END OF PROJECTION (age 100)
        results_array_final = np.array(results_final)
        p10_final = np.percentile(results_array_final, 10)
        p90_final = np.percentile(results_array_final, 90)
        median_final = median(results_final)

        # Calculate percentiles for MORTGAGE PAYOFF milestone
        results_array_payoff = np.array(results_at_payoff)
        p10_payoff = np.percentile(results_array_payoff, 10)
        p90_payoff = np.percentile(results_array_payoff, 90)
        median_payoff = median(results_at_payoff)

        # Generate strategy name with allocation
        stock_pct = user_input['financial'].get('stock_allocation_pct', 100)
        bond_pct = 100 - stock_pct
        bond_label = "Treasury Bonds" if bond_type == "treasury" else "Bond Fund"

        if stock_pct == 100:
            name = f"Pay Off Completely - Remaining in 100% SPY"
        elif bond_pct == 100:
            name = f"Pay Off Completely - Remaining in 100% {bond_label}"
        else:
            name = f"Pay Off Completely - Remaining in {stock_pct}% SPY / {bond_pct}% {bond_label}"

        return {
            'name': name,
            'bond_type': bond_type,
            'description': 'Pay off mortgage today, reduce portfolio',
            'success_rate': sum(1 for r in results_final if r >= 0) / len(results_final),
            # End of projection (age 100) outcomes
            'avg_outcome': mean(results_final),
            'median_outcome': median_final,
            'p10_outcome': p10_final,
            'p90_outcome': p90_final,
            'min_outcome': min(results_final),
            'max_outcome': max(results_final),
            # Mortgage payoff milestone outcomes
            'median_at_payoff': median_payoff,
            'p10_at_payoff': p10_payoff,
            'p90_at_payoff': p90_payoff,
            # Metadata
            'mortgage_payoff_year': mortgage_years,
            'projection_years': projection_years,
            # Details
            'results': results_final,
            'period_details': period_details,
            'worst_periods': worst_periods_list,
            'best_periods': sorted_periods[-5:][::-1]
        }

    async def _test_keep_invested(self, user_input: Dict, windows: List, projection_years: int, mortgage_years: int, bond_return: float, bond_type: str = "treasury") -> Dict:
        """Test keeping money invested."""
        is_retired = user_input['employment_status'] == 'retired'

        if is_retired:
            portfolio = user_input['financial']['portfolio']

            # Calculate mortgage payment to add to spending
            mortgage_payment = calculate_annual_payment(
                user_input['mortgage']['balance'],
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            # Total spending = living expenses + mortgage payment
            total_spending = user_input['financial']['spending'] + mortgage_payment

            # DEBUG LOGGING
            print(f"\n{'='*60}")
            print(f"DEBUG: Keep 100% Invested Strategy")
            print(f"{'='*60}")
            print(f"Portfolio: ${portfolio:,.0f}")
            print(f"Living Expenses: ${user_input['financial']['spending']:,.0f}/year")
            print(f"Mortgage Payment: ${mortgage_payment:,.2f}/year")
            print(f"Total Annual Spending: ${total_spending:,.0f}/year")
            print(f"Withdrawal Rate: {total_spending/portfolio*100:.2f}%")
            print(f"{'='*60}\n")

            results_final = []
            results_at_payoff = []
            period_details = []
            for window in windows:
                # Use either constant treasury rate or historical bond returns
                bond_data = bond_return if bond_type == "treasury" else window['bond_returns']
                # Enable annual rebalancing for bond fund option only
                should_rebalance = (bond_type == "fund")

                result = self._simulate_portfolio(
                    portfolio,
                    window['returns'],
                    user_input['financial']['spending'],  # Living expenses only
                    mortgage_years,
                    user_input['financial']['stock_allocation_pct'],
                    bond_data,
                    rebalance_annually=should_rebalance,
                    mortgage_payment=mortgage_payment  # Separate mortgage payment
                )
                results_final.append(result['final'])
                results_at_payoff.append(result['at_mortgage_payoff'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'balance_at_payoff': result['at_mortgage_payoff'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        else:
            # Working scenario - keep everything invested
            portfolio = user_input['financial']['portfolio']

            results_final = []
            results_at_payoff = []
            period_details = []
            for window in windows:
                # Use either constant treasury rate or historical bond returns
                bond_data = bond_return if bond_type == "treasury" else window['bond_returns']
                # Enable annual rebalancing for bond fund option only
                should_rebalance = (bond_type == "fund")

                result = self._simulate_portfolio_working(
                    portfolio,
                    window['returns'],
                    user_input['financial'].get('income', 0),
                    user_input['financial']['spending'],
                    mortgage_paid_off=False,
                    mortgage_years=mortgage_years,
                    income_years=user_input['financial'].get('income_years'),
                    stock_allocation_pct=user_input['financial']['stock_allocation_pct'],
                    bond_returns=bond_data,
                    rebalance_annually=should_rebalance
                )
                results_final.append(result['final'])
                results_at_payoff.append(result['at_mortgage_payoff'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'balance_at_payoff': result['at_mortgage_payoff'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        # Sort periods by outcome to find best/worst
        sorted_periods = sorted(period_details, key=lambda x: x['final_balance'])

        # Get worst 5 periods
        worst_periods_list = sorted_periods[:5]

        # Always include 2000-2025 period if it exists (includes dot-com crash & 2008 crisis)
        period_2000_2025 = next((p for p in period_details if p['start_year'] == 2000), None)
        if period_2000_2025 and period_2000_2025 not in worst_periods_list:
            worst_periods_list.append(period_2000_2025)
            # Re-sort by final_balance
            worst_periods_list = sorted(worst_periods_list, key=lambda x: x['final_balance'])

        # Calculate percentiles for END OF PROJECTION (age 100)
        results_array_final = np.array(results_final)
        p10_final = np.percentile(results_array_final, 10)
        p90_final = np.percentile(results_array_final, 90)
        median_final = median(results_final)

        # Calculate percentiles for MORTGAGE PAYOFF milestone
        results_array_payoff = np.array(results_at_payoff)
        p10_payoff = np.percentile(results_array_payoff, 10)
        p90_payoff = np.percentile(results_array_payoff, 90)
        median_payoff = median(results_at_payoff)

        # Generate strategy name with allocation
        stock_pct = user_input['financial'].get('stock_allocation_pct', 100)
        bond_pct = 100 - stock_pct
        bond_label = "Treasury Bonds" if bond_type == "treasury" else "Bond Fund"

        if stock_pct == 100:
            name = f"Keep 100% Invested - 100% SPY"
        elif bond_pct == 100:
            name = f"Keep 100% Invested - 100% {bond_label}"
        else:
            name = f"Keep 100% Invested - {stock_pct}% SPY / {bond_pct}% {bond_label}"

        return {
            'name': name,
            'bond_type': bond_type,
            'description': 'Keep mortgage, invest full amount',
            'success_rate': sum(1 for r in results_final if r >= 0) / len(results_final),
            # End of projection (age 100) outcomes
            'avg_outcome': mean(results_final),
            'median_outcome': median_final,
            'p10_outcome': p10_final,
            'p90_outcome': p90_final,
            'min_outcome': min(results_final),
            'max_outcome': max(results_final),
            # Mortgage payoff milestone outcomes
            'median_at_payoff': median_payoff,
            'p10_at_payoff': p10_payoff,
            'p90_at_payoff': p90_payoff,
            # Metadata
            'mortgage_payoff_year': mortgage_years,
            'projection_years': projection_years,
            # Details
            'results': results_final,
            'period_details': period_details,
            'worst_periods': worst_periods_list,
            'best_periods': sorted_periods[-5:][::-1]
        }

    async def _test_partial_payoff(self, user_input: Dict, windows: List, pct: float) -> Dict:
        """Test partial payoff."""
        payoff_amount = user_input['mortgage']['balance'] * pct
        is_retired = user_input['employment_status'] == 'retired'

        if is_retired:
            # Calculate new mortgage payment
            new_mortgage_balance = user_input['mortgage']['balance'] - payoff_amount
            new_mortgage_payment = calculate_annual_payment(
                new_mortgage_balance,
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            # Total spending = living expenses (from user) + new mortgage payment
            # User's spending input already excludes mortgage
            new_spending = user_input['financial']['spending'] + new_mortgage_payment

            new_portfolio = user_input['financial']['portfolio'] - payoff_amount

            results = []
            period_details = []
            for window in windows:
                result = self._simulate_portfolio(
                    new_portfolio,
                    window['returns'],
                    new_spending,
                    mortgage_years=None,
                    stock_allocation_pct=user_input['financial']['stock_allocation_pct'],
                    bond_return=4.0  # Use fallback for partial payoff (not used in main flow)
                )
                results.append(result['final'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        else:
            # Working scenario
            new_portfolio = user_input['financial']['portfolio'] - payoff_amount

            results = []
            period_details = []
            for window in windows:
                result = self._simulate_portfolio_working(
                    new_portfolio,
                    window['returns'],
                    user_input['financial']['income'],
                    user_input['financial']['spending'],
                    mortgage_paid_off=False,  # Still have partial mortgage
                    income_years=user_input['financial'].get('income_years'),
                    stock_allocation_pct=user_input['financial']['stock_allocation_pct'],
                    bond_return=4.0  # Use fallback for partial payoff (not used in main flow)
                )
                results.append(result['final'])
                period_details.append({
                    'period': window['period'],
                    'start_year': window['start_year'],
                    'end_year': window['end_year'],
                    'final_balance': result['final'],
                    'success': result['final'] >= 0,
                    'ran_out_year': result['ran_out_year']
                })

        # Sort periods by outcome to find best/worst
        sorted_periods = sorted(period_details, key=lambda x: x['final_balance'])

        # Get worst 5 periods
        worst_periods_list = sorted_periods[:5]

        # Always include 2000-2025 period if it exists (includes dot-com crash & 2008 crisis)
        period_2000_2025 = next((p for p in period_details if p['start_year'] == 2000), None)
        if period_2000_2025 and period_2000_2025 not in worst_periods_list:
            worst_periods_list.append(period_2000_2025)
            # Re-sort by final_balance
            worst_periods_list = sorted(worst_periods_list, key=lambda x: x['final_balance'])

        return {
            'name': f'Pay Off {int(pct*100)}%',
            'description': f'Pay off ${payoff_amount:,.0f} today',
            'success_rate': sum(1 for r in results if r >= 0) / len(results),
            'avg_outcome': mean(results),
            'median_outcome': median(results),
            'min_outcome': min(results),
            'max_outcome': max(results),
            'results': results,
            'period_details': period_details,
            'worst_periods': worst_periods_list,
            'best_periods': sorted_periods[-5:][::-1]
        }

    def _simulate_portfolio(self, initial: float, returns: List[float], annual_withdrawal: float,
                            mortgage_years: int = None, stock_allocation_pct: float = 100.0,
                            bond_returns = 4.0, rebalance_annually: bool = False,
                            mortgage_payment: float = 0.0) -> Dict[str, float]:
        """Simulate portfolio with withdrawals (retired).

        Args:
            annual_withdrawal: Living expenses (excluding mortgage)
            mortgage_payment: Mortgage payment (added for first mortgage_years, then drops to 0)
            mortgage_years: Years until mortgage is paid off
            bond_returns: Either a float (constant rate) or List[float] (historical returns)
            rebalance_annually: If True, rebalance to target allocation each year (for bond fund option)
        """
        balance = initial
        mortgage_payoff_balance = None
        ran_out_year = None

        # Calculate allocation percentages
        target_stock_pct = stock_allocation_pct / 100.0
        target_bond_pct = 1.0 - target_stock_pct

        # Check if bond_returns is a list or a constant
        bond_returns_is_list = isinstance(bond_returns, list)

        # Track separate stock and bond balances for rebalancing
        if rebalance_annually:
            stock_balance = balance * target_stock_pct
            bond_balance = balance * target_bond_pct
        else:
            stock_balance = None
            bond_balance = None

        for year_idx, stock_return in enumerate(returns, start=1):
            # Calculate withdrawal amount (includes mortgage payment until paid off)
            if mortgage_years and year_idx <= mortgage_years:
                total_withdrawal = annual_withdrawal + mortgage_payment
            else:
                total_withdrawal = annual_withdrawal

            if rebalance_annually:
                # With rebalancing: track stock and bond separately
                # Withdraw proportionally from both
                withdrawal_from_stocks = total_withdrawal * target_stock_pct
                withdrawal_from_bonds = total_withdrawal * target_bond_pct

                stock_balance -= withdrawal_from_stocks
                bond_balance -= withdrawal_from_bonds

                # Get bond return for this year
                if bond_returns_is_list:
                    bond_return = bond_returns[year_idx - 1]
                else:
                    bond_return = bond_returns

                # Apply returns to each portion
                stock_balance *= (1 + stock_return / 100.0)
                bond_balance *= (1 + bond_return / 100.0)

                # Rebalance back to target allocation
                total_balance = stock_balance + bond_balance
                stock_balance = total_balance * target_stock_pct
                bond_balance = total_balance * target_bond_pct

                balance = total_balance
            else:
                # Without rebalancing: use blended return (existing logic)
                balance -= total_withdrawal

                # Get bond return for this year
                if bond_returns_is_list:
                    bond_return = bond_returns[year_idx - 1]
                else:
                    bond_return = bond_returns

                # Apply blended return
                blended_return = (target_stock_pct * stock_return) + (target_bond_pct * bond_return)
                balance *= (1 + blended_return / 100.0)

            # Track when portfolio runs out
            if ran_out_year is None and balance < 0:
                ran_out_year = year_idx

            # Track balance when mortgage is paid off
            if mortgage_years and year_idx == mortgage_years:
                mortgage_payoff_balance = balance

        return {
            'final': balance,
            'at_mortgage_payoff': mortgage_payoff_balance if mortgage_payoff_balance is not None else balance,
            'ran_out_year': ran_out_year
        }

    def _simulate_portfolio_working(self, initial: float, returns: List[float],
                                     income: float, spending: float,
                                     mortgage_paid_off: bool = False, mortgage_years: int = None,
                                     income_years: int = None, stock_allocation_pct: float = 100.0,
                                     bond_returns = 4.0, rebalance_annually: bool = False) -> Dict[str, float]:
        """Simulate portfolio while working.

        Args:
            bond_returns: Either a float (constant rate) or List[float] (historical returns)
            rebalance_annually: If True, rebalance to target allocation each year (for bond fund option)
        """
        balance = initial
        mortgage_payoff_balance = None
        ran_out_year = None

        # Calculate allocation percentages
        target_stock_pct = stock_allocation_pct / 100.0
        target_bond_pct = 1.0 - target_stock_pct

        # Check if bond_returns is a list or a constant
        bond_returns_is_list = isinstance(bond_returns, list)

        # Track separate stock and bond balances for rebalancing
        if rebalance_annually:
            stock_balance = balance * target_stock_pct
            bond_balance = balance * target_bond_pct
        else:
            stock_balance = None
            bond_balance = None

        for year_idx, stock_return in enumerate(returns, start=1):
            if rebalance_annually:
                # With rebalancing: track stock and bond separately
                # Add savings (distributed proportionally) or subtract spending
                if income_years is None or year_idx <= income_years:
                    net_cashflow = income - spending
                    stock_balance += net_cashflow * target_stock_pct
                    bond_balance += net_cashflow * target_bond_pct
                else:
                    stock_balance -= spending * target_stock_pct
                    bond_balance -= spending * target_bond_pct

                # Get bond return for this year
                if bond_returns_is_list:
                    bond_return = bond_returns[year_idx - 1]
                else:
                    bond_return = bond_returns

                # Apply returns to each portion
                stock_balance *= (1 + stock_return / 100.0)
                bond_balance *= (1 + bond_return / 100.0)

                # Rebalance back to target allocation
                total_balance = stock_balance + bond_balance
                stock_balance = total_balance * target_stock_pct
                bond_balance = total_balance * target_bond_pct

                balance = total_balance
            else:
                # Without rebalancing: use blended return (existing logic)
                # Add savings (income - spending) only if still within income_years
                if income_years is None or year_idx <= income_years:
                    balance += (income - spending)
                else:
                    # After income stops, only subtract spending
                    balance -= spending

                # Get bond return for this year
                if bond_returns_is_list:
                    bond_return = bond_returns[year_idx - 1]
                else:
                    bond_return = bond_returns

                # Apply blended return
                blended_return = (target_stock_pct * stock_return) + (target_bond_pct * bond_return)
                balance *= (1 + blended_return / 100.0)

            # Track when portfolio runs out
            if ran_out_year is None and balance < 0:
                ran_out_year = year_idx

            # Track balance when mortgage is paid off
            if mortgage_years and year_idx == mortgage_years:
                mortgage_payoff_balance = balance

        return {
            'final': balance,
            'at_mortgage_payoff': mortgage_payoff_balance if mortgage_payoff_balance is not None else balance,
            'ran_out_year': ran_out_year
        }
