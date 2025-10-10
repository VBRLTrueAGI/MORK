#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Get edges
        edges_result = ws.download("(edge $s $t $type)", "($s $t $type)", max_results=5)
        print("Edge data:")
        print(edges_result.data)

        # Get names
        names_result = ws.download("(name $id $name)", "($id $name)", max_results=10)
        print("\nName data:")
        print(names_result.data)

        # Build name mapping
        name_map = {}
        if names_result.data:
            for line in names_result.data.strip().split('\n'):
                print(f"\nProcessing line: '{line}'")
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    print(f"  Inner: '{inner}'")
                    parts = inner.split(' ', 1)
                    print(f"  Parts: {parts}")
                    if len(parts) == 2:
                        entity_id = parts[0]
                        name = parts[1].strip('"')
                        name_map[entity_id] = name
                        print(f"  Mapped: {entity_id} -> {name}")

        print(f"\nName map: {name_map}")

        # Test mapping
        if edges_result.data:
            for line in edges_result.data.strip().split('\n')[:3]:
                print(f"\nProcessing edge: '{line}'")
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    parts = inner.split()
                    if len(parts) >= 3:
                        source, target, reltype = parts[0], parts[1], parts[2]
                        source_name = name_map.get(source, source)[:30]
                        target_name = name_map.get(target, target)[:30]
                        print(f"  {source} -> {source_name}")
                        print(f"  {target} -> {target_name}")
                        print(f"  Edge: {source_name} --[{reltype}]--> {target_name}")