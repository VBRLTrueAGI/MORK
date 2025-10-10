#!/usr/bin/env python3
"""
Interactive queries for the Chronic Stress data in MORK
"""

from client import ManagedMORK

def run_queries():
    print("="*80)
    print("QUERYING CHRONIC STRESS DATA IN MORK")
    print("="*80)
    
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        with server.work_at("stress-analysis") as ws:
            
            # Query 1: Find all concepts
            print("\n1️⃣  ALL CONCEPTS (entities of type 'concept'):")
            result = ws.download("(entity $id (type \"concept\") (name $name))", "$name", max_results=20)
            if result.data:
                for i, name in enumerate(result.data.strip().split('\n'), 1):
                    print(f"   {i}. {name}")
            
            # Query 2: Find entities with "stress" in the name
            print("\n2️⃣  ENTITIES WITH 'Stress' IN NAME:")
            result = ws.download("(entity $id $type (name $name))", "$name", max_results=100)
            if result.data:
                stress_items = [n for n in result.data.strip().split('\n') if 'Stress' in n or 'stress' in n]
                for i, name in enumerate(stress_items[:10], 1):
                    print(f"   {i}. {name}")
            
            # Query 3: Get descriptions
            print("\n3️⃣  SAMPLE DESCRIPTIONS:")
            result = ws.download("(description $id $desc)", "($id $desc)", max_results=5)
            if result.data:
                for line in result.data.strip().split('\n')[:5]:
                    print(f"   {line[:100]}...")
            
            # Query 4: Find page references
            print("\n4️⃣  PAGE REFERENCES (which pages mention which entities):")
            result = ws.download("(pages $id $page)", "($id $page)", max_results=10)
            if result.data:
                for line in result.data.strip().split('\n')[:10]:
                    print(f"   {line}")
            
            # Query 5: Find all relationships
            print("\n5️⃣  RELATIONSHIPS (first 10):")
            result = ws.download("(relationship $id (type $type) (source $s) (target $t))", 
                               "($type $s $t)", max_results=10)
            if result.data:
                for i, rel in enumerate(result.data.strip().split('\n')[:10], 1):
                    print(f"   {i}. {rel}")
            
            # Query 6: Find what connects to a specific entity
            print("\n6️⃣  WHAT CONNECTS TO 'e1' (Hunting Groups)?")
            result = ws.download("(relationship $id $type (source $s) (target e1))", 
                               "$s", max_results=10)
            if result.data:
                for line in result.data.strip().split('\n')[:10]:
                    print(f"   Connected from: {line}")
            
            # Query 7: Create a network view
            print("\n7️⃣  NETWORK VIEW (source -> target pairs):")
            result = ws.download("(relationship $id $type (source $s) (target $t))", 
                               "($s -> $t)", max_results=15)
            if result.data:
                for line in result.data.strip().split('\n')[:15]:
                    print(f"   {line}")
            
            # Advanced: Transform to create entity-to-entity connections
            print("\n8️⃣  CREATING DERIVED CONNECTIONS...")
            ws.transform(
                ("(relationship $id (type $reltype) (source $s) (target $t))",),
                ("(connected $s $t $reltype)",)
            ).block()
            
            result = ws.download("(connected $a $b $type)", "($a --[$type]--> $b)", max_results=10)
            if result.data:
                print("   Derived connections:")
                for line in result.data.strip().split('\n')[:10]:
                    print(f"   {line}")
            
            # Query for entity type counts
            print("\n9️⃣  COUNT ENTITIES BY TYPE:")
            types_result = ws.download("(type $id $typename)", "$typename", max_results=10000)
            if types_result.data:
                types = types_result.data.strip().split('\n')
                type_counts = {}
                for t in types:
                    t = t.strip().strip('"')
                    type_counts[t] = type_counts.get(t, 0) + 1
                
                for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                    print(f"   {t}: {count}")
            
            print("\n" + "="*80)
            print("QUERY COMPLETE!")
            print("="*80)

if __name__ == "__main__":
    run_queries()