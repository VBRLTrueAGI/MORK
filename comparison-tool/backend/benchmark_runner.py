import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from models import (
    BenchmarkRequest, BenchmarkResult, TestResult, TestCategory, 
    PerformanceMetrics, DataStructure
)
from mork_client import MORKClient
from neo4j_client import Neo4jClient
from data_converter import DataConverter
from performance_monitor import BenchmarkTimer

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    """Orchestrates benchmark comparisons between MORK and Neo4j"""
    
    def __init__(self, mork_client: MORKClient, neo4j_client: Neo4jClient):
        self.mork_client = mork_client
        self.neo4j_client = neo4j_client
        self.converter = DataConverter()
        
        # Define benchmark test suites for each category
        self.test_suites = {
            TestCategory.KNOWLEDGE_GRAPHS: [
                "relationship_traversal",
                "multi_hop_queries", 
                "property_filtering",
                "transitive_closure"
            ],
            TestCategory.GRAPH_ALGORITHMS: [
                "clique_detection",
                "shortest_paths",
                "connected_components",
                "centrality_measures"
            ],
            TestCategory.LOGICAL_INFERENCE: [
                "pattern_matching",
                "rule_application",
                "unification",
                "constraint_satisfaction"
            ]
        }
    
    async def run_comparison(self, request: BenchmarkRequest) -> BenchmarkResult:
        """Run complete benchmark comparison"""
        benchmark_id = request.upload_id
        start_time = time.time()
        
        try:
            # Load and convert data
            file_path = Path(f"/app/data/{request.upload_id}_{request.filename}")
            file_info = await self.converter.analyze_file(file_path)
            
            # Convert data for both systems
            mork_data = await self.converter.convert_to_mork(file_path, file_info)
            neo4j_data = await self.converter.convert_to_neo4j(file_path, file_info)
            
            # Run benchmark tests for each selected category
            test_results = []
            
            for category in request.categories:
                category_results = await self._run_category_tests(
                    category, mork_data, neo4j_data, file_info
                )
                test_results.extend(category_results)
            
            end_time = time.time()
            
            # Generate summary
            summary = self._generate_summary(test_results)
            
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                status="completed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end_time - start_time,
                file_info=file_info.dict(),
                test_results=test_results,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Benchmark comparison failed: {e}")
            raise
    
    async def _run_category_tests(self, category: TestCategory, mork_data: str, 
                                 neo4j_data: DataStructure, file_info: Any) -> List[TestResult]:
        """Run all tests for a specific category"""
        results = []
        test_names = self.test_suites[category]
        
        for test_name in test_names:
            try:
                logger.info(f"Running {category.value} test: {test_name}")
                
                # Run MORK test
                mork_metrics = await self._run_mork_test(category, test_name, mork_data)
                mork_sample = await self.mork_client.get_sample_result(
                    self._get_mork_query_pattern(category, test_name),
                    "$x"
                )
                
                # Run Neo4j test  
                neo4j_metrics = await self._run_neo4j_test(category, test_name, neo4j_data)
                neo4j_sample = await self.neo4j_client.get_sample_result(
                    self._get_neo4j_query(category, test_name)
                )
                
                # Calculate comparison metrics
                speedup_factor = neo4j_metrics.execution_time_ms / mork_metrics.execution_time_ms if mork_metrics.execution_time_ms > 0 else 0
                memory_efficiency = neo4j_metrics.memory_usage_mb / mork_metrics.memory_usage_mb if mork_metrics.memory_usage_mb > 0 else 0
                
                test_result = TestResult(
                    test_name=test_name,
                    category=category,
                    mork_metrics=mork_metrics,
                    neo4j_metrics=neo4j_metrics,
                    mork_result_sample=mork_sample[:500],  # Truncate for display
                    neo4j_result_sample=neo4j_sample[:500],
                    speedup_factor=speedup_factor,
                    memory_efficiency=memory_efficiency,
                    notes=self._get_test_notes(category, test_name, speedup_factor)
                )
                
                results.append(test_result)
                
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                # Continue with other tests
                continue
        
        return results
    
    async def _run_mork_test(self, category: TestCategory, test_name: str, data: str) -> PerformanceMetrics:
        """Run a specific MORK test"""
        setup_data, patterns, templates = self._get_mork_test_config(category, test_name, data)
        
        return await self.mork_client.run_benchmark_test(
            f"{category.value}_{test_name}",
            setup_data,
            patterns,
            templates
        )
    
    async def _run_neo4j_test(self, category: TestCategory, test_name: str, data: DataStructure) -> PerformanceMetrics:
        """Run a specific Neo4j test"""
        setup_queries, benchmark_query = self._get_neo4j_test_config(category, test_name, data)
        
        return await self.neo4j_client.run_benchmark_test(
            f"{category.value}_{test_name}",
            setup_queries,
            benchmark_query
        )
    
    def _get_mork_test_config(self, category: TestCategory, test_name: str, data: str) -> tuple:
        """Get MORK test configuration (setup_data, patterns, templates)"""
        
        if category == TestCategory.KNOWLEDGE_GRAPHS:
            if test_name == "relationship_traversal":
                return (
                    data,
                    ["(person (id $id) (name $name))"],
                    ["(result (person_name $id $name))"]
                )
            elif test_name == "multi_hop_queries":
                return (
                    data,
                    ["(relationship (from $p1) (to $p2) (type parent))", "(relationship (from $p2) (to $p3) (type parent))"],
                    ["(result (grandparent $p1 $p3))"]
                )
            elif test_name == "property_filtering":
                return (
                    data,
                    ["(person (age $age) (name $name))", "($age > 30)"],
                    ["(result (adult $name $age))"]
                )
            elif test_name == "transitive_closure":
                return (
                    data,
                    ["(relationship (from $a) (to $b) (type parent))", "(relationship (from $b) (to $c) (type parent))"],
                    ["(result (ancestor $a $c))"]
                )
        
        elif category == TestCategory.GRAPH_ALGORITHMS:
            if test_name == "clique_detection":
                return (
                    data,
                    ["(edge (from $a) (to $b))", "(edge (from $b) (to $c))", "(edge (from $c) (to $a))"],
                    ["(result (triangle $a $b $c))"]
                )
            elif test_name == "shortest_paths":
                return (
                    data,
                    ["(edge (from $start) (to $end))"],
                    ["(result (connected $start $end))"]
                )
            elif test_name == "connected_components":
                return (
                    data,
                    ["(edge (from $a) (to $b))"],
                    ["(result (component $a $b))"]
                )
            elif test_name == "centrality_measures":
                return (
                    data,
                    ["(edge (from $node) (to $_))"],
                    ["(result (degree $node))"]
                )
        
        elif category == TestCategory.LOGICAL_INFERENCE:
            if test_name == "pattern_matching":
                return (
                    data,
                    ["(fact (predicate $p) (subject $s) (object $o))"],
                    ["(result (triple $p $s $o))"]
                )
            elif test_name == "rule_application":
                return (
                    data + "\n(exec 0 (, (parent $x $y) (parent $y $z)) (, (grandparent $x $z)))",
                    ["(grandparent $gp $gc)"],
                    ["(result (grandparent_relation $gp $gc))"]
                )
            elif test_name == "unification":
                return (
                    data,
                    ["(pattern $x $x)", "(data $a $b)"],
                    ["(result (unified $x))"]
                )
            elif test_name == "constraint_satisfaction":
                return (
                    data,
                    ["(constraint (var $x) (domain $d))", "(assignment (var $x) (value $v))"],
                    ["(result (valid_assignment $x $v))"]
                )
        
        # Default fallback
        return (data, ["$x"], ["$x"])
    
    def _get_neo4j_test_config(self, category: TestCategory, test_name: str, data: DataStructure) -> tuple:
        """Get Neo4j test configuration (setup_queries, benchmark_query)"""
        
        # Setup queries to load data
        setup_queries = []
        
        # Load nodes
        for node in data.nodes:
            labels = ':'.join(node.get('labels', ['Node']))
            props = ', '.join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                              for k, v in node.items() if k not in ['labels']])
            setup_queries.append(f"CREATE (:{labels} {{{props}}})")
        
        # Load relationships
        for rel in data.relationships:
            rel_type = rel['type']
            from_id = rel['from']
            to_id = rel['to']
            props = ', '.join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                              for k, v in rel.items() if k not in ['from', 'to', 'type']])
            
            query = f"""
            MATCH (a {{id: '{from_id}'}}), (b {{id: '{to_id}'}})
            CREATE (a)-[:{rel_type}{' {' + props + '}' if props else ''}]->(b)
            """
            setup_queries.append(query)
        
        # Benchmark queries based on category and test
        if category == TestCategory.KNOWLEDGE_GRAPHS:
            if test_name == "relationship_traversal":
                benchmark_query = "MATCH (n) RETURN n.id, n.name"
            elif test_name == "multi_hop_queries":
                benchmark_query = "MATCH (a)-[:PARENT]->(b)-[:PARENT]->(c) RETURN a.id, c.id"
            elif test_name == "property_filtering":
                benchmark_query = "MATCH (n) WHERE n.age > 30 RETURN n.name, n.age"
            elif test_name == "transitive_closure":
                benchmark_query = "MATCH (a)-[:PARENT*1..3]->(c) RETURN a.id, c.id"
        
        elif category == TestCategory.GRAPH_ALGORITHMS:
            if test_name == "clique_detection":
                benchmark_query = """
                MATCH (a)-[:CONNECTED]-(b)-[:CONNECTED]-(c)-[:CONNECTED]-(a)
                WHERE id(a) < id(b) AND id(b) < id(c)
                RETURN a.id, b.id, c.id
                """
            elif test_name == "shortest_paths":
                benchmark_query = """
                MATCH (a), (b) WHERE a.id <> b.id
                WITH a, b LIMIT 100
                MATCH path = shortestPath((a)-[*]-(b))
                RETURN a.id, b.id, length(path)
                """
            elif test_name == "connected_components":
                benchmark_query = "MATCH (a)-[*]-(b) RETURN a.id, b.id"
            elif test_name == "centrality_measures":
                benchmark_query = """
                MATCH (n)-[r]-()
                RETURN n.id, count(r) as degree
                ORDER BY degree DESC
                """
        
        elif category == TestCategory.LOGICAL_INFERENCE:
            if test_name == "pattern_matching":
                benchmark_query = "MATCH (n) WHERE n.predicate IS NOT NULL RETURN n"
            elif test_name == "rule_application":
                benchmark_query = """
                MATCH (a)-[:PARENT]->(b)-[:PARENT]->(c)
                RETURN a.id as grandparent, c.id as grandchild
                """
            elif test_name == "unification":
                benchmark_query = "MATCH (n) RETURN DISTINCT n.type"
            elif test_name == "constraint_satisfaction":
                benchmark_query = "MATCH (n) WHERE n.value IS NOT NULL RETURN n"
        
        return setup_queries, benchmark_query or "MATCH (n) RETURN count(n)"
    
    def _get_mork_query_pattern(self, category: TestCategory, test_name: str) -> str:
        """Get MORK query pattern for sample results"""
        if category == TestCategory.KNOWLEDGE_GRAPHS:
            return "(result $x)"
        elif category == TestCategory.GRAPH_ALGORITHMS:
            return "(result $x)"
        elif category == TestCategory.LOGICAL_INFERENCE:
            return "(result $x)"
        return "$x"
    
    def _get_neo4j_query(self, category: TestCategory, test_name: str) -> str:
        """Get Neo4j query for sample results"""
        return "MATCH (n) RETURN n LIMIT 5"
    
    def _generate_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Generate benchmark summary statistics"""
        if not test_results:
            return {}
        
        # Calculate aggregate metrics
        total_tests = len(test_results)
        mork_faster_count = sum(1 for r in test_results if r.speedup_factor > 1.0)
        neo4j_faster_count = total_tests - mork_faster_count
        
        avg_speedup = sum(r.speedup_factor for r in test_results) / total_tests
        avg_memory_efficiency = sum(r.memory_efficiency for r in test_results) / total_tests
        
        # Best/worst performers
        best_mork_test = max(test_results, key=lambda r: r.speedup_factor)
        best_neo4j_test = min(test_results, key=lambda r: r.speedup_factor)
        
        # Category breakdown
        category_breakdown = {}
        for category in TestCategory:
            category_tests = [r for r in test_results if r.category == category]
            if category_tests:
                category_breakdown[category.value] = {
                    "test_count": len(category_tests),
                    "avg_speedup": sum(r.speedup_factor for r in category_tests) / len(category_tests),
                    "mork_wins": sum(1 for r in category_tests if r.speedup_factor > 1.0),
                    "neo4j_wins": sum(1 for r in category_tests if r.speedup_factor <= 1.0)
                }
        
        return {
            "total_tests": total_tests,
            "mork_faster_count": mork_faster_count,
            "neo4j_faster_count": neo4j_faster_count,
            "average_speedup_factor": avg_speedup,
            "average_memory_efficiency": avg_memory_efficiency,
            "best_mork_test": {
                "name": best_mork_test.test_name,
                "speedup": best_mork_test.speedup_factor,
                "category": best_mork_test.category.value
            },
            "best_neo4j_test": {
                "name": best_neo4j_test.test_name,
                "speedup": best_neo4j_test.speedup_factor,
                "category": best_neo4j_test.category.value
            },
            "category_breakdown": category_breakdown,
            "recommendations": self._generate_recommendations(test_results)
        }
    
    def _generate_recommendations(self, test_results: List[TestResult]) -> List[str]:
        """Generate recommendations based on benchmark results"""
        recommendations = []
        
        # Analyze performance patterns
        mork_strong_categories = []
        neo4j_strong_categories = []
        
        for category in TestCategory:
            category_tests = [r for r in test_results if r.category == category]
            if category_tests:
                avg_speedup = sum(r.speedup_factor for r in category_tests) / len(category_tests)
                if avg_speedup > 1.2:
                    mork_strong_categories.append(category.value)
                elif avg_speedup < 0.8:
                    neo4j_strong_categories.append(category.value)
        
        # Generate specific recommendations
        if TestCategory.LOGICAL_INFERENCE.value in mork_strong_categories:
            recommendations.append("MORK excels at logical inference and symbolic reasoning tasks")
        
        if TestCategory.KNOWLEDGE_GRAPHS.value in mork_strong_categories:
            recommendations.append("MORK shows superior performance for complex knowledge graph operations")
        
        if TestCategory.GRAPH_ALGORITHMS.value in neo4j_strong_categories:
            recommendations.append("Neo4j performs better for traditional graph algorithm operations")
        
        # Memory efficiency recommendations
        avg_memory_efficiency = sum(r.memory_efficiency for r in test_results) / len(test_results)
        if avg_memory_efficiency > 1.2:
            recommendations.append("MORK demonstrates better memory efficiency for this dataset")
        elif avg_memory_efficiency < 0.8:
            recommendations.append("Neo4j uses memory more efficiently for this workload")
        
        # Scale-based recommendations
        total_data_size = sum(r.mork_metrics.results_count for r in test_results)
        if total_data_size > 10000:
            recommendations.append("For large-scale data processing, consider MORK's parallel processing capabilities")
        
        if not recommendations:
            recommendations.append("Both systems show comparable performance for this dataset")
        
        return recommendations
    
    def _get_test_notes(self, category: TestCategory, test_name: str, speedup_factor: float) -> str:
        """Generate notes explaining test results"""
        notes = []
        
        if speedup_factor > 2.0:
            notes.append("MORK shows significant performance advantage")
        elif speedup_factor > 1.2:
            notes.append("MORK performs moderately better")
        elif speedup_factor < 0.5:
            notes.append("Neo4j shows significant performance advantage")
        elif speedup_factor < 0.8:
            notes.append("Neo4j performs moderately better")
        else:
            notes.append("Comparable performance between systems")
        
        # Add test-specific context
        if category == TestCategory.LOGICAL_INFERENCE:
            notes.append("Tests MORK's symbolic AI capabilities vs Neo4j's graph operations")
        elif category == TestCategory.KNOWLEDGE_GRAPHS:
            notes.append("Compares hypergraph vs traditional graph representations")
        elif category == TestCategory.GRAPH_ALGORITHMS:
            notes.append("Evaluates algorithm performance on graph structures")
        
        return "; ".join(notes)

class BenchmarkTestGenerator:
    """Generates benchmark test data and queries"""
    
    @staticmethod
    def generate_synthetic_graph(nodes: int, edges: int) -> Dict[str, Any]:
        """Generate synthetic graph data for testing"""
        import random
        
        # Generate nodes
        node_data = []
        for i in range(nodes):
            node_data.append({
                "id": str(i),
                "name": f"Node_{i}",
                "type": random.choice(["A", "B", "C"]),
                "value": random.randint(1, 100)
            })
        
        # Generate edges
        edge_data = []
        for _ in range(edges):
            from_node = random.randint(0, nodes - 1)
            to_node = random.randint(0, nodes - 1)
            if from_node != to_node:
                edge_data.append({
                    "from": str(from_node),
                    "to": str(to_node),
                    "type": random.choice(["CONNECTED", "RELATES", "LINKS"]),
                    "weight": random.uniform(0.1, 1.0)
                })
        
        return {
            "nodes": node_data,
            "edges": edge_data
        }
    
    @staticmethod
    def generate_family_tree(generations: int = 3) -> Dict[str, Any]:
        """Generate family tree data for knowledge graph testing"""
        import random
        
        people = []
        relationships = []
        
        # Generate people across generations
        person_id = 0
        for gen in range(generations):
            gen_size = 2 ** gen  # Exponential growth per generation
            for i in range(gen_size):
                people.append({
                    "id": str(person_id),
                    "name": f"Person_{person_id}",
                    "generation": gen,
                    "gender": random.choice(["M", "F"]),
                    "age": 80 - (gen * 25) + random.randint(-5, 5)
                })
                
                # Add parent relationships (except for first generation)
                if gen > 0:
                    parent_id = (person_id - gen_size) // 2
                    relationships.append({
                        "from": str(parent_id),
                        "to": str(person_id),
                        "type": "parent"
                    })
                
                person_id += 1
        
        return {
            "people": people,
            "relationships": relationships
        }