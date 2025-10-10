# Usage Guide - MORK vs Neo4j Comparison Tool

## Overview

This tool helps you compare MORK and Neo4j performance across different workload types. Upload your data, select benchmark categories, and get detailed performance comparisons with visualizations.

## Quick Start Guide

### Step 1: Launch the Application

```bash
cd comparison-tool
./start.sh
```

Wait for all services to start (usually 10-20 seconds). You'll see:
```
✅ All services started successfully!
📊 Access the comparison tool at: http://localhost:3000
```

### Step 2: Open Web Interface

Navigate to **http://localhost:3000** in your browser.

You should see:
- 🟢 Green status indicators for both MORK and Neo4j (indicating they're connected)
- A file upload section with drag-and-drop area

### Step 3: Upload Your Data

**Option A: Use Your Own Data**

Drag and drop a JSON or CSV file into the upload area, or click to browse files.

**Supported File Formats:**
- **JSON**: Structured data with nodes/edges or people/relationships
- **CSV**: Tabular data with relationship columns

**Option B: Use Example Data**

Click the "📋 Use Example Data" button to select from pre-loaded examples:
- **Family Tree (JSON)**: Knowledge graph testing with family relationships
- **Social Network (CSV)**: Graph algorithm testing with social connections
- **Logic Rules (JSON)**: Logical inference testing with rule-based reasoning

### Step 4: Review File Analysis

After upload, you'll see:
- File information (name, size, format)
- Estimated nodes and relationships
- Sample data preview
- **Suggested benchmark categories** (auto-selected based on your data)

### Step 5: Select Benchmark Categories

Three category types are available:

#### 🧠 Knowledge Graphs
Tests relationship-based queries:
- **Relationship Traversal**: Find direct connections
- **Multi-hop Queries**: Find connections through intermediaries (e.g., aunts, cousins)
- **Property Filtering**: Filter by node attributes
- **Transitive Closure**: Find all descendants/ancestors

**Best for**: Family trees, organizational hierarchies, knowledge bases

#### 🔗 Graph Algorithms
Tests classical graph operations:
- **Clique Detection**: Find fully connected subgroups
- **Shortest Paths**: Distance between nodes
- **Connected Components**: Find isolated subgraphs
- **Centrality Measures**: Identify important nodes

**Best for**: Social networks, network analysis, infrastructure graphs

#### 🧮 Logical Inference
Tests MORK's symbolic AI capabilities:
- **Pattern Matching**: Complex structural queries
- **Rule Application**: If-then logical reasoning
- **Unification**: Variable binding and substitution
- **Constraint Satisfaction**: Find valid solutions

**Best for**: Rule-based systems, logical databases, symbolic reasoning

**Categories are auto-suggested** based on your data structure, but you can select/deselect any category.

### Step 6: Start Benchmark

Click **"🏁 Start Benchmark"** to begin the comparison.

You'll see:
- Real-time progress bar
- Current test being executed
- Percentage completion

Benchmarking typically takes **1-5 minutes** depending on data size and selected categories.

### Step 7: View Results

Results appear automatically when benchmarking completes.

#### Summary Cards
- **Overall Winner**: Which system performed better overall
- **Speed Comparison**: Average speedup factor
- **Memory Efficiency**: Memory usage ratio
- **Tests Completed**: Total number of tests run

#### Performance Charts
- **Execution Time Comparison**: Bar chart showing time for each test
- **Memory Usage Comparison**: Bar chart showing memory consumption

#### Detailed Results Table
Sortable/filterable table showing:
- Test name and category
- MORK execution time (ms)
- Neo4j execution time (ms)
- Speedup factor (>1.0 means MORK is faster)
- Memory efficiency ratio
- Notes explaining results

#### Recommendations
Smart recommendations based on your results:
- When to use MORK vs Neo4j
- Performance optimization tips
- Workload-specific insights

### Step 8: Export Results

Export benchmark results in multiple formats:

**📄 Export JSON**
- Complete benchmark data
- All metrics and raw results
- Machine-readable format

**📊 Export CSV**
- Results table as spreadsheet
- Easy to analyze in Excel/Sheets
- Share with colleagues

**📋 Generate Report**
- Formatted HTML report
- Ready to present to stakeholders
- Includes charts and recommendations

## Understanding the Results

### Speedup Factor

`Speedup Factor = Neo4j Time / MORK Time`

- **> 1.0**: MORK is faster (e.g., 2.0x means MORK is 2× faster)
- **< 1.0**: Neo4j is faster (e.g., 0.5x means Neo4j is 2× faster)
- **≈ 1.0**: Comparable performance

### Memory Efficiency

`Memory Ratio = Neo4j Memory / MORK Memory`

- **> 1.0**: MORK uses less memory (more efficient)
- **< 1.0**: Neo4j uses less memory (more efficient)

### When MORK Typically Excels

✅ **Complex Pattern Matching**: Queries with multiple variables and constraints
✅ **Logical Inference**: Rule-based reasoning and symbolic AI
✅ **Hypergraph Operations**: Relationships with multiple participants
✅ **Large-Scale Transformations**: Bulk data transformations
✅ **Concurrent Operations**: Parallel query processing

### When Neo4j Typically Excels

✅ **Simple Traversals**: Basic relationship following
✅ **Index-Heavy Queries**: When you have many specialized indexes
✅ **ACID Transactions**: When strict transactional guarantees needed
✅ **Standard Graph Algorithms**: Using optimized built-in procedures

## Example Usage Scenarios

### Scenario 1: Evaluating Knowledge Graph Performance

**Your Goal**: Determine if MORK or Neo4j is better for your knowledge base

**Steps**:
1. Export your knowledge graph to JSON format
2. Upload to the tool
3. Select "Knowledge Graphs" category
4. Review results focusing on:
   - Multi-hop query performance
   - Memory usage at scale
   - Transitive closure speed

**What to Look For**:
- If MORK shows >2x speedup on multi-hop queries → Consider MORK
- If memory efficiency is important and MORK uses <50% of Neo4j → MORK advantage
- Check recommendations for your specific query patterns

### Scenario 2: Graph Algorithm Comparison

**Your Goal**: Compare algorithm performance

**Steps**:
1. Upload social network or connectivity data (CSV format works well)
2. Select "Graph Algorithms" category
3. Pay attention to:
   - Clique detection performance
   - Shortest path computation
   - Scalability with data size

**What to Look For**:
- Neo4j often has optimized algorithms via APOC
- MORK may excel with custom/complex algorithm logic
- Consider which operations you run most frequently

### Scenario 3: Symbolic AI Evaluation

**Your Goal**: Test logical reasoning capabilities

**Steps**:
1. Upload rule-based data (logic_rules.json example)
2. Select "Logical Inference" category
3. Focus on:
   - Rule application speed
   - Pattern matching complexity
   - Unification performance

**What to Look For**:
- MORK designed for symbolic AI → expect significant advantages
- Check if your use case needs logical reasoning
- Consider hybrid approach for mixed workloads

## Data Format Guidelines

### JSON Format - Graph Structure

```json
{
  "nodes": [
    {"id": "1", "label": "Person", "name": "Alice", "age": 30},
    {"id": "2", "label": "Person", "name": "Bob", "age": 25}
  ],
  "edges": [
    {"source": "1", "target": "2", "type": "KNOWS", "since": 2020}
  ]
}
```

**Or** alternative format:

```json
{
  "people": [
    {"id": "1", "name": "Alice"},
    {"id": "2", "name": "Bob"}
  ],
  "relationships": [
    {"from": "1", "to": "2", "type": "friend"}
  ]
}
```

### CSV Format - Edge List

```csv
source,target,relationship,weight
Alice,Bob,friend,0.8
Bob,Carol,colleague,0.6
Carol,Dave,friend,0.9
```

**Or** node attributes:

```csv
id,name,type,value
1,Alice,typeA,100
2,Bob,typeB,200
3,Carol,typeA,150
```

## Advanced Features

### Custom Queries (Coming Soon)

Specify your own benchmark queries for both systems to test specific operations.

### Batch Benchmarking (Coming Soon)

Upload multiple files and run comparisons in batch mode.

### Historical Comparison (Coming Soon)

Track performance changes over time with different datasets.

## Tips for Meaningful Comparisons

1. **Use Representative Data**: Upload data similar to your production workload
2. **Test Multiple Sizes**: Try small, medium, and large datasets
3. **Focus on Your Use Case**: Select categories matching your actual needs
4. **Consider Context**: Raw numbers aren't everything—consider ease of use, ecosystem, etc.
5. **Verify Results**: Sample results are shown for validation

## Getting Help

If you encounter issues:

1. **Check Logs**:
   ```bash
   docker-compose logs backend
   docker logs neo4j-benchmark
   ```

2. **Verify Connections**:
   ```bash
   curl http://localhost:8080/api/health
   ```

3. **Review SETUP.md** for troubleshooting steps

4. **Check GitHub Issues** for known problems

## Interpreting for Your Manager

### Creating a Presentation

1. Run benchmarks with your actual data
2. Export the HTML report
3. Key points to highlight:
   - **Overall winner** for your workload type
   - **Specific strengths** of each system
   - **Cost implications** (memory = infrastructure cost)
   - **Scalability** considerations
   - **Use case fit** based on recommendations

### Key Metrics to Emphasize

For technical audiences:
- Execution time comparisons
- Memory efficiency ratios
- Scalability characteristics

For business audiences:
- "X times faster" messaging
- Cost implications of memory usage
- Use case alignment
- Risk mitigation (when one system struggles)

## Next Steps After Benchmarking

1. **MORK Looks Better?**
   - Review MORK documentation
   - Consider pilot project
   - Evaluate integration effort

2. **Neo4j Looks Better?**
   - Stick with proven technology
   - Leverage existing Neo4j tools
   - Maybe revisit MORK for specialized workloads

3. **Mixed Results?**
   - Consider hybrid approach
   - Use each for its strengths
   - Plan for specific use cases

---

**Need more help?** Check the [README.md](README.md) for architecture details or [SETUP.md](SETUP.md) for installation troubleshooting.