# services/orchestrator-agent/src/workflow/graph.py

from langgraph.graph import StateGraph, END
from .state import VideoGenerationState
from .nodes import creative_planner_node, asset_generator_node, post_production_node

# Create a new StateGraph with our defined state
workflow = StateGraph(VideoGenerationState)

# Add the nodes to the graph
workflow.add_node("creative_planner", creative_planner_node)
workflow.add_node("asset_generator", asset_generator_node)
workflow.add_node("post_production", post_production_node)

# Define the sequence of operations (the edges)
workflow.set_entry_point("creative_planner")
workflow.add_edge("creative_planner", "asset_generator")
workflow.add_edge("asset_generator", "post_production")
workflow.add_edge("post_production", END) # The special END node signifies the workflow is complete

# Compile the graph into a runnable LangChain object
graph_app = workflow.compile()

print("✅ LangGraph workflow compiled successfully!")