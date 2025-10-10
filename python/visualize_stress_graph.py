#!/usr/bin/env python3
"""
Visualize the Chronic Stress knowledge graph from MORK
Requires: pip install matplotlib networkx
"""

try:
    import matplotlib.pyplot as plt
    import networkx as nx
except ImportError:
    print("❌ Missing dependencies!")
    print("Install with: pip install matplotlib networkx")
    exit(1)

from client import ManagedMORK

def create_graph_visualization():
    print("Creating knowledge graph visualization...")
    
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        with server.work_at("stress") as ws:
            
            # Get edges
            print("Fetching edges...")
            edges_result = ws.download("(edge $s $t $type)", "($s $t $type)", max_results=500)
            
            # Get names
            print("Fetching entity names...")
            names_result = ws.download("(name $id $name)", "($id $name)", max_results=10000)
            
            # Build name mapping
            name_map = {}
            if names_result.data:
                for line in names_result.data.strip().split('\n'):
                    # Line format: (e1 "Name Here") or (e1 Name)
                    line = line.strip()
                    if line.startswith('(') and line.endswith(')'):
                        inner = line[1:-1]  # Remove outer parens
                        parts = inner.split(' ', 1)
                        if len(parts) == 2:
                            entity_id = parts[0]
                            name = parts[1].strip('"').strip("'")  # Remove all quotes
                            name_map[entity_id] = name
            
            # Create graph
            G = nx.DiGraph()
            edge_labels = {}
            
            if edges_result.data:
                for line in edges_result.data.strip().split('\n'):
                    # Parse (source target type)
                    line = line.strip()
                    if line.startswith('(') and line.endswith(')'):
                        inner = line[1:-1]
                        parts = inner.split()
                        if len(parts) >= 3:
                            source, target, reltype = parts[0], parts[1], parts[2]

                            # Get names (use ID if no name found)
                            source_name = name_map.get(source, source)[:30]
                            target_name = name_map.get(target, target)[:30]

                            G.add_edge(source_name, target_name)
                            edge_labels[(source_name, target_name)] = reltype
            
            print(f"✓ Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            
            # Create visualization
            plt.figure(figsize=(20, 16))
            
            # Use spring layout for positioning
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
            
            # Draw nodes
            node_sizes = [G.degree(node) * 100 + 100 for node in G.nodes()]
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                  node_size=node_sizes, alpha=0.7)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                  arrows=True, arrowsize=10, alpha=0.5)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            plt.title("Chronic Stress Knowledge Graph (first 500 edges)", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            
            output_file = "stress_knowledge_graph.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"\n✅ Graph saved to: {output_file}")
            
            # Create a focused subgraph around "Stress"
            print("\nCreating focused subgraph around 'Stress'...")
            stress_neighbors = list(G.neighbors("Stress")) if "Stress" in G else []
            if stress_neighbors:
                subgraph_nodes = ["Stress"] + stress_neighbors[:30]
                H = G.subgraph(subgraph_nodes)
                
                plt.figure(figsize=(16, 12))
                pos_sub = nx.spring_layout(H, k=1, iterations=50, seed=42)
                
                # Color nodes by distance from Stress
                node_colors = ['red' if node == 'Stress' else 'lightblue' for node in H.nodes()]
                node_sizes = [1500 if node == 'Stress' else 500 for node in H.nodes()]
                
                nx.draw_networkx_nodes(H, pos_sub, node_color=node_colors,
                                      node_size=node_sizes, alpha=0.8)
                nx.draw_networkx_edges(H, pos_sub, edge_color='gray',
                                      arrows=True, arrowsize=15, alpha=0.6, width=2)
                nx.draw_networkx_labels(H, pos_sub, font_size=10, font_weight='bold')
                
                plt.title("Stress-Centered Knowledge Subgraph", fontsize=16, fontweight='bold')
                plt.axis('off')
                plt.tight_layout()
                
                output_file2 = "stress_centered_graph.png"
                plt.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"✅ Focused graph saved to: {output_file2}")

            # Statistics
            print("\n📊 GRAPH STATISTICS:")
            print(f"   Total nodes: {G.number_of_nodes()}")
            print(f"   Total edges: {G.number_of_edges()}")
            print(f"   Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
            
            # Find most central nodes
            if G.number_of_nodes() > 0:
                degree_cent = nx.degree_centrality(G)
                top_central = sorted(degree_cent.items(), key=lambda x: -x[1])[:10]
                print(f"\n   Top 10 most central nodes:")
                for node, centrality in top_central:
                    print(f"     {node}: {centrality:.3f}")

if __name__ == "__main__":
    create_graph_visualization()