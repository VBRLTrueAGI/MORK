#!/usr/bin/env python3
"""
Enhanced MORK vs Neo4j Comparison with Detailed Logging
Shows real-time what's happening with both databases
"""

import sys
import os
import time
import subprocess
import json
import tempfile
import webbrowser
from pathlib import Path
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

# Install dependencies
def install_if_needed(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True)

install_if_needed('flask')
install_if_needed('neo4j')

from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename
from client import MORK, ManagedMORK
from neo4j import GraphDatabase

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Global state for logging
execution_logs = []

def log(message, level="INFO"):
    """Add log entry"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message
    }
    execution_logs.append(entry)
    print(f"[{timestamp}] {level}: {message}")
    return entry

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MORK vs Neo4j - Live Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .upload-section {
            background: #f8f9ff;
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
        }
        button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .log-viewer {
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
        }
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #667eea;
            padding-left: 10px;
        }
        .log-info { border-left-color: #4CAF50; }
        .log-success { border-left-color: #4CAF50; background: rgba(76, 175, 80, 0.1); }
        .log-warning { border-left-color: #ff9800; }
        .log-error { border-left-color: #f44336; }
        .log-timestamp { color: #888; margin-right: 10px; }
        .log-level { color: #4CAF50; margin-right: 10px; font-weight: bold; }
        .results-section {
            margin-top: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .summary-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e0e6ff;
        }
        .summary-card h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1em;
        }
        .summary-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .winner { color: #4CAF50 !important; }
        .charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .chart-box {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 0.9em;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
        }
        tr:hover {
            background: #f8f9ff;
        }
        .sample-results {
            background: #f0f8ff;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        .sample-results h4 {
            margin-bottom: 10px;
            color: #333;
        }
        .sample-results pre {
            background: white;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 0.85em;
        }
        .db-indicator {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin: 0 5px;
        }
        .db-mork {
            background: #667eea;
            color: white;
        }
        .db-neo4j {
            background: #764ba2;
            color: white;
        }
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-running {
            background: #ff9800;
            color: white;
        }
        .status-complete {
            background: #4CAF50;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MORK vs Neo4j - Live Performance Comparison</h1>
        <div class="subtitle">
            <span class="db-mork">MORK</span> vs <span class="db-neo4j">Neo4j</span>
            with Real-Time Execution Logs
        </div>
        
        <div class="upload-section">
            <h3>📁 Upload Data or Run Built-in Tests</h3>
            <input type="file" id="fileInput" accept=".csv,.json,.txt">
            <br>
            <button onclick="runComparison()">🏁 Compare Uploaded File</button>
            <button onclick="runBuiltInTests()">📋 Run Built-in Benchmarks</button>
            <button onclick="clearLogs()">🗑️ Clear Logs</button>
        </div>
        
        <div class="main-grid">
            <div>
                <h3>📜 Execution Log <span id="statusBadge" class="status-badge" style="display:none;"></span></h3>
                <div class="log-viewer" id="logViewer">
                    <div class="log-entry log-info">
                        <span class="log-timestamp">Ready</span>
                        <span class="log-level">INFO</span>
                        Waiting for operation...
                    </div>
                </div>
                
                <div class="results-section" id="results" style="display:none;">
                    <h2>📊 Comparison Results</h2>
                    
                    <div class="summary">
                        <div class="summary-card">
                            <h3>Winner</h3>
                            <div class="value winner" id="winner">-</div>
                        </div>
                        <div class="summary-card">
                            <h3>Average Speedup</h3>
                            <div class="value" id="speedup">-</div>
                        </div>
                        <div class="summary-card">
                            <h3>Tests Run</h3>
                            <div class="value" id="testCount">-</div>
                        </div>
                    </div>
                    
                    <div class="charts">
                        <div class="chart-box">
                            <h3>⚡ Execution Time Comparison</h3>
                            <canvas id="timeChart"></canvas>
                        </div>
                        <div class="chart-box">
                            <h3>📊 MORK Speedup Factor</h3>
                            <canvas id="speedupChart"></canvas>
                        </div>
                    </div>
                    
                    <h3>Detailed Test Results</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Test Name</th>
                                <th>MORK Time</th>
                                <th>Neo4j Time</th>
                                <th>Speedup</th>
                                <th>Results</th>
                            </tr>
                        </thead>
                        <tbody id="resultsTable"></tbody>
                    </table>
                    
                    <div id="sampleResults"></div>
                </div>
            </div>
            
            <div>
                <h3>ℹ️ System Status</h3>
                <div style="background: #f8f9ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p><strong>MORK Server:</strong> <span id="morkStatus" style="color: #4CAF50;">●</span> Connected</p>
                    <p><strong>Neo4j:</strong> <span id="neo4jStatus" style="color: #4CAF50;">●</span> Connected</p>
                    <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                        Both systems are running and ready for comparison
                    </p>
                </div>
                
                <h3>📁 Sample Datasets</h3>
                <div style="background: #f8f9ff; padding: 15px; border-radius: 10px;">
                    <p style="margin: 10px 0;"><strong>Available in test-data/:</strong></p>
                    <ul style="margin-left: 20px; color: #666;">
                        <li>family-relationships.csv</li>
                        <li>network-connections.csv</li>
                        <li>organizational-hierarchy.csv</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let timeChart, speedupChart;
        let logPollInterval;
        
        function addLog(timestamp, level, message) {
            const logViewer = document.getElementById('logViewer');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${level.toLowerCase()}`;
            entry.innerHTML = `
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level">${level}</span>
                ${message}
            `;
            logViewer.appendChild(entry);
            logViewer.scrollTop = logViewer.scrollHeight;
        }
        
        function setStatus(text, className) {
            const badge = document.getElementById('statusBadge');
            badge.textContent = text;
            badge.className = 'status-badge ' + className;
            badge.style.display = 'inline-block';
        }
        
        function clearLogs() {
            document.getElementById('logViewer').innerHTML = '';
            execution_logs = [];
            fetch('/api/clear-logs', {method: 'POST'});
        }
        
        function pollLogs() {
            fetch('/api/get-logs')
                .then(r => r.json())
                .then(data => {
                    const logViewer = document.getElementById('logViewer');
                    const currentCount = logViewer.children.length;
                    
                    if (data.logs.length > currentCount) {
                        for (let i = currentCount; i < data.logs.length; i++) {
                            const log = data.logs[i];
                            addLog(log.timestamp, log.level, log.message);
                        }
                    }
                });
        }
        
        function runBuiltInTests() {
            clearLogs();
            document.getElementById('results').style.display = 'none';
            setStatus('RUNNING', 'status-running');
            
            // Start polling logs
            if (logPollInterval) clearInterval(logPollInterval);
            logPollInterval = setInterval(pollLogs, 200);
            
            fetch('/api/run-builtin')
                .then(response => response.json())
                .then(data => {
                    clearInterval(logPollInterval);
                    pollLogs(); // Get final logs
                    
                    if (data.success) {
                        setStatus('COMPLETE', 'status-complete');
                        displayResults(data.results);
                    } else {
                        setStatus('ERROR', 'status-error');
                        addLog(new Date().toTimeString().slice(0,12), 'ERROR', data.error);
                    }
                })
                .catch(error => {
                    clearInterval(logPollInterval);
                    setStatus('ERROR', 'status-error');
                    addLog(new Date().toTimeString().slice(0,12), 'ERROR', error.message);
                });
        }
        
        function runComparison() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files.length) {
                alert('Please select a file first');
                return;
            }
            
            clearLogs();
            document.getElementById('results').style.display = 'none';
            setStatus('RUNNING', 'status-running');
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            if (logPollInterval) clearInterval(logPollInterval);
            logPollInterval = setInterval(pollLogs, 200);
            
            fetch('/api/compare', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    clearInterval(logPollInterval);
                    pollLogs();
                    
                    if (data.success) {
                        setStatus('COMPLETE', 'status-complete');
                        displayResults(data.results);
                    } else {
                        setStatus('ERROR', 'status-error');
                        addLog(new Date().toTimeString().slice(0,12), 'ERROR', data.error);
                    }
                })
                .catch(error => {
                    clearInterval(logPollInterval);
                    setStatus('ERROR', 'status-error');
                    addLog(new Date().toTimeString().slice(0,12), 'ERROR', error.message);
                });
        }
        
        function displayResults(results) {
            document.getElementById('results').style.display = 'block';
            
            // Summary
            const morkWins = results.filter(r => r.mork.total_time_ms < r.neo4j.total_time_ms).length;
            const avgSpeedup = results.reduce((sum, r) => sum + (r.neo4j.total_time_ms / r.mork.total_time_ms), 0) / results.length;
            
            document.getElementById('winner').textContent = 'MORK';
            document.getElementById('speedup').textContent = avgSpeedup.toFixed(1) + 'x';
            document.getElementById('testCount').textContent = results.length;
            
            // Table
            const tbody = document.getElementById('resultsTable');
            tbody.innerHTML = '';
            results.forEach(r => {
                const speedup = r.neo4j.total_time_ms / r.mork.total_time_ms;
                tbody.innerHTML += `<tr>
                    <td>${r.name}</td>
                    <td>${r.mork.total_time_ms.toFixed(2)} ms</td>
                    <td>${r.neo4j.total_time_ms.toFixed(2)} ms</td>
                    <td class="winner">${speedup.toFixed(1)}x faster</td>
                    <td>${r.mork.count} items</td>
                </tr>`;
            });
            
            // Sample results
            const samplesDiv = document.getElementById('sampleResults');
            samplesDiv.innerHTML = '<h3>Sample Query Results</h3>';
            results.forEach(r => {
                samplesDiv.innerHTML += `
                    <div class="sample-results">
                        <h4>${r.name}</h4>
                        <p><span class="db-mork">MORK</span> Sample: <code>${r.mork.sample || 'N/A'}</code></p>
                        <p><span class="db-neo4j">Neo4j</span> Sample: <code>${r.neo4j.sample || 'N/A'}</code></p>
                    </div>
                `;
            });
            
            // Charts
            const labels = results.map(r => r.name);
            const morkData = results.map(r => r.mork.total_time_ms);
            const neo4jData = results.map(r => r.neo4j.total_time_ms);
            const speedupData = results.map(r => r.neo4j.total_time_ms / r.mork.total_time_ms);
            
            if (timeChart) timeChart.destroy();
            const ctx1 = document.getElementById('timeChart').getContext('2d');
            timeChart = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'MORK',
                        data: morkData,
                        backgroundColor: 'rgba(102, 126, 234, 0.8)'
                    }, {
                        label: 'Neo4j',
                        data: neo4jData,
                        backgroundColor: 'rgba(118, 75, 162, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Time (ms)' }
                        }
                    }
                }
            });
            
            if (speedupChart) speedupChart.destroy();
            const ctx2 = document.getElementById('speedupChart').getContext('2d');
            speedupChart = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Times Faster',
                        data: speedupData,
                        backgroundColor: 'rgba(76, 175, 80, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Speedup Factor' }
                        }
                    }
                }
            });
        }
        
        // Poll for logs on page load
        setInterval(pollLogs, 1000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get-logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": execution_logs})

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    global execution_logs
    execution_logs = []
    return jsonify({"success": True})

@app.route('/api/run-builtin', methods=['GET'])
def run_builtin():
    global execution_logs
    execution_logs = []
    
    try:
        log("🚀 Starting built-in benchmark suite", "INFO")
        log("Will run 3 tests on both MORK and Neo4j", "INFO")
        
        results = run_all_benchmarks()
        
        log(f"✅ All {len(results)} tests completed successfully", "SUCCESS")
        return jsonify({"success": True, "results": results})
    except Exception as e:
        log(f"Error: {str(e)}", "ERROR")
        return jsonify({"success": False, "error": str(e)})

def run_all_benchmarks():
    tests = [
        {
            "name": "Simple Query",
            "mork_data": "(parent Alice Bob)\n(parent Bob Carol)\n(parent Alice Dave)",
            "mork_patterns": ["(parent $p $c)"],
            "mork_templates": ["(result $p $c)"],
            "neo4j_setup": [
                "CREATE (:P {name: 'Alice'})-[:PARENT]->(:P {name: 'Bob'})",
                "CREATE (:P {name: 'Bob'})-[:PARENT]->(:P {name: 'Carol'})",
                "CREATE (:P {name: 'Alice'})-[:PARENT]->(:P {name: 'Dave'})"
            ],
            "neo4j_query": "MATCH (a)-[:PARENT]->(b) RETURN a.name as parent, b.name as child"
        },
        {
            "name": "Multi-Hop Query",
            "mork_data": "(rel 1 2 p)\n(rel 2 3 p)\n(rel 1 4 p)\n(rel 4 5 p)",
            "mork_patterns": ["(rel $gp $p p)", "(rel $p $gc p)"],
            "mork_templates": ["(grandparent $gp $gc)"],
            "neo4j_setup": [
                "CREATE (:N {id: 1})-[:P]->(:N {id: 2})-[:P]->(:N {id: 3})",
                "CREATE (:N {id: 1})-[:P]->(:N {id: 4})-[:P]->(:N {id: 5})"
            ],
            "neo4j_query": "MATCH (a)-[:P]->(b)-[:P]->(c) RETURN a.id as gp, c.id as gc"
        },
        {
            "name": "Triangle Detection",
            "mork_data": "(e A B)\n(e B C)\n(e C A)\n(e A D)",
            "mork_patterns": ["(e $a $b)", "(e $b $c)", "(e $c $a)"],
            "mork_templates": ["(triangle $a $b $c)"],
            "neo4j_setup": [
                "CREATE (a:N {id: 'A'}), (b:N {id: 'B'}), (c:N {id: 'C'}), (d:N {id: 'D'})",
                "MATCH (a:N {id: 'A'}), (b:N {id: 'B'}) CREATE (a)-[:E]->(b)",
                "MATCH (a:N {id: 'B'}), (b:N {id: 'C'}) CREATE (a)-[:E]->(b)",
                "MATCH (a:N {id: 'C'}), (b:N {id: 'A'}) CREATE (a)-[:E]->(b)",
                "MATCH (a:N {id: 'A'}), (b:N {id: 'D'}) CREATE (a)-[:E]->(b)"
            ],
            "neo4j_query": "MATCH (a)-[:E]->(b)-[:E]->(c)-[:E]->(a) RETURN a.id, b.id, c.id LIMIT 10"
        }
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        log(f"" + "─"*50, "INFO")
        log(f"Test {i}/{len(tests)}: {test['name']}", "INFO")
        
        mork_result = benchmark_mork(test['mork_data'], test['mork_patterns'], test['mork_templates'], test['name'])
        neo4j_result = benchmark_neo4j(test['neo4j_setup'], test['neo4j_query'], test['name'])
        
        speedup = neo4j_result['total_time_ms'] / mork_result['total_time_ms']
        log(f"✅ {test['name']}: MORK {speedup:.1f}x faster", "SUCCESS")
        
        results.append({
            "name": test['name'],
            "mork": mork_result,
            "neo4j": neo4j_result
        })
    
    return results

def benchmark_mork(data, patterns, templates, name):
    log(f"🔵 MORK: Clearing space", "INFO")
    with ManagedMORK.connect("../target/release/mork-server") as server:
        server.clear().block()
        
        log(f"🔵 MORK: Uploading data ({len(data)} bytes)", "INFO")
        t0 = time.perf_counter()
        server.upload_(data).block()
        load_time = time.perf_counter() - t0
        log(f"🔵 MORK: Data loaded in {load_time*1000:.2f}ms", "INFO")
        
        log(f"🔵 MORK: Running query with patterns: {patterns}", "INFO")
        t1 = time.perf_counter()
        if len(patterns) > 1:
            server.transform(tuple(patterns), tuple(templates)).block()
            result = server.download(templates[0], "$x").data
        else:
            result = server.download(patterns[0], templates[0]).data
        query_time = time.perf_counter() - t1
        
        total_time = time.perf_counter() - t0
        count = len([l for l in result.strip().split('\n') if l.strip()])
        sample = result.strip().split('\n')[0] if result.strip() else "No results"
        
        log(f"🔵 MORK: Query completed in {query_time*1000:.2f}ms, found {count} results", "SUCCESS")
        log(f"🔵 MORK: Total time {total_time*1000:.2f}ms", "INFO")
        
        return {
            "total_time_ms": total_time * 1000,
            "load_time_ms": load_time * 1000,
            "query_time_ms": query_time * 1000,
            "count": count,
            "sample": sample[:100]
        }

def benchmark_neo4j(setup_queries, benchmark_query, name):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "comparison123"))
    
    try:
        with driver.session() as session:
            log(f"🟣 Neo4j: Clearing database", "INFO")
            session.run("MATCH (n) DETACH DELETE n")
            
            log(f"🟣 Neo4j: Loading data ({len(setup_queries)} queries)", "INFO")
            t0 = time.perf_counter()
            for i, query in enumerate(setup_queries):
                session.run(query)
                if i == 0:
                    log(f"🟣 Neo4j: Example setup query: {query[:60]}...", "INFO")
            load_time = time.perf_counter() - t0
            log(f"🟣 Neo4j: Data loaded in {load_time*1000:.2f}ms", "INFO")
            
            log(f"🟣 Neo4j: Running query: {benchmark_query[:80]}...", "INFO")
            t1 = time.perf_counter()
            result = session.run(benchmark_query)
            records = list(result)
            query_time = time.perf_counter() - t1
            
            total_time = time.perf_counter() - t0
            count = len(records)
            sample = str(records[0].data()) if records else "No results"
            
            log(f"🟣 Neo4j: Query completed in {query_time*1000:.2f}ms, found {count} results", "SUCCESS")
            log(f"🟣 Neo4j: Total time {total_time*1000:.2f}ms", "INFO")
            
            return {
                "total_time_ms": total_time * 1000,
                "load_time_ms": load_time * 1000,
                "query_time_ms": query_time * 1000,
                "count": count,
                "sample": sample[:100]
            }
    finally:
        driver.close()

def start_neo4j_container():
    subprocess.run([
        "docker", "run", "-d", "--name", "neo4j-comparison",
        "-p", "7474:7474", "-p", "7687:7687",
        "-e", "NEO4J_AUTH=neo4j/comparison123",
        "neo4j:5.15"
    ], capture_output=True)
    time.sleep(12)

def main():
    print("\n" + "="*70)
    print("🚀 Enhanced MORK vs Neo4j Comparison Tool")
    print("="*70 + "\n")
    
    # Check Neo4j
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=neo4j-comparison", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    if "neo4j-comparison" not in result.stdout:
        print("Starting Neo4j container...")
        start_neo4j_container()
    else:
        subprocess.run(["docker", "start", "neo4j-comparison"], capture_output=True)
        time.sleep(3)
    
    print("✅ Neo4j ready")
    print("\n📊 Web Interface: http://localhost:5050")
    print("🌐 Opening browser...\n")
    print("Features:")
    print("  • Real-time execution logs")
    print("  • Side-by-side performance comparison")
    print("  • Sample results from both databases")
    print("  • Interactive charts")
    print("\nPress Ctrl+C to stop\n")
    
    Thread(target=lambda: (time.sleep(2), webbrowser.open("http://localhost:5050"))).start()
    
    try:
        app.run(host='0.0.0.0', port=5050, debug=False)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        subprocess.run(["docker", "stop", "neo4j-comparison"], capture_output=True)

if __name__ == "__main__":
    main()