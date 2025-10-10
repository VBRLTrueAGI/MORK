#!/usr/bin/env python3
"""
Simple JSON to MORK converter using flat triples
"""

import json
from client import ManagedMORK

JSON_FILE = "/home/mrx/work/goku/MORK/The_Lethal_Mechanisms_of_Chronic_Stress_A_Multidisciplinary_Analysis.json"

def escape_string(s):
    """Escape string for MeTTa"""
    if not isinstance(s, str):
        return str(s)
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '')

def convert_to_simple_triples(data):
    """Convert JSON to simple (subject predicate object) triples"""
    triples = []
    
    # Process entities
    for entity in data.get("entities", []):
        eid = entity.get("id", "")
        
        # Basic entity properties
        if "type" in entity:
            triples.append(f'(type {eid} {entity["type"]})')
        
        if "name" in entity:
            name = escape_string(entity["name"])
            triples.append(f'(name {eid} "{name}")')
        
        # Attributes
        if "attributes" in entity:
            attrs = entity["attributes"]
            
            if "description" in attrs:
                desc = attrs["description"]
                if isinstance(desc, str):
                    desc = escape_string(desc)
                    # Split long descriptions
                    if len(desc) < 200:
                        triples.append(f'(description {eid} "{desc}")')
                    else:
                        # Truncate very long descriptions
                        triples.append(f'(description {eid} "{desc[:200]}...")')
                elif isinstance(desc, list):
                    for d in desc:
                        d = escape_string(str(d))
                        if len(d) < 200:
                            triples.append(f'(description {eid} "{d}")')
            
            if "mentioned_on_pages" in attrs and isinstance(attrs["mentioned_on_pages"], list):
                for page in attrs["mentioned_on_pages"][:10]:  # Limit pages
                    triples.append(f'(page {eid} {page})')
    
    # Process relationships
    for rel in data.get("relationships", []):
        rid = rel.get("id", "")
        
        if "type" in rel:
            triples.append(f'(reltype {rid} {rel["type"]})')
        
        if "source" in rel and "target" in rel:
            source = rel["source"]
            target = rel["target"]
            reltype = rel.get("type", "relates")
            
            # Create direct connection triple
            triples.append(f'(edge {source} {target} {reltype})')
    
    return triples

print("Converting JSON to simple MeTTa triples...")

# Load JSON
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

entities_count = len(data.get('entities', []))
relationships_count = len(data.get('relationships', []))
print(f"✓ Loaded {entities_count} entities, {relationships_count} relationships")

# Convert
triples = convert_to_simple_triples(data)
print(f"✓ Generated {len(triples)} triples")

# Show samples
print("\nSample triples:")
for i, t in enumerate(triples[:10], 1):
    print(f"{i}. {t[:120]}{'...' if len(t) > 120 else ''}")

# Upload to MORK
print("\nUploading to MORK...")
with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress").and_clear() as ws:
        # Upload in chunks to avoid arity errors
        chunk_size = 100
        for i in range(0, len(triples), chunk_size):
            chunk = triples[i:i+chunk_size]
            metta_chunk = "\n".join(chunk)
            ws.upload_(metta_chunk).block()
            print(f"  Uploaded chunk {i//chunk_size + 1}/{(len(triples)-1)//chunk_size + 1}")
        
        print(f"\n✓ Successfully uploaded {len(triples)} triples!")
        
        # Verify
        print("\nVerifying upload...")
        result = ws.download_(max_results=10)
        if result.data:
            print("✓ Data found in workspace!")
            print("\nFirst 10 items:")
            for i, line in enumerate(result.data.strip().split('\n')[:10], 1):
                print(f"{i}. {line}")
        else:
            print("✗ No data in workspace")

print("\n" + "="*80)
print("✅ UPLOAD COMPLETE - Data is in workspace 'stress'")
print("="*80)
print("\nRun: python query_stress_data.py  (to query the data)")