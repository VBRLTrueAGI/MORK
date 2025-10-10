import os
import asyncio
import uuid
from typing import List, Dict, Any, Optional
import time
import json
import logging
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from models import BenchmarkRequest, BenchmarkResult, TestCategory
from mork_client import MORKClient
from neo4j_client import Neo4jClient
from data_converter import DataConverter
from benchmark_runner import BenchmarkRunner
from performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MORK vs Neo4j Comparison Tool", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
mork_client = None
neo4j_client = None
benchmark_runner = None
active_benchmarks: Dict[str, Dict] = {}
websocket_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize connections to MORK and Neo4j"""
    global mork_client, neo4j_client, benchmark_runner
    
    try:
        # Initialize MORK client
        mork_url = os.getenv("MORK_SERVER_URL", "http://host.docker.internal:8000")
        mork_client = MORKClient(mork_url)
        await mork_client.connect()
        logger.info(f"Connected to MORK server at {mork_url}")
        
        # Initialize Neo4j client
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "benchmark123")
        
        neo4j_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
        await neo4j_client.connect()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
        
        # Initialize benchmark runner
        benchmark_runner = BenchmarkRunner(mork_client, neo4j_client)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections"""
    if neo4j_client:
        await neo4j_client.disconnect()
    if mork_client:
        await mork_client.disconnect()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and validate data file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.json', '.csv')):
            raise HTTPException(status_code=400, detail="Only JSON and CSV files are supported")
        
        # Save uploaded file
        upload_id = str(uuid.uuid4())
        file_path = Path(f"/app/data/{upload_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Analyze file structure
        converter = DataConverter()
        file_info = await converter.analyze_file(file_path)
        
        return {
            "upload_id": upload_id,
            "filename": file.filename,
            "size": len(content),
            "file_info": file_info,
            "suggested_benchmarks": await converter.suggest_benchmarks(file_info)
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/benchmark")
async def start_benchmark(request: BenchmarkRequest):
    """Start a benchmark comparison between MORK and Neo4j"""
    try:
        benchmark_id = str(uuid.uuid4())
        
        # Store benchmark info
        active_benchmarks[benchmark_id] = {
            "status": "running",
            "start_time": time.time(),
            "request": request.dict(),
            "results": None
        }
        
        # Start benchmark in background
        asyncio.create_task(run_benchmark_async(benchmark_id, request))
        
        return {"benchmark_id": benchmark_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Benchmark start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_benchmark_async(benchmark_id: str, request: BenchmarkRequest):
    """Run benchmark asynchronously and update status"""
    try:
        # Notify WebSocket clients
        await broadcast_status(benchmark_id, "running", "Starting benchmark...")
        
        # Run the actual benchmark
        results = await benchmark_runner.run_comparison(request)
        
        # Store results
        active_benchmarks[benchmark_id]["status"] = "completed"
        active_benchmarks[benchmark_id]["results"] = results
        active_benchmarks[benchmark_id]["end_time"] = time.time()
        
        # Notify completion
        await broadcast_status(benchmark_id, "completed", "Benchmark completed", results)
        
    except Exception as e:
        logger.error(f"Benchmark {benchmark_id} failed: {e}")
        active_benchmarks[benchmark_id]["status"] = "failed"
        active_benchmarks[benchmark_id]["error"] = str(e)
        await broadcast_status(benchmark_id, "failed", f"Benchmark failed: {e}")

@app.get("/api/benchmark/{benchmark_id}")
async def get_benchmark_results(benchmark_id: str):
    """Get benchmark results"""
    if benchmark_id not in active_benchmarks:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    return active_benchmarks[benchmark_id]

@app.get("/api/benchmark/{benchmark_id}/status")
async def get_benchmark_status(benchmark_id: str):
    """Get benchmark status"""
    if benchmark_id not in active_benchmarks:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    return {
        "benchmark_id": benchmark_id,
        "status": active_benchmarks[benchmark_id]["status"]
    }

@app.websocket("/ws/{benchmark_id}")
async def websocket_endpoint(websocket: WebSocket, benchmark_id: str):
    """WebSocket for real-time benchmark updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_status(benchmark_id: str, status: str, message: str, data: Any = None):
    """Broadcast status update to all connected WebSocket clients"""
    payload = {
        "benchmark_id": benchmark_id,
        "status": status,
        "message": message,
        "timestamp": time.time()
    }
    if data:
        payload["data"] = data
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_text(json.dumps(payload))
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    mork_status = await mork_client.health_check() if mork_client else False
    neo4j_status = await neo4j_client.health_check() if neo4j_client else False
    
    return {
        "status": "healthy" if mork_status and neo4j_status else "unhealthy",
        "mork": "connected" if mork_status else "disconnected",
        "neo4j": "connected" if neo4j_status else "disconnected"
    }

@app.get("/api/examples")
async def get_example_datasets():
    """Get list of example datasets for testing"""
    examples = [
        {
            "name": "Family Tree (JSON)",
            "description": "Family relationships for knowledge graph testing",
            "file": "examples/family_tree.json",
            "categories": ["knowledge_graphs"],
            "size": "small"
        },
        {
            "name": "Social Network (CSV)",
            "description": "Social connections for graph algorithm testing", 
            "file": "examples/social_network.csv",
            "categories": ["graph_algorithms"],
            "size": "medium"
        },
        {
            "name": "Logic Rules (JSON)",
            "description": "Rule-based data for logical inference testing",
            "file": "examples/logic_rules.json", 
            "categories": ["logical_inference"],
            "size": "small"
        }
    ]
    return examples

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)