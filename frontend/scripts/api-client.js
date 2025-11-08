// API Client

const API_BASE_URL = 'http://localhost:8080/api';

async function calculateInvestment(params) {
    const response = await fetch(`${API_BASE_URL}/calculate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'API request failed');
    }

    return await response.json();
}

async function getDataInfo() {
    const response = await fetch(`${API_BASE_URL}/data-info`);
    return await response.json();
}

async function checkHealth() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
}
