from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import time

class TestCategory(str, Enum):
    KNOWLEDGE_GRAPHS = "knowledge_graphs"
    GRAPH_ALGORITHMS = "graph_algorithms"
    LOGICAL_INFERENCE = "logical_inference"

class DataFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

class BenchmarkRequest(BaseModel):
    upload_id: str
    filename: str
    categories: List[TestCategory]
    data_format: DataFormat
    custom_queries: Optional[Dict[str, str]] = None

class PerformanceMetrics(BaseModel):
    execution_time_ms: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    query_count: int
    results_count: int

class TestResult(BaseModel):
    test_name: str
    category: TestCategory
    mork_metrics: PerformanceMetrics
    neo4j_metrics: PerformanceMetrics
    mork_result_sample: Optional[str] = None
    neo4j_result_sample: Optional[str] = None
    speedup_factor: float
    memory_efficiency: float
    notes: Optional[str] = None

class BenchmarkResult(BaseModel):
    benchmark_id: str
    status: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    file_info: Dict[str, Any]
    test_results: List[TestResult]
    summary: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True

class FileInfo(BaseModel):
    format: DataFormat
    size_bytes: int
    structure: Dict[str, Any]
    sample_data: Any
    estimated_nodes: int
    estimated_relationships: int

class DataStructure(BaseModel):
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    properties: Dict[str, List[str]]

class BenchmarkStatus(BaseModel):
    benchmark_id: str
    status: str
    message: str
    progress_percent: Optional[int] = None
    current_test: Optional[str] = None
    timestamp: float = time.time()