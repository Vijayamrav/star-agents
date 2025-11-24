from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    clean_data_node,
    generate_statistics_node,
    detect_anomalies_node,
    create_visualizations_node,
    generate_insights_node,
    generate_sql_node
)


def create_analysis_graph():
    """Create the LangGraph workflow for data analysis"""
    
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("clean_data", clean_data_node)
    workflow.add_node("generate_statistics", generate_statistics_node)
    workflow.add_node("detect_anomalies", detect_anomalies_node)
    workflow.add_node("create_visualizations", create_visualizations_node)
    workflow.add_node("generate_insights", generate_insights_node)
    workflow.add_node("generate_sql", generate_sql_node)
    
    # Define the workflow edges (sequential execution)
    workflow.set_entry_point("clean_data")
    workflow.add_edge("clean_data", "generate_statistics")
    workflow.add_edge("generate_statistics", "detect_anomalies")
    workflow.add_edge("detect_anomalies", "create_visualizations")
    workflow.add_edge("create_visualizations", "generate_insights")
    workflow.add_edge("generate_insights", "generate_sql")
    workflow.add_edge("generate_sql", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Create the compiled graph
analysis_graph = create_analysis_graph()
