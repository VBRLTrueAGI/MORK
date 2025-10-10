# Setup Guide - MORK vs Neo4j Comparison Tool

## Prerequisites

### Required Software
- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Rust** (latest stable) - for building MORK server
- **Git** - for cloning the repository

### System Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **CPU**: Multi-core processor recommended
- **Disk Space**: At least 2GB free

## Installation Steps

### 1. Build MORK Server

First, ensure you're in the MORK project root directory and build the server:

```bash
# From the MORK root directory
cargo build --release --bin mork-server
```

This will create the MORK server binary at `target/release/mork-server`.

### 2. Navigate to Comparison Tool

```bash
cd comparison-tool
```

### 3. Start All Services

```bash
./start.sh
```

This script will:
1. ✅ Check if MORK server is built
2. 🚀 Start MORK server on port 8000
3. 🐳 Launch Docker containers for Neo4j, Backend, and Frontend
4. ⏳ Wait for all services to be ready

### 4. Access the Tool

Once all services are running, open your browser and navigate to:

**🌐 http://localhost:3000**

You should see the MORK vs Neo4j comparison interface with green status indicators for both systems.

## Service Endpoints

- **Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **MORK Server**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `benchmark123`

## Stopping Services

To stop all services:

```bash
./stop.sh
```

This will:
- Stop all Docker containers
- Terminate the MORK server
- Clean up temporary files

## Troubleshooting

### MORK Server Won't Start

**Problem**: MORK server fails to start or is not responding

**Solutions**:
1. Check if port 8000 is already in use:
   ```bash
   lsof -i :8000
   ```
2. Rebuild the MORK server:
   ```bash
   cd .. && cargo clean && cargo build --release --bin mork-server
   ```
3. Check MORK server logs in `/tmp/mork_server_*.log`

### Neo4j Connection Failed

**Problem**: Backend can't connect to Neo4j

**Solutions**:
1. Check if Neo4j container is running:
   ```bash
   docker ps | grep neo4j
   ```
2. Check Neo4j logs:
   ```bash
   docker logs neo4j-benchmark
   ```
3. Restart Neo4j:
   ```bash
   docker-compose restart neo4j
   ```

### Docker Services Won't Start

**Problem**: Docker Compose fails to start services

**Solutions**:
1. Check Docker is running:
   ```bash
   docker info
   ```
2. Clean up old containers:
   ```bash
   docker-compose down -v
   docker system prune -f
   ```
3. Rebuild containers:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Frontend Can't Reach Backend

**Problem**: Web interface shows "Backend connection failed"

**Solutions**:
1. Check backend is running:
   ```bash
   docker logs mork-neo4j-backend
   ```
2. Verify backend health:
   ```bash
   curl http://localhost:8080/api/health
   ```
3. Check network connectivity:
   ```bash
   docker network ls
   docker network inspect comparison-tool_default
   ```

### Port Conflicts

**Problem**: "Port already in use" errors

**Solutions**:
1. Change ports in `docker-compose.yml`:
   - Frontend: Change `3000:3000` to `3001:3000`
   - Backend: Change `8080:8080` to `8081:8080`
   - Neo4j HTTP: Change `7474:7474` to `7475:7474`
   - Neo4j Bolt: Change `7687:7687` to `7688:7687`

2. Or stop conflicting services:
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill the process
   kill -9 <PID>
   ```

## Development Mode

For development with hot-reloading:

1. **Backend Development**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Development**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Performance Tuning

### For Better MORK Performance

Set environment variables before starting:
```bash
export RUST_LOG=info
export MORK_SERVER_ADDR=127.0.0.1
export MORK_SERVER_PORT=8000
./start.sh
```

### For Better Neo4j Performance

Edit `docker-compose.yml` and increase memory:
```yaml
environment:
  - NEO4J_dbms_memory_heap_initial_size=2G
  - NEO4J_dbms_memory_heap_max_size=4G
```

## Data Persistence

- **Neo4j data** is persisted in Docker volume `neo4j_data`
- **Uploaded files** are stored in `comparison-tool/data/`
- **MORK server** data is stored in `/tmp/mork_server_files/`

To clean all data:
```bash
docker-compose down -v
rm -rf data/*
rm -rf /tmp/mork_server_files/*
```

## Logs Location

- **MORK Server**: Check for log files in `/tmp/`
- **Backend**: `docker logs mork-neo4j-backend`
- **Frontend**: `docker logs mork-neo4j-frontend`
- **Neo4j**: `docker logs neo4j-benchmark`

## Next Steps

Once everything is running:
1. Upload a test file (JSON or CSV)
2. Select benchmark categories
3. Click "Start Benchmark"
4. View real-time results
5. Export comparison report

For more details, see the main [README.md](README.md)