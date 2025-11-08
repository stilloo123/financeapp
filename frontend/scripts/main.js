// Main Application

// Global variable to store current results for export
window.currentResults = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Mortgage vs. Investment Optimizer - Frontend Loaded');

    // Setup event handlers
    setupFormHandler();
    setupAdjustButton();
    setupExportButton();

    // Check API health on load
    checkHealth()
        .then(response => {
            console.log('API Health:', response);
        })
        .catch(error => {
            console.error('API health check failed:', error);
        });

    // Override renderResults to store results globally
    const originalRenderResults = window.renderResults;
    window.renderResults = function(data) {
        window.currentResults = data;
        originalRenderResults(data);
    };
});
