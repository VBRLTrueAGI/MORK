#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Get edges
        edges_result = ws.download("(edge $s $t $type)", "($s $t $type)", max_results=10)

        # Get names
        names_result = ws.download("(name $id $name)", "($id $name)", max_results=10000)
        print(f"Names result: {names_result}")
        print(f"Names result data: {repr(names_result.data)}")
        if names_result.data:
            print(f"Names result data first 200: {repr(names_result.data[:200])}")
        else:
            print("Names result data is None!")

        # Build name mapping
        name_map = {}
        if names_result.data:
            print("Processing names...")
            for line in names_result.data.strip().split('\n'):
                print(f"Processing line: {repr(line)}")
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    print(f"  Inner: {repr(inner)}")
                    parts = inner.split(' ', 1)
                    print(f"  Parts: {parts}")
                    if len(parts) == 2:
                        entity_id = parts[0]
                        name = parts[1].strip('"')
                        name_map[entity_id] = name
                        print(f"  Mapped: {entity_id} -> {name}")

        print(f"Name map has {len(name_map)} entries")
        print("Sample name mappings:")
        for i, (k, v) in enumerate(name_map.items()):
            if i < 5:
                print(f"  {k} -> {v}")

        # Test edge processing
        print("\nProcessing first 5 edges:")
        if edges_result.data:
            for line in edges_result.data.strip().split('\n')[:5]:
                line = line.strip()
                if line.startswith('(') and line.endswith(')'):
                    inner = line[1:-1]
                    parts = inner.split()
                    if len(parts) >= 3:
                        source, target, reltype = parts[0], parts[1], parts[2]

                        source_name = name_map.get(source, source)[:30]
                        target_name = name_map.get(target, target)[:30]

                        print(f"  Edge: {source} -> {source_name}")
                        print(f"        {target} -> {target_name}")
                        print(f"        Final: {source_name} --[{reltype}]--> {target_name}")
                        print()