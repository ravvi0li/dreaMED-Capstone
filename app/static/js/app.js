// Main JavaScript for Pharmacovigilance App

// API Base URL
const API_BASE = '/api';

// Global variables
let autocompleteTimeout;
let modelComparisonChart;
let featureImportanceChart;

// DOM Elements
const searchInput = document.getElementById('drug-search-input');
const predictBtn = document.getElementById('predict-btn');
const autocompleteResults = document.getElementById('autocomplete-results');
const loadingSpinner = document.getElementById('loading-spinner');
const errorMessage = document.getElementById('error-message');
const resultsSection = document.getElementById('results');

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Pharmacovigilance App initialized');
    
    // Load initial data
    loadDatabaseStats();
    loadModelComparison();
    loadFeatureImportance();
    loadTopSideEffects();
    
    // Event listeners
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keypress', handleKeyPress);
    predictBtn.addEventListener('click', handlePredict);
    
    // Click outside to close autocomplete
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
            autocompleteResults.classList.remove('show');
        }
    });
});

// ============================================================================
// SEARCH & AUTOCOMPLETE
// ============================================================================

function handleSearchInput(e) {
    const query = e.target.value.trim();
    
    if (query.length < 2) {
        autocompleteResults.classList.remove('show');
        return;
    }
    
    // Debounce search
    clearTimeout(autocompleteTimeout);
    autocompleteTimeout = setTimeout(() => {
        searchDrugs(query);
    }, 300);
}

function handleKeyPress(e) {
    if (e.key === 'Enter') {
        handlePredict();
    }
}

async function searchDrugs(query) {
    try {
        const response = await fetch(`${API_BASE}/drugs/search?q=${encodeURIComponent(query)}&limit=10`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            displayAutocomplete(data.results);
        } else {
            autocompleteResults.classList.remove('show');
        }
    } catch (error) {
        console.error('Search error:', error);
    }
}

function displayAutocomplete(results) {
    autocompleteResults.innerHTML = '';
    
    results.forEach(drug => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <strong>${drug.name}</strong>
            <br>
            <small class="text-muted">CID: ${drug.cid}</small>
        `;
        item.addEventListener('click', () => {
            searchInput.value = drug.name;
            autocompleteResults.classList.remove('show');
            handlePredict();
        });
        autocompleteResults.appendChild(item);
    });
    
    autocompleteResults.classList.add('show');
}

// ============================================================================
// PREDICTION
// ============================================================================

async function handlePredict() {
    const drugName = searchInput.value.trim();
    
    if (!drugName) {
        showError('Please enter a drug name');
        return;
    }
    
    // Hide previous results and errors
    resultsSection.style.display = 'none';
    errorMessage.style.display = 'none';
    autocompleteResults.classList.remove('show');
    
    // Show loading
    loadingSpinner.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ drug_name: drugName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
        } else {
            showError(data.error || 'Drug not found. Please check the spelling and try again.');
        }
    } catch (error) {
        console.error('Prediction error:', error);
        showError('An error occurred. Please try again.');
    } finally {
        loadingSpinner.style.display = 'none';
    }
}

function displayResults(data) {
    // Update drug info
    document.getElementById('result-drug-name').textContent = data.drug;
    document.getElementById('result-cid').textContent = data.cid;
    document.getElementById('result-model').textContent = data.model;
    document.getElementById('result-summary').textContent = data.summary;
    document.getElementById('total-predicted').textContent = data.total_predicted;
    
    // Display side effects
    const sideEffectsList = document.getElementById('side-effects-list');
    sideEffectsList.innerHTML = '';
    
    if (data.predictions && data.predictions.length > 0) {
        data.predictions.forEach((prediction, index) => {
            const card = createSideEffectCard(prediction, index + 1);
            sideEffectsList.appendChild(card);
        });
    } else {
        sideEffectsList.innerHTML = '<p class="text-muted">No significant side effects predicted.</p>';
    }
    
    // Show results with animation
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function createSideEffectCard(prediction, rank) {
    const col = document.createElement('div');
    col.className = 'col-md-6 mb-3';
    
    const probability = prediction.probability * 100;
    const severity = prediction.severity;
    
    col.innerHTML = `
        <div class="side-effect-card">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6>
                    <span class="badge bg-secondary me-2">#${rank}</span>
                    ${prediction.side_effect}
                </h6>
                <span class="severity-badge ${severity}">
                    ${severity.toUpperCase()}
                </span>
            </div>
            <div class="probability-bar">
                <div class="probability-fill ${severity}" style="width: ${probability}%">
                    ${probability.toFixed(1)}%
                </div>
            </div>
        </div>
    `;
    
    return col;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.classList.add('fade-in');
}

// ============================================================================
// STATISTICS & VISUALIZATIONS
// ============================================================================

async function loadDatabaseStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        // Update stats
        animateCounter('stat-drugs', data.database.total_drugs);
        animateCounter('stat-side-effects', data.database.total_side_effects);
        
        const f1Score = (data.model.metrics.f1_macro * 100).toFixed(1);
        animateCounter('stat-accuracy', f1Score, '%');
        
    } catch (error) {
        console.error('Stats loading error:', error);
    }
}

async function loadModelComparison() {
    try {
        const response = await fetch(`${API_BASE}/visualizations/model-comparison`);
        const data = await response.json();
        
        const ctx = document.getElementById('model-comparison-chart').getContext('2d');
        
        modelComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.models,
                datasets: [{
                    label: 'F1-Score (Macro)',
                    data: data.f1_scores,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'F1-Score: ' + (context.parsed.y * 100).toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Model comparison loading error:', error);
    }
}

async function loadFeatureImportance() {
    try {
        const response = await fetch(`${API_BASE}/visualizations/feature-importance`);
        const data = await response.json();
        
        const ctx = document.getElementById('feature-importance-chart').getContext('2d');
        
        // Take top 10 for better visualization
        const top10Features = data.features.slice(0, 10);
        const top10Importance = data.importance.slice(0, 10);
        
        featureImportanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top10Features,
                datasets: [{
                    label: 'Importance Score',
                    data: top10Importance,
                    backgroundColor: 'rgba(155, 89, 182, 0.8)',
                    borderColor: 'rgba(155, 89, 182, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Importance Score'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Features'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Importance: ' + context.parsed.x.toFixed(4);
                            }
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Feature importance loading error:', error);
    }
}

async function loadTopSideEffects() {
    try {
        const response = await fetch(`${API_BASE}/side-effects/top?limit=15`);
        const data = await response.json();
        
        const container = document.getElementById('top-side-effects-list');
        container.innerHTML = '';
        
        data.side_effects.forEach((se, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';
            col.innerHTML = `
                <div class="top-se-item">
                    <span class="se-name">
                        <span class="badge bg-secondary me-2">${index + 1}</span>
                        ${se.name}
                    </span>
                    <span class="se-count">${se.count}</span>
                </div>
            `;
            container.appendChild(col);
        });
        
    } catch (error) {
        console.error('Top side effects loading error:', error);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function animateCounter(elementId, targetValue, suffix = '') {
    const element = document.getElementById(elementId);
    const duration = 1500;
    const startValue = 0;
    const increment = targetValue / (duration / 16);
    
    let currentValue = startValue;
    
    const timer = setInterval(() => {
        currentValue += increment;
        if (currentValue >= targetValue) {
            currentValue = targetValue;
            clearInterval(timer);
        }
        element.textContent = Math.floor(currentValue) + suffix;
    }, 16);
}
