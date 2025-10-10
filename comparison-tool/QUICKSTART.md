# Quick Start - MORK vs Neo4j Comparison Tool

## For Managers: 5-Minute Demo Guide

This tool shows you **when and why to use MORK instead of Neo4j** through practical performance comparisons.

### 🎯 What This Tool Does

Compares MORK and Neo4j performance across **three key areas**:

1. **🧠 Knowledge Graphs** - Relationship queries, family trees, org charts
2. **🔗 Graph Algorithms** - Network analysis, pathfinding, clustering  
3. **🧮 Logical Inference** - Rule-based reasoning, symbolic AI (MORK's strength)

### ⚡ 3-Step Usage

#### Step 1: Start (One Command)
```bash
cd comparison-tool
./start.sh
```

Wait ~20 seconds, then open: **http://localhost:3000**

#### Step 2: Upload & Configure
- Drag your JSON/CSV file to the upload area
  - **OR** click "Use Example Data" to try pre-loaded samples
- Select test categories (auto-suggested based on your data)
- Click "Start Benchmark"

#### Step 3: View Results
- See **real-time performance comparison**
- Get clear winner and speedup factors
- **Export professional HTML report** for presentations

### 📊 What You'll See

**Summary Cards:**
- Which system is faster overall
- Average speedup (e.g., "MORK is 3.2x faster")
- Memory efficiency comparison
- Total tests completed

**Visual Charts:**
- Side-by-side execution time comparison
- Memory usage comparison
- Per-test performance breakdown

**Smart Recommendations:**
- When to use MORK
- When to use Neo4j
- Use case-specific insights

### 💡 Key Insights You'll Gain

**✅ MORK Excels At:**
- Complex pattern matching with multiple variables
- Logical reasoning and rule application
- Large-scale data transformations
- Symbolic AI workloads
- Memory-efficient operations

**✅ Neo4j Excels At:**
- Simple relationship traversals
- Standard graph algorithms (with APOC)
- Traditional graph database operations
- ACID transactions

### 📁 Example Data Included

1. **Family Tree** - Test knowledge graph relationships
2. **Social Network** - Test graph algorithms
3. **Logic Rules** - Test symbolic reasoning (MORK's strength)

### 🎬 Demo Script for Stakeholders

**Opening** (30 seconds):
> "I want to show you a tool that compares MORK and Neo4j performance on real data."

**Upload** (30 seconds):
> "Let me upload our sample dataset..." [drag file or use example]

**Configure** (15 seconds):
> "The tool suggests these test categories based on the data structure..."

**Run** (1 minute):
> "Now it's running equivalent operations on both systems..."
> [Show real-time progress]

**Results** (2 minutes):
> "Here are the results:
> - MORK is X times faster on average
> - Uses Y% less memory
> - Particularly strong in [category]
> - Recommendations: [show smart insights]"

**Export** (30 seconds):
> "I can export this as a report we can review in detail..."

### 🚀 What's Next?

After reviewing results:

**If MORK performs better:**
- Review detailed test results
- Check which specific operations benefit most
- Consider pilot project with MORK
- Evaluate integration requirements

**If results are mixed:**
- Identify MORK's strengths for specific use cases
- Consider hybrid approach
- Plan phased adoption

**If Neo4j performs better:**
- Understand why (data structure, query patterns)
- Keep Neo4j for current workload
- Revisit MORK for specialized future needs

### 🎓 Understanding the Metrics

**Speedup Factor:**
- `2.0x` = MORK is twice as fast
- `0.5x` = Neo4j is twice as fast
- `1.0x` = Same performance

**Memory Efficiency:**
- Higher = MORK uses less memory (good!)
- Lower = Neo4j uses less memory

### 🛠️ Troubleshooting

**Services won't start?**
```bash
./stop.sh
./start.sh
```

**Need to rebuild?**
```bash
cd .. && cargo build --release --bin mork-server
cd comparison-tool && docker-compose build
```

**Check status:**
```bash
docker-compose ps
curl http://localhost:8080/api/health
```

### 📞 Getting Help

- **Setup Issues**: See [SETUP.md](SETUP.md)
- **Usage Questions**: See [USAGE.md](USAGE.md)  
- **Technical Details**: See [README.md](README.md)

---

## 🎯 Decision Framework

After running benchmarks, use this framework:

| MORK Shows Better Performance | Action |
|-------------------------------|--------|
| **>2x faster** on key operations | Strong candidate for adoption |
| **1.2-2x faster** with better memory | Good fit, evaluate integration effort |
| **Similar performance** but logical inference needed | MORK for AI workloads, Neo4j for CRUD |
| **Slower** on most operations | Stick with Neo4j, monitor MORK development |

**Remember**: Performance is just one factor. Also consider:
- Team expertise and learning curve
- Existing infrastructure and tooling
- Long-term roadmap and support
- Total cost of ownership

---

**Ready to start?** Run `./start.sh` and visit **http://localhost:3000**