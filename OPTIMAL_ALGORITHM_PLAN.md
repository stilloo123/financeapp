# Optimal Mortgage Funding Problem: Mathematical Framework & Algorithm

## Problem Statement

### Formal Definition

**Given:**
- Mortgage balance: M = $500,000
- Mortgage rate: r_m = 3.0%
- Term: T = 25 years
- Annual payment: P = $28,713.94
- Historical returns sequence: R = {r₁, r₂, ..., r_T}
- Cash return rate: r_c = 3.7% (constant)
- Stock return rates: r_s(t) = R[t] (time-varying)

**Find:**
Minimum initial capital allocation (S₀, C₀) such that:
1. **Survival constraint**: S_t + C_t ≥ 0 for all t ∈ [1, T]
2. **Early payoff objective**: Minimize time τ where S_τ + C_τ ≥ M_remaining(τ)
3. **Capital minimization**: Minimize S₀ + C₀

**State Evolution:**
```
Each year t:
  1. Withdrawal decision: w_s(t) + w_c(t) = P
  2. Balance update:
     S_{t+1} = (S_t - w_s(t)) × (1 + r_s(t))
     C_{t+1} = (C_t - w_c(t)) × (1 + r_c)
  3. Mortgage: M_t = M_{t-1} - P
```

**Withdrawal Policy π (Smart Withdrawal Strategy):**
```python
if r_s(t) < 0:  # Market down
    w_c(t) = min(P, C_t)
    w_s(t) = P - w_c(t)
elif S_t > B:  # Market up, stocks above base B=$100K
    w_s(t) = min(P, S_t - B)
    w_c(t) = P - w_s(t)
else:  # Market up, stocks below base
    w_c(t) = min(P, C_t)
    w_s(t) = P - w_c(t)
```

---

## Academic Framework

### 1. Retirement Portfolio Research Framework

This problem is a **reverse annuity problem** from retirement planning literature:

#### **William Bengen (1994)** - "Determining Withdrawal Rates Using Historical Data"
- Introduced the **4% rule** for retirement
- Key concept: **Sequence of returns risk** - order matters when withdrawing
- Method: Historical backtesting across rolling periods
- **Our adaptation**: Fixed withdrawal ($28,714/year) instead of percentage

#### **Wade Pfau & Michael Kitces (2014)** - "Reducing Retirement Risk"
- **Rising equity glide paths** - adjust stock/bond allocation over time
- **Dynamic withdrawal strategies** - adjust based on market performance
- **Our adaptation**: Dynamic source selection (stocks vs. cash) based on market direction

#### **Guyton-Klinger Decision Rules (2006)**
- Conditional withdrawal adjustments based on portfolio performance
- **Prosperity rule**: Increase withdrawals after good years
- **Capital preservation rule**: Decrease during bad markets
- **Our adaptation**: Never sell stocks in down markets (capital preservation)

### 2. Actuarial Ruin Theory Framework

From insurance mathematics (Lundberg 1903, Cramér 1930):

#### **Probability of Ruin**
```
ψ(u) = P(min{S_t + C_t} < 0 | S₀ + C₀ = u)
```
Where:
- u = initial capital
- Goal: Find minimum u such that ψ(u) ≤ ε (acceptable failure rate)

#### **Adjustment Coefficient**
For continuous-time ruin theory:
```
R = sup{r : E[e^{rX}] ≤ 1}
```
Where X = claim distribution (our withdrawals adjusted for returns)

**Our discrete-time analog:**
- Claims = annual payments P
- Premiums = investment returns (r_s(t) on stocks, r_c on cash)
- **Ruin** = S_t + C_t < 0

### 3. Asset-Liability Management (ALM)

From pension fund management:

#### **Immunization Theory (Redington 1952)**
- Match asset duration to liability duration
- **Our version**: Match stock/cash allocation to withdrawal timeline

#### **Liability-Driven Investing**
- Minimize shortfall probability
- Optimize asset mix for known liabilities
- **Our approach**: Minimize initial capital for known mortgage liability

---

## Optimal Algorithm: Two-Phase Binary Search

### Algorithm Choice Rationale

**Why not other methods:**
1. **Dynamic Programming**: State space too large (continuous balances)
2. **Linear Programming**: Withdrawal rules are non-linear (if/else on market direction)
3. **Convex Optimization**: Objective not convex due to conditional logic
4. **MIP**: Would work but overkill for deterministic historical data
5. **Grid Search**: O(n²) too slow for fine granularity

**Why Two-Phase Binary Search:**
- **Phase 1**: Binary search on total capital → O(log M)
- **Phase 2**: Golden section search on stock/cash split → O(log M)
- **Total complexity**: O(log² M × T) where T=25
- **For M=$500K**: ~200 simulations vs. 250,000 for grid search

### Algorithm Specification

```python
def find_optimal_allocation(
    returns_sequence: List[float],
    annual_payment: float,
    mortgage_balance: float,
    protected_base: float = 100000,
    tolerance: float = 1000  # $1K precision
) -> Tuple[float, float, SimulationResult]:
    """
    Find minimum capital (stock, cash) allocation using two-phase optimization.

    Phase 1: Binary search on total capital
    Phase 2: Golden section search on stock/cash split

    Returns:
        (optimal_stock, optimal_cash, simulation_result)
    """

    def can_survive_with_capital(total_capital: float) -> Tuple[bool, float, float]:
        """
        Phase 2: For given total capital, find best stock/cash split.
        Uses golden section search on the split ratio.
        """
        phi = (1 + sqrt(5)) / 2  # Golden ratio

        def evaluate_split(stock_ratio: float) -> Tuple[bool, Dict]:
            stock = total_capital * stock_ratio
            cash = total_capital * (1 - stock_ratio)
            result = simulate_smart_withdrawal(
                stock, cash, returns_sequence, annual_payment,
                mortgage_balance, protected_base
            )
            return result

        # Golden section search on [0, 1]
        a, b = 0.0, 1.0
        c = b - (b - a) / phi
        d = a + (b - a) / phi

        best_result = None
        best_ratio = 0.5

        while abs(b - a) > 0.01:  # 1% precision on ratio
            result_c = evaluate_split(c)
            result_d = evaluate_split(d)

            # Prefer successful results, then earlier payoff
            if result_c['success'] and result_d['success']:
                if result_c['years_to_payoff'] <= result_d['years_to_payoff']:
                    b = d
                    best_result = result_c
                    best_ratio = c
                else:
                    a = c
                    best_result = result_d
                    best_ratio = d
            elif result_c['success']:
                b = d
                best_result = result_c
                best_ratio = c
            elif result_d['success']:
                a = c
                best_result = result_d
                best_ratio = d
            else:
                # Neither succeeds, try middle
                b = d

            c = b - (b - a) / phi
            d = a + (b - a) / phi

        if best_result and best_result['success']:
            stock = total_capital * best_ratio
            cash = total_capital * (1 - best_ratio)
            return True, stock, cash
        else:
            return False, 0, 0

    # Phase 1: Binary search on total capital
    low = 0
    high = mortgage_balance  # Can't need more than mortgage

    optimal_total = high
    optimal_stock = 0
    optimal_cash = 0

    while high - low > tolerance:
        mid = (low + high) / 2
        success, stock, cash = can_survive_with_capital(mid)

        if success:
            # Can succeed with this capital, try less
            optimal_total = mid
            optimal_stock = stock
            optimal_cash = cash
            high = mid
        else:
            # Need more capital
            low = mid

    # Final simulation with optimal allocation
    final_result = simulate_smart_withdrawal(
        optimal_stock, optimal_cash, returns_sequence,
        annual_payment, mortgage_balance, protected_base
    )

    return optimal_stock, optimal_cash, final_result
```

### Complexity Analysis

**Phase 1 (Binary search on total):**
- Range: [0, $500K]
- Precision: $1K
- Iterations: log₂(500,000 / 1,000) = log₂(500) ≈ 9

**Phase 2 (Golden section on split):**
- Range: [0, 1] (ratio)
- Precision: 0.01 (1%)
- Iterations: log_φ(1 / 0.01) = log_φ(100) ≈ 10

**Per simulation:**
- Time steps: 25 years
- Operations per step: O(1)

**Total complexity:**
```
O(Phase1_iterations × Phase2_iterations × T)
= O(9 × 10 × 25)
= O(2,250 simulations)
```

**vs. Grid Search:**
```
Grid: 100 total levels × 100 split levels × 25 years
= O(250,000 simulations)
```

**Speedup: 111x faster**

---

## Comparison: Grid Search vs. Optimal Algorithm

### Grid Search (Current Approach)
```python
# Test predefined allocations
test_cases = [
    (200000, 50000),
    (220000, 60000),
    ...
]

for stock, cash in test_cases:
    result = simulate(stock, cash)
    if result.success and stock + cash < best_total:
        best = (stock, cash)
```

**Pros:**
- Simple to implement
- Easy to understand
- Can visualize all results

**Cons:**
- Misses optimal points between grid lines
- Fixed granularity (e.g., $20K steps)
- O(n²) complexity for 2D grid
- May test far-from-optimal points

### Two-Phase Binary Search (Optimal)
```python
optimal_stock, optimal_cash, result = find_optimal_allocation(
    returns, annual_payment, mortgage_balance
)
```

**Pros:**
- Guaranteed to find minimum (within tolerance)
- Adaptive precision (zooms into optimal region)
- O(log² M) complexity
- Finds exact optimal stock/cash split

**Cons:**
- More complex implementation
- Less visibility into near-optimal solutions
- Requires more sophisticated search logic

---

## Implementation Plan

### Phase 1: Implement Core Algorithm

**File**: `backend/services/optimal_allocator.py`

```python
class OptimalAllocator:
    """
    Find minimum capital allocation using two-phase binary search.

    Based on:
    - Bengen (1994): Historical backtesting methodology
    - Pfau & Kitces (2014): Dynamic withdrawal strategies
    - Ruin theory: Minimum capital for survival guarantee
    """

    def __init__(self, returns_sequence, annual_payment, mortgage_balance):
        self.returns = returns_sequence
        self.payment = annual_payment
        self.mortgage = mortgage_balance

    def find_minimum(self, success_probability=1.0, tolerance=1000):
        """
        Find minimum allocation with target success probability.

        Args:
            success_probability: 0.0 to 1.0 (e.g., 0.9 for 90% success)
            tolerance: Dollar precision (default $1K)
        """
        pass

    def find_for_all_periods(self, start_year, end_year):
        """
        Run optimization across all rolling 25-year windows.
        Returns distribution of minimum capital needed.
        """
        pass
```

### Phase 2: Backtest Framework

**File**: `backend/services/historical_optimizer.py`

```python
class HistoricalOptimizer:
    """
    Comprehensive historical backtesting using optimal allocation.

    Produces:
    - Percentile analysis (10th, 50th, 90th percentile scenarios)
    - Success rate curves (capital vs. success probability)
    - Monte Carlo projections for future scenarios
    """

    def percentile_analysis(self, percentiles=[10, 25, 50, 75, 90]):
        """
        Find capital requirements at different historical percentiles.

        Example output:
        - 10th percentile (easiest): $240K
        - 50th percentile (median): $300K
        - 90th percentile (hardest): $380K
        - 95th percentile (2000-2024): $490K
        """
        pass

    def success_curve(self, capital_range):
        """
        Generate capital vs. success rate curve.

        Shows: "With $X capital, succeeds in Y% of historical periods"
        """
        pass
```

### Phase 3: API Integration

**Update**: `backend/api/routes.py`

Add endpoints:
- `/api/optimize/minimum` - Find minimum for specific period
- `/api/optimize/percentiles` - Get percentile requirements
- `/api/optimize/success-curve` - Get capital vs. success curve

### Phase 4: Frontend Visualization

**Update**: `frontend/index.html`

Add charts:
1. **Capital vs. Success Rate** curve
2. **Percentile Requirements** bar chart
3. **Optimal Stock/Cash Split** for selected capital

---

## Expected Results

### Validation Against Known Research

**4% Rule (Bengen 1994):**
- For $1M portfolio, safe withdrawal = $40K/year
- Our $500K mortgage needs $28.7K/year (5.7% rate)
- Higher than 4% → expect higher capital needs
- **Prediction**: Will need significantly more than just $500K in worst case

**Sequence of Returns Risk:**
- 2000-2024 worst case due to two crashes in first decade
- Early crashes are most damaging
- **Prediction**: 2000-2024 will require ~2x median capital

**Stock/Cash Optimization:**
- Too much cash → drag from lower returns
- Too little cash → forced to sell stocks in crashes
- **Prediction**: Optimal split ~70-80% stocks, 20-30% cash

### Performance Targets

**Accuracy:**
- Find minimum within $1,000 tolerance
- Optimal split within 1% ratio

**Speed:**
- Single period optimization: <1 second
- Full historical backtest (75 periods): <30 seconds
- Success curve generation: <60 seconds

**Reliability:**
- Guaranteed convergence (binary search always converges)
- Reproducible results (deterministic algorithm)

---

## References

### Academic Papers

1. **Bengen, W. P. (1994)**. "Determining Withdrawal Rates Using Historical Data."
   *Journal of Financial Planning*, 7(4), 171-180.

2. **Pfau, W. D., & Kitces, M. (2014)**. "Reducing Retirement Risk with a Rising Equity Glide Path."
   *Journal of Financial Planning*, 27(1), 38-45.

3. **Guyton, J. T., & Klinger, W. J. (2006)**. "Decision Rules and Maximum Initial Withdrawal Rates."
   *Journal of Financial Planning*, 19(3), 48-58.

4. **Lundberg, F. (1903)**. "Approximerad Framställning av Sannolikhetsfunktionen."
   *Almqvist & Wiksell*.

5. **Cramér, H. (1930)**. "On the Mathematical Theory of Risk."
   *Skandia Jubilee Volume*, Stockholm.

### Online Resources

- [Bogleheads Wiki - Safe Withdrawal Rates](https://www.bogleheads.org/wiki/Safe_withdrawal_rates)
- [Early Retirement Now - Safe Withdrawal Rate Series](https://earlyretirementnow.com/safe-withdrawal-rate-series/)
- [Portfolio Charts - Withdrawal Rates](https://portfoliocharts.com/portfolio/withdrawal-rates/)

---

## Next Steps

1. ✅ Problem formalized mathematically
2. ✅ Algorithm selected (Two-phase binary search)
3. ✅ Framework established (Bengen + Ruin Theory)
4. ⏳ Implement `OptimalAllocator` class
5. ⏳ Implement `HistoricalOptimizer` class
6. ⏳ Create API endpoints
7. ⏳ Build frontend visualizations
8. ⏳ Validate against known results
9. ⏳ Generate comprehensive report

**Estimated completion**: 2-3 hours of focused implementation
