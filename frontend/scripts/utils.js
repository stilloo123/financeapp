// Utility Functions

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatPercent(value) {
    return `${value.toFixed(1)}%`;
}

function showElement(elementId) {
    document.getElementById(elementId).classList.remove('hidden');
}

function hideElement(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

function showLoading() {
    hideElement('input-section');
    hideElement('results-section');
    showElement('loading');
}

function showResults() {
    hideElement('loading');
    showElement('results-section');
    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function showInput() {
    hideElement('loading');
    hideElement('results-section');
    showElement('input-section');
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
