# Mortgage vs. Investment Optimizer - Design Document

## Problem Statement

**Scenario:**
Instead of paying off a mortgage with a lump sum, what if you invested that money in an S&P 500 index fund (like VTI) and withdrew only what you need each year for mortgage payments?

**Goal:**
Build a web application that calculates the minimum initial investment $X needed to fund all mortgage payments over the remaining term, using historical S&P 500 returns to account for market volatility.

**Example (Default Values):**
- Mortgage: $500,000 at 3% APR, 25 years remaining
- Investment: VTI (S&P 500 index fund)
- Question: What's the minimum $X to invest that will cover all payments?

**Key Challenge:**
Unlike constant return assumptions (8% average), real markets have volatility. Sequence of returns matters critically - starting withdrawals during a downturn (2008: -37%) can deplete funds much faster than starting during a bull market (1995: +37%), even with identical average returns.

**Why This Matters:**
If the median required investment is $300K vs. paying off $500K directly, you potentially save $200K by leveraging market returns. But we need to account for risk via historical backtesting.

## Objectives

1. **Web Application**: Interactive interface for users to input their specific mortgage parameters
2. **Flexible Inputs**: All parameters configurable (mortgage amount, rate, years, etc.)
3. **Historical Backtesting**: Use 100 years of S&P 500 returns (1926-2025) for realistic scenarios
4. **Comprehensive Analysis**: Run simulations across all possible historical periods
5. **Visual Results**: Display results with interactive charts and graphs
6. **Risk Assessment**: Show worst-case, best-case, median, and percentile scenarios
7. **Actionable Insights**: Clear recommendations with confidence levels

## Data Requirements

### Historical Returns
- S&P 500 annual returns: 1926-2025 (100 years)
- Source: https://www.slickcharts.com/sp500/returns
- Data file: `data/sp500_returns.json`
- Format: JSON with year and return percentage
- Total return includes dividends (not just price appreciation)
- Note: 2025 returns are YTD as of October 31, 2025

### User Input Parameters (All Configurable)

**Mortgage Details:**
- **Current Mortgage Balance**: Dollar amount (e.g., $500,000)
  - Default: $500,000
  - Range: $50,000 - $5,000,000
  - Validation: Must be positive number

- **Mortgage Interest Rate**: Annual percentage rate (e.g., 3%)
  - Default: 3.0%
  - Range: 0.1% - 15%
  - Validation: Must be positive number

- **Years Remaining**: Years left on mortgage (e.g., 25)
  - Default: 25 years
  - Range: 1 - 30 years
  - Validation: Must be whole number between 1-30

**Optional Advanced Parameters:**
- **Risk Tolerance**: Which percentile to use for recommendation
  - Options: Conservative (90th), Moderate (75th), Aggressive (median)
  - Default: Conservative (90th percentile)

- **Starting Year** (Advanced): Simulate specific historical period
  - Default: "All scenarios" (backtests all periods)
  - Options: 1926-2000 (any year with 25+ years of data remaining)

**Calculated Values (Auto-computed):**
- Annual mortgage payment (using amortization formula)
- Total interest to be paid over remaining term
- Total amount to be paid (principal + interest)

## Algorithm Design

### Step 1: Calculate Mortgage Payment

Using standard amortization formula:
```
PMT = P × [r(1+r)^n] / [(1+r)^n - 1]

Where:
P = Principal ($500,000)
r = Annual interest rate (0.03)
n = Number of years (25)
```

Expected annual payment: ~$35,700

### Step 2: Historical Backtesting (Dynamic Runtime Computation)

**IMPORTANT**: Windows are computed **dynamically at runtime** based on user's `years_remaining` input, NOT pre-computed for all possible scenarios.

**Data Loading:**
```python
import json

# Load historical returns from data file (done once at startup)
with open('data/sp500_returns.json', 'r') as f:
    data = json.load(f)
    returns_data = data['returns']  # List of {year, return} dicts (1926-2024)
```

**Window Generation (Dynamic):**
Based on user's `years_remaining` input, generate rolling windows:

- User enters **5 years** → Generate ~95 windows (1926-1930, 1927-1931, ..., 2020-2024)
- User enters **10 years** → Generate ~90 windows (1926-1935, 1927-1936, ..., 2015-2024)
- User enters **25 years** → Generate ~75 windows (1926-1950, 1927-1951, ..., 2000-2024)
- User enters **30 years** → Generate ~70 windows (1926-1955, 1927-1956, ..., 1995-2024)

**Algorithm:**
```python
def generate_windows(all_returns, years_remaining):
    windows = []
    max_start_year = 2024 - years_remaining + 1  # 2024 is last complete year

    for start_year in range(1926, max_start_year + 1):
        end_year = start_year + years_remaining - 1
        window_returns = extract_returns(all_returns, start_year, end_year)
        windows.append({
            'period': f"{start_year}-{end_year}",
            'returns': window_returns
        })

    return windows
```

**For each window:**
1. Extract actual historical returns for those N years from the data file
2. Binary search to find minimum initial investment $X where:
   - Year 0: Balance = $X
   - Year i: Balance = Balance × (1 + return[i]/100) - annual_payment
   - Year N: Balance ≥ $0
3. Record the required $X for this sequence

**Example:**
- User has **25 years** remaining
- Window 2000-2024: Extract returns [-9.10%, -11.89%, -22.10%, 28.68%, ...]
- Run optimization to find minimum $X

**Performance:**
- 25-year mortgage: ~75 windows × 20 binary search iterations = ~1,500 simulations
- Expected runtime: **< 1 second** on modern hardware
- No need to pre-compute all possible year combinations

### Step 3: Optimization Function

```python
def simulate_investment(initial_amount, returns_sequence, annual_payment):
    """
    Simulates investment account balance over time with annual withdrawals.

    Args:
        initial_amount: Starting investment amount ($)
        returns_sequence: List of annual returns as percentages (e.g., [11.62, -37.00, 26.46])
        annual_payment: Amount withdrawn each year for mortgage payment ($)

    Returns:
        final_balance: Balance after all years
        year_by_year: List of yearly details
    """
    balance = initial_amount
    year_by_year = []

    for year, annual_return_pct in enumerate(returns_sequence):
        # Withdraw at beginning of year for mortgage payment
        balance -= annual_payment

        # Apply market return (convert percentage to decimal)
        balance *= (1 + annual_return_pct / 100)

        year_by_year.append({
            'year': year + 1,
            'return': annual_return_pct,
            'balance': balance
        })

    return balance, year_by_year

def find_minimum_investment(returns_sequence, annual_payment):
    # Binary search for minimum initial investment
    low, high = 0, 1_000_000
    tolerance = 100  # Within $100

    while high - low > tolerance:
        mid = (low + high) / 2
        final_balance, _ = simulate_investment(mid, returns_sequence, annual_payment)

        if final_balance < 0:
            low = mid  # Need more money
        else:
            high = mid  # Can use less money

    return high
```

### Step 4: Analysis and Reporting

**Metrics to Calculate:**
1. **Worst-case scenario**: Maximum $X needed (most adverse sequence)
2. **Best-case scenario**: Minimum $X needed (most favorable sequence)
3. **Median scenario**: 50th percentile
4. **Percentiles**: 25th, 75th, 90th, 95th
5. **Average required investment**

**For Key Scenarios (Worst/Best/Median):**
- Show year-by-year breakdown
- Identify which historical period it represents
- Chart balance over time
- Highlight major market events in that period

## API Design

### Backend Endpoints

**POST /api/calculate**
- **Description**: Main calculation endpoint
- **Input** (JSON):
  ```json
  {
    "mortgage_balance": 500000,
    "interest_rate": 3.0,
    "years_remaining": 25,
    "risk_tolerance": "conservative",  // "aggressive", "moderate", "conservative"
    "starting_year": null  // null = all scenarios, or specific year (1926-2000)
  }
  ```
- **Output** (JSON):
  ```json
  {
    "mortgage_details": {
      "balance": 500000,
      "rate": 3.0,
      "years": 25,
      "annual_payment": 35693,
      "total_to_pay": 892325
    },
    "scenarios_tested": 75,
    "results": {
      "best_case": {
        "investment_required": 280000,
        "period": "1975-1999",
        "year_by_year": [...]
      },
      "median": {
        "investment_required": 350000,
        "period": "1985-2009",
        "year_by_year": [...]
      },
      "percentile_75": {
        "investment_required": 380000,
        "period": "1970-1994",
        "year_by_year": [...]
      },
      "percentile_90": {
        "investment_required": 420000,
        "period": "1995-2019",
        "year_by_year": [...]
      },
      "percentile_95": {
        "investment_required": 450000,
        "period": "2000-2024",
        "year_by_year": [...]
      },
      "worst_case": {
        "investment_required": 520000,
        "period": "1929-1953",
        "year_by_year": [...]
      }
    },
    "recommendation": {
      "amount": 420000,
      "risk_level": "conservative",
      "success_rate": 0.90,
      "savings_vs_payoff": 80000
    },
    "all_scenarios": [
      {
        "period": "1926-1950",
        "investment_required": 480000
      },
      // ... 74 more scenarios
    ]
  }
  ```

**GET /api/health**
- **Description**: Health check endpoint
- **Output**: `{"status": "ok", "data_loaded": true}`

**GET /api/data-info**
- **Description**: Returns information about available historical data
- **Output**:
  ```json
  {
    "years_available": "1926-2025",
    "total_years": 100,
    "max_term_years": 75
  }
  ```

## Implementation Plan

### Phase 1: Backend Core (Python)
**Estimated Time: 3-4 hours**

- [x] Create S&P 500 returns data structure (1926-2025) - **COMPLETED**
  - File: `data/sp500_returns.json`
  - Contains 100 years of annual returns (1926-2025)

- [ ] Implement mortgage calculator module
  - Calculate annual payment using amortization formula
  - Validate against online calculators
  - Unit tests for edge cases

- [ ] Implement investment simulator
  - `simulate_investment()` function
  - `find_minimum_investment()` binary search
  - Test with known scenarios

- [ ] Implement backtesting engine
  - Load historical data from JSON (once at startup)
  - **Dynamically generate rolling N-year windows** based on user's years_remaining
  - Run optimization for each window (binary search)
  - Calculate statistics (percentiles, min, max, median)
  - Performance target: < 1 second for 30-year mortgage

### Phase 2: Backend API (Flask/FastAPI)
**Estimated Time: 2-3 hours**

- [ ] Set up Flask/FastAPI project structure
- [ ] Implement `/api/calculate` endpoint
  - Input validation
  - Error handling
  - Call backtesting engine
  - Format response

- [ ] Implement utility endpoints
  - `/api/health`
  - `/api/data-info`

- [ ] Add CORS support for frontend
- [ ] Add request logging
- [ ] Write API tests

### Phase 3: Frontend - Basic Structure
**Estimated Time: 3-4 hours**

- [ ] Create HTML structure
  - Input form page
  - Results dashboard page
  - Navigation/routing

- [ ] Implement CSS styling
  - Responsive grid layout
  - Form styling
  - Card components
  - Mobile-first approach

- [ ] Set up JavaScript modules
  - API client
  - Form validation
  - State management

### Phase 4: Frontend - Input Form & Validation
**Estimated Time: 2-3 hours**

- [ ] Build input form
  - Mortgage balance input
  - Interest rate input
  - Years remaining input
  - Advanced options (collapsible)

- [ ] Implement client-side validation
  - Number ranges
  - Format validation
  - Real-time feedback

- [ ] Add loading states
  - Spinner during calculation
  - Disable form during processing

### Phase 5: Frontend - Results Visualization
**Estimated Time: 4-5 hours**

- [ ] Build summary cards
  - Mortgage details card
  - Recommended investment card
  - Potential savings card
  - Scenarios tested card

- [ ] Implement Chart.js/Plotly visualizations
  - Distribution histogram
  - Box plot for risk analysis
  - Line chart for scenario comparison
  - Line chart for historical returns

- [ ] Create results table
  - Investment requirements by risk level
  - Sortable columns
  - Highlight selected risk tolerance

- [ ] Build expandable scenario details
  - Worst/best/median cases
  - Year-by-year breakdown tables
  - Key events annotations

### Phase 6: Additional Features
**Estimated Time: 2-3 hours**

- [ ] Export functionality
  - Download results as PDF
  - Export data as CSV

- [ ] Share functionality
  - Generate shareable URL with parameters
  - Copy link to clipboard

- [ ] "Adjust Parameters" button
  - Navigate back to form
  - Preserve previous inputs

### Phase 7: Testing & Polish
**Estimated Time: 2-3 hours**

- [ ] End-to-end testing
  - Test all input combinations
  - Test edge cases
  - Verify calculations manually

- [ ] Cross-browser testing
  - Chrome, Firefox, Safari, Edge

- [ ] Mobile responsiveness testing
  - Phone, tablet, desktop

- [ ] Performance optimization
  - Optimize calculations
  - Minimize API response time
  - Lazy load charts

- [ ] UI/UX polish
  - Animations/transitions
  - Error messages
  - Tooltips and help text

### Phase 8: Documentation & Deployment
**Estimated Time: 1-2 hours**

- [ ] Write README.md
  - How to run locally
  - Dependencies
  - API documentation

- [ ] Add inline code documentation
- [ ] Create user guide
- [ ] Set up local development instructions
- [ ] (Optional) Deploy to cloud platform

## Web Application Design

### Technology Stack

**Backend:**
- Python 3.10+
- Flask or FastAPI (RESTful API)
- JSON for data exchange

**Frontend:**
- HTML5 / CSS3
- JavaScript (Vanilla or React)
- Chart.js or Plotly.js for visualizations
- Responsive design (mobile-friendly)

**Deployment:**
- Local development server initially
- Option for cloud deployment (Heroku, Vercel, etc.)

### User Interface Layout

#### Page 1: Input Form

**Header:**
- Title: "Mortgage vs. Investment Optimizer"
- Subtitle: "Should you pay off your mortgage or invest in the market?"

**Input Section (Left Panel - 40% width):**

```
┌─────────────────────────────────────┐
│ YOUR MORTGAGE DETAILS               │
├─────────────────────────────────────┤
│                                     │
│ Current Mortgage Balance            │
│ [$500,000          ] 💵             │
│                                     │
│ Mortgage Interest Rate (APR)        │
│ [3.0               ] %              │
│                                     │
│ Years Remaining                     │
│ [25                ] years          │
│                                     │
│ ▼ Advanced Options (collapsible)    │
│   Risk Tolerance:                   │
│   ○ Conservative (90th percentile)  │
│   ○ Moderate (75th percentile)      │
│   ○ Aggressive (Median)             │
│                                     │
│   Starting Year:                    │
│   [All Scenarios   ▼]               │
│                                     │
│ [Calculate Results] 🚀              │
│                                     │
└─────────────────────────────────────┘
```

**Info Panel (Right Panel - 60% width):**
- Brief explanation of what the tool does
- Key assumptions listed
- Visual icon/graphic of mortgage vs. investment concept

#### Page 2: Results Dashboard (After clicking Calculate)

**Summary Cards (Top Section):**

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESULTS SUMMARY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 YOUR MORTGAGE               💰 RECOMMENDED INVESTMENT       │
│  ─────────────────              ───────────────────────         │
│  Balance:      $500,000         Initial Amount: $XXX,XXX        │
│  Rate:         3.0%             (90th Percentile)               │
│  Years:        25 years         Success Rate: 90%               │
│  Annual Pmt:   $35,693                                          │
│  Total Paid:   $892,325         💵 POTENTIAL SAVINGS            │
│                                 ───────────────────────         │
│  📈 SCENARIOS TESTED            Direct Payoff:  $500,000        │
│  ─────────────────              Investment:     $XXX,XXX        │
│  Historical Periods: 75         Savings:        $XXX,XXX        │
│  Years Analyzed: 1926-2024                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Charts Section (Middle Section):**

1. **Distribution Chart** (Bar Chart or Histogram)
   - X-axis: Required investment amount (bins)
   - Y-axis: Number of historical scenarios
   - Highlights: Median, 75th, 90th, 95th percentiles marked
   - Title: "Required Investment Across All Historical 25-Year Periods"

2. **Risk Analysis Chart** (Box Plot or Violin Plot)
   - Shows distribution: min, 25th, median, 75th, 90th, 95th, max
   - Color-coded risk zones (green = best case, red = worst case)
   - Title: "Investment Amount Distribution"

3. **Scenario Comparison** (Line Chart with 3 lines)
   - X-axis: Years (1-25)
   - Y-axis: Account balance ($)
   - Three lines:
     - Worst Case (red) - labeled with period
     - Median Case (blue) - labeled with period
     - Best Case (green) - labeled with period
   - Horizontal line at $0 (danger zone)
   - Title: "Account Balance Over Time - Key Scenarios"

4. **Historical Return Sequence** (Line Chart - for each scenario)
   - X-axis: Years (1-25)
   - Y-axis: S&P 500 Annual Return (%)
   - Shows actual returns for selected scenarios
   - Highlights negative return years in red
   - Title: "Market Returns During Period"

**Detailed Results Tables (Bottom Section):**

```
┌─────────────────────────────────────────────────────────────────┐
│ INVESTMENT REQUIREMENTS BY RISK LEVEL                           │
├─────────────────┬───────────────┬──────────────┬────────────────┤
│ Risk Level      │ Investment    │ Success Rate │ Historical     │
│                 │ Required      │              │ Period Example │
├─────────────────┼───────────────┼──────────────┼────────────────┤
│ Best Case       │ $XXX,XXX      │ N/A          │ 1975-1999      │
│ Aggressive      │ $XXX,XXX      │ 50%          │ 1985-2009      │
│ Moderate        │ $XXX,XXX      │ 75%          │ 1970-1994      │
│ Conservative    │ $XXX,XXX ⭐   │ 90%          │ 1995-2019      │
│ Very Safe       │ $XXX,XXX      │ 95%          │ 2000-2024      │
│ Worst Case      │ $XXX,XXX      │ 100%         │ 1929-1953      │
└─────────────────┴───────────────┴──────────────┴────────────────┘
⭐ = Your selected risk tolerance
```

**Expandable Scenario Details:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 WORST CASE SCENARIO DETAILS (Click to expand)                │
├─────────────────────────────────────────────────────────────────┤
│ Period: 1929-1953                                               │
│ Required Investment: $XXX,XXX                                   │
│                                                                 │
│ Year-by-Year Breakdown:                                         │
│ ┌──────┬─────────────┬─────────────┬─────────────┐            │
│ │ Year │ S&P Return  │ Withdrawal  │ Balance     │            │
│ ├──────┼─────────────┼─────────────┼─────────────┤            │
│ │ 1929 │ -8.42%     │ $35,693     │ $XXX,XXX    │            │
│ │ 1930 │ -24.90% ⚠️  │ $35,693     │ $XXX,XXX    │            │
│ │ 1931 │ -43.34% 🔴  │ $35,693     │ $XXX,XXX    │            │
│ │ ...  │ ...         │ ...         │ ...         │            │
│ └──────┴─────────────┴─────────────┴─────────────┘            │
│                                                                 │
│ Key Events: Great Depression (1929-1933)                        │
└─────────────────────────────────────────────────────────────────┘
```

Similar expandable sections for:
- Best Case Scenario
- Median Scenario
- Your Selected Risk Level Scenario

**Action Buttons (Bottom):**
- [Download Full Report (PDF)]
- [Export Data (CSV)]
- [Adjust Parameters] (goes back to input form)
- [Share Results] (generates shareable link)

### Responsive Design Considerations

**Mobile View:**
- Stack input form and info panel vertically
- Charts render as full-width, scrollable
- Tables convert to card layout
- Touch-friendly input controls

**Tablet View:**
- Side-by-side layout for some sections
- Charts resize appropriately

**Desktop View:**
- Full layout as described above
- Maximum width: 1400px (centered)

## Technical Considerations

### Computation Strategy

**Why Dynamic Runtime Computation?**
- **Flexibility**: Supports any year input (1-30 years) without pre-computing all scenarios
- **Performance**: < 1 second even for 30-year mortgages (~70 windows × 20 iterations = ~1,400 simulations)
- **Storage**: No need to store pre-computed results (would be ~2,500+ scenarios for all year combinations)
- **Maintainability**: Easy to update with new historical data (just add to JSON file)

**Optimization:**
- Load S&P 500 data once at server startup (not per request)
- Binary search converges quickly (~15-20 iterations per window)
- Simple simulation loop (no complex dependencies)

### Edge Cases
- What if account goes negative mid-period? (Binary search ensures final balance ≥ $0)
- Should we allow margin/borrowing? (No - account can't go negative)
- Tax implications (ignored for now, assume tax-advantaged account like IRA)
- Inflation adjustment (Phase 2 enhancement)
- 2025 partial year data (exclude from windows ending in 2025)

### Assumptions
1. Annual withdrawals (simplified from monthly for now)
2. Withdrawals happen at beginning of year, returns apply to remaining balance
3. No additional contributions after initial investment
4. No taxes or transaction fees
5. Perfect market tracking (no fund fees beyond VTI's 0.03% expense ratio)
6. Historical returns include dividends (total return, not just price appreciation)

### Future Enhancements

**HIGH PRIORITY - Cash Buffer Strategy (Bucket Strategy):**

**Problem:**
- Current implementation assumes 100% stocks with forced annual withdrawals
- Maximizes sequence of returns risk
- Must sell stocks even during crashes (e.g., -37% in 2008)
- Results in very high initial investment requirements for bad sequences

**Solution - Optimized Cash Buffer:**
This is a **2-dimensional optimization problem**:

**Variables to Optimize:**
1. **Initial investment amount** (what we want to minimize)
2. **Cash buffer size** (in years of payments) - this is also optimized, not fixed!

**Strategy Logic:**
- Keep N years of payments in cash/money market (N is optimized)
- Remaining amount invested in stocks (S&P 500)
- Withdrawal logic:
  - Always withdraw payment from cash buffer
  - Replenishment logic (optimize this too):
    - If positive stock return: sell stocks to replenish cash to target buffer
    - If negative stock return: only replenish if cash critically low (< 1 year)
    - If great year (>20%): opportunistically top up buffer beyond target
- Goal: Never sell stocks at losses if possible

**Optimization Goal:**
**Maximize probability of success while minimizing required investment**

Specifically:
- **Ignore worst case (Great Depression)**: That's a 1-in-100 year event, too extreme to optimize for
- **Focus on 90th-95th percentile**: These are the "conservative" and "very safe" recommendations
- **Goal**: Find minimum investment that gives you 90-95% success rate across all historical scenarios

**Why This Matters:**
- Current: 90th percentile needs $430K (86% of mortgage!)
- With optimization: Maybe 90th percentile only needs $310K (62% of mortgage)
- **Same 90% success rate, but $120K less capital required**

The best/median cases already work fine with low investment amounts.
The problem is the moderately-bad scenarios (not Great Depression, but things like 2000-2024 with two crashes).

**Optimization Approach:**
For each historical period:
1. Try different cash buffer sizes (0 to 10 years)
2. For each buffer size, find minimum initial investment using binary search
3. Select the (buffer_size, investment) combination that minimizes total investment
4. Return: optimal_investment, optimal_buffer_size

**Expected Results:**

| Scenario | Current (No Buffer) | With Optimized Buffer | Buffer Size | Target |
|----------|---------------------|----------------------|-------------|---------|
| **Best Case** | $175K | ~$175K (no buffer) | 0 years | Not optimizing (already good) |
| **Median (50th)** | $264K | ~$260K (minimal buffer) | 0-1 years | Not optimizing (already good) |
| **Conservative (90th)** | **$430K** | **~$310K** ⭐ | 3-4 years | **PRIMARY TARGET** |
| **Very Safe (95th)** | **$549K** | **~$380K** ⭐ | 4-5 years | **PRIMARY TARGET** |
| **Worst Case (100th)** | $768K | Not optimizing | N/A | Accept as extreme outlier |

**The KEY VALUE is:**
- **90th percentile (Conservative)**: Reduce from $430K → $310K = **$120K savings**
- **95th percentile (Very Safe)**: Reduce from $549K → $380K = **$169K savings**
- **Same success rate (90-95%), much less capital required**

These are the recommendations users will actually follow. Making them more achievable is the goal.

**Why This Works:**
- **1929-1953**: With 6-year buffer, you ride out the brutal 1929-1933 crash without selling stocks at -43%
- **2000-2024**: With 4-year buffer, you don't sell during 2008 crash (-37%) or dot-com crash
- **Best case periods**: Buffer not needed, so optimal buffer = 0 (avoid cash drag)

**User Experience:**
Show comparison:
```
Conservative (90th percentile):
  Without buffer: $430,319 (100% stocks, forced selling in crashes)
  With optimal buffer: $305,000 (4-year cash buffer, avoid selling in downturns)
  YOU SAVE: $125,000 by using optimized bucket strategy!

  Recommendation: Invest $305,000 total:
    - $193,000 in S&P 500 (VTI)
    - $112,000 in cash/money market (4 years of payments)
```

**Implementation Phases:**
1. **Phase 1**: Implement buffer simulation logic
   - `simulate_with_cash_buffer(initial, returns, payment, buffer_years)`
   - Logic for when to sell stocks, how to manage cash

2. **Phase 2**: Implement 2D optimization
   - For each buffer size (0-10 years), find minimum investment
   - Return optimal combination: `(min_investment, optimal_buffer_years)`

3. **Phase 3**: Run backtesting with buffer optimization
   - For each historical period, find optimal buffer strategy
   - Compare results: no-buffer vs. optimized-buffer
   - Show how much buffer strategy reduces required investment

4. **Phase 4**: UI updates
   - Add toggle: "Use Cash Buffer Strategy" (yes/no)
   - Show comparison table:
     - No buffer (100% stocks): $X
     - Optimized buffer: $Y with N years cash
     - Savings: $X - $Y
   - Show buffer size varies by scenario (worst case might need 5 years, median might need 1 year)

**Success Metrics for Implementation:**
1. **90th percentile drops below $350K** (currently $430K) = Success!
2. **95th percentile drops below $425K** (currently $549K) = Success!
3. **Median stays roughly same or better** (currently $264K) = No harm done
4. **Best case doesn't get worse** (currently $175K) = Buffer optional for good periods

**Key Questions to Test:**
1. Does buffer actually help the 90-95th percentile scenarios? (This determines if we ship it)
2. What's the optimal buffer size for 2000-2024 period (2 crashes)?
3. Does cash earning 2% change the equation enough vs. my earlier 0% test?
4. Is there a simpler strategy than dynamic replenishment rules?

**Key Assumptions:**
- **Cash return: 2%** (realistic for money market funds / short-term bonds over long term)
  - Current money market ~5% but won't last
  - 10-20 year treasuries have interest rate risk, not suitable for liquid buffer
  - 2% is conservative average for truly liquid, stable-value assets
- **Buffer is static**: Fixed N years maintained throughout (future: could make dynamic)
- **Taxes**: Ignored (assume tax-advantaged account like IRA)

**Replenishment Logic (Needs Testing):**
- **Target buffer**: N years of payments in cash (N is optimized)
- **Withdrawal**: Always take payment from cash at start of year
- **Replenishment rules**:
  - If cash < 1 year of payments: MUST replenish from stocks (regardless of return)
  - If stock return > 10% AND cash < target: Replenish to target from stocks
  - If stock return 0-10%: Only replenish if cash < 2 years
  - If stock return < 0%: Don't touch stocks unless critically low (<1 year cash)
- **Goal**: Avoid selling stocks at significant losses when possible

**Important Note:**
Initial testing suggests buffer strategy might NOT help (or even hurt) due to cash opportunity cost.
Need to implement and test before committing to this feature.

**Other Enhancements:**
- Monte Carlo simulation (random sampling from historical returns)
- Monthly payment/return calculations
- Tax considerations
- Inflation adjustment
- Multiple asset allocations (60/40 stocks/bonds, etc.)
- Dynamic withdrawal strategies (skip/reduce payment in crash years if possible)
- What-if scenario builder

## Success Criteria

1. ✓ Accurate mortgage payment calculation
2. ✓ Successful simulation using real historical data
3. ✓ Identification of worst/best case scenarios
4. ✓ Statistical distribution of required investments
5. ✓ Clear recommendation with confidence levels
6. ✓ Reproducible results with documented methodology

## File Structure

```
finance-app/
├── DESIGN.md                           # This design document
├── README.md                           # User documentation & setup guide
├── requirements.txt                    # Python dependencies
│
├── data/
│   └── sp500_returns.json              # Historical S&P 500 returns (1926-2025)
│
├── backend/
│   ├── __init__.py
│   ├── app.py                          # Flask/FastAPI main app
│   ├── config.py                       # Configuration settings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── mortgage_calculator.py      # Mortgage calculations
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── investment_simulator.py     # Investment simulation logic
│   │   ├── backtester.py               # Historical backtesting engine
│   │   └── data_loader.py              # Load S&P 500 data
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                   # API endpoints
│   │
│   └── tests/
│       ├── test_mortgage.py
│       ├── test_simulator.py
│       └── test_backtester.py
│
├── frontend/
│   ├── index.html                      # Main HTML page
│   ├── styles/
│   │   ├── main.css                    # Global styles
│   │   ├── form.css                    # Input form styles
│   │   ├── results.css                 # Results dashboard styles
│   │   └── responsive.css              # Mobile/tablet responsive styles
│   │
│   ├── scripts/
│   │   ├── main.js                     # Main application logic
│   │   ├── api-client.js               # API communication
│   │   ├── form-handler.js             # Form validation & submission
│   │   ├── results-renderer.js         # Render results dashboard
│   │   ├── chart-builder.js            # Chart.js/Plotly chart creation
│   │   └── utils.js                    # Utility functions
│   │
│   ├── assets/
│   │   ├── images/
│   │   │   └── logo.svg                # App logo/icon
│   │   └── fonts/
│   │       └── (custom fonts if needed)
│   │
│   └── lib/
│       ├── chart.min.js                # Chart.js library
│       └── (other third-party libs)
│
└── docs/
    ├── API.md                          # API documentation
    ├── CALCULATIONS.md                 # Explanation of formulas
    └── USER_GUIDE.md                   # End-user guide
```

## Timeline Estimate

### Development Phases
- **Phase 1**: Backend Core (Python) - **3-4 hours**
- **Phase 2**: Backend API (Flask/FastAPI) - **2-3 hours**
- **Phase 3**: Frontend Basic Structure - **3-4 hours**
- **Phase 4**: Frontend Input Form - **2-3 hours**
- **Phase 5**: Frontend Results Visualization - **4-5 hours**
- **Phase 6**: Additional Features - **2-3 hours**
- **Phase 7**: Testing & Polish - **2-3 hours**
- **Phase 8**: Documentation & Deployment - **1-2 hours**

### Total Estimates
- **Minimum**: 19 hours
- **Expected**: 23 hours
- **Maximum**: 27 hours

### Milestone Breakdown
1. **MVP (Minimum Viable Product)** - Phases 1-4: ~10-14 hours
   - Backend working with API
   - Basic frontend with input form
   - Can calculate and display results (no fancy charts)

2. **Full Featured** - Phases 1-6: ~16-22 hours
   - All visualizations
   - Export/share functionality
   - Polished UI

3. **Production Ready** - All Phases: ~19-27 hours
   - Fully tested
   - Documented
   - Ready to deploy

---

## Open Questions & Design Decisions

### Resolved Decisions:
1. **Withdrawals timing**: Beginning of year (more conservative, easier to model)
2. **User inputs**: All mortgage parameters fully configurable
3. **Interface**: Web application (not just CLI)
4. **Visualizations**: 4 main charts as specified
5. **Risk tolerance options**: Conservative (90th), Moderate (75th), Aggressive (median)

### Outstanding Questions:
1. **Technology preference**:
   - Backend: Flask (simpler) vs. FastAPI (modern, async)?
   - Frontend: Vanilla JS (lighter) vs. React (more maintainable)?
   - Charts: Chart.js (simpler) vs. Plotly (more interactive)?

2. **Deployment target**:
   - Local only initially?
   - Cloud hosting needed? (Heroku, Vercel, AWS, etc.)

3. **Advanced features priority**:
   - Should we include tax considerations in v1?
   - Should we support monthly calculations or stick with annual?
   - Should we add Monte Carlo simulation alongside historical backtesting?

4. **Partial years in data**:
   - 2025 has YTD data only - exclude from 25-year windows ending in 2025?
   - Decision: Yes, only use complete calendar year data

## Next Steps

### Immediate Actions:
1. ✅ **Review and approve this design**
2. **Make technology stack decisions** (Flask vs FastAPI, etc.)
3. **Begin Phase 1 implementation** (Backend Core)
   - Start with mortgage calculator
   - Then investment simulator
   - Finally backtesting engine
4. **Set up project structure** (create directories, initial files)

### Development Workflow:
1. **Iterative development**: Build and test each phase
2. **Start with MVP**: Get basic functionality working first
3. **Add visualizations**: Once core calculations work
4. **Polish and optimize**: After all features complete

### Success Metrics:
- Calculations match hand-calculated examples
- UI is intuitive and responsive
- Performance: Results return in < 2 seconds
- Code is well-documented and tested

---

## Summary

This design document outlines a comprehensive **web-based Mortgage vs. Investment Optimizer** that:

✅ **Accepts flexible user inputs** (mortgage balance, interest rate, years remaining)
✅ **Uses real historical data** (100 years of S&P 500 returns from 1926-2024)
✅ **Dynamically computes backtests** (generates N-year rolling windows at runtime based on user's years remaining)
✅ **Runs thorough historical analysis** (tests all possible historical periods for the given timeframe)
✅ **Provides visual insights** (4 interactive charts showing distribution, risk, and scenarios)
✅ **Recommends investment amount** based on user's risk tolerance (50th/75th/90th percentile)
✅ **Shows potential savings** vs. paying off mortgage directly

**Key Innovation**: Unlike simple average return calculators, this tool accounts for **sequence of returns risk** using actual historical market data, providing realistic scenarios from best case to worst case.

**Technical Approach**:
- **Dynamic computation** at runtime (not pre-computed) for maximum flexibility
- Supports any timeframe (1-30 years)
- Fast performance (< 1 second even for 30-year mortgages)

**Expected Outcome**: Users can make informed decisions about whether to pay off their mortgage or invest in the market, understanding both the potential upside and the risks involved.

**Development Time**: ~20-25 hours for full-featured, production-ready web application.
