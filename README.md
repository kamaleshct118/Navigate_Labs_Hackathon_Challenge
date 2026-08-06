# 🏛️ Enterprise Compliance AI Assistant (Agentic RAG)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)

An enterprise-grade, highly deterministic Agentic Retrieval-Augmented Generation (RAG) system built to navigate, synthesize, and strictly enforce complex corporate compliance policies.

This system guarantees zero-hallucination legal policy retrieval by implementing a **LangGraph State Machine** combined with a rigid **Cross-Encoder Anti-Hallucination Threshold**. It is designed to intercept ambiguous queries, resolve regional contradictions (e.g., conflicting PTO policies between NY and London offices), and provide uncompromised accuracy for legal, HR, and IT security protocols.

---

## ✨ Core Features

* **🧠 Agentic Orchestration (LangGraph)**: Replaces traditional linear prompt chains with a state machine. Dynamically routes queries to specialized execution nodes (`clarify`, `escalate`, `multi-hop`, `answer_direct`).
* **⚖️ The Contradiction Engine**: Automatically detects when a user asks a broad policy question that has conflicting regional variants. Pauses execution and mounts a React disambiguation widget to ask the user for their location.
* **🛡️ Hard-coded Legal Circuit Breakers**: If a user asks for direct legal advice or makes a litigious threat, the system bypasses generative AI entirely and returns a hard-coded legal refusal to prevent corporate liability.
* **🔍 Hybrid RAG Pipeline**: Fuses **ChromaDB (HNSW / Dense)** and **BM25 (Sparse)** using **Reciprocal Rank Fusion (RRF)** for unparalleled retrieval accuracy.
* **🎯 Cross-Encoder Re-Ranking**: Uses `ms-marco-MiniLM` to calculate deep token-level cross-attention. If no document surpasses the strict relevance threshold, the system aborts generation ("Policy Not Found") rather than hallucinating an answer.
* **⏱️ In-Memory TTL Session Cache**: Maintains a strict 30-minute stateless pause/resume architecture, automatically swept by a background garbage collection thread to prevent memory leaks and protect PII.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend UI** | React 18, Vite, TypeScript, Tailwind CSS (Glassmorphism) |
| **API Gateway** | FastAPI (Python), Pydantic Strict Schemas |
| **Orchestration** | LangGraph, LangChain |
| **Vector Store** | ChromaDB (HNSW Graph), BM25 (In-Memory Lexical) |
| **Embeddings** | Nomic Embed Text v1.5 (Local, 768-dim) |
| **Re-Ranking** | MS-Marco MiniLM Cross-Encoder |
| **Inference LLM** | NVIDIA NIM (Nemotron) |

---

## 📂 Project Structure

```text
├── backend/
│   ├── main.py                     # FastAPI entry point & CORS
│   ├── chroma_builder.py           # Offline ingestion & version reconciliation
│   ├── loader.py                   # YAML front-matter parser & chunker
│   ├── hybrid_retriever.py         # Dense + Sparse + RRF + Cross-Encoder
│   ├── session_cache.py            # TTL Memory Dictionary & GC Thread
│   └── graph/                      # LangGraph Architecture
│       ├── agent_graph.py          # State Machine compilation
│       ├── nodes.py                # Execution nodes (router, clarify, escalate)
│       ├── state.py                # TypedDict state payload
│       └── prompts.py              # Strict system prompts
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Core layout & Chat history state
│   │   ├── main.tsx                # DOM mount
│   │   ├── index.css               # Glassmorphism design system
│   │   ├── types.ts                # TypeScript interfaces (mirrors backend payloads)
│   │   ├── components/             # React UI components (Disambiguation, Banners)
│   │   └── hooks/                  # Custom hooks (useSpeech, useHealth)
├── sample_docs/                    # Enterprise Markdown policies (HR, IT, Legal)
├── database/                       # Persisted ChromaDB & parent_docs.json
└── Project Documentation.docx      # 50-Page Enterprise Technical Design Document
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA NIM API Key (`NVIDIA_API_KEY`)

### 2. Backend Setup
Navigate to the backend directory and set up the Python environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
NVIDIA_API_KEY=your_nim_api_key_here
```

**Build the Vector Index:**
Before running the server, ingest the sample policies:
```bash
python chroma_builder.py
```

**Run the API Server:**
```bash
python main.py
```
*(The backend runs locally on http://localhost:8000)*

### 3. Frontend Setup
Open a new terminal, navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```
*(The UI runs locally on http://localhost:5173)*

---

## 📖 Deep Dive Documentation
For an exhaustive, academic breakdown of the computer science theories, compliance mandates, and code-level flow tracing, please refer to the **`Project Documentation.docx`** included in this repository.

---
*Built for Enterprise Security. Designed for Deterministic Accuracy.*
