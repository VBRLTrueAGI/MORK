#!/usr/bin/env python3
"""
Complete demo of working with Chronic Stress data in MORK
Run this to see all capabilities in action
"""

from client import ManagedMORK
import sys

def demo():
    print("\n" + "="*80)
    print(" 🧠 CHRONIC STRESS KNOWLEDGE GRAPH - MORK DEMO")
    print("="*80)
    
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        with server.work_at("stress") as ws:
            
            # 1. Basic stats
            print("\n📊 DATA OVERVIEW:")
            all_data = ws.download("($a $b $c)", "x", max_results=100000)
            if all_data.data:
                total = len(all_data.data.strip().split('\n'))
                print(f"   Total triples in database: ~{total:,}")
            
            # 2. Entity types
            print("\n🏷️  ENTITY TYPES (top 10):")
            types = ws.download("(type $id $t)", "$t", max_results=10000)
            if types.data:
                type_list = types.data.strip().split('\n')
                type_counts = {}
                for t in type_list:
                    type_counts[t] = type_counts.get(t, 0) + 1
                
                for i, (t, c) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])[:10], 1):
                    print(f"   {i}. {t}: {c}")
            
            # 3. Key entities
            print("\n⭐ KEY ENTITIES:")
            key_names = ["Stress", "Cortisol", "COASTER", "Miklashek"]
            for name in key_names:
                result = ws.download(f"(name $id \"{name}\")", "$id", max_results=1)
                if result.data:
                    eid = result.data.strip().split('\n')[0]
                    
                    # Count connections
                    out_edges = ws.download(f"(edge {eid} $t $type)", "$t", max_results=1000)
                    out_count = len(out_edges.data.strip().split('\n')) if out_edges.data else 0
                    
                    print(f"   • {name} ({eid}): {out_count} outgoing connections")
            
            # 4. Relationship analysis
            print("\n🔗 RELATIONSHIP TYPES (top 10):")
            edges = ws.download("(edge $s $t $type)", "$type", max_results=10000)
            if edges.data:
                edge_types = edges.data.strip().split('\n')
                type_counts = {}
                for et in edge_types:
                    type_counts[et] = type_counts.get(et, 0) + 1
                
                for i, (et, c) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])[:10], 1):
                    print(f"   {i}. {et}: {c}")
            
            # 5. Example transform query
            print("\n🔄 TRANSFORM EXAMPLE - Finding Stress Causes:")
            
            # Find what causes stress
            causes = ws.download("(edge $cause e4 causes)", "$cause", max_results=20)
            if causes.data:
                cause_ids = causes.data.strip().split('\n')
                print(f"   Found {len(cause_ids)} direct causes of Stress:")
                
                for cid in cause_ids[:10]:
                    name_result = ws.download(f"(name {cid} $name)", "$name", max_results=1)
                    if name_result.data:
                        name = name_result.data.strip().strip('"')
                        print(f"   • {name}")
            
            # 6. Multi-pattern matching
            print("\n🎯 MULTI-PATTERN QUERY - Entities with name AND description:")
            ws.transform(
                ("(name $id $name)", "(description $id $desc)"),
                ("(documented $id $name)",)
            ).block()
            
            result = ws.download("(documented $id $name)", "$name", max_results=15)
            if result.data:
                print("   Documented entities:")
                for i, name in enumerate(result.data.strip().split('\n')[:15], 1):
                    print(f"   {i}. {name}")
            
            # 7. Page analysis
            print("\n📖 PAGE DISTRIBUTION:")
            pages = ws.download("(page $id $p)", "$p", max_results=10000)
            if pages.data:
                page_list = [int(p) for p in pages.data.strip().split('\n') if p.isdigit()]
                if page_list:
                    print(f"   Pages mentioned: {min(page_list)} - {max(page_list)}")
                    print(f"   Total page references: {len(page_list)}")
                    
                    # Most referenced
                    page_counts = {}
                    for p in page_list:
                        page_counts[p] = page_counts.get(p, 0) + 1
                    
                    top_pages = sorted(page_counts.items(), key=lambda x: -x[1])[:5]
                    print(f"   Most referenced pages:")
                    for p, c in top_pages:
                        print(f"   • Page {p}: {c} mentions")
            
            print("\n" + "="*80)
            print("✅ DEMO COMPLETE!")
            print("="*80)
            print("\n💡 Next steps:")
            print("   • Run: python advanced_queries.py  (more complex queries)")
            print("   • Run: python visualize_stress_graph.py  (create graphs)")
            print("   • Check: STRESS_DATA_GUIDE.md  (full documentation)")
            print(f"   • View graph: python/stress_knowledge_graph.png")

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)