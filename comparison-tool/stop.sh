#!/bin/bash

# MORK vs Neo4j Comparison Tool - Shutdown Script

echo "🛑 Stopping MORK vs Neo4j Comparison Tool..."
echo ""

# Detect which compose command to use
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Stop Docker Compose services
echo "Stopping Docker services..."
$COMPOSE_CMD down

# Find and stop MORK server process
echo "Stopping MORK server..."
MORK_PIDS=$(pgrep -f "mork-server")

if [ -n "$MORK_PIDS" ]; then
    echo "Found MORK server process(es): $MORK_PIDS"
    kill $MORK_PIDS 2>/dev/null
    sleep 2
    
    # Force kill if still running
    MORK_PIDS=$(pgrep -f "mork-server")
    if [ -n "$MORK_PIDS" ]; then
        echo "Force stopping MORK server..."
        kill -9 $MORK_PIDS 2>/dev/null
    fi
    echo "✅ MORK server stopped"
else
    echo "ℹ️  No MORK server process found"
fi

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -rf /tmp/mork_server_files/* 2>/dev/null

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "To start again, run: ./start.sh"