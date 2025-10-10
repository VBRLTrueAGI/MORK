import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
import psutil
import os

from models import PerformanceMetrics
from performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Client for interfacing with Neo4j database"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None
        self.monitor = PerformanceMonitor()
    
    async def connect(self):
        """Initialize connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # Test connection
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.consume()
            
            logger.info("Neo4j connection established")
        except Exception as e:
            await self.disconnect()
            raise Exception(f"Failed to connect to Neo4j: {e}")
    
    async def disconnect(self):
        """Close connection"""
        if self.driver:
            await self.driver.close()
    
    async def health_check(self) -> bool:
        """Check if Neo4j is healthy"""
        try:
            if not self.driver:
                return False
            async with self.driver.session() as session:
                result = await session.run("RETURN 1")
                await result.consume()
                return True
        except:
            return False
    
    async def clear_database(self):
        """Clear all data from Neo4j"""
        try:
            async with self.driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            logger.info("Neo4j database cleared")
        except Exception as e:
            logger.error(f"Clear database failed: {e}")
            raise
    
    async def load_nodes(self, nodes: List[Dict[str, Any]]):
        """Load nodes into Neo4j"""
        try:
            async with self.driver.session() as session:
                for node in nodes:
                    node_id = node.get('id')
                    labels = node.get('labels', ['Node'])
                    properties = {k: v for k, v in node.items() if k not in ['id', 'labels']}
                    
                    # Build Cypher query
                    labels_str = ':'.join(labels)
                    props_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])
                    
                    cypher = f"CREATE (n:{labels_str} {{id: $id{', ' + props_str if props_str else ''}}})"
                    params = {'id': node_id, **properties}
                    
                    await session.run(cypher, params)
        except Exception as e:
            logger.error(f"Load nodes failed: {e}")
            raise
    
    async def load_relationships(self, relationships: List[Dict[str, Any]]):
        """Load relationships into Neo4j"""
        try:
            async with self.driver.session() as session:
                for rel in relationships:
                    from_id = rel['from']
                    to_id = rel['to']
                    rel_type = rel.get('type', 'RELATED')
                    properties = {k: v for k, v in rel.items() if k not in ['from', 'to', 'type']}
                    
                    # Build Cypher query
                    props_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])
                    
                    cypher = f"""
                    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                    CREATE (a)-[r:{rel_type}{' {' + props_str + '}' if props_str else ''}]->(b)
                    """
                    params = {'from_id': from_id, 'to_id': to_id, **properties}
                    
                    await session.run(cypher, params)
        except Exception as e:
            logger.error(f"Load relationships failed: {e}")
            raise
    
    async def run_benchmark_test(self, test_name: str, setup_queries: List[str], 
                                benchmark_query: str) -> PerformanceMetrics:
        """Run a single benchmark test with performance monitoring"""
        
        # Clear database
        await self.clear_database()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        start_time = time.perf_counter()
        result_count = 0
        
        try:
            async with self.driver.session() as session:
                # Execute setup queries
                for setup_query in setup_queries:
                    await session.run(setup_query)
                
                # Execute benchmark query and count results
                result = await session.run(benchmark_query)
                records = await result.data()
                result_count = len(records)
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Stop monitoring and get metrics
            metrics = self.monitor.stop_monitoring()
            
            return PerformanceMetrics(
                execution_time_ms=execution_time,
                memory_usage_mb=metrics["memory_usage_mb"],
                peak_memory_mb=metrics["peak_memory_mb"],
                cpu_usage_percent=metrics["cpu_usage_percent"],
                query_count=len(setup_queries) + 1,
                results_count=result_count
            )
            
        except Exception as e:
            self.monitor.stop_monitoring()
            logger.error(f"Benchmark test {test_name} failed: {e}")
            raise
    
    async def get_sample_result(self, query: str, limit: int = 5) -> str:
        """Get sample results for display"""
        try:
            async with self.driver.session() as session:
                result = await session.run(f"{query} LIMIT {limit}")
                records = await result.data()
                return str(records) if records else "No results"
        except:
            return "No results"
    
    # Knowledge Graph Queries
    async def find_relationships(self, node_id: str, rel_type: str, direction: str = "out") -> List[Dict]:
        """Find relationships from/to a node"""
        direction_clause = "->" if direction == "out" else "<-"
        opposite_direction = "<-" if direction == "out" else "->"
        
        cypher = f"""
        MATCH (a {{id: $node_id}}){direction_clause}[r:{rel_type}]{opposite_direction}(b)
        RETURN a, r, b
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, {"node_id": node_id})
            return await result.data()
    
    async def find_transitive_relationships(self, start_node: str, rel_type: str, max_depth: int = 3) -> List[Dict]:
        """Find transitive relationships (e.g., all descendants)"""
        cypher = f"""
        MATCH path = (start {{id: $start_node}})-[:{rel_type}*1..{max_depth}]->(end)
        RETURN path, start, end, length(path) as depth
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, {"start_node": start_node})
            return await result.data()
    
    # Graph Algorithm Queries
    async def find_cliques(self, min_size: int = 3) -> List[Dict]:
        """Find cliques in the graph"""
        # This is a simplified clique detection - in practice you'd use APOC procedures
        cypher = f"""
        MATCH (a)-[:CONNECTED]-(b)-[:CONNECTED]-(c)-[:CONNECTED]-(a)
        WHERE id(a) < id(b) AND id(b) < id(c)
        RETURN a, b, c
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher)
            return await result.data()
    
    async def shortest_path(self, start_node: str, end_node: str) -> Dict:
        """Find shortest path between two nodes"""
        cypher = """
        MATCH (start {id: $start_node}), (end {id: $end_node})
        MATCH path = shortestPath((start)-[*]-(end))
        RETURN path, length(path) as distance
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, {"start_node": start_node, "end_node": end_node})
            record = await result.single()
            return record.data() if record else {}
    
    async def connected_components(self) -> List[Dict]:
        """Find connected components"""
        cypher = """
        CALL gds.wcc.stream('*')
        YIELD nodeId, componentId
        RETURN gds.util.asNode(nodeId).id as nodeId, componentId
        ORDER BY componentId
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher)
            return await result.data()