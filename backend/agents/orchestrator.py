"""Orchestrator - Coordinate all agents."""

import asyncio
from typing import Dict, Any, AsyncGenerator
from .data_agent import DataAgent
from .strategy_agent import StrategyAgent
from .risk_agent import RiskAgent


class AnalysisOrchestrator:
    """Orchestrates the analysis workflow."""

    def __init__(self):
        self.data_agent = DataAgent()
        self.strategy_agent = StrategyAgent()
        self.risk_agent = RiskAgent()

    async def analyze(self, user_input: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Run complete analysis with progress updates."""

        # Calculate projection parameters
        current_age = user_input.get('age', 55)
        end_age = 100  # Project to age 100
        projection_years = end_age - current_age
        mortgage_years = user_input['mortgage']['years']

        context = {
            "user_input": user_input,
            "projection_years": projection_years,
            "mortgage_years": mortgage_years,
            "current_age": current_age,
            "end_age": end_age
        }

        # Agent 1: Data Agent
        yield self.data_agent.report_progress("working", "Loading 100 years of S&P 500 returns")
        data_result = await self.data_agent.execute(context)
        context.update(data_result)
        yield self.data_agent.report_progress("complete", f"Found {data_result['num_periods']} historical periods")

        # Agent 2: Strategy Agent
        yield self.strategy_agent.report_progress("working", "Testing Strategy 1: Pay off completely")
        await asyncio.sleep(0.1)  # Small delay for UI

        yield self.strategy_agent.report_progress("working", "Testing Strategy 2: Keep 100% invested")
        await asyncio.sleep(0.1)

        strategy_result = await self.strategy_agent.execute(context)
        context.update(strategy_result)
        yield self.strategy_agent.report_progress("complete", f"Tested {len(strategy_result['strategies'])} strategies across {data_result['num_periods']} periods")

        # Agent 3: Risk Agent
        yield self.risk_agent.report_progress("working", "Analyzing risk factors")
        risk_result = await self.risk_agent.execute(context)
        context.update(risk_result)
        yield self.risk_agent.report_progress("complete", f"Risk level: {risk_result['overall_level'].upper()}")

        # Calculate additional insights
        insights = self._generate_insights(user_input, strategy_result, risk_result)

        # Final result
        yield {
            "agent": "complete",
            "status": "complete",
            "message": "Analysis complete",
            "result": {
                "recommended": strategy_result['recommended'],
                "strategies": strategy_result['strategies'],
                "risk_level": risk_result['overall_level'],
                "risks": risk_result['risks'],
                "insights": insights,
                "user_input": user_input,
                "projection_years": projection_years,
                "num_periods": data_result['num_periods'],
                "current_age": current_age,
                "end_age": end_age,
                "bond_return_used": strategy_result.get('bond_return_used', 4.0)
            }
        }

    def _generate_insights(self, user_input: Dict, strategy_result: Dict, risk_result: Dict) -> list:
        """Generate personalized insights."""
        insights = []

        is_retired = user_input['employment_status'] == 'retired'

        # Portfolio size insight
        if is_retired:
            mortgage_pct = user_input['mortgage']['balance'] / user_input['financial']['portfolio']

            if mortgage_pct < 0.15:
                insights.append({
                    'type': 'portfolio_size',
                    'message': f"With your ${user_input['financial']['portfolio']:,} portfolio, "
                              f"the ${user_input['mortgage']['balance']:,} mortgage is only "
                              f"{mortgage_pct*100:.0f}% of your assets. You can easily afford "
                              f"to keep it invested and capture market returns."
                })

        # Mortgage rate insight
        if user_input['mortgage']['rate'] < 3.5:
            insights.append({
                'type': 'low_rate',
                'message': f"Your {user_input['mortgage']['rate']}% rate is very low. "
                          f"Historical S&P 500 returns (10% avg) beat this easily."
            })

        # Expected benefit insight
        recommended = strategy_result['recommended']
        # Find a "Pay Off Completely" strategy (any variant)
        pay_off_strategies = [s for s in strategy_result['strategies'] if 'Pay Off Completely' in s['name']]

        if pay_off_strategies:
            # Use the first pay off strategy for comparison
            pay_off_strategy = pay_off_strategies[0]
            benefit = recommended['avg_outcome'] - pay_off_strategy['avg_outcome']

            if 'Pay Off Completely' not in recommended['name'] and benefit > 0:
                insights.append({
                    'type': 'expected_benefit',
                    'message': f"Expected benefit of keeping invested: ${abs(benefit):,.0f} over 25 years"
                })

        return insights
