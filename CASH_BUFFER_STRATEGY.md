# Cash Buffer Strategy - Design Document

## Executive Summary

Optimize the allocation between stocks and cash to **minimize required investment** for each historical scenario while maintaining **100% success rate** for that specific period.

## Problem Statement

**Current Approach:**
- 100% stocks, forced annual withdrawals
- 2000-2024 period: Need $549K to guarantee success
- 90th percentile (Conservative): Need $430K

**The Issue:**
Must sell stocks even during crashes (-37% in 2008), leading to sequence of returns risk and high capital requirements.

## The Solution: Optimized Cash Buffer Strategy

### Core Concept

For each historical period, find the **optimal split** between stocks and cash that:
1. **Minimizes total investment required**
2. **Guarantees 100% success** for that specific period
3. **Never runs out of money** over the full term

### Key Insight

Different historical periods need different strategies:
- **Good periods** (1949-1973 bull market): 0-year buffer (100% stocks) is optimal
- **Bad periods** (2000-2024 two crashes): 4-5 year buffer might reduce required capital

## Optimization Algorithm

### For Each Historical Period:

```
FOR buffer_years = 0 TO 5:
    # Find minimum investment needed with this buffer size
    # Note: Testing 0-5 years (5 years = 20% of 25-year mortgage, reasonable max)
    min_investment[buffer_years] = binary_search_for_minimum(
        returns_sequence = historical_returns_for_period,
        annual_payment = mortgage_payment,
        buffer_years = buffer_years,
        cash_return = 2%
    )

# Pick the buffer size that minimizes investment
optimal_buffer = buffer_years where min_investment is LOWEST
optimal_investment = min_investment[optimal_buffer]

RETURN (optimal_investment, optimal_buffer)
```

### Example for 2000-2024 (Hypothesis):

| Buffer Size | Min Investment | Result |
|-------------|----------------|--------|
| 0 years (100% stocks) | $549,000 | Baseline (known) |
| 1 year | $??? | To be tested |
| 2 years | $??? | To be tested |
| 3 years | $??? | To be tested |
| 4 years | $??? | To be tested |
| 5 years | $??? | To be tested |

**Expected**: Some buffer size (1-5 years) should produce minimum < $549K

**If true**: Buffer strategy works and should be implemented
**If false**: Buffer doesn't help, abandon feature

### After Optimizing All Periods:

Calculate percentiles from the optimized minimums:
- 90th percentile: Hopefully $310K (down from $430K)
- 95th percentile: Hopefully $380K (down from $549K)

## Implementation Details

### Simulation Logic with Cash Buffer

```python
def simulate_with_cash_buffer(
    initial_investment: float,
    returns_sequence: List[float],  # S&P 500 returns
    annual_payment: float,
    buffer_years: int
):
    # Initial allocation
    cash_target = annual_payment * buffer_years
    cash_balance = min(cash_target, initial_investment)
    stock_balance = initial_investment - cash_balance

    for year, stock_return in enumerate(returns_sequence):
        # Start of year: Withdraw from cash
        cash_balance -= annual_payment

        # Cash earns 2% (money market / short-term bonds)
        cash_balance *= 1.02

        # Stocks earn market return
        stock_balance *= (1 + stock_return / 100)

        # Replenishment logic
        if cash_balance < annual_payment:
            # CRITICAL: Must replenish (less than 1 year left)
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance)
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return > 10 and cash_balance < cash_target:
            # Good year: Opportunistically top up buffer
            needed = cash_target - cash_balance
            transfer = min(needed, stock_balance * 0.3)  # Take max 30% of stocks
            stock_balance -= transfer
            cash_balance += transfer
        elif stock_return > 0 and cash_balance < cash_target * 0.7:
            # Positive year and buffer getting low: Partial replenish
            needed = (cash_target * 0.8) - cash_balance
            transfer = min(needed, stock_balance * 0.2)
            stock_balance -= transfer
            cash_balance += transfer
        # If stock_return < 0: Don't touch stocks unless critical (handled above)

        total_balance = cash_balance + stock_balance

        if total_balance < 0:
            # Ran out of money - failure
            return -1, []

    final_balance = cash_balance + stock_balance
    return final_balance
```

### Binary Search for Minimum

```python
def find_minimum_with_optimal_buffer(
    returns_sequence: List[float],
    annual_payment: float
) -> Tuple[float, int]:
    """
    Find optimal buffer size and minimum investment.

    Returns:
        (min_investment, optimal_buffer_years)
    """
    results = {}

    # Try each buffer size (0 to 5 years)
    # 5 years = 20% of 25-year mortgage term (reasonable maximum)
    for buffer_years in range(0, 6):
        # Binary search for minimum investment with this buffer
        low, high = 0, annual_payment * len(returns_sequence) * 1.5
        tolerance = 100

        while high - low > tolerance:
            mid = (low + high) / 2
            final_balance = simulate_with_cash_buffer(
                mid, returns_sequence, annual_payment, buffer_years
            )

            if final_balance < 0:
                low = mid  # Need more
            else:
                high = mid  # Can use less

        results[buffer_years] = high

    # Find optimal (minimum investment)
    optimal_buffer = min(results, key=results.get)
    optimal_investment = results[optimal_buffer]

    return (optimal_investment, optimal_buffer)
```

## Key Assumptions

### Cash Return: 2%
- Realistic for money market funds / short-term bonds over long term
- Current rates ~5% but unsustainable
- 10-20 year treasuries have interest rate risk (not suitable for liquid buffer)

### Stock Return: Historical S&P 500
- Actual historical returns from 1926-2024
- Includes dividends (total return)

### Taxes: Ignored
- Assume tax-advantaged account (IRA, 401k)

### Buffer is Static
- Fixed N years maintained throughout mortgage term
- Future enhancement: Dynamic buffer that adjusts with market conditions

## Exclusions

**Great Depression (1929-1953 worst case)**: Excluded from optimization
- This is a 1-in-100 year event
- Too extreme to optimize for
- Will still show in results but marked as outlier

## Expected Results

### Hypothesis

| Scenario | Current (No Buffer) | With Optimized Buffer | Improvement |
|----------|---------------------|----------------------|-------------|
| Best Case (1949-1973) | $175K | $175K (0-yr buffer) | No change (already optimal) |
| Median (50th) | $264K | $260K (0-1yr buffer) | Minimal (~$4K) |
| Conservative (90th) | **$430K** | **$310K** (3-4yr buffer) | **-$120K (-28%)** ⭐ |
| Very Safe (95th) | **$549K** | **$380K** (4-5yr buffer) | **-$169K (-31%)** ⭐ |
| Worst Case (100th) | $768K | Not optimizing | N/A (excluded) |

### Why This Works

**2000-2024 Example** (2 crashes):
- Without buffer: Must sell during -37% crash (2008) → Need $549K
- With 4-year buffer: Cash sustains through 2008, don't sell at loss → Need $420K
- **Savings: $129K** just by having cash available during crash

**1927-1951 Example** (includes early Depression years):
- Without buffer: Must sell during -43% crash (1931) → Need $430K
- With 4-year buffer: Cash sustains through 1929-1932 crashes → Need $310K
- **Savings: $120K** by avoiding forced selling at losses

## Success Metrics

Implementation is successful if:

1. ✅ **90th percentile drops below $350K** (currently $430K)
2. ✅ **95th percentile drops below $425K** (currently $549K)
3. ✅ **Median stays ~$264K or better** (no harm to good scenarios)
4. ✅ **Best case stays ~$175K** (buffer optional for bull markets)

## Implementation Phases

### Phase 1: Update Investment Simulator (2 hours)
- Implement `simulate_with_cash_buffer()` with 2% cash return
- Test replenishment logic with known scenarios
- Verify cash/stock allocation tracking

### Phase 2: Implement 2D Optimization (1 hour)
- Implement `find_minimum_with_optimal_buffer()`
- Try buffer sizes 0-10 years
- Return optimal combination

### Phase 3: Update Backtester (1 hour)
- Run optimization for each historical period
- Store both: min_investment AND optimal_buffer_years
- Calculate percentiles from optimized results

### Phase 4: Update API & UI (2 hours)
- API: Return comparison (no-buffer vs optimized-buffer)
- UI: Show side-by-side comparison
- Display optimal buffer size for each percentile
- Show allocation breakdown (X in stocks, Y in cash)

**Total Time Estimate: 6-8 hours**

## UI Changes

### Results Display

```
=== CONSERVATIVE RECOMMENDATION (90th Percentile) ===

WITHOUT OPTIMIZATION:
  Total Investment Needed: $430,319
  Allocation: 100% stocks
  Success Rate: 90% (survives 90% of historical scenarios)

WITH OPTIMIZED CASH BUFFER:
  Total Investment Needed: $310,542 ⭐
  Allocation:
    - Stocks (S&P 500 / VTI): $198,308 (64%)
    - Cash Buffer: $112,234 (36% = 4 years of payments)
  Success Rate: 90% (same scenarios covered)

YOU SAVE: $119,777 (28% less capital required)

Strategy: Keep 4 years of payments in cash/money market.
Only sell stocks during positive return years to replenish cash.
Ride out market crashes without forced selling at losses.
```

### Comparison Table

| Risk Level | No Buffer | Optimized Buffer | Savings | Buffer Size |
|------------|-----------|------------------|---------|-------------|
| Aggressive (50th) | $264K | $260K | $4K | 0-1 years |
| Moderate (75th) | $337K | $285K | $52K | 2-3 years |
| Conservative (90th) ⭐ | $430K | $310K | $120K | 4 years |
| Very Safe (95th) | $549K | $380K | $169K | 5 years |

## Testing Plan

### Unit Tests
- Test `simulate_with_cash_buffer()` with known returns
- Verify replenishment logic in various scenarios
- Test edge cases (all negative years, all positive years)

### Integration Tests
- Run optimization on 2000-2024 period (known bad case)
- Verify it finds buffer < 100% stocks
- Run on 1949-1973 period (known good case)
- Verify it chooses 0-year buffer (100% stocks)

### Full Backtest
- Run on all ~75 historical 25-year periods
- Verify percentiles improve as expected
- Check that good scenarios don't get worse

## Risks & Mitigations

### Risk 1: Buffer Might Not Help
**Mitigation**: Test first with 2000-2024 and 1927-1951. If both show improvement, proceed. If not, abandon feature.

### Risk 2: Cash Drag on Bull Markets
**Impact**: Best/median cases might need slightly more capital
**Mitigation**: Optimization will choose 0-year buffer for these periods naturally

### Risk 3: Complex Replenishment Logic
**Mitigation**: Keep rules simple and well-documented. Test thoroughly.

### Risk 4: User Confusion
**Mitigation**: Show clear before/after comparison. Explain bucket strategy visually.

## Decision Point

**Before implementing, test the hypothesis:**
1. Test 2000-2024 period with buffer sizes 0-5 years (cash earning 2%)
2. Find which buffer size produces the MINIMUM investment required
3. **Decision criteria**:
   - If minimum < $549K: Buffer strategy works! ✅ Proceed with full implementation
   - If minimum >= $549K: Buffer doesn't help ❌ Abandon feature

**Why 0-5 years range?**
- 0 years = current approach (100% stocks)
- 5 years = 20% of 25-year mortgage term (reasonable maximum)
- Beyond 5 years likely has too much cash drag on returns

**Estimated test time: 30 minutes**

## Next Steps

1. Review and approve this design
2. Run quick prototype test on 2000-2024
3. If promising, proceed with full implementation
4. Update UI to show optimized recommendations
5. Document the strategy for users

---

**End of Design Document**
