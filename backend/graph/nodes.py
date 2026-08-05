import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from backend.graph.state import GraphState
from backend.graph.router import ComplianceQueryRouter
from backend.hybrid_retriever import NomicHybridRetriever
from backend.graph.prompts import ANSWER_DIRECT_SYSTEM_PROMPT, MULTI_HOP_SYSTEM_PROMPT

# Automatically load environment variables from backend/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=env_path)
load_dotenv()

retriever_instance = None

def get_retriever():
    global retriever_instance
    if retriever_instance is None:
        retriever_instance = NomicHybridRetriever()
    return retriever_instance


def call_nvidia_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Inner Agentic Workflow / Reasoning LLM using NVIDIA NIM (Nemotron)."""
    api_key = os.getenv("NVIDIA_API_KEY")
    model_name = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
    if not api_key:
        print("⚠️ Note: NVIDIA API Key not found.")
        return None

    try:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("choices") and data["choices"][0].get("message"):
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ Note: NVIDIA API call skipped/failed ({e}).")
    return None


def router_node(state: GraphState) -> GraphState:
    """
    Primary Entry Router Node:
    Extracts parameters, classifies initial intent, executes hybrid search, and checks for policy contradictions.
    """
    query = state["query"]
    print(f"\n⚡ [AGENT GRAPH] Starting Router Node for query: '{query}'")
    params = ComplianceQueryRouter.extract_parameters(query)
    intent = ComplianceQueryRouter.classify_intent(query, params)
    
    print(f"⚡ [STEP 1] Intent Classified: '{intent}' | Filters Extracted: {params}")
    
    retriever = get_retriever()
    retrieved_docs = []
    
    if intent in ["ANSWER_DIRECT", "CLARIFY"]:
        print(f"⚡ [STEP 2] Executing Parallel BM25 + Vector Search + RRF + Cross-Encoder Re-Ranking...")
        retrieved_docs = retriever.retrieve_parents(query, metadata_filter=params if "multi_regions" not in params else None, top_n_parents=4)
        print(f"   |-- Retrieved {len(retrieved_docs)} policy sections.")

    has_contradiction, contradiction_reason = ComplianceQueryRouter.detect_contradictions(retrieved_docs, params)
    
    if has_contradiction and "jurisdictions" in (contradiction_reason or ""):
        intent = "CLARIFY"
        print(f"[ROUTER DETECT] Location ambiguity detected across regional policies -> Route to CLARIFY")

    return {
        **state,
        "intent": intent,
        "parameters": params,
        "retrieved_docs": retrieved_docs,
        "has_contradiction": has_contradiction,
        "contradiction_reason": contradiction_reason
    }


def clarify_node(state: GraphState) -> GraphState:
    """
    CLARIFY Node (Ambiguity & Policy Conflict Handler):
    Asks targeted disambiguation questions when queries lack location context.
    """
    query = state["query"]
    print(f"\n⚡ [AGENT GRAPH] Entering CLARIFY Node...")
    print(f"⚡ [STEP 3] Presenting location buttons to user...")
    
    response = (
        "**Location Disambiguation Required**\n\n"
        f"Your query *\"{query}\"* touches on compliance standards that vary by branch location (such as annual leave allowances, hybrid work rules, and stipends).\n\n"
        "To provide the exact binding policy rule for your workplace, please select your office location below:"
    )
    
    return {
        **state,
        "response": response,
        "citations": [],
        "requires_human_escalation": False,
        "escalation_contact": None
    }


def answer_direct_node(state: GraphState) -> GraphState:
    """
    ANSWER_DIRECT Agent Node:
    Uses Generative LLM (Gemini) to process retrieved parent chunks, synthesize natural language answers,
    and build comparative matrices.
    """
    query = state["query"]
    print(f"\n⚡ [AGENT GRAPH] Entering ANSWER_DIRECT Node...")
    params = state.get("parameters", {})
    parents = state.get("retrieved_docs", [])
    retriever = get_retriever()
    
    if not parents:
        parents = retriever.retrieve_parents(query, metadata_filter=None, top_n_parents=4)

    if not parents:
        fallback_response = (
            "⚠️ **Policy Document Not Found in System**\n\n"
            f"The policy requested (*'{query}'*) is currently **not present** in the enterprise document repository.\n\n"
            "To prevent compliance hallucinations, automated answers are strictly limited to indexed documents.\n\n"
            "📌 **Action Required**:\n"
            "- Contact the HR/Compliance Helpdesk at `compliance@enterprise.com` to request this document.\n"
            "- Submit a document update ticket if this policy was recently enacted."
        )
        return {
            **state,
            "response": fallback_response,
            "citations": [],
            "requires_human_escalation": False,
            "escalation_contact": None
        }

    citations = []
    doc_contexts = []
    
    is_comparison = "multi_regions" in params or any(w in query.lower() for w in ["difference", "compare", "versus", "vs", "between", "what changed"])

    for p in parents:
        meta = p["metadata"]
        cite_str = f"[{meta['doc_id']} v{meta['version']} - {p['section_title']} (Effective: {meta['effective_date']})]"
        citations.append(cite_str)
        
        status_tag = f" ({meta['status']})" if meta.get('status') == 'SUPERSEDED' else ""
        region_tag = f" [{meta.get('region', 'Global')}]" if is_comparison else ""
        doc_contexts.append(f"DOCUMENT ID: {meta['doc_id']} (v{meta['version']}){status_tag} | REGION: {meta.get('region')}\nSECTION: {p['section_title']}\nCONTENT:\n{p['content']}")

    context_text = "\n\n".join(doc_contexts)

    # LLM Executive Synthesis
    print(f"⚡ [STEP 3] Generating executive answer using {len(parents)} retrieved policy sections (NVIDIA)...")
    system_prompt = ANSWER_DIRECT_SYSTEM_PROMPT
    user_prompt = f"USER QUERY: {query}\n\nRETRIEVED POLICY CONTEXT:\n{context_text}"
    
    llm_synthesized = call_nvidia_llm(system_prompt, user_prompt)
    
    if llm_synthesized:
        formatted_response = llm_synthesized
    else:
        formatted_response = "⚠️ System encountered an error connecting to the generative model."

    return {
        **state,
        "retrieved_docs": parents,
        "response": formatted_response,
        "citations": citations,
        "requires_human_escalation": False,
        "escalation_contact": None
    }


def multi_hop_node(state: GraphState) -> GraphState:
    """
    MULTI_HOP Agent Node:
    Uses Generative LLM to synthesize multi-document cross-department SOP workflows.
    """
    query = state["query"]
    print(f"\n⚡ [AGENT GRAPH] Entering MULTI_HOP Node...")
    print(f"⚡ [STEP 2] Multi-Hop Executing Dynamic Retrieval for query: '{query}'")
    retriever = get_retriever()
    
    all_parents = retriever.retrieve_parents(query, top_n_parents=4)
    print(f"   |-- Retrieved {len(all_parents)} multi-hop policy sections.")
    
    if not all_parents:
        return answer_direct_node(state)

    citations = []
    doc_contexts = []

    for p in all_parents:
        meta = p["metadata"]
        cite_str = f"[{meta['doc_id']} v{meta['version']} - {p['section_title']}]"
        citations.append(cite_str)
        doc_contexts.append(f"SECTION ({meta['doc_id']}): {p['section_title']}\nCONTENT:\n{p['content']}")

    context_text = "\n\n".join(doc_contexts)
    
    system_prompt = MULTI_HOP_SYSTEM_PROMPT
    user_prompt = f"USER QUERY: {query}\n\nPOLICY SECTIONS:\n{context_text}"
    
    print(f"⚡ [STEP 3] Synthesizing Multi-Hop workflow using {len(all_parents)} documents (NVIDIA)...")
    llm_synthesized = call_nvidia_llm(system_prompt, user_prompt)
    
    if llm_synthesized:
        formatted_response = llm_synthesized
    else:
        formatted_response = "⚠️ System encountered an error connecting to the generative model."

    return {
        **state,
        "retrieved_docs": all_parents,
        "response": formatted_response,
        "citations": citations,
        "requires_human_escalation": False,
        "escalation_contact": None
    }


def escalate_node(state: GraphState) -> GraphState:
    """
    ESCALATE Node:
    Triggered for high-risk legal queries, anti-bribery reports, or regulatory subpoenas.
    Refuses automated resolution and enforces official Human SME Escalation Protocol.
    """
    query = state["query"]
    print(f"\n🚨 [AGENT GRAPH] Entering ESCALATE Node...")
    print(f"⚡ [STEP 2] Escalate Executing Legal Policy Retrieval...")
    retriever = get_retriever()
    
    legal_parents = retriever.retrieve_parents(query, top_n_parents=1)
    print(f"   |-- Retrieved {len(legal_parents)} legal sections.")
    
    citations = []
    policy_clause = ""
    if legal_parents:
        p = legal_parents[0]
        meta = p["metadata"]
        cite_str = f"[{meta['doc_id']} v{meta['version']} - {p['section_title']}]"
        citations.append(cite_str)
        policy_clause = f"\n\n**Mandatory Policy Rule ({cite_str})**:\n> *{p['content'][:350]}...*"

    response = (
        "**HIGH-RISK COMPLIANCE MANDATE - AUTOMATED SYSTEM REFUSAL**\n\n"
        "Under Enterprise Legal & Anti-Bribery Policy (`LGL-POL-ETH-007`), automated AI systems "
        "and general staff **ARE STRICTLY PROHIBITED** from responding to or handling legal subpoenas, "
        "government bribery inquiries, or regulatory audits directly.\n"
        f"{policy_clause}\n\n"
        "--- \n"
        "**IMMEDIATE HUMAN ESCALATION PROTOCOL**:\n"
        "- **Chief Compliance Officer**: `compliance-officer@enterprise.com` | Line: +1 (800) 555-LEGAL\n"
        "- **Ethics Hotline (24/7 Confidential)**: `ethics-hotline@enterprise.com`\n"
        "- **Action Required**: Do NOT disclose documents or sign acknowledgments. Forward all official notices to Legal immediately."
    )

    return {
        **state,
        "retrieved_docs": legal_parents if legal_parents else [],
        "response": response,
        "citations": citations,
        "requires_human_escalation": True,
        "escalation_contact": "compliance-officer@enterprise.com"
    }
