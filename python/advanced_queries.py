#!/usr/bin/env python3
"""
Advanced queries for the Chronic Stress knowledge graph in MORK
"""

from client import ManagedMORK

def run_advanced_queries():
    print("="*80)
    print("ADVANCED QUERIES - Chronic Stress Knowledge Graph")
    print("="*80)
    
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        with server.work_at("stress") as ws:
            
            # Query 1: Find all entity types
            print("\n📊 1. ENTITY TYPES DISTRIBUTION:")
            result = ws.download("(type $id $typename)", "$typename", max_results=10000)
            if result.data:
                types = result.data.strip().split('\n')
                type_counts = {}
                for t in types:
                    type_counts[t] = type_counts.get(t, 0) + 1
                
                for typename, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                    print(f"   {typename}: {count}")
            
            # Query 2: Find concepts related to "Stress"
            print("\n🔗 2. WHAT'S CONNECTED TO 'Stress' (e4)?")
            result = ws.download("(edge e4 $target $reltype)", "($target via $reltype)", max_results=20)
            if result.data:
                print("   Outgoing:")
                for line in result.data.strip().split('\n')[:20]:
                    print(f"   {line}")
            
            result = ws.download("(edge $source e4 $reltype)", "($source via $reltype)", max_results=20)
            if result.data:
                print("\n   Incoming:")
                for line in result.data.strip().split('\n')[:20]:
                    print(f"   {line}")
            
            # Query 3: Find entities by type
            print("\n🧬 3. ALL BIOLOGICAL CONCEPTS:")
            result = ws.download("(type $id biological)", "$id", max_results=30)
            if result.data:
                bio_ids = result.data.strip().split('\n')
                # Get their names
                for bio_id in bio_ids[:10]:
                    name_result = ws.download(f"(name {bio_id} $name)", "$name", max_results=1)
                    if name_result.data:
                        print(f"   {bio_id}: {name_result.data.strip()}")
            else:
                print("   None found - trying 'concept' type...")
                result = ws.download("(type $id concept)", "$id", max_results=20)
                if result.data:
                    concept_ids = result.data.strip().split('\n')[:10]
                    for cid in concept_ids:
                        name_result = ws.download(f"(name {cid} $name)", "$name", max_results=1)
                        if name_result.data:
                            print(f"   {cid}: {name_result.data.strip()}")
            
            # Query 4: Find entity by name
            print("\n🔍 4. FIND ENTITY BY NAME 'Cortisol':")
            result = ws.download("(name $id \"Cortisol\")", "$id", max_results=1)
            if result.data:
                entity_id = result.data.strip()
                print(f"   ID: {entity_id}")
                
                # Get its type
                type_result = ws.download(f"(type {entity_id} $t)", "$t", max_results=1)
                if type_result.data:
                    print(f"   Type: {type_result.data.strip()}")
                
                # Get description
                desc_result = ws.download(f"(description {entity_id} $desc)", "$desc", max_results=1)
                if desc_result.data:
                    print(f"   Description: {desc_result.data.strip()[:100]}")
                
                # Get connections
                conn_result = ws.download(f"(edge {entity_id} $target $type)", "($type -> $target)", max_results=10)
                if conn_result.data:
                    print(f"   Connections: {conn_result.data.strip().split(chr(10))[:5]}")
            
            # Query 5: Find all relationship types
            print("\n🔗 5. RELATIONSHIP TYPES:")
            result = ws.download("(edge $s $t $reltype)", "$reltype", max_results=10000)
            if result.data:
                reltypes = result.data.strip().split('\n')
                reltype_counts = {}
                for rt in reltypes:
                    reltype_counts[rt] = reltype_counts.get(rt, 0) + 1
                
                for reltype, count in sorted(reltype_counts.items(), key=lambda x: -x[1])[:15]:
                    print(f"   {reltype}: {count} connections")
            
            # Query 6: Page frequency analysis
            print("\n📖 6. MOST REFERENCED PAGES:")
            result = ws.download("(page $id $pagenum)", "$pagenum", max_results=10000)
            if result.data:
                pages = [int(p) for p in result.data.strip().split('\n') if p.isdigit()]
                page_counts = {}
                for p in pages:
                    page_counts[p] = page_counts.get(p, 0) + 1
                
                for page, count in sorted(page_counts.items(), key=lambda x: -x[1])[:10]:
                    print(f"   Page {page}: mentioned {count} times")
            
            # Query 7: Transform - Create 2-hop paths
            print("\n🛤️  7. CREATING 2-HOP PATHS:")
            ws.transform(
                ("(edge $a $b $type1)", "(edge $b $c $type2)"),
                ("(path2 $a $c $b)",)
            ).block()
            
            result = ws.download("(path2 $start $end $via)", "($start -> $via -> $end)", max_results=10)
            if result.data:
                print("   Two-hop paths found:")
                for line in result.data.strip().split('\n')[:10]:
                    print(f"   {line}")
            
            # Query 8: Find most connected entities
            print("\n⭐ 8. MOST CONNECTED ENTITIES (by outgoing edges):")
            result = ws.download("(edge $source $target $type)", "$source", max_results=10000)
            if result.data:
                sources = result.data.strip().split('\n')
                source_counts = {}
                for s in sources:
                    source_counts[s] = source_counts.get(s, 0) + 1
                
                top_connected = sorted(source_counts.items(), key=lambda x: -x[1])[:10]
                for entity_id, count in top_connected:
                    name_result = ws.download(f"(name {entity_id} $name)", "$name", max_results=1)
                    name = name_result.data.strip() if name_result.data else "Unknown"
                    print(f"   {entity_id} ({name}): {count} outgoing edges")
            
            print("\n" + "="*80)
            print("QUERY COMPLETE!")
            print("="*80)

if __name__ == "__main__":
    run_advanced_queries()