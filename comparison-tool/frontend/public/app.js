// Application State
const state = {
    uploadId: null,
    filename: null,
    fileInfo: null,
    benchmarkId: null,
    selectedCategories: [],
    websocket: null,
    results: null
};

// Backend API URL
const API_URL = '/api';

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkSystemHealth();
});

// Event Listeners
function initializeEventListeners() {
    // File upload
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Category selection
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', () => toggleCategory(card));
    });
    
    // Benchmark controls
    document.getElementById('start-benchmark').addEventListener('click', startBenchmark);
    document.getElementById('use-example-data').addEventListener('click', showExamples);
    
    // Export buttons
    document.getElementById('export-json').addEventListener('click', () => exportResults('json'));
    document.getElementById('export-csv').addEventListener('click', () => exportResults('csv'));
    document.getElementById('export-report').addEventListener('click', () => exportResults('report'));
    
    // Category filter
    document.getElementById('category-filter').addEventListener('change', filterResultsTable);
    
    // Examples modal
    document.getElementById('close-examples').addEventListener('click', hideExamples);
}

// System Health Check
async function checkSystemHealth() {
    try {
        const response = await axios.get(`${API_URL}/health`);
        const health = response.data;
        
        updateStatusIndicator('mork-status', health.mork === 'connected');
        updateStatusIndicator('neo4j-status', health.neo4j === 'connected');
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatusIndicator('mork-status', false);
        updateStatusIndicator('neo4j-status', false);
    }
}

function updateStatusIndicator(elementId, isConnected) {
    const element = document.getElementById(elementId);
    if (isConnected) {
        element.textContent = '🟢 Connected';
        element.className = 'status-indicator connected';
    } else {
        element.textContent = '🔴 Disconnected';
        element.className = 'status-indicator disconnected';
    }
}

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

async function uploadFile(file) {
    // Validate file type
    if (!file.name.endsWith('.json') && !file.name.endsWith('.csv')) {
        alert('Please upload a JSON or CSV file');
        return;
    }
    
    showLoading('Uploading file...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API_URL}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        const data = response.data;
        state.uploadId = data.upload_id;
        state.filename = data.filename;
        state.fileInfo = data.file_info;
        
        displayFileInfo(data);
        showConfigSection();
        suggestCategories(data.suggested_benchmarks);
        
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Upload failed:', error);
        alert('Failed to upload file: ' + (error.response?.data?.detail || error.message));
    }
}

function displayFileInfo(data) {
    const fileInfo = document.getElementById('file-info');
    
    document.getElementById('file-name').textContent = data.filename;
    document.getElementById('file-size').textContent = formatBytes(data.size);
    document.getElementById('file-format').textContent = data.file_info.format.toUpperCase();
    document.getElementById('estimated-nodes').textContent = data.file_info.estimated_nodes;
    document.getElementById('estimated-relationships').textContent = data.file_info.estimated_relationships;
    document.getElementById('sample-data-content').textContent = JSON.stringify(data.file_info.sample_data, null, 2);
    
    fileInfo.style.display = 'block';
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

// Category Selection
function toggleCategory(card) {
    const checkbox = card.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        card.classList.add('selected');
        state.selectedCategories.push(checkbox.value);
    } else {
        card.classList.remove('selected');
        const index = state.selectedCategories.indexOf(checkbox.value);
        if (index > -1) state.selectedCategories.splice(index, 1);
    }
    
    updateStartButtonState();
}

function suggestCategories(suggested) {
    // Auto-select suggested categories
    suggested.forEach(category => {
        const card = document.querySelector(`.category-card[data-category="${category}"]`);
        if (card) {
            const checkbox = card.querySelector('input[type="checkbox"]');
            checkbox.checked = true;
            card.classList.add('selected');
            if (!state.selectedCategories.includes(category)) {
                state.selectedCategories.push(category);
            }
        }
    });
    
    updateStartButtonState();
}

function updateStartButtonState() {
    const startButton = document.getElementById('start-benchmark');
    startButton.disabled = state.selectedCategories.length === 0 || !state.uploadId;
}

function showConfigSection() {
    document.getElementById('config-section').style.display = 'block';
    document.getElementById('config-section').scrollIntoView({ behavior: 'smooth' });
}

// Benchmark Execution
async function startBenchmark() {
    if (state.selectedCategories.length === 0) {
        alert('Please select at least one test category');
        return;
    }
    
    showLoading('Starting benchmark...');
    
    try {
        const requestData = {
            upload_id: state.uploadId,
            filename: state.filename,
            categories: state.selectedCategories,
            data_format: state.fileInfo.format
        };
        
        const response = await axios.post(`${API_URL}/benchmark`, requestData);
        state.benchmarkId = response.data.benchmark_id;
        
        hideLoading();
        showProgressSection();
        connectWebSocket();
        pollBenchmarkStatus();
        
    } catch (error) {
        hideLoading();
        console.error('Benchmark start failed:', error);
        alert('Failed to start benchmark: ' + (error.response?.data?.detail || error.message));
    }
}

function showProgressSection() {
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('progress-section').scrollIntoView({ behavior: 'smooth' });
}

// WebSocket Connection
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${state.benchmarkId}`;
    
    state.websocket = new WebSocket(wsUrl);
    
    state.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    state.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    state.websocket.onclose = () => {
        console.log('WebSocket connection closed');
    };
}

function handleWebSocketMessage(data) {
    if (data.status === 'running') {
        updateProgress(data.message, data.progress_percent || 0);
        if (data.current_test) {
            document.getElementById('current-test').textContent = data.current_test;
        }
    } else if (data.status === 'completed') {
        updateProgress('Benchmark completed!', 100);
        state.results = data.data;
        displayResults(data.data);
    } else if (data.status === 'failed') {
        updateProgress('Benchmark failed: ' + data.message, 0);
        alert('Benchmark failed: ' + data.message);
    }
}

// Progress Polling (fallback if WebSocket fails)
async function pollBenchmarkStatus() {
    const maxAttempts = 120; // 2 minutes max
    let attempts = 0;
    
    const interval = setInterval(async () => {
        attempts++;
        
        try {
            const response = await axios.get(`${API_URL}/benchmark/${state.benchmarkId}/status`);
            const status = response.data.status;
            
            if (status === 'completed') {
                clearInterval(interval);
                const resultsResponse = await axios.get(`${API_URL}/benchmark/${state.benchmarkId}`);
                state.results = resultsResponse.data.results;
                displayResults(resultsResponse.data.results);
            } else if (status === 'failed' || attempts >= maxAttempts) {
                clearInterval(interval);
                alert('Benchmark failed or timed out');
            }
        } catch (error) {
            console.error('Status poll failed:', error);
        }
    }, 1000);
}

function updateProgress(message, percent) {
    document.getElementById('progress-text').textContent = message;
    document.getElementById('progress-percent').textContent = Math.round(percent) + '%';
    document.getElementById('progress-fill').style.width = percent + '%';
}

// Results Display
function displayResults(results) {
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    
    // Display summary
    displaySummary(results.summary);
    
    // Display charts
    displayCharts(results.test_results);
    
    // Display detailed results table
    displayResultsTable(results.test_results);
    
    // Display recommendations
    displayRecommendations(results.summary.recommendations);
}

function displaySummary(summary) {
    // Overall winner
    const avgSpeedup = summary.average_speedup_factor;
    const winner = avgSpeedup > 1.0 ? 'MORK' : 'Neo4j';
    const factor = avgSpeedup > 1.0 ? avgSpeedup : (1 / avgSpeedup);
    
    document.querySelector('#overall-winner .winner-name').textContent = winner;
    document.querySelector('#overall-winner .winner-factor').textContent = 
        `${factor.toFixed(2)}x faster on average`;
    
    // Speed comparison
    document.querySelector('#speed-comparison .metric-value').textContent = 
        avgSpeedup.toFixed(2) + 'x';
    
    // Memory efficiency
    document.querySelector('#memory-comparison .metric-value').textContent = 
        summary.average_memory_efficiency.toFixed(2) + 'x';
    
    // Tests completed
    document.querySelector('#tests-completed .metric-value').textContent = 
        summary.total_tests;
}

function displayCharts(testResults) {
    displayExecutionTimeChart(testResults);
    displayMemoryUsageChart(testResults);
}

function displayExecutionTimeChart(testResults) {
    const ctx = document.getElementById('execution-time-chart').getContext('2d');
    
    const labels = testResults.map(r => r.test_name);
    const morkData = testResults.map(r => r.mork_metrics.execution_time_ms);
    const neo4jData = testResults.map(r => r.neo4j_metrics.execution_time_ms);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'MORK',
                    data: morkData,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Neo4j',
                    data: neo4jData,
                    backgroundColor: 'rgba(118, 75, 162, 0.7)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Execution Time (ms)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} ms`;
                        }
                    }
                }
            }
        }
    });
}

function displayMemoryUsageChart(testResults) {
    const ctx = document.getElementById('memory-usage-chart').getContext('2d');
    
    const labels = testResults.map(r => r.test_name);
    const morkData = testResults.map(r => r.mork_metrics.memory_usage_mb);
    const neo4jData = testResults.map(r => r.neo4j_metrics.memory_usage_mb);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'MORK',
                    data: morkData,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Neo4j',
                    data: neo4jData,
                    backgroundColor: 'rgba(118, 75, 162, 0.7)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Memory Usage (MB)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

function displayResultsTable(testResults) {
    const tbody = document.getElementById('results-table-body');
    tbody.innerHTML = '';
    
    testResults.forEach(result => {
        const row = createResultRow(result);
        tbody.appendChild(row);
    });
}

function createResultRow(result) {
    const row = document.createElement('tr');
    row.dataset.category = result.category;
    
    const speedupClass = result.speedup_factor > 1.0 ? 'speedup-positive' : 'speedup-negative';
    const memoryClass = result.memory_efficiency > 1.0 ? 'speedup-negative' : 'speedup-positive';
    
    row.innerHTML = `
        <td>${formatTestName(result.test_name)}</td>
        <td>${formatCategory(result.category)}</td>
        <td>${result.mork_metrics.execution_time_ms.toFixed(2)}</td>
        <td>${result.neo4j_metrics.execution_time_ms.toFixed(2)}</td>
        <td class="${speedupClass}">${result.speedup_factor.toFixed(2)}x</td>
        <td class="${memoryClass}">${result.memory_efficiency.toFixed(2)}x</td>
        <td class="notes">${result.notes || '-'}</td>
    `;
    
    return row;
}

function formatTestName(name) {
    return name.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatCategory(category) {
    const categoryNames = {
        'knowledge_graphs': '🧠 Knowledge Graphs',
        'graph_algorithms': '🔗 Graph Algorithms',
        'logical_inference': '🧮 Logical Inference'
    };
    return categoryNames[category] || category;
}

function filterResultsTable() {
    const filter = document.getElementById('category-filter').value;
    const rows = document.querySelectorAll('#results-table-body tr');
    
    rows.forEach(row => {
        if (!filter || row.dataset.category === filter) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function displayRecommendations(recommendations) {
    const list = document.getElementById('recommendations-list');
    list.innerHTML = '';
    
    recommendations.forEach(recommendation => {
        const li = document.createElement('li');
        li.textContent = recommendation;
        list.appendChild(li);
    });
}

// Export Functions
function exportResults(format) {
    if (!state.results) {
        alert('No results to export');
        return;
    }
    
    let content, filename, mimeType;
    
    if (format === 'json') {
        content = JSON.stringify(state.results, null, 2);
        filename = `benchmark_results_${state.benchmarkId}.json`;
        mimeType = 'application/json';
    } else if (format === 'csv') {
        content = resultsToCSV(state.results.test_results);
        filename = `benchmark_results_${state.benchmarkId}.csv`;
        mimeType = 'text/csv';
    } else if (format === 'report') {
        content = generateReport(state.results);
        filename = `benchmark_report_${state.benchmarkId}.html`;
        mimeType = 'text/html';
    }
    
    downloadFile(content, filename, mimeType);
}

function resultsToCSV(testResults) {
    const headers = ['Test Name', 'Category', 'MORK Time (ms)', 'Neo4j Time (ms)', 'Speedup Factor', 'Memory Ratio', 'Notes'];
    const rows = testResults.map(r => [
        r.test_name,
        r.category,
        r.mork_metrics.execution_time_ms,
        r.neo4j_metrics.execution_time_ms,
        r.speedup_factor,
        r.memory_efficiency,
        r.notes || ''
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    return csv;
}

function generateReport(results) {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>MORK vs Neo4j Benchmark Report</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; }
        h1 { color: #667eea; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #667eea; color: white; }
        .summary { background: #f8f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>MORK vs Neo4j Performance Comparison Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> ${results.summary.total_tests}</p>
        <p><strong>Average Speedup:</strong> ${results.summary.average_speedup_factor.toFixed(2)}x</p>
        <p><strong>Memory Efficiency:</strong> ${results.summary.average_memory_efficiency.toFixed(2)}x</p>
    </div>
    <table>
        <tr>
            <th>Test</th>
            <th>Category</th>
            <th>MORK (ms)</th>
            <th>Neo4j (ms)</th>
            <th>Speedup</th>
        </tr>
        ${results.test_results.map(r => `
        <tr>
            <td>${r.test_name}</td>
            <td>${r.category}</td>
            <td>${r.mork_metrics.execution_time_ms.toFixed(2)}</td>
            <td>${r.neo4j_metrics.execution_time_ms.toFixed(2)}</td>
            <td style="color: ${r.speedup_factor > 1 ? 'green' : 'red'}">${r.speedup_factor.toFixed(2)}x</td>
        </tr>
        `).join('')}
    </table>
    <div class="summary">
        <h2>Recommendations</h2>
        <ul>
            ${results.summary.recommendations.map(r => `<li>${r}</li>`).join('')}
        </ul>
    </div>
</body>
</html>
    `;
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Example Datasets
async function showExamples() {
    try {
        const response = await axios.get(`${API_URL}/examples`);
        const examples = response.data;
        
        const grid = document.getElementById('examples-grid');
        grid.innerHTML = '';
        
        examples.forEach(example => {
            const card = createExampleCard(example);
            grid.appendChild(card);
        });
        
        document.getElementById('examples-modal').style.display = 'flex';
    } catch (error) {
        console.error('Failed to load examples:', error);
        alert('Failed to load example datasets');
    }
}

function createExampleCard(example) {
    const card = document.createElement('div');
    card.className = 'example-card';
    card.innerHTML = `
        <h4>${example.name}</h4>
        <p>${example.description}</p>
        <div class="example-meta">
            <span>Size: ${example.size}</span>
            <span>Tests: ${example.categories.length}</span>
        </div>
    `;
    
    card.addEventListener('click', () => loadExample(example));
    return card;
}

async function loadExample(example) {
    hideExamples();
    showLoading('Loading example dataset...');
    
    try {
        // Download and use example file
        const response = await axios.get(example.file);
        const blob = new Blob([JSON.stringify(response.data)], { type: 'application/json' });
        const file = new File([blob], example.name.replace(/\s/g, '_') + '.json', { type: 'application/json' });
        
        await uploadFile(file);
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Failed to load example:', error);
        alert('Failed to load example dataset');
    }
}

function hideExamples() {
    document.getElementById('examples-modal').style.display = 'none';
}

// UI Utilities
function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const text = overlay.querySelector('.loading-text');
    text.textContent = message;
    overlay.style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Utility Functions
function formatNumber(num) {
    return num.toLocaleString();
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms.toFixed(2)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
}

// Error Handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});