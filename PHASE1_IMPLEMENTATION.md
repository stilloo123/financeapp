# Phase 1 Implementation Plan

## Goal
Build end-to-end working flow with real recommendations

**Timeline:** Week 1-2

**Deliverables:**
1. Landing page (Page 1)
2. Form input (Page 2) with employment status branching
3. Agent analysis loading (Page 3) with real-time progress
4. Main results (Page 5) with recommendation
5. Backend agents: Data, Strategy, basic Risk

---

## Task Breakdown

### Backend (Days 1-4)

#### Day 1: Agent Infrastructure

**1. Create agent base structure**
```
backend/
  agents/
    __init__.py
    base_agent.py          # Abstract base class
    data_agent.py          # Load historical data
    strategy_agent.py      # Test strategies
    risk_agent.py          # Identify risks (basic)
    orchestrator.py        # Coordinate agents
```

**2. Implement base_agent.py**
- Abstract class for all agents
- Common logging
- Progress reporting interface

**3. Implement data_agent.py**
- Load S&P 500 data using existing SP500DataLoader
- Filter to 71 periods (exclude Great Depression)
- Return structured windows

#### Day 2: Strategy Agent

**1. Implement strategy_agent.py**
- Test Strategy 1: Pay off completely
- Test Strategy 2: Keep 100% invested
- Test Strategy 3: Pay off 50%
- Handle both working and retired scenarios
- Return ranked strategies

**2. Create simulation functions**
- `simulate_retired()` - Portfolio withdrawal simulation
- `simulate_working()` - Working scenario simulation
- Reuse existing logic from test files

#### Day 3: Risk Agent + Orchestrator

**1. Implement risk_agent.py (basic version)**
- Calculate withdrawal rate (retired only)
- Check if > 4% threshold
- Identify worst case scenario
- Return risk level + basic concerns

**2. Implement orchestrator.py**
- Coordinate all agents
- Stream progress updates
- Return complete analysis

#### Day 4: API Layer

**1. Update FastAPI app**
- POST /api/analyze endpoint
- GET /api/analysis/{id}/progress (SSE)
- GET /api/analysis/{id}/results

**2. Add response models**
- Pydantic models for all responses
- Proper error handling

**3. Add caching**
- Redis for analysis results
- Cache by input hash

---

### Frontend (Days 5-8)

#### Day 5: Project Setup + Landing Page

**1. Create new Next.js project**
```bash
npx create-next-app@latest payofforinvest-frontend --typescript --tailwind
```

**2. Install dependencies**
```bash
npm install @tanstack/react-query axios recharts framer-motion
```

**3. Build Landing Page (Page 1)**
- Clean, minimal design
- Hero headline
- 3 value props
- CTA button
- Social proof

**File:** `app/page.tsx`

#### Day 6: Form Input

**1. Build Form Input (Page 2)**
- Employment status radio buttons
- Mortgage fields (balance, rate, years)
- Financial fields (branches on employment status)
- Real-time validation
- Form state management

**Files:**
- `app/calculator/page.tsx`
- `components/MortgageForm.tsx`
- `components/EmploymentStatusSelector.tsx`

**2. Form validation logic**
- Required fields
- Numeric validation
- Range checking
- Error messages

#### Day 7: Agent Loading

**1. Build Agent Loading (Page 3)**
- 4 agent cards
- Real-time progress via SSE
- Animation/transitions
- Auto-advance when complete

**Files:**
- `app/analysis/[id]/page.tsx`
- `components/AgentProgress.tsx`
- `hooks/useAnalysisProgress.ts`

**2. SSE connection**
- Connect to /api/analysis/{id}/progress
- Parse SSE events
- Update UI in real-time

#### Day 8: Results Page

**1. Build Main Results (Page 5)**
- Hero recommendation card
- Key metrics display
- Success rate visualization
- Agent insight box
- Navigation to future pages (stub links)

**Files:**
- `app/results/[id]/page.tsx`
- `components/RecommendationCard.tsx`
- `components/MetricsDisplay.tsx`

**2. Results logic**
- Fetch from /api/analysis/{id}/results
- Display recommendation
- Format numbers
- Handle loading/error states

---

## Detailed Implementation

### Backend Implementation

#### 1. base_agent.py

```python
"""Base class for all agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task."""
        pass

    def report_progress(self, status: str, message: str) -> Dict[str, Any]:
        """Report progress update."""
        return {
            "agent": self.name,
            "status": status,
            "message": message
        }

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(f"[{self.name}] {message}")
```

#### 2. data_agent.py

```python
"""Data Agent - Load historical S&P 500 data."""

from typing import Dict, Any
from .base_agent import BaseAgent
from backend.services.data_loader import SP500DataLoader


class DataAgent(BaseAgent):
    """Agent responsible for loading historical data."""

    def __init__(self):
        super().__init__("data")
        self.loader = SP500DataLoader()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Load historical data."""
        self.log_info("Loading historical S&P 500 data")

        # Get all 25-year windows
        windows = self._load_windows()

        self.log_info(f"Loaded {len(windows)} historical periods")

        return {
            "historical_windows": windows,
            "num_periods": len(windows)
        }

    def _load_windows(self):
        """Load and filter historical windows."""
        great_depression = ['1928-1952', '1929-1953', '1930-1954', '1931-1955']
        windows = []

        for start_year in range(1926, 2001):
            end_year = start_year + 24
            if end_year <= 2025:
                period = f"{start_year}-{end_year}"
                if period not in great_depression:
                    try:
                        returns = self.loader.get_returns(start_year, end_year)
                        if len(returns) == 25:
                            windows.append({
                                'period': period,
                                'start_year': start_year,
                                'end_year': end_year,
                                'returns': returns
                            })
                    except:
                        pass

        return windows
```

#### 3. strategy_agent.py

```python
"""Strategy Agent - Test multiple strategies."""

from typing import Dict, Any, List
from statistics import mean, median
from .base_agent import BaseAgent
from backend.models.mortgage_calculator import calculate_annual_payment


class StrategyAgent(BaseAgent):
    """Agent responsible for testing strategies."""

    def __init__(self):
        super().__init__("strategy")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Test multiple strategies."""
        user_input = context['user_input']
        historical_windows = context['historical_windows']

        self.log_info("Testing strategies")

        strategies = []

        # Strategy 1: Pay off completely
        self.log_info("Testing Strategy 1: Pay off completely")
        strategy_1 = await self._test_payoff_completely(user_input, historical_windows)
        strategies.append(strategy_1)

        # Strategy 2: Keep 100% invested
        self.log_info("Testing Strategy 2: Keep 100% invested")
        strategy_2 = await self._test_keep_invested(user_input, historical_windows)
        strategies.append(strategy_2)

        # Strategy 3: Pay off 50%
        self.log_info("Testing Strategy 3: Pay off 50%")
        strategy_3 = await self._test_partial_payoff(user_input, historical_windows, 0.5)
        strategies.append(strategy_3)

        # Rank by expected value
        strategies.sort(key=lambda s: s['avg_outcome'], reverse=True)

        # Add rankings
        for i, s in enumerate(strategies):
            s['rank'] = i + 1
            s['emoji'] = ['🥇', '🥈', '🥉'][i]

        self.log_info(f"Tested {len(strategies)} strategies")

        return {
            "strategies": strategies,
            "recommended": strategies[0]  # Best strategy
        }

    async def _test_payoff_completely(self, user_input: Dict, windows: List) -> Dict:
        """Test paying off mortgage completely."""
        is_retired = user_input['employment_status'] == 'retired'

        if is_retired:
            # Calculate new withdrawal after paying off
            mortgage_payment = calculate_annual_payment(
                user_input['mortgage']['balance'],
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            if user_input['financial']['spending_includes_mortgage']:
                new_spending = user_input['financial']['spending'] - mortgage_payment
            else:
                new_spending = user_input['financial']['spending']

            new_portfolio = user_input['financial']['portfolio'] - user_input['mortgage']['balance']

            results = []
            for window in windows:
                final = self._simulate_portfolio(
                    new_portfolio,
                    window['returns'],
                    new_spending
                )
                results.append(final)

        else:
            # Working scenario
            # After paying off, no mortgage payment needed
            # Investment grows without withdrawals
            new_portfolio = user_input['financial']['portfolio'] - user_input['mortgage']['balance']

            results = []
            for window in windows:
                final = self._simulate_portfolio_working(
                    new_portfolio,
                    window['returns'],
                    user_input['financial']['income'],
                    user_input['financial']['spending']
                )
                results.append(final)

        return {
            'name': 'Pay Off Completely',
            'description': 'Pay off mortgage today, reduce portfolio',
            'success_rate': sum(1 for r in results if r >= 0) / len(results),
            'avg_outcome': mean(results),
            'median_outcome': median(results),
            'min_outcome': min(results),
            'max_outcome': max(results),
            'results': results
        }

    async def _test_keep_invested(self, user_input: Dict, windows: List) -> Dict:
        """Test keeping money invested."""
        is_retired = user_input['employment_status'] == 'retired'

        if is_retired:
            portfolio = user_input['financial']['portfolio']
            spending = user_input['financial']['spending']

            results = []
            for window in windows:
                final = self._simulate_portfolio(
                    portfolio,
                    window['returns'],
                    spending
                )
                results.append(final)

        else:
            # Working scenario - keep everything invested
            portfolio = user_input['financial']['portfolio']

            results = []
            for window in windows:
                final = self._simulate_portfolio_working(
                    portfolio,
                    window['returns'],
                    user_input['financial']['income'],
                    user_input['financial']['spending']
                )
                results.append(final)

        return {
            'name': 'Keep 100% Invested',
            'description': 'Keep mortgage, invest full amount',
            'success_rate': sum(1 for r in results if r >= 0) / len(results),
            'avg_outcome': mean(results),
            'median_outcome': median(results),
            'min_outcome': min(results),
            'max_outcome': max(results),
            'results': results
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

            old_mortgage_payment = calculate_annual_payment(
                user_input['mortgage']['balance'],
                user_input['mortgage']['rate'],
                user_input['mortgage']['years']
            )

            if user_input['financial']['spending_includes_mortgage']:
                new_spending = user_input['financial']['spending'] - (old_mortgage_payment - new_mortgage_payment)
            else:
                new_spending = user_input['financial']['spending'] + new_mortgage_payment

            new_portfolio = user_input['financial']['portfolio'] - payoff_amount

            results = []
            for window in windows:
                final = self._simulate_portfolio(
                    new_portfolio,
                    window['returns'],
                    new_spending
                )
                results.append(final)

        else:
            # Working scenario
            new_portfolio = user_input['financial']['portfolio'] - payoff_amount

            results = []
            for window in windows:
                final = self._simulate_portfolio_working(
                    new_portfolio,
                    window['returns'],
                    user_input['financial']['income'],
                    user_input['financial']['spending']
                )
                results.append(final)

        return {
            'name': f'Pay Off {int(pct*100)}%',
            'description': f'Pay off ${payoff_amount:,.0f} today',
            'success_rate': sum(1 for r in results if r >= 0) / len(results),
            'avg_outcome': mean(results),
            'median_outcome': median(results),
            'min_outcome': min(results),
            'max_outcome': max(results),
            'results': results
        }

    def _simulate_portfolio(self, initial: float, returns: List[float], annual_withdrawal: float) -> float:
        """Simulate portfolio with withdrawals (retired)."""
        balance = initial

        for stock_return in returns:
            balance -= annual_withdrawal
            balance *= (1 + stock_return / 100.0)

        return balance

    def _simulate_portfolio_working(self, initial: float, returns: List[float],
                                     income: float, spending: float) -> float:
        """Simulate portfolio while working."""
        balance = initial

        for stock_return in returns:
            # Add savings (income - spending)
            balance += (income - spending)
            # Apply return
            balance *= (1 + stock_return / 100.0)

        return balance
```

#### 4. risk_agent.py (basic version)

```python
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

            if withdrawal_rate >= 4.0:
                risks.append({
                    'type': 'withdrawal_rate',
                    'severity': 'medium' if withdrawal_rate < 4.5 else 'high',
                    'title': 'Withdrawal rate at threshold',
                    'description': f'Your {withdrawal_rate:.1f}% withdrawal rate is at or above the safe 4% limit.',
                    'mitigation': [
                        'Consider keeping 1-year cash reserve',
                        'Be prepared to reduce spending in bad years'
                    ]
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
```

#### 5. orchestrator.py

```python
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

        context = {"user_input": user_input}

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
        yield self.strategy_agent.report_progress("working", "Testing Strategy 3: Pay off 50%")
        strategy_result = await self.strategy_agent.execute(context)
        context.update(strategy_result)
        yield self.strategy_agent.report_progress("complete", f"Tested {len(strategy_result['strategies'])} strategies")

        # Agent 3: Risk Agent
        yield self.risk_agent.report_progress("working", "Analyzing risk factors")
        risk_result = await self.risk_agent.execute(context)
        context.update(risk_result)
        yield self.risk_agent.report_progress("complete", f"Risk level: {risk_result['overall_level'].upper()}")

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
                "user_input": user_input
            }
        }
```

#### 6. API endpoints (backend/app.py updates)

```python
"""API endpoints for PayOffOrInvest."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
import asyncio

from backend.agents.orchestrator import AnalysisOrchestrator

app = FastAPI()

# In-memory storage for Phase 1 (use Redis in production)
analyses = {}


class MortgageInput(BaseModel):
    balance: float
    rate: float
    years: int


class FinancialInput(BaseModel):
    portfolio: Optional[float] = None
    income: Optional[float] = None
    spending: float
    spending_includes_mortgage: bool


class AnalysisRequest(BaseModel):
    employment_status: str  # "working" or "retired"
    mortgage: MortgageInput
    financial: FinancialInput


@app.post("/api/analyze")
async def create_analysis(request: AnalysisRequest):
    """Start a new analysis."""
    analysis_id = str(uuid.uuid4())

    # Store input
    analyses[analysis_id] = {
        "status": "processing",
        "input": request.dict(),
        "result": None
    }

    # Start background processing
    asyncio.create_task(run_analysis(analysis_id, request.dict()))

    return {
        "analysis_id": analysis_id,
        "status": "processing"
    }


async def run_analysis(analysis_id: str, user_input: Dict[str, Any]):
    """Run analysis in background."""
    orchestrator = AnalysisOrchestrator()

    result = None
    async for update in orchestrator.analyze(user_input):
        if update.get("agent") == "complete":
            result = update["result"]

    # Store result
    analyses[analysis_id]["status"] = "complete"
    analyses[analysis_id]["result"] = result


@app.get("/api/analysis/{analysis_id}/progress")
async def get_analysis_progress(analysis_id: str):
    """Stream analysis progress via SSE."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def event_generator():
        orchestrator = AnalysisOrchestrator()
        user_input = analyses[analysis_id]["input"]

        async for update in orchestrator.analyze(user_input):
            # Format as SSE
            yield f"data: {json.dumps(update)}\n\n"

            if update.get("agent") == "complete":
                # Store result
                analyses[analysis_id]["status"] = "complete"
                analyses[analysis_id]["result"] = update["result"]
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get completed analysis results."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analyses[analysis_id]

    if analysis["status"] != "complete":
        return {
            "status": "processing",
            "result": None
        }

    return {
        "status": "complete",
        "result": analysis["result"]
    }
```

---

### Frontend Implementation

#### Day 5: Landing Page

**File: `app/page.tsx`**

```tsx
export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Should You Pay Off Your Mortgage?
          </h1>

          <p className="text-xl text-gray-600 mb-8">
            Get a data-backed answer in 60 seconds using
            <br />
            100 years of actual market returns
          </p>

          {/* Value Props */}
          <div className="space-y-4 mb-12">
            <div className="flex items-center justify-center gap-2 text-gray-700">
              <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Historical analysis across 71 time periods</span>
            </div>

            <div className="flex items-center justify-center gap-2 text-gray-700">
              <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Risk assessment for your specific situation</span>
            </div>

            <div className="flex items-center justify-center gap-2 text-gray-700">
              <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Multiple strategy comparison</span>
            </div>
          </div>

          {/* CTA Button */}
          <a
            href="/calculator"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg text-lg transition-colors"
          >
            Start Analysis →
          </a>
        </div>

        {/* Social Proof */}
        <div className="text-center text-gray-600">
          <p>Used by 10,000+ people</p>
          <div className="flex justify-center items-center gap-1 mt-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
            <span className="ml-2">4.9/5</span>
          </div>
        </div>
      </div>
    </main>
  );
}
```

---

## Testing Plan

### Unit Tests
- Test each agent independently
- Test simulation functions with known inputs
- Test API endpoints

### Integration Tests
- Test full flow: Form → Analysis → Results
- Test SSE streaming
- Test caching

### Manual Testing
- Test both working and retired scenarios
- Test edge cases (high withdrawal rate, etc.)
- Test error handling

---

## Success Criteria

- [ ] Backend agents working correctly
- [ ] API endpoints functional
- [ ] SSE streaming working
- [ ] Landing page looks good
- [ ] Form validates properly
- [ ] Agent loading shows progress
- [ ] Results page displays recommendation
- [ ] End-to-end flow works for both working and retired

---

## Next Steps After Phase 1

1. Review and test
2. Fix any bugs
3. Move to Phase 2: Strategy comparison + Risk analysis pages

---

**Status:** Ready to implement

**Start Date:** TBD

**Target Completion:** 2 weeks
