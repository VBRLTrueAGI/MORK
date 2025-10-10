import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import quote

from models import PerformanceMetrics
from performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class MORKClient:
    """Client for interfacing with MORK server HTTP API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitor = PerformanceMonitor()
    
    async def connect(self):
        """Initialize connection to MORK server"""
        self.session = aiohttp.ClientSession()
        
        # Test connection
        try:
            async with self.session.get(f"{self.base_url}/status/-") as response:
                if response.status != 200:
                    raise Exception(f"MORK server not responding: {response.status}")
            logger.info("MORK connection established")
        except Exception as e:
            await self.disconnect()
            raise Exception(f"Failed to connect to MORK: {e}")
    
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Check if MORK server is healthy"""
        try:
            if not self.session:
                return False
            async with self.session.get(f"{self.base_url}/status/-") as response:
                return response.status == 200
        except:
            return False
    
    async def clear_space(self, expr: str = "$x"):
        """Clear MORK space"""
        try:
            async with self.session.get(f"{self.base_url}/clear/{quote(expr)}/") as response:
                if response.status != 200:
                    raise Exception(f"Failed to clear space: {response.status}")
        except Exception as e:
            logger.error(f"Clear space failed: {e}")
            raise
    
    async def upload_data(self, data: str, pattern: str = "$x", template: str = "$x") -> bool:
        """Upload S-expression data to MORK"""
        try:
            url = f"{self.base_url}/upload/{quote(pattern)}/{quote(template)}/"
            headers = {"Content-Type": "text/plain"}
            
            async with self.session.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Upload failed: {response.status} - {error_text}")
                return True
        except Exception as e:
            logger.error(f"Upload data failed: {e}")
            raise
    
    async def query_data(self, pattern: str, template: str = "$x", max_results: Optional[int] = None) -> str:
        """Query data from MORK space"""
        try:
            url = f"{self.base_url}/export/{quote(pattern)}/{quote(template)}/"
            if max_results:
                url += f"?max_write={max_results}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Query failed: {response.status} - {error_text}")
                return await response.text()
        except Exception as e:
            logger.error(f"Query data failed: {e}")
            raise
    
    async def transform(self, patterns: List[str], templates: List[str]) -> bool:
        """Execute MORK transform operation"""
        try:
            patterns_str = " ".join(patterns)
            templates_str = " ".join(templates)
            payload = f"(transform (, {patterns_str}) (, {templates_str}))"
            
            headers = {"Content-Type": "text/plain"}
            async with self.session.post(f"{self.base_url}/transform/", 
                                       data=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Transform failed: {response.status} - {error_text}")
                return True
        except Exception as e:
            logger.error(f"Transform failed: {e}")
            raise
    
    async def count_data(self, expr: str) -> int:
        """Count items matching expression"""
        try:
            async with self.session.get(f"{self.base_url}/count/{quote(expr)}/") as response:
                if response.status != 200:
                    raise Exception(f"Count failed: {response.status}")
                
                # Poll for result
                return await self._poll_count_result(expr)
        except Exception as e:
            logger.error(f"Count data failed: {e}")
            raise
    
    async def _poll_count_result(self, expr: str, max_attempts: int = 20) -> int:
        """Poll for count result"""
        for _ in range(max_attempts):
            try:
                async with self.session.get(f"{self.base_url}/status/{quote(expr)}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        if status_data.get("status") == "pathClear":
                            await asyncio.sleep(0.1)
                            continue
                        elif "CountResult" in status_data:
                            return status_data["CountResult"]
            except:
                pass
            await asyncio.sleep(0.1)
        raise Exception("Count operation timed out")
    
    async def run_benchmark_test(self, test_name: str, setup_data: str, 
                                query_patterns: List[str], query_templates: List[str]) -> PerformanceMetrics:
        """Run a single benchmark test with performance monitoring"""
        
        # Clear space and upload test data
        await self.clear_space()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        start_time = time.perf_counter()
        
        try:
            # Upload data
            await self.upload_data(setup_data)
            
            # Execute query/transform
            if len(query_patterns) > 1 or len(query_templates) > 1:
                await self.transform(query_patterns, query_templates)
                result_count = await self.count_data(query_templates[0])
            else:
                result = await self.query_data(query_patterns[0], query_templates[0])
                result_count = len(result.strip().split('\n')) if result.strip() else 0
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Stop monitoring and get metrics
            metrics = self.monitor.stop_monitoring()
            
            return PerformanceMetrics(
                execution_time_ms=execution_time,
                memory_usage_mb=metrics["memory_usage_mb"],
                peak_memory_mb=metrics["peak_memory_mb"],
                cpu_usage_percent=metrics["cpu_usage_percent"],
                query_count=len(query_patterns),
                results_count=result_count
            )
            
        except Exception as e:
            self.monitor.stop_monitoring()
            logger.error(f"Benchmark test {test_name} failed: {e}")
            raise
    
    async def get_sample_result(self, pattern: str, template: str, limit: int = 5) -> str:
        """Get sample results for display"""
        try:
            return await self.query_data(pattern, template, max_results=limit)
        except:
            return "No results"