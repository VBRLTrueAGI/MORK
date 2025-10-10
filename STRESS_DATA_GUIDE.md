# Chronic Stress Knowledge Graph in MORK - Quick Guide

## ✅ Current Status

- **MORK Server**: Running on `http://127.0.0.1:8000`
- **Workspace**: `stress`
- **Data Loaded**: 23,997 triples
  - 5,097 entities
  - 6,206 relationships
  - Multiple entity types (concepts, persons, organizations, etc.)

## 🚀 Quick Start

### 1. Query the Data

```bash
cd python
python simple_query.py          # Basic queries
python advanced_queries.py      # Advanced analysis
```

### 2. Visualize the Graph

```bash
pip install matplotlib networkx  # Install dependencies if needed
python visualize_stress_graph.py # Creates PNG visualizations
```

## 📊 What's in the Data

**Entity Types** (top 10):
- 2,960 concepts
- 549 persons
- 252 organizations
- 132 books
- 121 symptoms
- 80 Persons (capitalized)
- 57 locations
- 52 diseases
- Plus 120+ other types!

**Relationship Types** (top 5):
- 560 `related_to`
- 177 `includes`
- 175 `causes`
- 160 `author_of`
- 153 `affects`

**Most Connected Entities**:
1. **Stress** (e4): 112 outgoing connections
2. **COASTER** (e8): 84 connections
3. **Miklashek** (e7): 81 connections
4. **Selye** (e148): 47 connections
5. **Cortisol** (e5): 35 connections

## 🔍 Example Queries

### Basic Pattern Matching

```python
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        
        # Get all entity names
        result = ws.download("(name $id $name)", "$name", max_results=100)
        
        # Get all concepts
        result = ws.download("(type $id concept)", "$id", max_results=50)
        
        # Find connections
        result = ws.download("(edge $source $target $type)", 
                           "($source -> $target)", max_results=100)
        
        # Find what connects TO entity e4 (Stress)
        result = ws.download("(edge $source e4 $type)", "$source", max_results=50)
        
        # Find what connects FROM entity e4 (Stress)
        result = ws.download("(edge e4 $target $type)", "$target", max_results=50)
```

### Advanced Transforms

```python
# Create derived 2-hop paths
ws.transform(
    ("(edge $a $b $type1)", "(edge $b $c $type2)"),
    ("(path2 $a $c)",)
).block()

# Query the new paths
result = ws.download("(path2 $start $end)", "($start => $end)", max_results=100)
```

### Multi-Pattern Queries

```python
# Find entities with both name and description
ws.transform(
    ("(name $id $name)", "(description $id $desc)"),
    ("(full $id $name $desc)",)
).block()
```

## 📈 Visualization Options

### 1. Network Graph (networkx + matplotlib)
```bash
python visualize_stress_graph.py
```
Creates:
- `stress_knowledge_graph.png` - Full graph (first 500 edges)
- `stress_centered_graph.png` - Focused on "Stress" entity

### 2. Export for External Tools

```python
# Export to MeTTa file
ws.sexpr_export_("file:///tmp/stress_data.metta").block()

# Export to .paths format
ws.paths_export_("file:///tmp/stress_data.paths").block()
```

Then use with:
- **Gephi**: Import exported data
- **Cytoscape**: Network analysis
- **D3.js**: Interactive web visualizations

## 🔬 Analysis Examples

### Find Stress-Related Entities
```python
# Get everything connected to Stress (e4)
result = ws.download("(edge e4 $target $type)", "($target $type)", max_results=200)

# Get names for those targets
for target_id in target_ids:
    name = ws.download(f"(name {target_id} $n)", "$n", max_results=1)
```

### Track Concept Relationships
```python
# Find cause-effect chains
ws.transform(
    ("(edge $a $b causes)", "(edge $b $c causes)"),
    ("(causes_chain $a $b $c)",)
).block()
```

### Page Analysis
```python
# Find which pages mention most entities
result = ws.download("(page $id $pagenum)", "$pagenum", max_results=10000)
# Then count frequency
```

## 🎯 Common Use Cases

### 1. Entity Lookup
```python
# Find entity by name
result = ws.download("(name $id \"Cortisol\")", "$id")
entity_id = result.data.strip()

# Get all info about that entity
type_result = ws.download(f"(type {entity_id} $t)", "$t")
desc_result = ws.download(f"(description {entity_id} $d)", "$d")
edges_result = ws.download(f"(edge {entity_id} $target $type)", "($type $target)")
```

### 2. Relationship Exploration
```python
# Find all "causes" relationships
result = ws.download("(edge $s $t causes)", "($s causes $t)", max_results=100)
```

### 3. Subgraph Extraction
```python
# Get neighborhood of an entity (1-hop)
ws.transform(
    ("(edge e4 $n1 $t1)",),
    ("(neighborhood e4 $n1)",)
).block()
```

## 🛠️ Available Scripts

| Script | Purpose |
|--------|---------|
| `upload_persistent.py` | Upload JSON data to MORK |
| `simple_query.py` | Basic query examples |
| `advanced_queries.py` | Complex queries & statistics |
| `visualize_stress_graph.py` | Create graph visualizations |
| `check_workspace.py` | Verify data in workspace |

## 💡 Pro Tips

1. **Start small**: Use `max_results=10` first to understand structure
2. **Use transforms**: Create derived data instead of complex queries
3. **Export often**: Save intermediate results for analysis
4. **Pattern syntax**:
   - `$x` = wildcard variable
   - `"string"` = exact string match
   - `(A B C)` = 3-element expression
5. **Performance**: MORK is fast - queries on 24K triples are instant!

## 🔗 Useful MORK Patterns

```python
# Count items
result = ws.download("(type $id $t)", "$t", max_results=10000)
# Then count in Python

# Find by attribute
result = ws.download("(name $id \"Specific Name\")", "$id")

# Multi-hop paths
ws.transform(
    ("(edge $a $b $t1)", "(edge $b $c $t2)", "(edge $c $d $t3)"),
    ("(path3 $a $d)",)
).block()

# Aggregate relationships
ws.transform(
    ("(edge $source $target $type)",),
    ("(connected $source $target)",)  # Ignores type
).block()
```

## 🎨 Visualization Tips

The generated graphs show:
- **Node size** = degree (number of connections)
- **Blue nodes** = entities
- **Red node** = Stress (in focused graph)
- **Arrows** = directed relationships
- **Labels** = entity names (truncated to 30 chars)

For better visualizations:
- Increase `max_results` in query
- Filter by entity type or relationship type
- Use different layouts: `nx.circular_layout()`, `nx.kamada_kawai_layout()`
- Export to Gephi for professional graphics

## 🆘 Troubleshooting

**No data showing up?**
```bash
python check_workspace.py  # Verify data exists
python upload_persistent.py  # Re-upload if needed
```

**Server not responding?**
```bash
pkill mork-server
./target/release/mork-server &
sleep 2
curl http://127.0.0.1:8000/status/-  # Check status
```

**Queries returning empty?**
- Check pattern syntax: spaces matter!
- Use `$x` not `$X` (case sensitive)
- Verify data structure with `simple_query.py` first

## 📚 Next Steps

1. **Explore**: Try different query patterns
2. **Transform**: Create derived relationships
3. **Visualize**: Generate custom graphs
4. **Analyze**: Find patterns and insights
5. **Export**: Share results in various formats

---

**Questions?** Check the main [README.md](../README.md) or run the example scripts!