from typing import List, Dict, Any, Optional, TypedDict

class GraphState(TypedDict):
    """
    LangGraph Workflow State representation for the Enterprise Compliance Agent.
    Tracks user input, routing intent, extracted parameters, retrieved context, contradictions, and final response.
    """
    query: str
    intent: Optional[str]  # "CLARIFY", "ANSWER_DIRECT", "MULTI_HOP", "ESCALATE"
    parameters: Dict[str, Any]  # e.g., {"region": "US-NY", "branch_id": "US-NY-01"}
    retrieved_docs: List[Dict[str, Any]]  # Parent Sections retrieved from NomicHybridRetriever
    has_contradiction: bool
    contradiction_reason: Optional[str]
    response: Optional[str]
    citations: List[str]
    requires_human_escalation: bool
    escalation_contact: Optional[str]
