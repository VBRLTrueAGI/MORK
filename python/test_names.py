#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Get raw names data
        result = ws.download("(name $id $name)", "($id $name)", max_results=10)
        print("Raw name data:")
        print(result.data)
        print("\n" + "="*50)
        
        # Parse it
        if result.data:
            print("\nParsed:")
            for line in result.data.strip().split('\n'):
                print(f"Line: '{line}'")
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    print(f"  Inner: '{inner}'")
                    parts = inner.split(' ', 1)
                    print(f"  Parts: {parts}")
                    if len(parts) == 2:
                        entity_id = parts[0]
                        name = parts[1].strip('"')
                        print(f"  Mapped: {entity_id} -> {name}")