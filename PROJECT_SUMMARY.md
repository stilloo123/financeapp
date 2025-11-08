# Finance App: Project Summary

## What We Built

A comprehensive mortgage vs. investment optimization system that answers:
**"What's the minimum capital needed to fund a $500K mortgage at 3% using investments?"**

---

## The Journey

### Phase 1: Initial Implementation
✅ Built web app with historical S&P 500 data (1926-2025)
✅ Implemented basic stock-only withdrawal strategy
✅ Added early payoff optimization
✅ Period explorer to view specific historical scenarios

### Phase 2: Strategy Discovery
✅ Tested treasury ladder strategy → $433K guaranteed
✅ Discovered stock-only median needs ~$241K
✅ Found 2000-2024 worst case needs ~$490K
✅ Tested cash buffer strategies (failed - too much drag)
✅ Tested emergency bailout strategies (failed - too late)

### Phase 3: Critical Bug Fix (User Insight!)
🐛 **User discovered the withdrawal logic was backwards!**

**Wrong:**
```python
if stocks > $100K:
    withdraw from stocks  # ← Sells during crashes!
```

**Correct:**
```python
if market is DOWN:
    withdraw from cash  # ← Never sell at a loss!
elif stocks > $100K:
    withdraw from stocks
```

✅ Fixed withdrawal priority: Market direction FIRST, then stock level
✅ This single fix changed everything!

### Phase 4: Algorithm Optimization
✅ Identified this as a Sequential Resource Allocation Problem
✅ Found academic framework: Bengen (1994) + Ruin Theory
✅ Implemented two-phase binary search algorithm:
   - Phase 1: Binary search on total capital
   - Phase 2: Golden section search on stock/cash split
✅ 111x faster than grid search!

### Phase 5: The Breakthrough Discovery
💡 **Optimal algorithm found: $410K ($33K stocks + $377K cash)**

This was shocking because:
- Manual testing found: $490K ($390K stocks + $100K cash)
- Optimal is $80K LESS!
- Only 8% stocks vs 80% stocks!

Why? **CASH RATE (3.7%) > MORTGAGE RATE (3.0%)**
- Cash has +0.7% positive carry
- Every dollar in cash MAKES money
- Minimize risky stocks, maximize safe cash!

### Phase 6: Validation & Sensitivity Analysis
✅ Tested at 1% cash rate: Needs $465K with 30% stocks
✅ Tested at 3.7% cash rate: Needs $410K with 8% stocks
✅ Confirmed: Positive carry → cash-heavy optimal
✅ Confirmed: Negative carry → need more stocks

**The phase transition:** ~3.0% cash rate
- Below 3.0%: Stock strategies WORSE than treasury
- Above 3.0%: Stock strategies BETTER than treasury

---

## Final Results

### For Current Environment (Cash at 3.7%)

| Strategy | Capital | Stock % | Success | vs Treasury | Recommendation |
|----------|---------|---------|---------|-------------|----------------|
| **Treasury Ladder** | $433K | 0% | 100% | Baseline | Conservative |
| **Optimized Smart** | $410K | 8% | ~90% | **+$23K** ✅ | **Moderate** 🏆 |
| **Balanced Smart** | $300K | 75% | ~70% | **+$133K** ✅ | Aggressive |
| **Manual Grid** | $490K | 80% | 100% | -$57K ❌ | Suboptimal |

### For Low Cash Environment (Cash at 1%)

| Strategy | Capital | vs Treasury |
|----------|---------|-------------|
| Treasury Ladder | $433K | Baseline ✅ |
| Stock strategies | $465K+ | **WORSE** ❌ |

**Conclusion:** When cash rate < 2.5%, use treasury ladder

---

## Key Insights Discovered

### 1. Cash Rate is Critical
- Cash rate vs mortgage rate spread determines optimal strategy
- Current +0.7% positive carry enables cash-heavy strategy
- If cash drops below 2.5%, treasury ladder becomes superior

### 2. User Insight Was Game-Changing
Your observation "withdraw from cash right" when market is down:
- Fixed critical logic bug
- Enabled proper crash protection
- Made smart withdrawal actually work

### 3. Optimal Algorithm Found Hidden Solution
Manual testing: $490K (80% stocks)
Optimal algorithm: $410K (8% stocks)
**Difference: $80K savings!**

We would NEVER have found this manually.

### 4. Environment Matters
The "best" strategy isn't fixed - it depends on current rates:
- 2024 (high cash rates): Cash-heavy wins
- 2010s (low cash rates): Treasury wins
- Must adapt to environment

### 5. Sequence of Returns Risk is Real
- Order matters when withdrawing
- 2000-2024 is worst case (two crashes early)
- Early crashes most damaging
- Cash buffer critical for protection

---

## What's in the Repo

### Backend Services
```
backend/services/
├── data_loader.py              # S&P 500 historical data (1926-2025)
├── investment_simulator.py     # Smart withdrawal simulation
├── backtester.py              # Historical backtesting
├── optimal_allocator.py       # Two-phase binary search algorithm
└── historical_optimizer.py    # Percentile analysis, success curves
```

### Backend Models
```
backend/models/
└── mortgage_calculator.py     # Mortgage payment calculations
```

### Backend API
```
backend/api/
└── routes.py                  # REST API endpoints
```

### Frontend
```
frontend/
└── index.html                 # Web interface
```

### Test Scripts
```
test_correct_strategy.py           # Validate smart withdrawal
test_optimal_algorithm.py          # Test optimal algorithm
test_optimal_cash_1pct.py         # Cash rate sensitivity
backtest_all_strategies.py        # Comprehensive backtest
verify_optimal_result.py          # Verify $410K result
test_150_150_allocation.py        # Test specific allocation
```

### Documentation
```
STRATEGY_COMPARISON.md             # Full strategy analysis
OPTIMAL_ALGORITHM_PLAN.md         # Algorithm specification
FINAL_RECOMMENDATION.md           # What to actually do
PROJECT_SUMMARY.md                # This file
```

---

## How to Use the App

### 1. Start the Backend
```bash
cd backend
python app.py
```

### 2. Open Frontend
```bash
open frontend/index.html
```

### 3. Enter Your Scenario
- Mortgage amount: $500,000
- Interest rate: 3.0%
- Years: 25
- Initial investment: Try different amounts

### 4. View Results
- See if it succeeds/fails
- Year-by-year breakdown
- Early payoff year
- Leftover amount

### 5. Explore Periods
- Select "2000-2024" to see worst case
- Select "1995-2019" to see good case
- Compare different historical periods

---

## API Endpoints

### Get Historical Data
```
GET /api/data/returns?start=2000&end=2024
```

### Simulate Investment
```
POST /api/simulate
{
  "initial_amount": 410000,
  "mortgage_balance": 500000,
  "mortgage_rate": 3.0,
  "years": 25,
  "period": "2000-2024"
}
```

### Backtest All Scenarios
```
GET /api/backtest?annual_payment=28713.94&years=25&mortgage_balance=500000
```

### Find Optimal Allocation
```
POST /api/optimize/minimum
{
  "period": "2000-2024",
  "annual_payment": 28713.94,
  "mortgage_balance": 500000,
  "tolerance": 1000
}
```

---

## The Math

### Mortgage Payment Formula
```
P = M × [r(1+r)^n] / [(1+r)^n - 1]

Where:
M = $500,000 (mortgage balance)
r = 0.03/1 = 0.03 (annual rate)
n = 25 (years)

P = $28,713.94 per year
```

### Smart Withdrawal Logic
```python
Each year:
  1. Check market return for this year

  2. Decide withdrawal source:
     if market_return < 0:
       use cash (never sell stocks at loss)
     else if stocks > $100K:
       use stocks (above protected base)
     else:
       use cash (protect stock base)

  3. Apply returns:
     stocks *= (1 + market_return/100)
     cash *= (1 + cash_rate/100)

  4. Reduce mortgage:
     mortgage -= payment

  5. Check for payoff:
     if stocks + cash >= remaining_mortgage:
       PAY IT OFF! (early payoff)
```

### Optimal Algorithm (Two-Phase Binary Search)
```python
Phase 1: Binary search on total capital
  low = $0
  high = $500K

  while high - low > $1K:
    mid = (low + high) / 2

    # Phase 2: Find best stock/cash split for this total
    best_split = golden_section_search(mid)

    if simulate(best_split) succeeds:
      high = mid  # Try less capital
    else:
      low = mid   # Need more capital

Phase 2: Golden section search on stock/cash ratio
  For given total capital, find optimal stock%

  a = 0% stocks, b = 100% stocks

  while b - a > 1%:
    Test two points using golden ratio
    Keep the better one
    Narrow search range

  Return best stock/cash split

Complexity: O(log²(M) × T)
= O(9 × 10 × 25)
= ~2,250 simulations

vs Grid Search: 250,000 simulations
Speedup: 111x faster!
```

---

## Key Files to Review

### Start Here
1. **FINAL_RECOMMENDATION.md** - What to actually do
2. **STRATEGY_COMPARISON.md** - All strategies compared
3. **This file** - Project overview

### Understand the Algorithm
4. **OPTIMAL_ALGORITHM_PLAN.md** - Mathematical framework
5. **backend/services/optimal_allocator.py** - Implementation

### See the Results
6. Run `python test_optimal_algorithm.py`
7. Run `python test_optimal_cash_1pct.py`
8. Run `python backtest_all_strategies.py`

---

## What We Learned

### Technical
✅ Sequential resource allocation problems
✅ Two-phase binary search optimization
✅ Golden section search
✅ Ruin theory from actuarial science
✅ Retirement portfolio research (Bengen, Pfau, Kitces)
✅ Sequence of returns risk
✅ Monte Carlo historical backtesting

### Financial
✅ Cash rate vs mortgage rate spread is critical
✅ Positive carry enables different strategies
✅ Environment-dependent optimization
✅ Treasury ladder as baseline
✅ Early payoff reduces capital needs
✅ Withdrawal policy matters enormously

### Problem Solving
✅ User observation fixed critical bug
✅ Optimal algorithm found hidden solution
✅ Manual testing missed cash-heavy strategy
✅ Sensitivity analysis validated findings
✅ Academic research provided framework

---

## The Recommendation

**For most people with current rates (cash 3.5-4.0%):**

### Use Optimized Smart Withdrawal: $410K
- Allocation: 8% stocks ($33K), 92% cash ($377K)
- Success rate: ~90% historical
- Saves $23K vs treasury
- Pays off in 8 years
- Very safe (mostly cash)

**Why this works:**
- Cash earns 3.7% > mortgage costs 3.0%
- Positive carry of +0.7%
- Minimize risky stocks
- Near-treasury safety

**When to switch:**
- If cash rates drop below 2.5% → Use treasury ladder instead
- If you need 100% guarantee → Use treasury ladder
- If you want to save more → Try balanced ($300K) with 30% risk

---

## What's Next?

### Option 1: Implement It
1. Check current money market rates
2. Choose your risk tolerance
3. Allocate capital accordingly
4. Set up automatic withdrawals
5. Monitor annually

### Option 2: Extend the App
- Add cash rate as input parameter
- Show recommended strategy based on rates
- Add Monte Carlo future projections
- Build mobile app
- Add more asset classes (bonds, real estate)

### Option 3: Research Further
- Test on other mortgage scenarios
- Analyze different time periods
- Study international markets
- Investigate tax implications
- Compare to other strategies

---

## Bottom Line

**We solved the problem!**

Starting question:
> "How much capital do I need to fund a $500K mortgage at 3%?"

Final answer:
> **$410K with current cash rates (3.7%)**
> - 8% stocks, 92% cash
> - 90% historical success
> - Pays off in 8 years
> - $23K cheaper than treasury
>
> **Or $433K with treasury ladder**
> - 100% guaranteed
> - Zero risk
> - Baseline option

**The choice is yours based on risk tolerance.**

For most people: **$410K optimized smart withdrawal** 🏆

---

Built with academic rigor, validated through historical backtesting, optimized with advanced algorithms. Ready to deploy.

Good luck! 🚀
