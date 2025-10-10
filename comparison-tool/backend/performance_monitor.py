import time
import psutil
import threading
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor system performance during benchmark execution"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics = {
            "memory_usage_mb": 0.0,
            "peak_memory_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "start_time": 0.0,
            "samples": []
        }
        self.lock = threading.Lock()
    
    def start_monitoring(self):
        """Start performance monitoring in background thread"""
        with self.lock:
            if self.monitoring:
                return
            
            self.monitoring = True
            self.metrics = {
                "memory_usage_mb": 0.0,
                "peak_memory_mb": 0.0,
                "cpu_usage_percent": 0.0,
                "start_time": time.time(),
                "samples": []
            }
            
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return collected metrics"""
        with self.lock:
            if not self.monitoring:
                return self.metrics
            
            self.monitoring = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        # Calculate final metrics
        if self.metrics["samples"]:
            self.metrics["memory_usage_mb"] = sum(s["memory"] for s in self.metrics["samples"]) / len(self.metrics["samples"])
            self.metrics["cpu_usage_percent"] = sum(s["cpu"] for s in self.metrics["samples"]) / len(self.metrics["samples"])
            self.metrics["peak_memory_mb"] = max(s["memory"] for s in self.metrics["samples"])
        
        return {
            "memory_usage_mb": self.metrics["memory_usage_mb"],
            "peak_memory_mb": self.metrics["peak_memory_mb"],
            "cpu_usage_percent": self.metrics["cpu_usage_percent"]
        }
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Get current memory usage (in MB)
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # Get current CPU usage
                cpu_percent = process.cpu_percent()
                
                # Store sample
                sample = {
                    "timestamp": time.time(),
                    "memory": memory_mb,
                    "cpu": cpu_percent
                }
                
                with self.lock:
                    if self.monitoring:  # Double-check in case we're stopping
                        self.metrics["samples"].append(sample)
                        
                        # Update peak memory
                        if memory_mb > self.metrics["peak_memory_mb"]:
                            self.metrics["peak_memory_mb"] = memory_mb
                
                time.sleep(0.1)  # Sample every 100ms
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                break

class SystemPerformanceMonitor:
    """Monitor overall system performance"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get current system performance info"""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            return {
                "cpu_count": cpu_count,
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "memory_total_gb": memory.total / 1024 / 1024 / 1024,
                "memory_used_gb": memory.used / 1024 / 1024 / 1024,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "memory_usage_percent": memory.percent
            }
        except Exception as e:
            logger.error(f"System info error: {e}")
            return {}
    
    @staticmethod
    def check_system_resources() -> Dict[str, bool]:
        """Check if system has sufficient resources for benchmarking"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "sufficient_memory": memory.available > 1024 * 1024 * 1024,  # 1GB available
                "sufficient_disk": disk.free > 1024 * 1024 * 1024,  # 1GB free
                "low_cpu_usage": psutil.cpu_percent(interval=1) < 80,
                "overall_ready": (
                    memory.available > 1024 * 1024 * 1024 and
                    disk.free > 1024 * 1024 * 1024 and
                    psutil.cpu_percent(interval=1) < 80
                )
            }
        except Exception as e:
            logger.error(f"Resource check error: {e}")
            return {"overall_ready": False}

class BenchmarkTimer:
    """High-precision timer for benchmark measurements"""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()
    
    def stop(self) -> float:
        """Stop timing and return elapsed time in milliseconds"""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.perf_counter()
        return (self.end_time - self.start_time) * 1000  # Convert to milliseconds
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds (can be called while timer is running)"""
        if self.start_time is None:
            return 0.0
        
        current_time = self.end_time if self.end_time else time.perf_counter()
        return (current_time - self.start_time) * 1000