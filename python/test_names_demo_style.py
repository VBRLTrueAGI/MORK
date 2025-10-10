#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        # Test the exact same query as demo script
        result = ws.download("(name $id \"Stress\")", "$id", max_results=1)
        print("Stress lookup result:", result)
        print("Data:", repr(result.data))

        # Test general name query
        result = ws.download("(name $id $name)", "($id $name)", max_results=5)
        print("\nName query result:", result)
        print("Data:", repr(result.data))