import json
import csv
import pandas as pd
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import asyncio

from models import DataFormat, TestCategory, FileInfo, DataStructure

logger = logging.getLogger(__name__)

class DataConverter:
    """Converts uploaded data into MORK and Neo4j compatible formats"""
    
    def __init__(self):
        self.supported_formats = [DataFormat.JSON, DataFormat.CSV]
    
    async def analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze uploaded file and extract structure information"""
        try:
            file_size = file_path.stat().st_size
            
            if file_path.suffix.lower() == '.json':
                return await self._analyze_json(file_path, file_size)
            elif file_path.suffix.lower() == '.csv':
                return await self._analyze_csv(file_path, file_size)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            raise
    
    async def _analyze_json(self, file_path: Path, file_size: int) -> FileInfo:
        """Analyze JSON file structure"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract structure information
            structure = self._analyze_json_structure(data)
            sample_data = self._get_json_sample(data)
            
            # Estimate nodes and relationships
            estimated_nodes, estimated_relationships = self._estimate_graph_size_json(data)
            
            return FileInfo(
                format=DataFormat.JSON,
                size_bytes=file_size,
                structure=structure,
                sample_data=sample_data,
                estimated_nodes=estimated_nodes,
                estimated_relationships=estimated_relationships
            )
            
        except Exception as e:
            logger.error(f"JSON analysis failed: {e}")
            raise
    
    async def _analyze_csv(self, file_path: Path, file_size: int) -> FileInfo:
        """Analyze CSV file structure"""
        try:
            # Read CSV with pandas for better analysis
            df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows
            
            structure = {
                "columns": list(df.columns),
                "row_count": len(df),
                "data_types": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
            sample_data = df.head(5).to_dict('records')
            
            # Estimate nodes and relationships based on CSV structure
            estimated_nodes, estimated_relationships = self._estimate_graph_size_csv(df)
            
            return FileInfo(
                format=DataFormat.CSV,
                size_bytes=file_size,
                structure=structure,
                sample_data=sample_data,
                estimated_nodes=estimated_nodes,
                estimated_relationships=estimated_relationships
            )
            
        except Exception as e:
            logger.error(f"CSV analysis failed: {e}")
            raise
    
    def _analyze_json_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively analyze JSON structure"""
        if current_depth >= max_depth:
            return {"type": type(data).__name__, "truncated": True}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "properties": {k: self._analyze_json_structure(v, max_depth, current_depth + 1) 
                              for k, v in list(data.items())[:10]}  # Limit to first 10 properties
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "item_structure": self._analyze_json_structure(data[0], max_depth, current_depth + 1) if data else None
            }
        else:
            return {"type": type(data).__name__, "value": str(data)[:100]}
    
    def _get_json_sample(self, data: Any) -> Any:
        """Get a representative sample of JSON data"""
        if isinstance(data, dict):
            return {k: v for k, v in list(data.items())[:5]}
        elif isinstance(data, list):
            return data[:5]
        else:
            return data
    
    def _estimate_graph_size_json(self, data: Any) -> Tuple[int, int]:
        """Estimate number of nodes and relationships from JSON"""
        nodes = 0
        relationships = 0
        
        if isinstance(data, dict):
            # Check for common graph structures
            if 'nodes' in data and 'edges' in data:
                nodes = len(data['nodes']) if isinstance(data['nodes'], list) else 1
                relationships = len(data['edges']) if isinstance(data['edges'], list) else 1
            elif 'people' in data and 'relationships' in data:
                nodes = len(data['people']) if isinstance(data['people'], list) else 1
                relationships = len(data['relationships']) if isinstance(data['relationships'], list) else 1
            else:
                # Count objects as potential nodes
                nodes = self._count_objects(data)
                relationships = max(0, nodes - 1)  # Estimate relationships
        elif isinstance(data, list):
            nodes = len(data)
            relationships = max(0, nodes - 1)
        
        return nodes, relationships
    
    def _estimate_graph_size_csv(self, df: pd.DataFrame) -> Tuple[int, int]:
        """Estimate number of nodes and relationships from CSV"""
        rows = len(df)
        
        # Check if it's an edge list format
        if any(col.lower() in ['source', 'target', 'from', 'to'] for col in df.columns):
            # Edge list format
            unique_nodes = set()
            for col in df.columns:
                if col.lower() in ['source', 'target', 'from', 'to']:
                    unique_nodes.update(df[col].dropna().unique())
            return len(unique_nodes), rows
        else:
            # Assume each row is a node
            return rows, max(0, rows - 1)
    
    def _count_objects(self, data: Any) -> int:
        """Recursively count objects in nested data"""
        if isinstance(data, dict):
            count = 1  # The dict itself
            for value in data.values():
                if isinstance(value, (dict, list)):
                    count += self._count_objects(value)
            return count
        elif isinstance(data, list):
            count = 0
            for item in data:
                if isinstance(item, (dict, list)):
                    count += self._count_objects(item)
                else:
                    count += 1
            return count
        else:
            return 1
    
    async def suggest_benchmarks(self, file_info: FileInfo) -> List[TestCategory]:
        """Suggest appropriate benchmark categories based on file structure"""
        suggestions = []
        
        if file_info.format == DataFormat.JSON:
            structure = file_info.structure
            
            # Check for knowledge graph patterns
            if self._has_relationship_structure(structure):
                suggestions.append(TestCategory.KNOWLEDGE_GRAPHS)
            
            # Check for graph algorithm suitability
            if file_info.estimated_relationships > 10:
                suggestions.append(TestCategory.GRAPH_ALGORITHMS)
            
            # Check for logical inference patterns
            if self._has_logical_structure(structure):
                suggestions.append(TestCategory.LOGICAL_INFERENCE)
        
        elif file_info.format == DataFormat.CSV:
            columns = file_info.structure.get("columns", [])
            
            # Check for edge list format
            if any(col.lower() in ['source', 'target', 'from', 'to'] for col in columns):
                suggestions.extend([TestCategory.KNOWLEDGE_GRAPHS, TestCategory.GRAPH_ALGORITHMS])
            
            # Check for entity data
            if any(col.lower() in ['id', 'name', 'type'] for col in columns):
                suggestions.append(TestCategory.KNOWLEDGE_GRAPHS)
        
        # Always suggest knowledge graphs as fallback
        if not suggestions:
            suggestions.append(TestCategory.KNOWLEDGE_GRAPHS)
        
        return suggestions
    
    def _has_relationship_structure(self, structure: Dict) -> bool:
        """Check if JSON has relationship/graph structure"""
        if structure.get("type") == "object":
            keys = structure.get("keys", [])
            return any(key.lower() in ['relationships', 'edges', 'connections', 'links', 'people', 'nodes'] for key in keys)
        return False
    
    def _has_logical_structure(self, structure: Dict) -> bool:
        """Check if JSON has logical inference structure"""
        if structure.get("type") == "object":
            keys = structure.get("keys", [])
            return any(key.lower() in ['rules', 'axioms', 'facts', 'predicates', 'logic'] for key in keys)
        return False
    
    async def convert_to_mork(self, file_path: Path, file_info: FileInfo) -> str:
        """Convert data to MORK S-expressions"""
        try:
            if file_info.format == DataFormat.JSON:
                return await self._json_to_mork(file_path)
            elif file_info.format == DataFormat.CSV:
                return await self._csv_to_mork(file_path)
            else:
                raise ValueError(f"Unsupported format: {file_info.format}")
        except Exception as e:
            logger.error(f"MORK conversion failed: {e}")
            raise
    
    async def _json_to_mork(self, file_path: Path) -> str:
        """Convert JSON to MORK S-expressions"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        sexpr_lines = []
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if 'nodes' in data and 'edges' in data:
                # Graph format
                for node in data['nodes']:
                    sexpr_lines.append(self._dict_to_sexpr('node', node))
                for edge in data['edges']:
                    sexpr_lines.append(self._dict_to_sexpr('edge', edge))
            
            elif 'people' in data and 'relationships' in data:
                # Family/social format
                for person in data['people']:
                    sexpr_lines.append(self._dict_to_sexpr('person', person))
                for rel in data['relationships']:
                    sexpr_lines.append(self._dict_to_sexpr('relationship', rel))
            
            else:
                # Generic object conversion
                sexpr_lines.extend(self._object_to_sexpr(data))
        
        elif isinstance(data, list):
            # Array of objects
            for i, item in enumerate(data):
                sexpr_lines.append(self._dict_to_sexpr('item', item))
        
        return '\n'.join(sexpr_lines)
    
    async def _csv_to_mork(self, file_path: Path) -> str:
        """Convert CSV to MORK S-expressions"""
        df = pd.read_csv(file_path)
        sexpr_lines = []
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            sexpr_lines.append(self._dict_to_sexpr('data', row_dict))
        
        return '\n'.join(sexpr_lines)
    
    def _dict_to_sexpr(self, predicate: str, data: Dict[str, Any]) -> str:
        """Convert dictionary to S-expression"""
        args = []
        for key, value in data.items():
            if isinstance(value, str):
                args.append(f'({key} "{value}")')
            elif isinstance(value, (int, float)):
                args.append(f'({key} {value})')
            elif isinstance(value, bool):
                args.append(f'({key} {str(value).lower()})')
            elif isinstance(value, list):
                list_items = ' '.join(str(item) for item in value)
                args.append(f'({key} ({list_items}))')
            else:
                args.append(f'({key} "{str(value)}")')
        
        args_str = ' '.join(args)
        return f'({predicate} {args_str})'
    
    def _object_to_sexpr(self, obj: Dict[str, Any], prefix: str = "") -> List[str]:
        """Convert nested object to S-expressions"""
        sexpr_lines = []
        
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                sexpr_lines.extend(self._object_to_sexpr(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        sexpr_lines.append(self._dict_to_sexpr(full_key, item))
                    else:
                        sexpr_lines.append(f'({full_key} {i} {item})')
            else:
                sexpr_lines.append(f'({full_key} {value})')
        
        return sexpr_lines
    
    async def convert_to_neo4j(self, file_path: Path, file_info: FileInfo) -> DataStructure:
        """Convert data to Neo4j nodes and relationships"""
        try:
            if file_info.format == DataFormat.JSON:
                return await self._json_to_neo4j(file_path)
            elif file_info.format == DataFormat.CSV:
                return await self._csv_to_neo4j(file_path)
            else:
                raise ValueError(f"Unsupported format: {file_info.format}")
        except Exception as e:
            logger.error(f"Neo4j conversion failed: {e}")
            raise
    
    async def _json_to_neo4j(self, file_path: Path) -> DataStructure:
        """Convert JSON to Neo4j nodes and relationships"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        nodes = []
        relationships = []
        properties = {"node_properties": set(), "relationship_properties": set()}
        
        if isinstance(data, dict):
            if 'nodes' in data and 'edges' in data:
                # Standard graph format
                for node in data['nodes']:
                    node_data = {"id": str(node.get('id', len(nodes))), "labels": ["Node"]}
                    node_data.update({k: v for k, v in node.items() if k != 'id'})
                    nodes.append(node_data)
                    properties["node_properties"].update(node_data.keys())
                
                for edge in data['edges']:
                    rel_data = {
                        "from": str(edge.get('source', edge.get('from'))),
                        "to": str(edge.get('target', edge.get('to'))),
                        "type": edge.get('type', 'CONNECTED')
                    }
                    rel_data.update({k: v for k, v in edge.items() if k not in ['source', 'target', 'from', 'to', 'type']})
                    relationships.append(rel_data)
                    properties["relationship_properties"].update(rel_data.keys())
            
            elif 'people' in data and 'relationships' in data:
                # Family/social format
                for person in data['people']:
                    person_data = {"id": str(person.get('id', len(nodes))), "labels": ["Person"]}
                    person_data.update({k: v for k, v in person.items() if k != 'id'})
                    nodes.append(person_data)
                    properties["node_properties"].update(person_data.keys())
                
                for rel in data['relationships']:
                    rel_data = {
                        "from": str(rel['from']),
                        "to": str(rel['to']),
                        "type": rel.get('type', 'RELATED').upper()
                    }
                    rel_data.update({k: v for k, v in rel.items() if k not in ['from', 'to', 'type']})
                    relationships.append(rel_data)
                    properties["relationship_properties"].update(rel_data.keys())
        
        # Convert sets to lists for JSON serialization
        properties["node_properties"] = list(properties["node_properties"])
        properties["relationship_properties"] = list(properties["relationship_properties"])
        
        return DataStructure(
            nodes=nodes,
            relationships=relationships,
            properties=properties
        )
    
    async def _csv_to_neo4j(self, file_path: Path) -> DataStructure:
        """Convert CSV to Neo4j nodes and relationships"""
        df = pd.read_csv(file_path)
        nodes = []
        relationships = []
        properties = {"node_properties": set(), "relationship_properties": set()}
        
        columns = [col.lower() for col in df.columns]
        
        # Check if it's an edge list format
        if any(col in ['source', 'target', 'from', 'to'] for col in columns):
            # Edge list format - extract nodes and relationships
            node_ids = set()
            
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Find source and target columns
                source_col = next((col for col in df.columns if col.lower() in ['source', 'from']), None)
                target_col = next((col for col in df.columns if col.lower() in ['target', 'to']), None)
                
                if source_col and target_col:
                    source_id = str(row_dict[source_col])
                    target_id = str(row_dict[target_col])
                    
                    node_ids.add(source_id)
                    node_ids.add(target_id)
                    
                    # Create relationship
                    rel_type = row_dict.get('type', row_dict.get('relationship', 'CONNECTED'))
                    rel_data = {
                        "from": source_id,
                        "to": target_id,
                        "type": str(rel_type).upper()
                    }
                    
                    # Add other columns as properties
                    for col, val in row_dict.items():
                        if col.lower() not in ['source', 'target', 'from', 'to', 'type', 'relationship']:
                            rel_data[col] = val
                    
                    relationships.append(rel_data)
                    properties["relationship_properties"].update(rel_data.keys())
            
            # Create nodes from unique IDs
            for node_id in node_ids:
                nodes.append({"id": node_id, "labels": ["Node"]})
                properties["node_properties"].add("id")
        
        else:
            # Each row is a node
            for i, row in df.iterrows():
                row_dict = row.to_dict()
                node_data = {"id": str(i), "labels": ["Data"]}
                
                for col, val in row_dict.items():
                    if pd.notna(val):
                        node_data[col] = val
                
                nodes.append(node_data)
                properties["node_properties"].update(node_data.keys())
        
        # Convert sets to lists
        properties["node_properties"] = list(properties["node_properties"])
        properties["relationship_properties"] = list(properties["relationship_properties"])
        
        return DataStructure(
            nodes=nodes,
            relationships=relationships,
            properties=properties
        )