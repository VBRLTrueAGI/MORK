#!/usr/bin/env python3
"""
Test script to check JSON upload and query the stress data.
"""

from client import ManagedMORK

JSON_FILE = "/home/mrx/work/goku/MORK/The_Lethal_Mechanisms_of_Chronic_Stress_A_Multidisciplinary_Analysis.json"

print("Testing JSON upload to MORK...\n")

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("test-json").and_clear() as ws:
        print("1. Uploading JSON...")
        file_uri = f"file://{JSON_FILE}"
        ws.sexpr_import_(file_uri).block()
        print("✓ Upload complete\n")
        
        print("2. Checking what's in the workspace...")
        # Try to get everything (no limit first)
        result = ws.download_()
        
        if result.data:
            print(f"✓ Found data! Length: {len(result.data)} characters")
            print("\nFirst 2000 characters:")
            print(result.data[:2000])
            print("\n...")
            
            # Try to count lines
            lines = result.data.strip().split('\n')
            print(f"\nTotal lines/expressions: {len(lines)}")
            
            # Show first few complete expressions
            print("\nFirst 5 expressions:")
            for i, line in enumerate(lines[:5]):
                print(f"{i+1}. {line[:200]}{'...' if len(line) > 200 else ''}")
            
        else:
            print("✗ No data found in workspace")
            
        print("\n3. Trying pattern queries...")
        
        # Try different patterns
        patterns = [
            "(entities $x)",
            "(type $x)",
            "(id $x)",
            "($a $b)",
            "($a $b $c)",
        ]
        
        for pattern in patterns:
            result = ws.download(pattern, "$x", max_results=5)
            if result.data and result.data.strip():
                print(f"✓ Pattern '{pattern}' matched:")
                print(f"  {result.data[:300]}")
            else:
                print(f"✗ Pattern '{pattern}' - no matches")

print("\nTest complete!")