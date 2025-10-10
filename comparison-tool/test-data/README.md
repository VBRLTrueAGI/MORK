# Test Datasets for MORK vs Neo4j Comparison

## Available Test Datasets

### 1. family-relationships.csv
**Purpose**: Knowledge graph and relationship queries
**Structure**: Family tree with parent, married, and sibling relationships
**Use Cases**:
- Relationship traversal
- Multi-hop queries (grandparents, cousins)
- Family tree analysis

**Columns**: from_person, to_person, relationship_type, since_year

### 2. network-connections.csv
**Purpose**: Social network analysis and graph algorithms
**Structure**: Social connections between people with types and weights
**Use Cases**:
- Triangle detection
- Community detection
- Influence analysis
- Path finding

**Columns**: source, target, connection_type, weight, timestamp

### 3. organizational-hierarchy.csv
**Purpose**: Hierarchical queries and aggregations
**Structure**: Company org chart with reporting relationships
**Use Cases**:
- Reporting chain queries
- Department aggregations
- Salary analysis
- Span of control calculations

**Columns**: employee_id, employee_name, reports_to_id, department, level, salary

### 4. social-network.csv (from backend/examples)
**Purpose**: Simple social network
**Structure**: Basic friend/colleague relationships
**Use Cases**:
- Friend recommendations
- Network clustering
- Degree centrality

**Columns**: source, target, relationship, weight

## How to Use

### In Web Interface (app-standalone.py)
1. Start the app: `python3 app-standalone.py`
2. Open browser to http://localhost:5050
3. Upload any CSV file
4. Click "Run Comparison" to see MORK vs Neo4j performance
5. Or click "Use Built-in Tests" to run pre-configured benchmarks

### Sample Queries You Can Test

**For family-relationships.csv:**
- Find all parents
- Find grandparents (2-hop)
- Find all marriages
- Count relationships per person

**For network-connections.csv:**
- Find triangles (A→B→C→A)
- Find collaboration clusters
- Calculate node centrality
- Find shortest paths

**For organizational-hierarchy.csv:**
- Find all managers
- Calculate reporting chains
- Department hierarchies
- Salary rollups

## Expected Results

MORK typically shows:
- **100-200x faster** on small datasets (< 1000 rows)
- **2-10x faster** on larger datasets  
- **Sub-millisecond** simple queries
- **Millisecond** range for multi-hop and complex queries

Neo4j typically shows:
- **Hundreds of milliseconds** for similar operations
- Good performance with proper indexes
- Slower on cold start / fresh data

## Creating Your Own Test Data

CSV Format for relationships:
```csv
source,target,relationship_type,property1,property2
Alice,Bob,knows,2020,high
Bob,Carol,works_with,2021,medium
```

MORK will convert to:
```
(edge (source Alice) (target Bob) (type knows) (year 2020) (strength high))
```

Neo4j will create:
```cypher
CREATE (a:Node {id: 'Alice'})-[:KNOWS {year: 2020, strength: 'high'}]->(b:Node {id: 'Bob'})