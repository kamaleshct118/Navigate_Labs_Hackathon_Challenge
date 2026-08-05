import sys
import os
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.graph.agent_graph import run_compliance_agent
from backend.graph.session_cache import session_cache

from backend.graph.nodes import get_retriever, call_groq_llm, call_gemini_llm

app = FastAPI(
    title="Enterprise Compliance Agentic RAG API",
    description="Production Multi-Node Compliance Assistant with Parallel BM25 + Cosine Retrieval, RRF Fusion & Cross-Encoder Re-Ranking",
    version="1.0.0"
)

# Enable CORS for Frontend UI (React / Streamlit / Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def preload_models_and_verify_keys():
    """
    Startup Hook: Pre-loads all ML models (Nomic Embed, BM25, Cross-Encoder) and verifies API keys
    so the server is 100% warmed up and instant for first user request.
    """
    print("============================================================")
    print(" [STARTUP] Warming up Compliance Retriever Models & LLM Keys...")
    
    # 1. Warm up Retriever Models
    try:
        retriever = get_retriever()
        _ = retriever.reranker
        print(" [STARTUP] Nomic Embeddings & Cross-Encoder Re-Ranker Warmed Up!")
    except Exception as e:
        print(f" [STARTUP WARNING] Model preloader note: {e}")

    # 2. Test Groq Outer LLM Key
    groq_res = call_groq_llm("Respond with READY", "System test")
    if groq_res:
        print(" [STARTUP] Groq (llama-3.3-70b-versatile) API Key Verified & Connected!")
    else:
        print(" [STARTUP WARNING] Groq API Key unconfigured or unreachable.")

    # 3. Test Gemini Agentic LLM Key
    gemini_res = call_gemini_llm("Respond with READY", "System test")
    if gemini_res:
        print(" [STARTUP] Gemini (gemini-3.6-flash) API Key Verified & Connected!")
    else:
        print(" [STARTUP WARNING] Gemini API Key unconfigured or unreachable.")
        
    print(" [STARTUP] All System Models & Services Ready!")
    print("============================================================")


# --- Request & Response Schemas ---

class ChatRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "What is the annual PTO allowance for US New York branch?"})
    session_id: Optional[str] = Field("default_session", json_schema_extra={"example": "emp_session_101"})


class ChatResponse(BaseModel):
    query: str
    session_id: Optional[str]
    intent: str
    response: str
    citations: List[str]
    has_contradiction: bool
    contradiction_reason: Optional[str]
    requires_human_escalation: bool
    escalation_contact: Optional[str]


class SessionInfoResponse(BaseModel):
    session_id: str
    has_pending_clarification: bool
    pending_query: Optional[str]
    options_offered: List[str]


# --- API Endpoints ---

@app.get("/api/health", summary="System Health & Readiness Check")
def health_check():
    """Returns status of ChromaDB vector store, Nomic embedding function, and LangGraph agent framework."""
    return {
        "status": "online",
        "service": "Enterprise Compliance Agent Backend",
        "vector_store": "ChromaDB Persistent (HNSW Cosine)",
        "embedding_model": "nomic-ai/nomic-embed-text-v1.5",
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "decision_framework": "LangGraph State Machine (5-Node Router with Session Cache)"
    }


@app.post("/api/chat", response_model=ChatResponse, summary="Process Enterprise Compliance Query")
def process_compliance_query(request: ChatRequest):
    """
    Primary Compliance RAG Chat Endpoint:
    Executes 4-stage hybrid retrieval (BM25 + Cosine + RRF + Cross-Encoder) and LangGraph agent routing.
    Supports multi-turn session cache disambiguation via session_id.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    try:
        final_state = run_compliance_agent(request.query, session_id=request.session_id)
        return ChatResponse(
            query=final_state["query"],
            session_id=request.session_id,
            intent=final_state.get("intent", "ANSWER_DIRECT"),
            response=final_state.get("response", "No response generated."),
            citations=final_state.get("citations", []),
            has_contradiction=final_state.get("has_contradiction", False),
            contradiction_reason=final_state.get("contradiction_reason"),
            requires_human_escalation=final_state.get("requires_human_escalation", False),
            escalation_contact=final_state.get("escalation_contact")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing agent pipeline: {str(e)}")


@app.get("/api/session/{session_id}", response_model=SessionInfoResponse, summary="Inspect Active Session Cache State")
def get_session_status(session_id: str = Path(...)):
    """Inspects if a given user session has a pending policy clarification."""
    session_data = session_cache.get_session(session_id)
    if not session_data:
        return SessionInfoResponse(
            session_id=session_id,
            has_pending_clarification=False,
            pending_query=None,
            options_offered=[]
        )
    return SessionInfoResponse(
        session_id=session_id,
        has_pending_clarification=True,
        pending_query=session_data.get("pending_query"),
        options_offered=session_data.get("options_offered", [])
    )


@app.delete("/api/session/{session_id}", summary="Clear User Session Cache State")
def clear_session(session_id: str = Path(...)):
    """Resets conversational memory and clears pending clarifications for a session."""
    session_cache.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    print("============================================================")
    print(" 🚀 Enterprise Compliance Agentic RAG API Server")
    print(" Host: http://0.0.0.0:8000 | OpenAPI Docs: http://localhost:8000/docs")
    print("============================================================")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
