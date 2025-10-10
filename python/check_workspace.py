#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Check what's actually there
        result = ws.download_()
        print(f"Total data length: {len(result.data) if result.data else 0}")
        print(f"\nFirst 2000 chars:\n{result.data[:2000] if result.data else 'EMPTY'}")
        
        # Count lines
        if result.data:
            lines = result.data.strip().split('\n')
            print(f"\nTotal expressions: {len(lines)}")
            print(f"\nFirst 20 expressions:")
            for i, line in enumerate(lines[:20], 1):
                print(f"{i}. {line[:150]}")