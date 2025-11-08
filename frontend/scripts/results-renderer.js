// Results Renderer

function renderResults(data) {
    // Update summary cards
    document.getElementById('summary-balance').textContent = formatCurrency(data.mortgage_details.balance);
    document.getElementById('summary-rate').textContent = formatPercent(data.mortgage_details.rate);
    document.getElementById('summary-years').textContent = `${data.mortgage_details.years} years`;
    document.getElementById('summary-payment').textContent = formatCurrency(data.mortgage_details.annual_payment);

    document.getElementById('recommended-amount').textContent = formatCurrency(data.recommendation.amount);
    document.getElementById('recommended-label').textContent = getRiskLabel(data.recommendation.risk_level);
    document.getElementById('success-rate').textContent = formatPercent(data.recommendation.success_rate * 100);

    // Update early payoff information
    const yearsToPayoff = data.recommendation.years_to_payoff;
    const mortgageYears = data.mortgage_details.years;
    const paidOffEarly = data.recommendation.paid_off_early;

    if (paidOffEarly) {
        document.getElementById('payoff-time').textContent = `${yearsToPayoff} years (early!)`;
        document.getElementById('payoff-time').style.color = '#10b981'; // Green
    } else {
        document.getElementById('payoff-time').textContent = `${yearsToPayoff} years`;
        document.getElementById('payoff-time').style.color = '';
    }

    document.getElementById('leftover-amount').textContent = formatCurrency(data.recommendation.leftover_amount);

    document.getElementById('savings-amount').textContent = formatCurrency(data.recommendation.savings_vs_payoff);
    document.getElementById('scenarios-tested').textContent = data.scenarios_tested;

    // Render charts
    createDistributionChart(data);
    createRiskChart(data);
    createBalanceChart(data);

    // Render table
    renderTable(data);

    // Initialize period explorer
    initializePeriodExplorer(data);

    // Show results
    showResults();
}

function renderTable(data) {
    const tbody = document.getElementById('requirements-tbody');
    tbody.innerHTML = '';

    const rows = [
        { label: 'Best Case', data: data.results.best_case, rate: 'N/A' },
        { label: 'Aggressive (Median)', data: data.results.median, rate: '50%' },
        { label: 'Moderate (75th %ile)', data: data.results.percentile_75, rate: '75%' },
        { label: 'Conservative (90th %ile)', data: data.results.percentile_90, rate: '90%' },
        { label: 'Very Safe (95th %ile)', data: data.results.percentile_95, rate: '95%' },
        { label: 'Worst Case', data: data.results.worst_case, rate: '100%' }
    ];

    const mortgageYears = data.mortgage_details.years;

    rows.forEach(row => {
        const tr = document.createElement('tr');

        // Highlight user's selected risk level
        const selectedPercentile = data.recommendation.percentile;
        if ((row.label.includes('Median') && selectedPercentile === 'median') ||
            (row.label.includes('75th') && selectedPercentile === 'percentile_75') ||
            (row.label.includes('90th') && selectedPercentile === 'percentile_90')) {
            tr.classList.add('highlight-row');
        }

        // Format years to payoff with early indicator
        const yearsText = row.data.paid_off_early
            ? `${row.data.years_to_payoff} <span style="color: #10b981;">✓</span>`
            : `${row.data.years_to_payoff}`;

        tr.innerHTML = `
            <td>${row.label}</td>
            <td>${formatCurrency(row.data.investment_required)}</td>
            <td>${yearsText}</td>
            <td>${formatCurrency(row.data.leftover_amount)}</td>
            <td>${row.rate}</td>
            <td>${row.data.period}</td>
        `;

        tbody.appendChild(tr);
    });
}

function getRiskLabel(riskLevel) {
    const labels = {
        'aggressive': 'Median (50th percentile)',
        'moderate': '75th Percentile',
        'conservative': '90th Percentile'
    };
    return labels[riskLevel] || '90th Percentile';
}

// Store the full data for period explorer
let fullResultsData = null;
let periodChart = null;

function initializePeriodExplorer(data) {
    fullResultsData = data;

    // Populate dropdown with all scenarios
    const select = document.getElementById('period-select');
    select.innerHTML = '<option value="">-- Choose a period --</option>';

    // Sort scenarios by start year
    const sortedScenarios = [...data.all_scenarios].sort((a, b) => {
        const yearA = parseInt(a.period.split('-')[0]);
        const yearB = parseInt(b.period.split('-')[0]);
        return yearA - yearB;
    });

    sortedScenarios.forEach((scenario, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = scenario.period;
        select.appendChild(option);
    });

    // Add event listener
    select.addEventListener('change', (e) => {
        if (e.target.value === '') {
            document.getElementById('period-details').classList.add('hidden');
        } else {
            const scenarioIndex = parseInt(e.target.value);
            showPeriodDetails(sortedScenarios[scenarioIndex]);
        }
    });
}

function showPeriodDetails(scenario) {
    // Update summary
    document.getElementById('period-name').textContent = scenario.period;
    document.getElementById('period-investment').textContent = formatCurrency(scenario.investment_required);
    document.getElementById('period-years').textContent = `${scenario.years_to_payoff} years`;
    document.getElementById('period-leftover').textContent = formatCurrency(scenario.leftover_amount);
    document.getElementById('period-early').textContent = scenario.paid_off_early ? 'Yes ✓' : 'No';
    document.getElementById('period-early').style.color = scenario.paid_off_early ? '#10b981' : '#666';

    // Show details section
    document.getElementById('period-details').classList.remove('hidden');

    // Create chart
    createPeriodChart(scenario);
}

function createPeriodChart(scenario) {
    const ctx = document.getElementById('period-chart');

    // Destroy existing chart
    if (periodChart) {
        periodChart.destroy();
    }

    // Get year by year data
    const yearByYear = scenario.year_by_year;
    const startYear = parseInt(scenario.period.split('-')[0]);

    // Prepare data
    const labels = yearByYear.map((y, i) => startYear + i);
    const balanceData = yearByYear.map(y => y.balance);
    const mortgageData = yearByYear.map(y => y.remaining_mortgage);

    // Find payoff point
    const payoffYear = yearByYear.findIndex(y => y.can_payoff_early);

    periodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Investment Balance',
                    data: balanceData,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Remaining Mortgage',
                    data: mortgageData,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += formatCurrency(context.parsed.y);

                            // Add note if this is the payoff year
                            if (context.dataIndex === payoffYear) {
                                label += ' ← Paid off!';
                            }
                            return label;
                        }
                    }
                },
                annotation: payoffYear >= 0 ? {
                    annotations: {
                        payoffLine: {
                            type: 'line',
                            xMin: payoffYear,
                            xMax: payoffYear,
                            borderColor: '#10b981',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Paid Off!',
                                position: 'start'
                            }
                        }
                    }
                } : {}
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}
