// Form Handler

function setupFormHandler() {
    const form = document.getElementById('mortgage-form');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get form data
        const formData = new FormData(form);
        const params = {
            mortgage_balance: parseFloat(formData.get('mortgage_balance')),
            interest_rate: parseFloat(formData.get('interest_rate')),
            years_remaining: parseInt(formData.get('years_remaining')),
            risk_tolerance: formData.get('risk_tolerance')
        };

        // Validate
        if (params.mortgage_balance < 50000 || params.mortgage_balance > 5000000) {
            alert('Mortgage balance must be between $50,000 and $5,000,000');
            return;
        }

        if (params.interest_rate < 0.1 || params.interest_rate > 15) {
            alert('Interest rate must be between 0.1% and 15%');
            return;
        }

        if (params.years_remaining < 1 || params.years_remaining > 30) {
            alert('Years remaining must be between 1 and 30');
            return;
        }

        // Show loading
        showLoading();

        try {
            // Call API
            const results = await calculateInvestment(params);

            // Render results
            renderResults(results);

        } catch (error) {
            alert('Error: ' + error.message);
            showInput();
        }
    });
}

function setupAdjustButton() {
    document.getElementById('adjust-btn').addEventListener('click', () => {
        showInput();
    });
}

function setupExportButton() {
    document.getElementById('export-btn').addEventListener('click', () => {
        // Get current results (stored in window for simplicity)
        if (!window.currentResults) {
            alert('No results to export');
            return;
        }

        const data = window.currentResults;
        let csv = 'Period,Investment Required\\n';

        data.all_scenarios.forEach(scenario => {
            csv += `${scenario.period},${scenario.investment_required}\\n`;
        });

        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mortgage_investment_analysis.csv';
        a.click();
    });
}
