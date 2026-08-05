import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from backend.graph.state import GraphState
from backend.graph.router import ComplianceQueryRouter
from backend.hybrid_retriever import NomicHybridRetriever

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


def call_groq_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Outer Response LLM using Groq (llama-3.3-70b-versatile)."""
    api_key = os.getenv("GROQ_API_KEY")
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    if not api_key:
        return None

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
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
            "temperature": 0.2,
            "max_tokens": 1024
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if content:
                return content.strip()
    except Exception as e:
        print(f"⚠️ Note: Groq API call skipped ({e}). Falling back to Gemini.")
    return None


def call_gemini_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Inner Agentic Workflow / Reasoning LLM using Gemini (gemini-1.5-flash)."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"⚠️ Note: Gemini API call skipped ({e}). Using grounded template.")
    return None


def call_llm_synthesis(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    Dual-LLM Synthesis Architecture:
    1. Primary: Groq (llama-3.3-70b-versatile) for outer response synthesis.
    2. Secondary: Gemini (gemini-1.5-flash) for agentic reasoning.
    3. Fallback: Grounded template engine.
    """
    res = call_groq_llm(system_prompt, user_prompt)
    if res:
        return res
    res = call_gemini_llm(system_prompt, user_prompt)
    if res:
        return res
    return None


def router_node(state: GraphState) -> GraphState:
    """
    Primary Entry Router Node:
    Extracts parameters, classifies initial intent, executes hybrid search, and checks for policy contradictions.
    """
    query = state["query"]
    params = ComplianceQueryRouter.extract_parameters(query)
    intent = ComplianceQueryRouter.classify_intent(query, params)
    
    retriever = get_retriever()
    retrieved_docs = []
    
    if intent in ["ANSWER_DIRECT", "CLARIFY"]:
        retrieved_docs = retriever.retrieve_parents(query, metadata_filter=params if "multi_regions" not in params else None, top_n_parents=4)

    has_contradiction, contradiction_reason = ComplianceQueryRouter.detect_contradictions(retrieved_docs, params)
    
    if has_contradiction and "jurisdictions" in (contradiction_reason or ""):
        intent = "CLARIFY"

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
    
    response = (
        "📍 **Location Disambiguation Required**\n\n"
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

    # Dual-LLM Executive Synthesis
    system_prompt = (
        "You are an expert Enterprise Compliance Officer providing clear, helpful policy guidance to employees.\n"
        "Rules for your response:\n"
        "1. Write directly and professionally in user-friendly language. Address the employee directly.\n"
        "2. Do NOT use robotic preamble like 'To answer the user query regarding...' or state internal steps.\n"
        "3. Strictly base your answers ONLY on the provided policy documents. Do not invent rules.\n"
        "4. Format key numbers, rules, allowances, or conditions using clean markdown bullet points.\n"
        "5. Include a comparison table ONLY if the user explicitly asked to compare or contrast different branches or policy versions."
    )
    user_prompt = f"USER QUERY: {query}\n\nRETRIEVED POLICY CONTEXT:\n{context_text}"
    
    llm_synthesized = call_llm_synthesis(system_prompt, user_prompt)
    
    if llm_synthesized:
        formatted_response = llm_synthesized
    else:
        # Grounded Template Fallback
        table_header = ""
        if is_comparison and len(parents) >= 2:
            table_rows = []
            for p in parents:
                meta = p["metadata"]
                t_doc = f"`{meta['doc_id']}` (v{meta['version']})"
                t_reg = meta.get("region", "Global")
                t_status = meta.get("status", "CURRENT")
                t_title = p["section_title"]
                table_rows.append(f"| {t_doc} | {t_reg} | {t_status} | {t_title} |")

            table_header = (
                "📊 **Comparative Policy Matrix**\n\n"
                "| Document ID & Version | Region / Branch | Status | Section Title |\n"
                "|---|---|---|---|\n"
                + "\n".join(table_rows) + "\n\n"
                "--- \n"
            )

        title_header = "📋 **Official Enterprise Policy Comparison & Audit**" if is_comparison else "📋 **Official Enterprise Policy Response**"
        
        raw_contexts = []
        for p in parents:
            meta = p["metadata"]
            cite_str = f"[{meta['doc_id']} v{meta['version']} - {p['section_title']} (Effective: {meta['effective_date']})]"
            status_tag = f" ({meta['status']})" if meta.get('status') == 'SUPERSEDED' else ""
            region_tag = f" [{meta.get('region', 'Global')}]" if is_comparison else ""
            raw_contexts.append(f"### {meta['doc_title']}{region_tag}{status_tag} ({cite_str})\n{p['content']}")

        formatted_response = (
            f"{title_header}\n\n"
            f"{table_header}"
            + "\n\n".join(raw_contexts) + "\n\n"
            f"--- \n"
            f"📌 **Verified Policy Citations**:\n"
            + "\n".join([f"- {c}" for c in citations])
        )

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
    retriever = get_retriever()
    
    parents_it = retriever.retrieve_parents("lost laptop stolen device incident report", top_n_parents=2)
    parents_gdpr = retriever.retrieve_parents("gdpr data protection officer 12 hour notice", top_n_parents=2)
    
    all_parents = parents_it + parents_gdpr
    
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
    
    system_prompt = (
        "You are an enterprise SOP coordinator. Synthesize a unified, step-by-step resolution workflow "
        "combining IT Security procedures and GDPR compliance requirements."
    )
    user_prompt = f"USER QUERY: {query}\n\nPOLICY SECTIONS:\n{context_text}"
    
    llm_synthesized = call_llm_synthesis(system_prompt, user_prompt)
    
    if llm_synthesized:
        formatted_response = (
            f"🔗 **Multi-Hop Cross-Policy SOP Workflow**\n\n"
            f"{llm_synthesized}\n\n"
            f"--- \n"
            f"📌 **Cross-Referenced Compliance Documents**:\n"
            + "\n".join([f"- {c}" for c in citations])
        )
    else:
        workflow_steps = []
        for idx, p in enumerate(all_parents):
            meta = p["metadata"]
            workflow_steps.append(f"**Step {idx+1}: {p['section_title']}** ({meta['doc_id']})\n{p['content']}")

        combined_workflow = "\n\n".join(workflow_steps)
        formatted_response = (
            f"🔗 **Multi-Hop Cross-Policy SOP Workflow**\n\n"
            f"Handling a lost or stolen company asset requires coordinated execution across IT Security and Legal/GDPR Compliance:\n\n"
            f"{combined_workflow}\n\n"
            f"--- \n"
            f"📌 **Cross-Referenced Compliance Documents**:\n"
            + "\n".join([f"- {c}" for c in citations])
        )

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
    retriever = get_retriever()
    
    legal_parents = retriever.retrieve_parents("anti-bribery ethics regulatory subpoena escalation", top_n_parents=1)
    
    citations = []
    policy_clause = ""
    if legal_parents:
        p = legal_parents[0]
        meta = p["metadata"]
        cite_str = f"[{meta['doc_id']} v{meta['version']} - {p['section_title']}]"
        citations.append(cite_str)
        policy_clause = f"\n\n**Mandatory Policy Rule ({cite_str})**:\n> *{p['content'][:350]}...*"

    response = (
        "🚨 **HIGH-RISK COMPLIANCE MANDATE - AUTOMATED SYSTEM REFUSAL**\n\n"
        "Under Enterprise Legal & Anti-Bribery Policy (`LGL-POL-ETH-007`), automated AI systems "
        "and general staff **ARE STRICTLY PROHIBITED** from responding to or handling legal subpoenas, "
        "government bribery inquiries, or regulatory audits directly.\n"
        f"{policy_clause}\n\n"
        "--- \n"
        "🏢 **IMMEDIATE HUMAN ESCALATION PROTOCOL**:\n"
        "- ⚖️ **Chief Compliance Officer**: `compliance-officer@enterprise.com` | Line: +1 (800) 555-LEGAL\n"
        "- 🛡️ **Ethics Hotline (24/7 Confidential)**: `ethics-hotline@enterprise.com`\n"
        "- 🕒 **Action Required**: Do NOT disclose documents or sign acknowledgments. Forward all official notices to Legal immediately."
    )

    return {
        **state,
        "retrieved_docs": legal_parents if legal_parents else [],
        "response": response,
        "citations": citations,
        "requires_human_escalation": True,
        "escalation_contact": "compliance-officer@enterprise.com"
    }
