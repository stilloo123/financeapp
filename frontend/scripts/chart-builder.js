// Chart Builder

let distributionChart = null;
let riskChart = null;
let balanceChart = null;

function createDistributionChart(data) {
    const ctx = document.getElementById('distribution-chart').getContext('2d');

    // Destroy existing chart
    if (distributionChart) {
        distributionChart.destroy();
    }

    // Prepare histogram data
    const investments = data.all_scenarios.map(s => s.investment_required);
    const bins = createHistogramBins(investments, 15);

    distributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: bins.labels,
            datasets: [{
                label: 'Number of Scenarios',
                data: bins.counts,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Count' }
                },
                x: {
                    title: { display: true, text: 'Investment Required ($)' }
                }
            }
        }
    });
}

function createRiskChart(data) {
    const ctx = document.getElementById('risk-chart').getContext('2d');

    if (riskChart) {
        riskChart.destroy();
    }

    const results = data.results;

    riskChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Best', '25th%', 'Median', '75th%', '90th%', '95th%', 'Worst'],
            datasets: [{
                label: 'Investment Required',
                data: [
                    results.best_case.investment_required,
                    data.statistics.min, // Using min as proxy for 25th
                    results.median.investment_required,
                    results.percentile_75.investment_required,
                    results.percentile_90.investment_required,
                    results.percentile_95.investment_required,
                    results.worst_case.investment_required
                ],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.7)',
                    'rgba(132, 204, 22, 0.7)',
                    'rgba(234, 179, 8, 0.7)',
                    'rgba(249, 115, 22, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                    'rgba(220, 38, 38, 0.7)',
                    'rgba(185, 28, 28, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });
}

function createBalanceChart(data) {
    const ctx = document.getElementById('balance-chart').getContext('2d');

    if (balanceChart) {
        balanceChart.destroy();
    }

    const worst = data.results.worst_case;
    const median = data.results.median;
    const best = data.results.best_case;

    const years = worst.year_by_year.map(y => y.year);

    balanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: `Worst Case (${worst.period})`,
                    data: worst.year_by_year.map(y => y.balance),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3
                },
                {
                    label: `Median (${median.period})`,
                    data: median.year_by_year.map(y => y.balance),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3
                },
                {
                    label: `Best Case (${best.period})`,
                    data: best.year_by_year.map(y => y.balance),
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true, position: 'top' }
            },
            scales: {
                y: {
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                },
                x: {
                    title: { display: true, text: 'Year' }
                }
            }
        }
    });
}

function createHistogramBins(data, numBins) {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const binSize = (max - min) / numBins;

    const bins = Array(numBins).fill(0);
    const labels = [];

    for (let i = 0; i < numBins; i++) {
        const binStart = min + i * binSize;
        const binEnd = binStart + binSize;
        labels.push(formatCurrency(binStart));

        data.forEach(value => {
            if (value >= binStart && (i === numBins - 1 ? value <= binEnd : value < binEnd)) {
                bins[i]++;
            }
        });
    }

    return { labels, counts: bins };
}
