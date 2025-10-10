#!/usr/bin/env python3
"""
Script to upload and explore the Chronic Stress Analysis JSON data in MORK.
This demonstrates how to work with large JSON datasets in MORK.
"""

import sys
import json
from pathlib import Path
from client import ManagedMORK

# Path to your JSON file
JSON_FILE = "/home/mrx/work/goku/MORK/The_Lethal_Mechanisms_of_Chronic_Stress_A_Multidisciplinary_Analysis.json"

def main():
    print("=" * 80)
    print("MORK Chronic Stress Data Explorer")
    print("=" * 80)
    
    # Connect to running MORK server
    print("\n[1] Connecting to MORK server...")
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        
        # Create a workspace for our data
        with server.work_at("stress-data").and_clear() as workspace:
            print("✓ Connected to MORK server")
            print(f"✓ Created workspace: stress-data")
            
            # Upload the JSON file
            print(f"\n[2] Uploading JSON file: {JSON_FILE}")
            print("    This may take a moment for large files...")
            
            # Import the JSON file using file:// URI
            file_uri = f"file://{JSON_FILE}"
            workspace.sexpr_import_(file_uri).block()
            print("✓ JSON data uploaded successfully")
            
            # Explore the data structure
            print("\n[3] Exploring data structure...")
            
            # Get a sample of the data
            print("\n--- Sample Data (first 10 items) ---")
            sample = workspace.download_(max_results=10)
            print(sample.data)
            
            # Count total items
            print("\n[4] Querying the data...")
            
            # Example queries - adjust based on your JSON structure
            print("\n--- Query Examples ---")
            
            # Query 1: Get all top-level keys/structure
            print("\n• Query 1: Exploring top-level structure")
            result = workspace.download_(max_results=20)
            if result.data:
                print(result.data[:1000] + "..." if len(result.data) > 1000 else result.data)
            
            # Query 2: Pattern matching example
            # Adjust this based on your JSON structure
            print("\n• Query 2: Pattern matching")
            # This looks for specific patterns in your data
            # For example, if your JSON has nested structures like (section (topic ...))
            result = workspace.download("(section $x)", "$x", max_results=10)
            if result.data:
                print(result.data[:500] + "..." if len(result.data) > 500 else result.data)
            else:
                print("No matches - adjust pattern based on your data structure")
            
            # Transform example - create relationships
            print("\n[5] Transform example - creating derived data...")
            # This is an example of how to create new relationships from existing data
            # workspace.transform(
            #     ("(data $x)",),  # Pattern to match
            #     ("(processed $x)",)  # Template for new data
            # ).block()
            print("(Example - uncomment and adjust for your data structure)")
            
            print("\n" + "=" * 80)
            print("EXPLORATION COMPLETE")
            print("=" * 80)
            
            # Tips for working with the data
            print_usage_tips()

def print_usage_tips():
    """Print helpful tips for working with MORK"""
    print("\n📚 Tips for Working with Your Data in MORK:")
    print("\n1. QUERY PATTERNS:")
    print("   - Use '$x' as wildcards in patterns")
    print("   - Example: download('(topic $x)', '$x') matches (topic ...) structures")
    print("   - Combine patterns: download('(section $s (topic $t))', '($s $t)')")
    
    print("\n2. TRANSFORMS:")
    print("   - Create new relationships from existing data")
    print("   - Example: transform(('(A $x)',), ('(B $x)',)) creates B from A")
    print("   - Can match multiple patterns and create multiple outputs")
    
    print("\n3. EXPLORATION:")
    print("   - Use explore_() to navigate the data structure interactively")
    print("   - Start with small max_results values to understand structure")
    print("   - Then scale up once you know what you're looking for")
    
    print("\n4. VISUALIZATION:")
    print("   - Export data: workspace.sexpr_export_('output.metta')")
    print("   - Process exported data with pandas, networkx, or matplotlib")
    print("   - Create graphs showing relationships between concepts")
    
    print("\n5. ADVANCED QUERIES:")
    print("   - Chain transforms to create complex derived data")
    print("   - Use MM2 execution for logic-based reasoning")
    print("   - Combine with Python for hybrid symbolic/numeric analysis")

def create_visualization_script():
    """Create a separate script for visualizing MORK data"""
    script_path = Path("python/visualize_stress_data.py")
    
    vis_script = '''#!/usr/bin/env python3
"""
Visualization script for MORK stress data.
Requires: matplotlib, networkx, pandas
"""

import matplotlib.pyplot as plt
import networkx as nx
from client import ManagedMORK

def visualize_graph():
    """Create a network graph from MORK data"""
    print("Creating visualization...")
    
    with ManagedMORK.connect(url="http://127.0.0.1:8000") as server:
        with server.work_at("stress-data") as workspace:
            # Download relationship data
            data = workspace.download_("$x", "$x", max_results=100)
            
            # Parse and create graph
            G = nx.DiGraph()
            
            # Add your parsing logic here based on your data structure
            # Example:
            # for line in data.data.split('\\n'):
            #     if line.startswith('(relates'):
            #         # Parse and add edges
            #         pass
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                   node_size=500, font_size=8, arrows=True)
            plt.title("Chronic Stress Relationships")
            plt.savefig("stress_graph.png", dpi=300, bbox_inches='tight')
            print("✓ Graph saved to stress_graph.png")

if __name__ == "__main__":
    visualize_graph()
'''
    
    with open(script_path, 'w') as f:
        f.write(vis_script)
    
    print(f"\n✓ Created visualization script: {script_path}")
    print("  Install dependencies: pip install matplotlib networkx pandas")
    print(f"  Run: python {script_path}")

if __name__ == "__main__":
    try:
        main()
        
        # Offer to create visualization script
        print("\n" + "=" * 80)
        response = input("\nCreate visualization script? (y/n): ").lower()
        if response == 'y':
            create_visualization_script()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)