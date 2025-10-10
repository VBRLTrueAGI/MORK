# MORK vs Neo4j Performance Comparison Tool

A web-based tool to demonstrate performance differences between MORK and Neo4j across different use cases.

## Features

- **Web Interface**: Upload JSON/CSV data via drag-and-drop
- **Multi-Category Benchmarks**: Knowledge graphs, graph algorithms, logical inference
- **Real-time Comparison**: Side-by-side performance metrics
- **Visual Results**: Interactive charts and detailed analysis

## Quick Start

1. **Prerequisites**:
   - Docker and Docker Compose
   - MORK server binary built (`cargo build --release --bin mork-server`)

2. **Launch**:
   ```bash
   cd comparison-tool
   docker-compose up
   ```

3. **Access**: Open http://localhost:3000 in your browser

## Architecture

- **Frontend**: Modern web interface with Chart.js visualizations
- **Backend**: Python FastAPI orchestrator
- **MORK**: High-performance hypergraph processing
- **Neo4j**: Traditional graph database
- **Benchmarks**: Knowledge graphs, graph algorithms, logical inference

## Benchmark Categories

### Knowledge Graph Operations
- Relationship traversal and querying
- Multi-hop relationship discovery
- Property filtering and matching
- Transitive closure operations

### Graph Algorithms
- Clique detection
- Shortest path algorithms
- Connected components analysis
- Centrality measures

### Logical Inference
- Complex pattern matching
- Unification operations
- Rule-based reasoning
- Constraint satisfaction problems

## Use Cases

Perfect for demonstrating:
- When MORK's symbolic AI excels vs traditional graph operations
- Performance scaling characteristics
- Memory efficiency differences
- Complex query handling capabilities