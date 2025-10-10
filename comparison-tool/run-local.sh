#!/bin/bash

# Simple local deployment without Docker for easier debugging

echo "🚀 Starting MORK vs Neo4j Comparison Tool (Local Mode)"
echo ""

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"  
    exit 1
fi

# Source cargo environment
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
fi

# Build MORK server if needed
if [ ! -f "../target/release/mork-server" ]; then
    echo "Building MORK server..."
    cd .. && cargo build --release --bin mork-server
    cd comparison-tool
fi

# Start MORK server
echo "📡 Starting MORK server on port 8000..."
../target/release/mork-server &
MORK_PID=$!
echo "MORK server PID: $MORK_PID"
sleep 2

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt --quiet
cd ..

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install --silent
cd ..

# Start backend (without Neo4j for now - simplified demo)
echo "🔧 Starting backend server on port 8080..."
cd backend
export MORK_SERVER_URL=http://localhost:8000
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=benchmark123
python3 main.py &
BACKEND_PID=$!
cd ..
sleep 3

# Start frontend
echo "🌐 Starting frontend server on port 3000..."
cd frontend
export BACKEND_URL=http://localhost:8080
node server.js &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Access the tool at: http://localhost:3000"
echo "🔧 Backend API at: http://localhost:8080"
echo "📡 MORK server at: http://localhost:8000"
echo ""
echo "PIDs: MORK=$MORK_PID, Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo ""
echo "To stop: kill $MORK_PID $BACKEND_PID $FRONTEND_PID"
echo "Or use: pkill -f 'mork-server|main.py|server.js'"