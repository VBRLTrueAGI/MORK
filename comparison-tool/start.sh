#!/bin/bash

# MORK vs Neo4j Comparison Tool - Startup Script

echo "🚀 Starting MORK vs Neo4j Comparison Tool..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for docker compose (new syntax) or docker-compose (old syntax)
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker with Compose plugin."
    exit 1
fi

# Use the available compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi
echo "Using: $COMPOSE_CMD"

# Check if MORK server is built
if [ ! -f "../target/release/mork-server" ]; then
    echo "⚠️  MORK server binary not found at ../target/release/mork-server"
    echo "Building MORK server..."
    cd .. && cargo build --release --bin mork-server
    if [ $? -ne 0 ]; then
        echo "❌ Failed to build MORK server"
        exit 1
    fi
    cd comparison-tool
    echo "✅ MORK server built successfully"
fi

# Start MORK server in background
echo "📡 Starting MORK server on port 8000..."
../target/release/mork-server &
MORK_PID=$!
echo "MORK server PID: $MORK_PID"

# Wait for MORK server to be ready
echo "Waiting for MORK server to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:8000/status/- > /dev/null 2>&1; then
        echo "✅ MORK server is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ MORK server failed to start"
        kill $MORK_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start Docker Compose services
echo ""
echo "🐳 Starting Docker services (Neo4j, Backend, Frontend)..."
$COMPOSE_CMD up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 Access the comparison tool at: http://localhost:3000"
echo "🔧 Backend API at: http://localhost:8080"
echo "🗄️  Neo4j browser at: http://localhost:7474 (user: neo4j, password: benchmark123)"
echo ""
echo "To stop all services, run: ./stop.sh"
echo "To view logs, run: $COMPOSE_CMD logs -f"
echo ""
echo "MORK server PID: $MORK_PID (kill manually with: kill $MORK_PID)"