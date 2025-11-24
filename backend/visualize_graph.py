import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.graph import analysis_graph

def visualize_graph():
    """Generate a Mermaid diagram of the analysis graph"""
    print("Generating graph visualization...")
    
    try:
        # Get the graph definition in Mermaid format
        mermaid_graph = analysis_graph.get_graph().draw_mermaid()
        
        # Save to file
        output_file = "analysis_graph.mermaid"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mermaid_graph)
            
        print(f"Graph visualization saved to {output_file}")
        print("\nMermaid Graph Definition:")
        print("-" * 50)
        print(mermaid_graph)
        print("-" * 50)
        print("\nYou can view this graph at https://mermaid.live/")
        
    except Exception as e:
        print(f"Error visualizing graph: {str(e)}")

if __name__ == "__main__":
    visualize_graph()
