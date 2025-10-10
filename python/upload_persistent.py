#!/usr/bin/env python3
"""
Upload stress data to MORK persistently (without clearing on exit)
"""

import json
from client import ManagedMORK

JSON_FILE = "/home/mrx/work/goku/MORK/The_Lethal_Mechanisms_of_Chronic_Stress_A_Multidisciplinary_Analysis.json"

def escape_string(s):
    if not isinstance(s, str):
        return str(s)
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '')

def convert_to_triples(data):
    triples = []
    
    for entity in data.get("entities", []):
        eid = entity.get("id", "")
        
        if "type" in entity:
            triples.append(f'(type {eid} {entity["type"]})')
        
        if "name" in entity:
            name = escape_string(entity["name"])
            triples.append(f'(name {eid} "{name}")')
        
        if "attributes" in entity:
            attrs = entity["attributes"]
            
            if "description" in attrs:
                desc = attrs["description"]
                if isinstance(desc, str):
                    desc = escape_string(desc)[:200]
                    triples.append(f'(description {eid} "{desc}")')
            
            if "mentioned_on_pages" in attrs:
                for page in attrs["mentioned_on_pages"][:10]:
                    triples.append(f'(page {eid} {page})')
    
    for rel in data.get("relationships", []):
        if "source" in rel and "target" in rel:
            source = rel["source"]
            target = rel["target"]
            reltype = rel.get("type", "relates")
            triples.append(f'(edge {source} {target} {reltype})')
    
    return triples

print("Loading and converting JSON...")
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

triples = convert_to_triples(data)
print(f"✓ Generated {len(triples)} triples from {len(data['entities'])} entities and {len(data['relationships'])} relationships")

print("\nUploading to MORK (without clearing on exit)...")
with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    # Clear first manually
    server.work_at("stress").clear().block()
    
    # Upload without and_clear() so data persists
    with server.work_at("stress") as ws:
        chunk_size = 100
        for i in range(0, len(triples), chunk_size):
            chunk = triples[i:i+chunk_size]
            ws.upload_("\n".join(chunk)).block()
            if (i // chunk_size) % 50 == 0:
                print(f"  Progress: {i}/{len(triples)} ({100*i//len(triples)}%)")
        
        print(f"\n✓ Upload complete!")
        
        # Verify immediately
        result = ws.download_(max_results=10)
        print(f"\nVerification (first 10 items):")
        if result.data:
            for i, line in enumerate(result.data.strip().split('\n')[:10], 1):
                print(f"{i}. {line}")
        else:
            print("WARNING: No data found!")

print("\n✅ DONE! Data should persist in 'stress' workspace")