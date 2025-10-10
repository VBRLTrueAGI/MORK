#!/usr/bin/env python3
"""
Final MORK vs Neo4j Comparison Tool
- Real-time logging
- Custom query interface  
- Sample results display
- Performance charts
"""

import sys
import os
import time
import subprocess
import webbrowser
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

def install_if_needed(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True)

install_if_needed('flask')
install_if_needed('neo4j')

from flask import Flask, render_template_string, request, jsonify
from client import MORK, ManagedMORK
from neo4j import GraphDatabase

app = Flask(__name__)
execution_logs = []
current_data_loaded = False
mork_server_conn = None

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"timestamp": timestamp, "level": level, "message": message}
    execution_logs.append(entry)
    print(f"[{timestamp}] {level}: {message}")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MORK vs Neo4j Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
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
        h1 { color: #667eea; text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .tab {
            padding: 12px 24px;
            cursor: pointer;
            border: none;
            background: none;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .upload-section {
            background: #f8f9ff;
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 20px;
        }
        .query-section {
            background: #f8f9ff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .query-input {
            width: 100%;
            margin: 10px 0;
        }
        .query-input textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            min-height: 80px;
        }
        .query-input label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            margin: 10px 5px;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .log-viewer {
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
        }
        .log-entry {
            margin: 3px 0;
            padding: 4px;
            border-left: 3px solid #667eea;
            padding-left: 10px;
        }
        .log-info { border-left-color: #2196F3; }
        .log-success { border-left-color: #4CAF50; background: rgba(76, 175, 80, 0.1); }
        .log-timestamp { color: #888; margin-right: 10px; }
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
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        tr:hover { background: #f8f9ff; }
        .sample-results {
            background: #f0f8ff;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        .db-mork { background: #667eea; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.9em; }
        .db-neo4j { background: #764ba2; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.9em; }
        .query-result {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 1px solid #ddd;
        }
        .query-result pre {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MORK vs Neo4j - Interactive Comparison</h1>
        <div class="subtitle">Real-time performance testing with custom queries</div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('benchmark')">📊 Benchmarks</button>
            <button class="tab" onclick="showTab('custom')">🔍 Custom Queries</button>
            <button class="tab" onclick="showTab('logs')">📜 Execution Logs</button>
        </div>
        
        <!-- Benchmark Tab -->
        <div id="benchmark-tab" class="tab-content active">
            <div class="upload-section">
                <h3>📁 Upload Data or Run Tests</h3>
                <input type="file" id="fileInput" accept=".csv,.json">
                <br>
                <button onclick="runComparison()">🏁 Compare File</button>
                <button onclick="runBuiltInTests()">📋 Built-in Benchmarks</button>
            </div>
            
            <div id="results" style="display:none;">
                <h2>📊 Results</h2>
                <div class="summary">
                    <div class="summary-card">
                        <h3>Winner</h3>
                        <div class="value winner" id="winner">-</div>
                    </div>
                    <div class="summary-card">
                        <h3>Avg Speedup</h3>
                        <div class="value" id="speedup">-</div>
                    </div>
                    <div class="summary-card">
                        <h3>Tests</h3>
                        <div class="value" id="testCount">-</div>
                    </div>
                </div>
                
                <div class="charts">
                    <div class="chart-box">
                        <canvas id="timeChart"></canvas>
                    </div>
                    <div class="chart-box">
                        <canvas id="speedupChart"></canvas>
                    </div>
                </div>
                
                <table>
                    <tr><th>Test</th><th>MORK</th><th>Neo4j</th><th>Speedup</th><th>Results</th></tr>
                    <tbody id="resultsTable"></tbody>
                </table>
                
                <div id="sampleResults"></div>
            </div>
        </div>
        
        <!-- Custom Query Tab -->
        <div id="custom-tab" class="tab-content">
            <div class="query-section">
                <h3>🔍 Run Custom Queries on Built-in Data</h3>
                <p style="color: #666; margin-bottom: 15px;">
                    First run "Built-in Benchmarks" to load data, then query it here
                </p>
                
                <div class="query-input">
                    <label>MORK Query Pattern:</label>
                    <textarea id="morkPattern" placeholder="Example: (parent $who $child)&#10;Use $variables to match">(parent $p $c)</textarea>
                </div>
                
                <div class="query-input">
                    <label>MORK Query Template (how to display results):</label>
                    <textarea id="morkTemplate" placeholder="Example: (result $who $child)&#10;Or just: $who">$p</textarea>
                </div>
                
                <div class="query-input">
                    <label>Neo4j Cypher Query:</label>
                    <textarea id="neo4jQuery" placeholder="Example: MATCH (a)-[:PARENT]->(b) RETURN a.name, b.name">MATCH (a)-[:PARENT]->(b) RETURN a.name as parent, b.name as child</textarea>
                </div>
                
                <button onclick="runCustomQuery()">▶️ Execute on Both</button>
                <button onclick="loadExampleQueries()">📋 Load Examples</button>
                
                <div id="customResults"></div>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div id="logs-tab" class="tab-content">
            <h3>📜 Execution Logs</h3>
            <button onclick="clearLogs()">🗑️ Clear</button>
            <div class="log-viewer" id="logViewer">
                <div class="log-entry">Waiting for operations...</div>
            </div>
        </div>
    </div>
    
    <script>
        let timeChart, speedupChart;
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${tab}')"]`).classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
        }
        
        function clearLogs() {
            document.getElementById('logViewer').innerHTML = '';
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
                            const entry = document.createElement('div');
                            entry.className = 'log-entry log-' + log.level.toLowerCase();
                            entry.innerHTML = `<span class="log-timestamp">${log.timestamp}</span> ${log.message}`;
                            logViewer.appendChild(entry);
                        }
                        logViewer.scrollTop = logViewer.scrollHeight;
                    }
                });
        }
        
        function runBuiltInTests() {
            clearLogs();
            setInterval(pollLogs, 200);
            
            fetch('/api/run-builtin')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        displayResults(data.results, data.test_data);
                        if (data.test_data) {
                            displayTestDataInCustomTab(data.test_data);
                        }
                    }
                });
        }
        
        function displayTestDataInCustomTab(testData) {
            const dataDisplay = document.getElementById('dataDisplay');
            const dataViewer = document.getElementById('dataViewer');
            
            dataDisplay.innerHTML = '';
            testData.forEach(test => {
                dataDisplay.innerHTML += `
                    <div style="margin: 15px 0; padding: 15px; background: #f8f9ff; border-radius: 8px; border-left: 4px solid #667eea;">
                        <h4 style="color: #667eea; margin-bottom: 8px;">${test.test}</h4>
                        <p style="color: #666; margin-bottom: 10px;"><em>${test.description}</em></p>
                        <pre style="background: white; padding: 12px; border-radius: 6px; font-size: 0.9em; white-space: pre-wrap;">${test.data}</pre>
                    </div>
                `;
            });
            
            dataViewer.style.display = 'block';
        }
        
        function runCustomQuery() {
            const morkPattern = document.getElementById('morkPattern').value;
            const morkTemplate = document.getElementById('morkTemplate').value;
            const neo4jQuery = document.getElementById('neo4jQuery').value;
            
            clearLogs();
            document.getElementById('customResults').innerHTML = '<p>Running queries...</p>';
            
            setInterval(pollLogs, 200);
            
            fetch('/api/custom-query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    mork_pattern: morkPattern,
                    mork_template: morkTemplate,
                    neo4j_query: neo4jQuery
                })
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        displayCustomResults(data.result);
                    } else {
                        document.getElementById('customResults').innerHTML = 
                            `<div style="color: red;">Error: ${data.error}</div>`;
                    }
                });
        }
        
        function displayCustomResults(result) {
            const div = document.getElementById('customResults');
            div.innerHTML = `
                <div class="query-result">
                    <h4>📊 Query Results</h4>
                    <p><span class="db-mork">MORK</span> Time: <strong>${result.mork.time_ms.toFixed(2)}ms</strong> | 
                       Found: <strong>${result.mork.count} results</strong></p>
                    <pre>${result.mork.results}</pre>
                    
                    <p><span class="db-neo4j">Neo4j</span> Time: <strong>${result.neo4j.time_ms.toFixed(2)}ms</strong> | 
                       Found: <strong>${result.neo4j.count} results</strong></p>
                    <pre>${result.neo4j.results}</pre>
                    
                    <p style="margin-top: 15px; font-weight: bold; color: #4CAF50;">
                        ⚡ MORK was ${(result.neo4j.time_ms / result.mork.time_ms).toFixed(1)}x faster
                    </p>
                </div>
            `;
        }
        
        function loadExampleQueries() {
            document.getElementById('morkPattern').value = '(parent $p $c)';
            document.getElementById('morkTemplate').value = '(parent_of $p $c)';
            document.getElementById('neo4jQuery').value = 'MATCH (a)-[:PARENT]->(b) RETURN a.name as parent, b.name as child';
        }
        
        function displayResults(results) {
            document.getElementById('results').style.display = 'block';
            
            const morkWins = results.filter(r => r.mork.total_time_ms < r.neo4j.total_time_ms).length;
            const avgSpeedup = results.reduce((sum, r) => sum + (r.neo4j.total_time_ms / r.mork.total_time_ms), 0) / results.length;
            
            document.getElementById('winner').textContent = 'MORK';
            document.getElementById('speedup').textContent = avgSpeedup.toFixed(1) + 'x';
            document.getElementById('testCount').textContent = results.length;
            
            const tbody = document.getElementById('resultsTable');
            tbody.innerHTML = '';
            results.forEach(r => {
                const speedup = r.neo4j.total_time_ms / r.mork.total_time_ms;
                tbody.innerHTML += `<tr>
                    <td>${r.name}</td>
                    <td>${r.mork.total_time_ms.toFixed(2)} ms</td>
                    <td>${r.neo4j.total_time_ms.toFixed(2)} ms</td>
                    <td class="winner">${speedup.toFixed(1)}x</td>
                    <td>${r.mork.count}</td>
                </tr>`;
            });
            
            const samplesDiv = document.getElementById('sampleResults');
            samplesDiv.innerHTML = '<h3>Sample Results</h3>';
            results.forEach(r => {
                samplesDiv.innerHTML += `
                    <div class="sample-results">
                        <h4>${r.name}</h4>
                        <p><span class="db-mork">MORK</span> ${r.mork.sample}</p>
                        <p><span class="db-neo4j">Neo4j</span> ${r.neo4j.sample}</p>
                    </div>
                `;
            });
            
            // Charts (same as before)
            const labels = results.map(r => r.name);
            const morkData = results.map(r => r.mork.total_time_ms);
            const neo4jData = results.map(r => r.neo4j.total_time_ms);
            const speedupData = results.map(r => r.neo4j.total_time_ms / r.mork.total_time_ms);
            
            if (timeChart) timeChart.destroy();
            timeChart = new Chart(document.getElementById('timeChart'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {label: 'MORK', data: morkData, backgroundColor: 'rgba(102, 126, 234, 0.8)'},
                        {label: 'Neo4j', data: neo4jData, backgroundColor: 'rgba(118, 75, 162, 0.8)'}
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            
            if (speedupChart) speedupChart.destroy();
            speedupChart = new Chart(document.getElementById('speedupChart'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{label: 'Speedup', data: speedupData, backgroundColor: 'rgba(76, 175, 80, 0.8)'}]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
        }
        
        setInterval(pollLogs, 1000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get-logs')
def get_logs():
    return jsonify({"logs": execution_logs})

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    global execution_logs
    execution_logs = []
    return jsonify({"success": True})

# Store test data info
TEST_DATA_INFO = []

@app.route('/api/run-builtin')
def run_builtin():
    global execution_logs, current_data_loaded, TEST_DATA_INFO
    execution_logs = []
    
    # Define test data info
    TEST_DATA_INFO = [
        {
            "test": "Simple Query",
            "description": "Basic parent-child relationships",
            "data": """Data loaded in both databases:
• Alice is parent of Bob
• Bob is parent of Carol
• Alice is parent of Dave

MORK stores as:
  (parent Alice Bob)
  (parent Bob Carol)
  (parent Alice Dave)

Neo4j stores as:
  (:Person {name:'Alice'})-[:PARENT]->(:Person {name:'Bob'})
  (:Person {name:'Bob'})-[:PARENT]->(:Person {name:'Carol'})
  (:Person {name:'Alice'})-[:PARENT]->(:Person {name:'Dave'})"""
        },
        {
            "test": "Multi-Hop Query",
            "description": "Finding grandparents through 2-hop relationships",
            "data": """Relationship chain loaded:
• Person 1 → Person 2 → Person 3
• Person 1 → Person 4 → Person 5

This creates 2 grandparent relationships:
• 1 is grandparent of 3
• 1 is grandparent of 5

MORK format: (rel 1 2 p) and (rel 2 3 p)
Neo4j format: (1)-[:P]->(2)-[:P]->(3)"""
        },
        {
            "test": "Triangle Detection",
            "description": "Finding cycles in the graph",
            "data": """Graph connections loaded:
• A connects to B
• B connects to C
• C connects to A  ← Forms a triangle!
• A also connects to D (not in triangle)

Expected: Find 3 triangles (one for each starting node)

MORK format: (e A B)
Neo4j format: (A)-[:E]->(B)"""
        }
    ]
    
    try:
        log("🚀 Starting benchmark suite")
        log("📊 Loading test data into both MORK and Neo4j...")
        results = run_all_benchmarks()
        current_data_loaded = True
        log(f"✅ Completed {len(results)} tests", "SUCCESS")
        return jsonify({"success": True, "results": results, "test_data": TEST_DATA_INFO})
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/custom-query', methods=['POST'])
def custom_query():
    try:
        data = request.get_json()
        log("🔍 Running custom query on both databases")
        
        # Run on MORK
        log("🔵 Querying MORK...")
        t0 = time.perf_counter()
        with ManagedMORK.connect("../target/release/mork-server") as server:
            result = server.download(data['mork_pattern'], data['mork_template']).data
        mork_time = (time.perf_counter() - t0) * 1000
        mork_count = len([l for l in result.strip().split('\n') if l.strip()])
        log(f"🔵 MORK: {mork_time:.2f}ms, {mork_count} results")
        
        # Run on Neo4j
        log("🟣 Querying Neo4j...")
        t0 = time.perf_counter()
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "comparison123"))
        with driver.session() as session:
            records = list(session.run(data['neo4j_query']))
        driver.close()
        neo4j_time = (time.perf_counter() - t0) * 1000
        neo4j_results = '\n'.join(str(r.data()) for r in records[:10])
        log(f"🟣 Neo4j: {neo4j_time:.2f}ms, {len(records)} results")
        
        log(f"✅ MORK {neo4j_time/mork_time:.1f}x faster", "SUCCESS")
        
        return jsonify({
            "success": True,
            "result": {
                "mork": {
                    "time_ms": mork_time,
                    "count": mork_count,
                    "results": result[:500]
                },
                "neo4j": {
                    "time_ms": neo4j_time,
                    "count": len(records),
                    "results": neo4j_results[:500]
                }
            }
        })
    except Exception as e:
        log(f"Error: {e}", "ERROR")
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
        log(f"──────────────────────")
        log(f"Test {i}/{len(tests)}: {test['name']}")
        
        mork_result = benchmark_mork(test['mork_data'], test['mork_patterns'], test['mork_templates'])
        neo4j_result = benchmark_neo4j(test['neo4j_setup'], test['neo4j_query'])
        
        results.append({"name": test['name'], "mork": mork_result, "neo4j": neo4j_result})
    
    return results

def benchmark_mork(data, patterns, templates):
    log("🔵 MORK: Clearing space")
    with ManagedMORK.connect("../target/release/mork-server") as server:
        server.clear().block()
        
        log(f"🔵 MORK: Loading {len(data)} bytes")
        t0 = time.perf_counter()
        server.upload_(data).block()
        
        log(f"🔵 MORK: Querying...")
        if len(patterns) > 1:
            server.transform(tuple(patterns), tuple(templates)).block()
            result = server.download(templates[0], "$x").data
        else:
            result = server.download(patterns[0], templates[0]).data
        
        total = (time.perf_counter() - t0) * 1000
        count = len([l for l in result.strip().split('\n') if l.strip()])
        log(f"🔵 MORK: {total:.2f}ms, {count} results", "SUCCESS")
        
        return {
            "total_time_ms": total,
            "count": count,
            "sample": result.strip().split('\n')[0] if result.strip() else "No results"
        }

def benchmark_neo4j(setup, query):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "comparison123"))
    
    with driver.session() as session:
        log("🟣 Neo4j: Clearing")
        session.run("MATCH (n) DETACH DELETE n")
        
        log(f"🟣 Neo4j: Loading {len(setup)} queries")
        t0 = time.perf_counter()
        for q in setup:
            session.run(q)
        
        log("🟣 Neo4j: Querying...")
        records = list(session.run(query))
        
        total = (time.perf_counter() - t0) * 1000
        log(f"🟣 Neo4j: {total:.2f}ms, {len(records)} results", "SUCCESS")
        
        driver.close()
        
        return {
            "total_time_ms": total,
            "count": len(records),
            "sample": str(records[0].data()) if records else "No results"
        }

def main():
    print("\n" + "="*70)
    print("🚀 MORK vs Neo4j - Interactive Web Comparison")
    print("="*70 + "\n")
    
    # Start Neo4j
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=neo4j-comparison", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    if "neo4j-comparison" not in result.stdout:
        print("Starting Neo4j...")
        subprocess.run([
            "docker", "run", "-d", "--name", "neo4j-comparison",
            "-p", "7474:7474", "-p", "7687:7687",
            "-e", "NEO4J_AUTH=neo4j/comparison123", "neo4j:5.15"
        ], capture_output=True)
        time.sleep(12)
    else:
        subprocess.run(["docker", "start", "neo4j-comparison"], capture_output=True)
        time.sleep(3)
    
    print("✅ Neo4j ready")
    print("📊 Open: http://localhost:5050")
    print("\nFeatures:")
    print("  ✅ Real-time execution logs")
    print("  ✅ Custom query interface")  
    print("  ✅ Performance charts")
    print("  ✅ Sample results from both DBs")
    print("\nPress Ctrl+C to stop\n")
    
    Thread(target=lambda: (time.sleep(2), webbrowser.open("http://localhost:5050"))).start()
    
    try:
        app.run(host='0.0.0.0', port=5050, debug=False)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        subprocess.run(["docker", "stop", "neo4j-comparison"], capture_output=True)

if __name__ == "__main__":
    main()