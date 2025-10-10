#!/usr/bin/env python3
"""
Convert JSON to MeTTa s-expressions and upload to MORK.
"""

import json
from client import ManagedMORK

JSON_FILE = "/home/mrx/work/goku/MORK/The_Lethal_Mechanisms_of_Chronic_Stress_A_Multidisciplinary_Analysis.json"

def json_to_metta(obj, prefix=""):
    """Convert JSON object to MeTTa s-expressions"""
    expressions = []
    
    if isinstance(obj, dict):
        if "entities" in obj:
            # Handle entities list
            for entity in obj.get("entities", []):
                entity_id = entity.get("id", "unknown")
                entity_type = entity.get("type", "unknown")
                entity_name = entity.get("name", "unknown")
                
                # Create entity expression
                expressions.append(f'(entity {entity_id} (type "{entity_type}") (name "{entity_name}"))')
                
                # Add attributes
                if "attributes" in entity:
                    attrs = entity["attributes"]
                    if "description" in attrs:
                        desc = attrs["description"]
                        if isinstance(desc, str):
                            desc = desc.replace('"', '\\"').replace('\n', ' ')
                            expressions.append(f'(description {entity_id} "{desc}")')
                        elif isinstance(desc, list):
                            for d in desc:
                                d = str(d).replace('"', '\\"').replace('\n', ' ')
                                expressions.append(f'(description {entity_id} "{d}")')
                    
                    if "mentioned_on_pages" in attrs:
                        pages = " ".join(str(p) for p in attrs["mentioned_on_pages"])
                        expressions.append(f'(pages {entity_id} {pages})')
        
        if "relationships" in obj:
            # Handle relationships
            for rel in obj.get("relationships", []):
                rel_id = rel.get("id", "unknown")
                rel_type = rel.get("type", "unknown")
                source = rel.get("source", "unknown")
                target = rel.get("target", "unknown")
                
                expressions.append(f'(relationship {rel_id} (type "{rel_type}") (source {source}) (target {target}))')
    
    return expressions

print("Converting JSON to MeTTa s-expressions...")

# Load JSON
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

print(f"✓ Loaded JSON with {len(data.get('entities', []))} entities and {len(data.get('relationships', []))} relationships")

# Convert to MeTTa
metta_expressions = json_to_metta(data)
print(f"✓ Generated {len(metta_expressions)} MeTTa expressions")

# Show sample
print("\nSample expressions:")
for i, expr in enumerate(metta_expressions[:5]):
    print(f"{i+1}. {expr[:150]}{'...' if len(expr) > 150 else ''}")

# Upload to MORK
print("\nUploading to MORK...")
with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress-analysis").and_clear() as ws:
        # Upload expressions
        metta_data = "\n".join(metta_expressions)
        ws.upload_(metta_data).block()
        print(f"✓ Uploaded {len(metta_expressions)} expressions")
        
        # Verify upload
        print("\nVerifying data...")
        result = ws.download_(max_results=5)
        if result.data:
            print("✓ Data successfully uploaded!")
            print("\nFirst few items:")
            print(result.data)
        else:
            print("✗ No data found after upload")
        
        # Try some queries
        print("\n" + "="*60)
        print("EXAMPLE QUERIES")
        print("="*60)
        
        # Query 1: Get all entities
        print("\n1. Get all entity IDs:")
        result = ws.download("(entity $id $type $name)", "$id", max_results=10)
        if result.data:
            print(result.data)
        
        # Query 2: Get entity names
        print("\n2. Get entity names:")
        result = ws.download("(entity $id (type $type) (name $name))", "$name", max_results=10)
        if result.data:
            print(result.data)
        
        # Query 3: Get relationships
        print("\n3. Get relationships:")
        result = ws.download("(relationship $id $type $source $target)", "($source $target)", max_results=10)
        if result.data:
            print(result.data)
        
        # Transform example: Create inverse relationships
        print("\n4. Creating derived relationships...")
        ws.transform(
            ("(relationship $id (type $type) (source $s) (target $t))",),
            ("(connects $s $t)",)
        ).block()
        
        result = ws.download("(connects $a $b)", "($a $b)", max_results=10)
        if result.data:
            print("✓ Derived relationships:")
            print(result.data)

print("\n" + "="*60)
print("COMPLETE! Your data is now in MORK workspace 'stress-analysis'")
print("="*60)