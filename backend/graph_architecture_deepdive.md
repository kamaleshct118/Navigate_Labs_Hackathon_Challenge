# Enterprise Compliance AI Assistant - LangGraph State Machine Architecture

## 1. Graph State Schema & Data Contract (`GraphState`)

The state machine maintains a shared, immutable-update state dictionary (`GraphState`) passed sequentially across all nodes.

```python
class GraphState(TypedDict):
    query: str                                # Active user query (or merged multi-turn query)
    intent: Optional[str]                     # Classified intent: CLARIFY | ANSWER_DIRECT | MULTI_HOP | ESCALATE
    parameters: Dict[str, Any]                # Extracted metadata: region, branch_id, department, multi_regions
    retrieved_docs: List[Dict[str, Any]]      # Pre-fetched parent section chunks with metadata
    has_contradiction: bool                   # True if conflicting branch policies detected without location
    contradiction_reason: Optional[str]       # Human-readable breakdown of the policy conflict
    response: Optional[str]                   # Final synthesized Markdown answer or refusal notice
    citations: List[str]                      # Verified document citations [DOC_ID vVERSION - Section (Date)]
    requires_human_escalation: bool           # True if high-risk legal/anti-bribery protocol triggered
    escalation_contact: Optional[str]         # SME contact (e.g. compliance-officer@enterprise.com)
```

---

## 2. Graph Topology & Conditional Decision Engine

```text
                        ┌──────────────────────────────┐
                        │        [ START ENTRY ]       │
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │         router_node          │
                        │ (Primary Intelligence Engine)│
                        └──────────────┬───────────────┘
                                       │
                    Evaluates route_next_step(state)
                                       │
      ┌────────────────────┬───────────┴───────────┬────────────────────┐
      │ (intent==CLARIFY)  │ (intent==DIRECT)      │ (intent==MULTI_HOP)│ (intent==ESCALATE)
      ▼                    ▼                       ▼                    ▼
┌──────────────┐   ┌──────────────┐        ┌──────────────┐     ┌──────────────┐
│ clarify_node │   │answer_direct │        │multi_hop_node│     │escalate_node │
└──────┬───────┘   └──────┬───────┘        └──────┬───────┘     └──────┬───────┘
       │                  │                       │                    │
       └──────────────────┴───────────┬───────────┴────────────────────┘
                                      │
                                      ▼
                        ┌──────────────────────────────┐
                        │           [ END ]            │
                        └──────────────────────────────┘
```

---

## 3. Node-by-Node Execution Deep Dive

### 🔹 Node 1: `router_node` (Primary Intelligence Engine)
* **Purpose**: Primary entry point. Extracts query metadata, performs 4-stage hybrid search, and evaluates contradiction rules.
* **Execution Flow**:
  1. **Dynamic Parameter Extraction**: Compares query against active taxonomy in `parent_docs.json` to extract `region`, `branch_id`, or `department`.
  2. **Intent Classification**: Evaluates high-risk keywords (FCPA, subpoena $\rightarrow$ `ESCALATE`), multi-hop keywords (lost laptop, GDPR breach $\rightarrow$ `MULTI_HOP`), or location ambiguity ($\rightarrow$ `CLARIFY`).
  3. **Parallel Hybrid Search**: Executes 4-stage retrieval (BM25 + Nomic Vector Search $\rightarrow$ RRF Fusion $\rightarrow$ Cross-Encoder Re-Ranking).
  4. **Policy Contradiction Detection**: If retrieved chunks belong to multiple regions and user did not specify location, flags `has_contradiction = True` and overrides intent to `CLARIFY`.
* **State Output**: Mutates `intent`, `parameters`, `retrieved_docs`, `has_contradiction`, `contradiction_reason`.

---

### 🔹 Node 2: `clarify_node` (Ambiguity & Conflict Resolution Agent)
* **Purpose**: Triggered when a query matches multiple regional policy standards without location context.
* **Execution Flow**:
  1. Inspects `state["retrieved_docs"]` to extract the conflicting regional variants (e.g. `US-NY` vs `EU-London`).
  2. Formulates a transparent policy disambiguation prompt detailing the exact conflicting choices found.
  3. Returns quick-selection options (`US-NY`, `US-Austin`, `EU-London`).
* **State Output**: Sets `response`, `citations = []`, `requires_human_escalation = False`.

---

### 🔹 Node 3: `answer_direct_node` (Grounded Answer & Matrix Comparison Agent)
* **Purpose**: Synthesizes verified natural language answers, comparative tables, and citations.
* **Execution Flow**:
  1. **Tier 2/3 Fallback**: If retrieved docs are empty, runs global search. If still empty, triggers **Graceful Non-Hallucination Refusal**.
  2. **Comparison Matrix Detection**: If query contains comparison keywords or `multi_regions` parameter, builds a structured **Comparative Policy Matrix Table** (`Document ID | Region | Status | Title`).
  3. **Generative LLM Synthesis**: Passes retrieved parent sections to `Google Gemini 1.5/2.5 Flash` to synthesize a grounded, professional response.
  4. **Citation Extraction**: Extracts exact citations (`[HR-POL-US-001 v2.0 - Section 1]`).
* **State Output**: Sets `response`, `citations`, `requires_human_escalation = False`.

---

### 🔹 Node 4: `multi_hop_node` (Cross-Department SOP Workflow Agent)
* **Purpose**: Handles complex incidents touching multiple policy documents (e.g., Lost Laptop + GDPR Notice).
* **Execution Flow**:
  1. Retrieves parent sections across IT Infrastructure (`SOP-IT-SEC-004`) and Legal (`HR-POL-EU-003`).
  2. Passes multi-doc context to Gemini LLM to synthesize a single step-by-step resolution plan (`Step 1: IT Remote Lock` $\rightarrow$ `Step 2: Security Form` $\rightarrow$ `Step 3: 12-hr GDPR DPO Notice`).
* **State Output**: Sets `response`, `citations`, `requires_human_escalation = False`.

---

### 🔹 Node 5: `escalate_node` (High-Risk Legal Circuit Breaker Agent)
* **Purpose**: Enforces mandatory automated refusal for legal subpoenas, government bribery inquiries, or regulatory audits.
* **Execution Flow**:
  1. Retrieves relevant anti-bribery governance section (`LGL-POL-ETH-007`).
  2. Formulates an immediate automated refusal notice citing company policy.
  3. Provides 24/7 Chief Compliance Officer email (`compliance-officer@enterprise.com`) and Ethics Hotline.
* **State Output**: Sets `response`, `citations`, `requires_human_escalation = True`, `escalation_contact = "compliance-officer@enterprise.com"`.
