# Mortgage vs. Investment Optimizer

A web application that helps you decide whether to pay off your mortgage or invest in the market, using 100 years of historical S&P 500 data.

## Features

- **Historical Backtesting**: Uses actual S&P 500 returns (1926-2024) to simulate all possible scenarios
- **Dynamic Computation**: Generates analysis based on your specific mortgage parameters
- **Risk Analysis**: Shows best case, worst case, and percentile-based recommendations
- **Interactive Charts**: Visualize distribution, risk, and balance projections
- **Export Data**: Download results as CSV

## Project Structure

```
finance-app/
├── backend/              # Python Flask API
│   ├── models/          # Mortgage calculator
│   ├── services/        # Investment simulator & backtester
│   └── api/             # REST API endpoints
├── frontend/            # HTML/CSS/JavaScript UI
│   ├── styles/         # CSS files
│   └── scripts/        # JavaScript modules
├── data/               # Historical S&P 500 returns
└── docs/               # Documentation
```

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

1. **Clone or navigate to the project directory**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python backend/app.py
   ```

2. **Open your browser**
   ```
   http://localhost:5000
   ```

The server will:
- Serve the frontend at `http://localhost:5000/`
- Provide API endpoints at `http://localhost:5000/api/`

## API Endpoints

### GET /api/health
Health check endpoint

### GET /api/data-info
Get information about available historical data

### POST /api/calculate
Main calculation endpoint

**Request Body:**
```json
{
  "mortgage_balance": 500000,
  "interest_rate": 3.0,
  "years_remaining": 25,
  "risk_tolerance": "conservative"
}
```

**Response:**
```json
{
  "mortgage_details": { ... },
  "results": {
    "best_case": { ... },
    "median": { ... },
    "percentile_90": { ... },
    "worst_case": { ... }
  },
  "recommendation": { ... },
  "statistics": { ... }
}
```

## How It Works

1. **User Input**: Enter mortgage balance, interest rate, and years remaining
2. **Mortgage Calculation**: Calculates annual payment using amortization formula
3. **Historical Backtesting**:
   - Generates all possible N-year rolling windows from 1926-2024
   - For each window, finds minimum investment needed to fund all payments
   - Uses binary search optimization
4. **Statistical Analysis**: Calculates percentiles, best/worst cases
5. **Visualization**: Displays results with interactive charts

## Key Assumptions

- Investment in S&P 500 index fund (like VTI)
- Annual withdrawals for mortgage payments
- Historical returns include dividends (total return)
- No taxes (assumes tax-advantaged account like IRA)
- Account reaches $0 at end of mortgage term
- Withdrawals happen at beginning of each year

## Testing Backend Modules

Test individual modules:

```bash
# Test mortgage calculator
python backend/models/mortgage_calculator.py

# Test investment simulator
python backend/services/investment_simulator.py

# Test data loader
python backend/services/data_loader.py

# Test backtester
python -m backend.services.backtester
```

## Technologies Used

### Backend
- Python 3.10+
- Flask (web framework)
- Flask-CORS (cross-origin support)

### Frontend
- HTML5 / CSS3
- Vanilla JavaScript
- Chart.js (data visualization)

### Data
- S&P 500 historical returns (1926-2024)
- Source: https://www.slickcharts.com/sp500/returns

## Performance

- Typical calculation time: < 1 second for 25-year mortgage
- ~75 historical scenarios tested for 25-year term
- ~90 historical scenarios tested for 10-year term
- Uses binary search for fast optimization (~15-20 iterations per scenario)

## Future Enhancements

- [ ] Monthly calculations (vs. annual)
- [ ] Monte Carlo simulation
- [ ] Tax considerations
- [ ] Inflation adjustment
- [ ] Multiple investment strategies (bonds, real estate)
- [ ] PDF report generation
- [ ] Shareable results URL

## License

MIT

## Contributing

Pull requests welcome! Please ensure tests pass and code follows the existing style.
