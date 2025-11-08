"""Risk Agent - Identify risks (basic version for Phase 1)."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from backend.models.mortgage_calculator import calculate_annual_payment


class RiskAgent(BaseAgent):
    """Agent responsible for identifying risks."""

    def __init__(self):
        super().__init__("risk")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Identify risks."""
        user_input = context['user_input']
        strategies = context['strategies']

        self.log_info("Analyzing risks")

        risks = []

        # Check withdrawal rate (retired only)
        if user_input['employment_status'] == 'retired':
            withdrawal_rate = self._calc_withdrawal_rate(user_input)

            # Determine severity based on withdrawal rate
            if withdrawal_rate >= 8.0:
                severity = 'high'
                title = f'{withdrawal_rate:.1f}% withdrawal rate is dangerously high'
                description = (
                    f'Your {withdrawal_rate:.1f}% withdrawal rate is more than DOUBLE the safe 4% rule. '
                    f'Historical data shows this has a very high failure rate. In roughly half of all 25-year '
                    f'periods since 1926, you would have run out of money with this withdrawal rate.'
                )
                mitigation = [
                    f'CRITICAL: Reduce spending to ${user_input["financial"]["portfolio"] * 0.04:,.0f}/year (4% rule)',
                    f'Or increase portfolio to ${user_input["financial"]["spending"] / 0.04:,.0f} to support current spending',
                    'Pay off mortgage completely to reduce spending needs',
                    'Consider part-time work to supplement income'
                ]
            elif withdrawal_rate >= 4.5:
                severity = 'high'
                title = f'{withdrawal_rate:.1f}% withdrawal rate exceeds safe limits'
                description = (
                    f'Your {withdrawal_rate:.1f}% withdrawal rate exceeds the safe 4% rule. '
                    f'This significantly increases your risk of running out of money in retirement.'
                )
                mitigation = [
                    f'Reduce spending to ${user_input["financial"]["portfolio"] * 0.04:,.0f}/year (4% rule)',
                    'Build larger cash reserves (2+ years)',
                    'Be prepared to cut spending in down markets'
                ]
            elif withdrawal_rate >= 4.0:
                severity = 'medium'
                title = 'Withdrawal rate at safe threshold'
                description = f'Your {withdrawal_rate:.1f}% withdrawal rate is at the 4% rule threshold.'
                mitigation = [
                    'Keep 1-year cash reserve',
                    'Monitor portfolio regularly',
                    'Be flexible with spending in bad years'
                ]

            if withdrawal_rate >= 4.0:
                risks.append({
                    'type': 'withdrawal_rate',
                    'severity': severity,
                    'title': title,
                    'description': description,
                    'mitigation': mitigation,
                    'withdrawal_rate': withdrawal_rate
                })

        # Check worst case
        recommended = strategies[0]
        if recommended['min_outcome'] < 0:
            risks.append({
                'type': 'worst_case_failure',
                'severity': 'high',
                'title': 'Portfolio can fail in worst case',
                'description': 'In the worst historical scenario, your portfolio runs out of money.',
                'mitigation': [
                    'Reduce spending',
                    'Pay off mortgage for safety',
                    'Increase starting capital'
                ]
            })

        # Check affordability (working only)
        if user_input['employment_status'] == 'working':
            mortgage_payment = calculate_annual_payment(
                user_input['mortgage']['balance'],
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            payment_ratio = mortgage_payment / user_input['financial']['income']

            if payment_ratio > 0.25:
                risks.append({
                    'type': 'high_payment_ratio',
                    'severity': 'medium',
                    'title': 'Mortgage payment is high relative to income',
                    'description': f'Your mortgage payment is {payment_ratio*100:.1f}% of income (typically want <25%).',
                    'mitigation': [
                        'Consider paying down some principal',
                        'Build emergency fund for job loss',
                        'Consider refinancing'
                    ]
                })

        # Determine overall risk level
        if any(r['severity'] == 'high' for r in risks):
            overall_level = 'high'
        elif any(r['severity'] == 'medium' for r in risks):
            overall_level = 'medium'
        else:
            overall_level = 'low'

        self.log_info(f"Identified {len(risks)} risks, overall level: {overall_level}")

        return {
            "overall_level": overall_level,
            "risks": risks
        }

    def _calc_withdrawal_rate(self, user_input: Dict) -> float:
        """Calculate withdrawal rate."""
        portfolio = user_input['financial']['portfolio']
        spending = user_input['financial']['spending']
        return (spending / portfolio) * 100
