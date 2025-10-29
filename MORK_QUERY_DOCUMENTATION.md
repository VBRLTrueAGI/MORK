# MORK Query Documentation

Complete guide to querying MORK (MeTTa Optimal Reduction Kernel) with all variants and patterns.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Query Methods](#core-query-methods)
3. [Pattern Matching Syntax](#pattern-matching-syntax)
4. [Query Variants](#query-variants)
5. [Transform Operations](#transform-operations)
6. [Advanced Query Patterns](#advanced-query-patterns)
7. [Data Loading & Export](#data-loading--export)
8. [Namespace Management](#namespace-management)
9. [Practical Examples](#practical-examples)
10. [Performance Tips](#performance-tips)

---

## Introduction

**MORK** is a blazing-fast hypergraph processing kernel for symbolic AI at scale. It's built on PathMap (a trie-based data structure) and runs as an HTTP server with Python client API.

**Key Features:**
- 199x faster than Neo4j on simple queries, 134x on multi-hop queries
- S-expression based pattern matching
- Knowledge inference through transforms
- Namespace-scoped operations
- Multiple data format support (MeTTa, CSV, JSON, Paths)

---

## Core Query Methods

### 1. `download(pattern, template, max_results=None)`

The primary method for querying data from MORK.

**Parameters:**
- `pattern`: S-expression pattern with variables (`$x`, `$id`, etc.)
- `template`: Output format template using captured variables
- `max_results`: Optional limit on returned results

**Basic Usage:**

```python
from MORK.python.client import MORK

# Connect to MORK server
server = MORK()
with server.work_at("my-workspace") as ws:

    # Get all data (limited)
    result = ws.download("$x", "$x", max_results=20)

    # Match specific patterns
    result = ws.download("(type $id concept)", "$id")

    # Extract with custom formatting
    result = ws.download("(name $id $name)", "$name")
    result = ws.download("(edge $source $target $type)", "($source -> $target)")
```

---

### 2. `query(patterns, project=None, unit=None, target="{}", ortho=False)`

Higher-level query abstraction with auto-generated templates.

**Parameters:**
- `patterns`: List of pattern strings or single pattern
- `project`: Variables to project into results
- `unit`: Unit expression to write out
- `ortho`: Write each variable to its own expression
- `target`: Namespace to write results to

**Usage:**

```python
# Simple query with projection
ws.query(
    patterns="(edge $a $b $type)",
    project=["$a", "$b"]
)

# Multi-pattern query
ws.query(
    patterns=["(type $id concept)", "(name $id $name)"],
    project=["$id", "$name"]
)
```

---

### 3. `transform(patterns, templates)`

**The most powerful feature** - pattern matching with knowledge inference.

**Parameters:**
- `patterns`: Tuple of pattern strings to match simultaneously
- `templates`: Tuple of template strings to materialize from matches

**Basic Transform:**

```python
# Create derived facts from existing data
ws.transform(
    patterns=("(edge $a $b type1)", "(edge $b $c type2)"),
    templates=("(indirect_path $a $c)",)
).block()
```

**Multi-Pattern Transform:**

```python
# Infer parent relationships
ws.transform(
    patterns=("(parent $pid $cid)", "(female $pid)"),
    templates=("(mother $pid $cid)",)
).block()

# Complex multi-pattern inference
ws.transform(
    patterns=(
        "(parent $pid $cid0)",
        "(parent $pid $cid1)",
        "(isIdDifferent $cid0 $cid1)",
        "(female $cid0)"
    ),
    templates=("(sister $cid0 $cid1)",)
).block()
```

---

## Pattern Matching Syntax

### Variables

**Named Variables:** Start with `$`
```python
"$x"           # Match anything, bind to variable x
"$id"          # Match anything, bind to variable id
"$name"        # Match anything, bind to variable name
"$source"      # Match anything, bind to variable source
```

**Anonymous Variables:** Use `_`
```python
"_"            # Match anything, don't capture
"(edge _ $target _)"  # Only care about target
```

**De Bruijn Indexed Variables:** `_1`, `_2`, `_3`
- Used in templates for positional reference
- Rarely needed in modern MORK usage

---

### Pattern Structures

**Simple Patterns:**

```python
# Match 2-element expression
"($a $b)"

# Match 3-element expression
"($a $b $c)"

# Match specific structure
"(type $entity $typename)"
"(name $entity $name)"
"(edge $source $target $reltype)"
```

**Nested Patterns:**

```python
# Complex nested structures
"(src (Individuals $i (Id $id)))"
"(src (Individuals $i (Fullname $name)))"

# Hierarchical patterns
"(namespace (entity $id (property $value)))"
```

**Literal Matching:**

```python
# Match exact values (use quotes)
'(name $id "Cortisol")'      # Find entity named "Cortisol"
'(type $id "biological")'    # Find entities of type "biological"

# Match partial structure with literals
'(edge $source "e4" $reltype)'  # Edges ending at e4
```

---

## Query Variants

### 1. Basic Pattern Matching

**Get all entities:**
```python
ws.download("$x", "$x", max_results=100)
```

**Find entities by type:**
```python
ws.download("(type $id concept)", "$id")
ws.download("(type $id biological)", "$id")
```

**Get entity attributes:**
```python
# Get names
ws.download("(name $id $name)", "$name")

# Get descriptions
ws.download("(description $id $desc)", "$desc")

# Get multiple attributes with formatting
ws.download("(name $id $name)", "($id : $name)")
```

---

### 2. Relationship Queries

**Find all edges:**
```python
ws.download("(edge $s $t $type)", "($s -> $t)")
```

**Find outgoing edges from entity:**
```python
ws.download("(edge e4 $target $reltype)", "($target via $reltype)")
```

**Find incoming edges to entity:**
```python
ws.download("(edge $source e4 $reltype)", "($source via $reltype)")
```

**Filter by relationship type:**
```python
ws.download('(edge $s $t "influences")', "($s -> $t)")
ws.download('(edge $s $t "characterizes")', "($s -> $t)")
```

---

### 3. Multi-Pattern Queries

Match multiple patterns simultaneously:

```python
# Entity with type AND name
patterns = [
    "(type $id biological)",
    "(name $id $name)"
]
# Use query() or transform() for multi-pattern matching
```

**Intersection Queries:**
```python
# Find entities that are BOTH biological AND have descriptions
ws.transform(
    patterns=(
        "(type $id biological)",
        "(description $id $desc)"
    ),
    templates=("(bio_with_desc $id $desc)",)
).block()

result = ws.download("(bio_with_desc $id $desc)", "($id: $desc)")
```

---

### 4. Graph Traversal Queries

**Direct neighbors:**
```python
# 1-hop from entity
ws.download("(edge START_ID $neighbor $type)", "$neighbor")
```

**2-hop paths:**
```python
# First create 2-hop inference
ws.transform(
    patterns=("(edge $a $b $type1)", "(edge $b $c $type2)"),
    templates=("(path2 $a $c $b)",)
).block()

# Then query the paths
ws.download("(path2 START_ID $end $via)", "($end via $via)")
```

**Multi-hop path finding:**
```python
# Create 3-hop paths
ws.transform(
    patterns=(
        "(edge $a $b $t1)",
        "(edge $b $c $t2)",
        "(edge $c $d $t3)"
    ),
    templates=("(path3 $a $d ($b $c))",)
).block()
```

---

### 5. Search and Filter Queries

**Find by exact value:**
```python
# Find entity with specific name
ws.download('(name $id "Cortisol")', "$id")

# Find entity with specific type
ws.download('(type $id "biological")', "$id")
```

**Pattern-based search:**
```python
# Get all relationship types (for inspection)
result = ws.download("(edge $s $t $type)", "$type", max_results=1000)

# Get all entity types
result = ws.download("(type $id $typename)", "$typename", max_results=1000)
```

---

### 6. Aggregation Queries

**Count by type:**
```python
result = ws.download("(type $id $typename)", "$typename", max_results=10000)
type_counts = {}
for typename in result.data.strip().split('\n'):
    if typename:
        type_counts[typename] = type_counts.get(typename, 0) + 1

print(sorted(type_counts.items(), key=lambda x: -x[1]))
```

**Most connected entities:**
```python
result = ws.download("(edge $source $target $type)", "$source", max_results=10000)
source_counts = {}
for source in result.data.strip().split('\n'):
    if source:
        source_counts[source] = source_counts.get(source, 0) + 1

top_connected = sorted(source_counts.items(), key=lambda x: -x[1])[:10]
```

---

## Transform Operations

Transforms are MORK's unique knowledge inference capability.

### Basic Transform Pattern

```python
# Pattern: What to match
# Template: What to create

ws.transform(
    patterns=("(parent $p $c)", "(male $p)"),
    templates=("(father $p $c)",)
).block()
```

### Common Transform Patterns

**1. Relationship Inference:**
```python
# Infer grandparent relationships
ws.transform(
    patterns=("(parent $gp $p)", "(parent $p $gc)"),
    templates=("(grandparent $gp $gc)",)
).block()
```

**2. Property Propagation:**
```python
# Propagate properties through relationships
ws.transform(
    patterns=("(edge $a $b influences)", "(property $b $prop)"),
    templates=("(indirect_property $a $prop)",)
).block()
```

**3. Bidirectional Relations:**
```python
# Create reverse relationships
ws.transform(
    patterns=("(edge $a $b $type)",),
    templates=("(reverse_edge $b $a $type)",)
).block()
```

**4. Complex Inference:**
```python
# Aunt relationship: parent's sister
ws.transform(
    patterns=("(parent $pid $cid)", "(sister $aid $pid)"),
    templates=("(aunt $aid $cid)",)
).block()
```

**5. Multi-Template Transforms:**
```python
# Create multiple derived facts from one match
ws.transform(
    patterns=("(src (Individuals $i (Id $id)))", "(src (Individuals $i (Fullname $name)))"),
    templates=(
        "(simple (hasName $id $name))",
        "(simple (hasId $name $id))"
    )
).block()
```

---

### Transform with Constraints

```python
# Only match when IDs are different
ws.transform(
    patterns=(
        "(parent $pid $cid0)",
        "(parent $pid $cid1)",
        "(isIdDifferent $cid0 $cid1)",  # Constraint
        "(female $cid0)"
    ),
    templates=("(sister $cid0 $cid1)",)
).block()
```

---

## Advanced Query Patterns

### 1. Explore - Hierarchical Navigation

```python
# Get hierarchical structure via breadth-first traversal
result = ws.explore_()
print(result)
```

This returns a tree-like view of your data structure.

---

### 2. Conditional Queries

```python
# Step 1: Find candidates
bio_result = ws.download("(type $id biological)", "$id", max_results=100)
bio_ids = bio_result.data.strip().split('\n')

# Step 2: Query each candidate
for bio_id in bio_ids[:10]:
    name_result = ws.download(f"(name {bio_id} $name)", "$name", max_results=1)
    if name_result.data.strip():
        print(f"{bio_id}: {name_result.data.strip()}")
```

---

### 3. Chained Transforms

```python
# Step 1: Infer mothers
ws.transform(
    patterns=("(parent $p $c)", "(female $p)"),
    templates=("(mother $p $c)",)
).block()

# Step 2: Infer grandmothers
ws.transform(
    patterns=("(mother $gm $p)", "(parent $p $gc)"),
    templates=("(grandmother $gm $gc)",)
).block()

# Step 3: Query grandmothers
result = ws.download("(grandmother $gm $gc)", "($gm -> $gc)")
```

---

### 4. Analytical Queries

**Degree distribution:**
```python
# Out-degree
result = ws.download("(edge $source $target $type)", "$source", max_results=10000)
degrees = {}
for source in result.data.strip().split('\n'):
    degrees[source] = degrees.get(source, 0) + 1

# In-degree
result = ws.download("(edge $source $target $type)", "$target", max_results=10000)
in_degrees = {}
for target in result.data.strip().split('\n'):
    in_degrees[target] = in_degrees.get(target, 0) + 1
```

**Relationship type distribution:**
```python
result = ws.download("(edge $s $t $reltype)", "$reltype", max_results=10000)
rel_counts = {}
for rel in result.data.strip().split('\n'):
    if rel:
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

print("Relationship types:", sorted(rel_counts.items(), key=lambda x: -x[1]))
```

---

## Data Loading & Export

### Import from Files

**S-expressions (MeTTa format):**
```python
# Local file
ws.sexpr_import("$x", "$x", "file:///path/to/data.metta")

# Remote file
ws.sexpr_import("$x", "$x", "https://example.com/data.metta")
```

**CSV files:**
```python
ws.csv_import("$x", "$x", "file:///path/to/data.csv")
ws.csv_import("$x", "$x", "https://example.com/data.csv")
```

**MORK Paths format:**
```python
ws.paths_import("$x", "$x", "file:///path/to/data.paths")
```

**JSON files:**
```python
ws.sexpr_import("$x", "$x", "file:///path/to/data.json")
```

---

### Upload Direct Data

**Plain upload:**
```python
data = """
(type e1 concept)
(name e1 "Entity 1")
(edge e1 e2 "relates_to")
(type e2 concept)
(name e2 "Entity 2")
"""
ws.upload_(data)
```

**Upload with transformation:**
```python
# Transform data during upload
ws.upload("(foo $x)", "$x", "(foo 1)\n(foo 2)\n(foo 3)\n")
```

---

### Export/Download Data

**Basic export:**
```python
# All data
result = ws.download("$x", "$x", max_results=10000)
print(result.data)
```

**Export to different formats:**
```python
# Format as CSV-like
result = ws.download("(type $id $type)", "$id,$type", max_results=1000)

# Format as JSON-like
result = ws.download("(name $id $name)", '{"id": "$id", "name": "$name"}', max_results=1000)

# Custom formatting
result = ws.download("(edge $s $t $type)", "$s -> $t [$type]", max_results=1000)
```

---

## Namespace Management

### Work-at Pattern

```python
# Create scoped workspace
with server.work_at("my-namespace") as ws:
    # All operations scoped to this namespace
    ws.upload_(data)
    result = ws.download("$x", "$x")
```

### Nested Namespaces

```python
# Hierarchical namespaces
with server.work_at("project") as proj:
    with proj.work_at("submodule") as sub:
        sub.upload_(data)
```

### Query Across Namespaces

```python
# Write to target namespace
ws.query(
    patterns="(edge $a $b $type)",
    project=["$a", "$b"],
    target="derived-facts"
)

# Then access derived-facts namespace
with server.work_at("derived-facts") as derived:
    result = derived.download("$x", "$x")
```

---

## Practical Examples

### Example 1: Knowledge Graph Analysis

```python
from MORK.python.client import MORK

server = MORK()
with server.work_at("knowledge-graph") as ws:

    # Load data
    ws.sexpr_import("$x", "$x", "file:///data/entities.metta")

    # Find all concept entities
    concepts = ws.download("(type $id concept)", "$id", max_results=1000)

    # Get their names
    for concept_id in concepts.data.strip().split('\n')[:10]:
        name = ws.download(f'(name {concept_id} $name)', "$name", max_results=1)
        edges = ws.download(f'(edge {concept_id} $t $type)', "($t : $type)", max_results=10)

        print(f"\n{concept_id}: {name.data.strip()}")
        print(f"  Connected to: {edges.data.strip()}")
```

---

### Example 2: Multi-Hop Inference

```python
with server.work_at("inference") as ws:

    # Load base facts
    ws.upload_("""
    (edge e1 e2 influences)
    (edge e2 e3 influences)
    (edge e3 e4 influences)
    (edge e1 e5 characterizes)
    (edge e5 e6 influences)
    """)

    # Create 2-hop inference
    ws.transform(
        patterns=('(edge $a $b "influences")', '(edge $b $c "influences")'),
        templates=('(indirect_influence $a $c)',)
    ).block()

    # Query indirect influences
    result = ws.download("(indirect_influence $start $end)", "($start ~> $end)")
    print("Indirect influences:", result.data)

    # Create 3-hop
    ws.transform(
        patterns=(
            '(edge $a $b "influences")',
            '(indirect_influence $b $c)'
        ),
        templates=('(very_indirect $a $c)',)
    ).block()

    result = ws.download("(very_indirect $start $end)", "($start ~~> $end)")
    print("Very indirect influences:", result.data)
```

---

### Example 3: Family Tree Reasoning

```python
with server.work_at("family") as ws:

    # Load family data
    ws.upload_("""
    (parent p1 c1)
    (parent p1 c2)
    (parent p2 c1)
    (parent p2 c2)
    (parent p3 c3)
    (parent p1 p3)
    (female p1)
    (male p2)
    (female c1)
    (male c2)
    """)

    # Infer mothers
    ws.transform(
        patterns=("(parent $p $c)", "(female $p)"),
        templates=("(mother $p $c)",)
    ).block()

    # Infer fathers
    ws.transform(
        patterns=("(parent $p $c)", "(male $p)"),
        templates=("(father $p $c)",)
    ).block()

    # Infer siblings
    ws.transform(
        patterns=(
            "(parent $p $c1)",
            "(parent $p $c2)",
            "(isIdDifferent $c1 $c2)"
        ),
        templates=("(sibling $c1 $c2)",)
    ).block()

    # Infer grandparents
    ws.transform(
        patterns=("(parent $gp $p)", "(parent $p $gc)"),
        templates=("(grandparent $gp $gc)",)
    ).block()

    # Query results
    print("Mothers:", ws.download("(mother $m $c)", "($m -> $c)").data)
    print("Fathers:", ws.download("(father $f $c)", "($f -> $c)").data)
    print("Siblings:", ws.download("(sibling $s1 $s2)", "($s1 <-> $s2)").data)
    print("Grandparents:", ws.download("(grandparent $gp $gc)", "($gp => $gc)").data)
```

---

### Example 4: Entity Deduplication

```python
with server.work_at("dedup") as ws:

    # Find entities with same name
    ws.transform(
        patterns=(
            "(name $id1 $name)",
            "(name $id2 $name)",
            "(isIdDifferent $id1 $id2)"
        ),
        templates=("(possible_duplicate $id1 $id2 $name)",)
    ).block()

    # Review duplicates
    result = ws.download(
        "(possible_duplicate $id1 $id2 $name)",
        "($id1 ~ $id2 : $name)"
    )
    print("Possible duplicates:", result.data)
```

---

## Performance Tips

### 1. Use max_results Wisely

```python
# For exploration
ws.download("$x", "$x", max_results=20)

# For analysis
ws.download("(type $id $type)", "$type", max_results=10000)

# For specific lookups
ws.download('(name $id "Cortisol")', "$id", max_results=1)
```

---

### 2. Leverage Transforms for Repeated Queries

Instead of:
```python
# Inefficient: Query 2-hop repeatedly
for entity in entities:
    # Find all 2-hop paths from entity...
```

Do this:
```python
# Efficient: Materialize 2-hop once
ws.transform(
    patterns=("(edge $a $b $t1)", "(edge $b $c $t2)"),
    templates=("(path2 $a $c $b)",)
).block()

# Now query is instant
for entity in entities:
    result = ws.download(f"(path2 {entity} $end $via)", "$end")
```

---

### 3. Use Specific Patterns

More specific patterns are faster:

```python
# Slower (too general)
ws.download("$x", "$x")

# Faster (specific structure)
ws.download("($a $b $c)", "($a $b $c)")

# Fastest (specific pattern)
ws.download("(type $id concept)", "$id")
```

---

### 4. Namespace Isolation

Partition large datasets:

```python
# Separate namespaces for different domains
with server.work_at("biology") as bio:
    bio.upload_(biology_data)

with server.work_at("chemistry") as chem:
    chem.upload_(chemistry_data)

# Queries are faster in smaller namespaces
bio_result = bio.download("(type $id $type)", "$id")
```

---

### 5. Batch Operations

```python
# Instead of many small queries
for item in items:
    ws.download(f"(name {item} $name)", "$name")  # Many round-trips

# Use single query with post-processing
all_names = ws.download("(name $id $name)", "($id : $name)", max_results=10000)
name_dict = dict(line.split(' : ') for line in all_names.data.strip().split('\n'))
```

---

## Query Cheat Sheet

| Goal | Pattern | Template |
|------|---------|----------|
| Get everything | `$x` | `$x` |
| Get all IDs of type | `(type $id concept)` | `$id` |
| Get entity name | `(name e1 $name)` | `$name` |
| Find edges from entity | `(edge e1 $t $type)` | `($t via $type)` |
| Find edges to entity | `(edge $s e1 $type)` | `($s via $type)` |
| Find by name | `(name $id "Cortisol")` | `$id` |
| Format as arrow | `(edge $s $t $type)` | `($s -> $t)` |
| 2-hop neighbors | `(path2 e1 $end $via)` | `$end` (after transform) |
| Count occurrences | `(type $id $type)` | `$type` (then count in Python) |

---

## HTTP API Reference

For direct HTTP usage without Python client:

**Export (Download):**
```bash
POST /space/my-namespace/export
Body: (export (metta) "$x" "$x" 100)
```

**Transform:**
```bash
POST /space/my-namespace/transform
Body: (transform (, (edge $a $b $t1) (edge $b $c $t2)) (, (path2 $a $c $b)))
```

**Upload:**
```bash
POST /space/my-namespace/upload
Body: (type e1 concept)\n(name e1 "Entity 1")
```

**Import:**
```bash
POST /space/my-namespace/import
Body: (import (metta) "$x" "$x" "file:///data.metta")
```

---

## Conclusion

MORK's query system provides:

✅ **Pattern matching** with S-expressions
✅ **Multi-pattern unification** for complex queries
✅ **Knowledge inference** through transforms
✅ **Template-based formatting** for results
✅ **Namespace scoping** for organization
✅ **Blazing-fast performance** via trie-based storage

This makes MORK uniquely powerful for:
- Knowledge graph reasoning
- Symbolic AI applications
- Complex pattern-based data manipulation
- Real-time hypergraph transformations
- Multi-hop inference at scale

For more examples, see:
- `MORK/python/simple_query.py`
- `MORK/python/advanced_queries.py`
- `MORK/python/aunt-kg.py`
- `MORK/client_demo.py`
