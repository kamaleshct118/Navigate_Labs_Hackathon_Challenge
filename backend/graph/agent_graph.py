from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from backend.graph.state import GraphState
from backend.graph.nodes import (
    router_node,
    clarify_node,
    answer_direct_node,
    multi_hop_node,
    escalate_node
)
from backend.graph.session_cache import session_cache

def route_next_step(state: GraphState) -> str:
    """Conditional Edge function evaluated after router_node mutates the state."""
    intent = state.get("intent", "ANSWER_DIRECT")
    
    if intent == "CLARIFY":
        return "clarify"
    elif intent == "MULTI_HOP":
        return "multi_hop"
    elif intent == "ESCALATE":
        return "escalate"
    else:
        return "answer_direct"


def create_agent_graph():
    """
    Builds and compiles the 5-Node Agentic Compliance LangGraph State Machine:
    [START] -> router -> (clarify | answer_direct | multi_hop | escalate) -> [END]
    """
    workflow = StateGraph(GraphState)
    
    # Add Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("answer_direct", answer_direct_node)
    workflow.add_node("multi_hop", multi_hop_node)
    workflow.add_node("escalate", escalate_node)
    
    # Set Entry Point
    workflow.set_entry_point("router")
    
    # Add Conditional Edge from router node to destination node
    workflow.add_conditional_edges(
        "router",
        route_next_step,
        {
            "clarify": "clarify",
            "answer_direct": "answer_direct",
            "multi_hop": "multi_hop",
            "escalate": "escalate"
        }
    )
    
    # Connect destination nodes to END
    workflow.add_edge("clarify", END)
    workflow.add_edge("answer_direct", END)
    workflow.add_edge("multi_hop", END)
    workflow.add_edge("escalate", END)
    
    return workflow.compile()


# Compiled Singleton Graph Instance
compliance_agent_app = create_agent_graph()


def run_compliance_agent(query: str, session_id: Optional[str] = None) -> GraphState:
    """
    High-level execution helper for running a query through the LangGraph pipeline.
    Includes Session Cache Layer resolution for multi-turn disambiguation conversations.
    """
    active_query = query
    is_cached_followup = False
    
    if session_id:
        active_query, is_cached_followup = session_cache.resolve_pending_clarification(session_id, query)
    
    initial_state: GraphState = {
        "query": active_query,
        "intent": None,
        "parameters": {},
        "retrieved_docs": [],
        "has_contradiction": False,
        "contradiction_reason": None,
        "response": None,
        "citations": [],
        "requires_human_escalation": False,
        "escalation_contact": None
    }
    
    final_state = compliance_agent_app.invoke(initial_state)
    
    # If final intent is CLARIFY and session_id is provided, store pending query in session cache
    if session_id and final_state.get("intent") == "CLARIFY":
        session_cache.set_pending_clarification(
            session_id=session_id,
            original_query=active_query,
            options_offered=["US-NY", "US-Austin", "EU-London"]
        )
        
    return final_state
