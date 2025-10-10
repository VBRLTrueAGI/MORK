#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Get raw edge data
        result = ws.download("(edge $s $t $type)", "($s $t $type)", max_results=5)
        print("Raw edge data:")
        print(result.data)
        print("\n" + "="*50)
        
        # Parse it
        if result.data:
            print("\nParsing edges:")
            for line in result.data.strip().split('\n'):
                print(f"Line: '{line}'")
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    print(f"  Inner: '{inner}'")
                    parts = inner.split()
                    print(f"  Parts: {parts}")
                    if len(parts) >= 3:
                        source, target, reltype = parts[0], parts[1], parts[2]
                        print(f"  Edge: {source} --[{reltype}]--> {target}")