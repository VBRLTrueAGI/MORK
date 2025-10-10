#!/usr/bin/env python3
from client import ManagedMORK

with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
    with server.work_at("stress") as ws:
        print("Testing simple queries...\n")
        
        # Test 1: Get everything
        print("1. Get ALL data (first 20):")
        result = ws.download("$x", "$x", max_results=20)
        if result.data:
            for i, line in enumerate(result.data.strip().split('\n')[:20], 1):
                print(f"  {i}. {line}")
        else:
            print("  EMPTY")
        
        # Test 2: Match any 3-element expression
        print("\n2. Match (A B C) pattern:")
        result = ws.download("($a $b $c)", "($a $b $c)", max_results=10)
        if result.data:
            for line in result.data.strip().split('\n')[:10]:
                print(f"  {line}")
        else:
            print("  NO MATCHES")
        
        # Test 3: Specific patterns
        print("\n3. Match (name X Y) pattern:")
        result = ws.download("(name $x $y)", "($x : $y)", max_results=10)
        if result.data:
            for line in result.data.strip().split('\n')[:10]:
                print(f"  {line}")
        else:
            print("  NO MATCHES")
        
        print("\n4. Match (type X Y) pattern:")
        result = ws.download("(type $x $y)", "($x is $y)", max_results=10)
        if result.data:
            for line in result.data.strip().split('\n')[:10]:
                print(f"  {line}")
        else:
            print("  NO MATCHES")
        
        print("\n5. Match (edge X Y Z) pattern:")
        result = ws.download("(edge $x $y $z)", "($x -> $y)", max_results=10)
        if result.data:
            for line in result.data.strip().split('\n')[:10]:
                print(f"  {line}")
        else:
            print("  NO MATCHES")