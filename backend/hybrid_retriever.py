import os
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from rank_bm25 import BM25Okapi
import chromadb
from backend.data_build.chroma_builder import NomicEmbeddingFunction, get_db_subpath

class CrossEncoderReRanker:
    """
    Lightweight Cross-Encoder Re-Ranker using ms-marco-MiniLM-L-6-v2.
    Computes full query-document cross-attention for high precision (<30ms latency on CPU).
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            print(f"[OK] Pre-loaded Cross-Encoder Re-Ranker into memory: {model_name}")
        except Exception as e:
            print(f"[NOTE] CrossEncoder initialization note: {e}")

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        if not candidates:
            return []
            
        if self.model is None:
            return candidates[:top_n]
                
        pairs = [[query, candidate["text"]] for candidate in candidates]
        scores = self.model.predict(pairs)
        
        for idx, score in enumerate(scores):
            candidates[idx]["cross_encoder_score"] = float(score)
            
        reranked_candidates = sorted(candidates, key=lambda c: c["cross_encoder_score"], reverse=True)
        return reranked_candidates[:top_n]


class NomicHybridRetriever:
    def __init__(
        self,
        vector_db_dir: str = None,
        processed_dir: str = None,
        nomic_model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.vector_db_dir = vector_db_dir or get_db_subpath("vector_store")
        self.processed_dir = processed_dir or get_db_subpath("processed")
        self.collection_name = "nomic_enterprise_child_chunks"
        
        # Load Parent Document Key-Value Store
        self.parent_store_path = os.path.join(self.processed_dir, "parent_docs.json")
        self.parent_docs: Dict[str, Any] = {}
        if os.path.exists(self.parent_store_path):
            with open(self.parent_store_path, 'r', encoding='utf-8') as f:
                self.parent_docs = json.load(f)
                
        # Initialize ChromaDB & Nomic Embedding Function
        self.nomic_embed_fn = NomicEmbeddingFunction(model_name=nomic_model_name)
        self.chroma_client = chromadb.PersistentClient(path=self.vector_db_dir)
        
        # Initialize Cross-Encoder Re-Ranker
        self.reranker = CrossEncoderReRanker(model_name=reranker_model_name)
        
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name,
                embedding_function=self.nomic_embed_fn
            )
        except Exception:
            self.collection = None

        self._build_bm25_index()

    def _build_bm25_index(self):
        """Builds in-memory BM25 index over child chunks retrieved from ChromaDB."""
        if not self.collection:
            self.bm25_index = None
            self.bm25_docs = []
            self.bm25_metadatas = []
            self.bm25_ids = []
            return

        try:
            db_contents = self.collection.get(include=["documents", "metadatas"])
            self.bm25_docs = db_contents.get("documents", []) or []
            self.bm25_metadatas = db_contents.get("metadatas", []) or []
            self.bm25_ids = db_contents.get("ids", []) or []

            if self.bm25_docs:
                tokenized_corpus = [doc.lower().split() for doc in self.bm25_docs]
                self.bm25_index = BM25Okapi(tokenized_corpus)
            else:
                self.bm25_index = None
        except Exception as e:
            print(f"⚠️ Warning during BM25 index build: {e}")
            self.bm25_index = None

    def search_vector(self, query: str, top_k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None, include_superseded: bool = False) -> List[Dict[str, Any]]:
        """Dense Cosine Similarity Search in ChromaDB using Nomic Query Prefix."""
        if not self.collection:
            return []

        nomic_formatted_query = f"search_query: {query}"
        
        filter_conditions = []
        if not include_superseded:
            filter_conditions.append({"status": "CURRENT"})

        if metadata_filter:
            for k, v in metadata_filter.items():
                if v:
                    filter_conditions.append({k: str(v)})

        query_where = None
        if len(filter_conditions) > 1:
            query_where = {"$and": filter_conditions}
        elif len(filter_conditions) == 1:
            query_where = filter_conditions[0]

        try:
            results = self.collection.query(
                query_texts=[nomic_formatted_query],
                n_results=top_k,
                where=query_where,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"⚠️ Warning during ChromaDB query: {e}")
            return []

        vector_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for idx in range(len(ids)):
                vector_results.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metadatas[idx],
                    "score": float(1.0 - distances[idx])
                })
            print(f"   [Retriever] Vector Search found {len(vector_results)} candidates.")
        return vector_results

    def search_bm25(self, query: str, top_k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None, include_superseded: bool = False) -> List[Dict[str, Any]]:
        """Sparse BM25 Keyword Search."""
        if not self.bm25_index or not self.bm25_docs:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k*2]

        bm25_results = []
        for idx in top_indices:
            score = scores[idx]
            if score <= 0:
                continue

            meta = self.bm25_metadatas[idx]
            if not include_superseded and meta.get("status") != "CURRENT":
                continue

            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if v and str(meta.get(k)) != str(v):
                        match = False
                        break
                if not match:
                    continue

            bm25_results.append({
                "id": self.bm25_ids[idx],
                "text": self.bm25_docs[idx],
                "metadata": meta,
                "score": float(score)
            })

            if len(bm25_results) >= top_k:
                break

        print(f"   [Retriever] BM25 Sparse Search found {len(bm25_results)} candidates.")
        return bm25_results

    def reciprocal_rank_fusion(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]], k: int = 60, top_n: int = 6) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        child_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(vector_results):
            cid = item["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))
            child_map[cid] = item

        for rank, item in enumerate(bm25_results):
            cid = item["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))
            if cid not in child_map:
                child_map[cid] = item

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_n]
        fused = []
        for cid in sorted_cids:
            chunk = child_map[cid]
            chunk["rrf_score"] = rrf_scores[cid]
            fused.append(chunk)
        print(f"   [Retriever] RRF Fusion completed, keeping top {top_n} unified candidates.")
        return fused

    def retrieve_parents(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None, top_n_parents: int = 3, include_superseded: bool = False) -> List[Dict[str, Any]]:
        """
        Truly Parallel 4-Stage Retrieval Engine:
        Supports explicit include_superseded flag for Version Comparison Queries (v1.0 vs v2.0).
        """
        q_lower = query.lower()
        if any(w in q_lower for w in ["compare", "old version", "previous version", "v1.0", "v1_0", "what changed", "history"]):
            include_superseded = True

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_vector = executor.submit(self.search_vector, query, 10, metadata_filter, include_superseded)
            future_bm25 = executor.submit(self.search_bm25, query, 10, metadata_filter, include_superseded)
            
            vector_res = future_vector.result()
            bm25_res = future_bm25.result()
        
        print(f"   [Retriever] Parallel Vector/BM25 queries complete.")
        fused_candidates = self.reciprocal_rank_fusion(vector_res, bm25_res, top_n=6)
        
        print(f"   [Retriever] Re-ranking fused candidates with Cross-Encoder...")
        reranked_candidates = self.reranker.rerank(query, fused_candidates, top_n=5)
        
        parents = []
        seen_parent_ids = set()
        for child in reranked_candidates:
            # Using -5.0 as a threshold to prevent dropping valid multi-hop matches that don't have perfect semantic alignment
            if child.get("cross_encoder_score", 0.0) < -5.0:
                continue
                
            pid = child["metadata"].get("parent_id")
            if pid and pid not in seen_parent_ids:
                seen_parent_ids.add(pid)
                parent_data = self.parent_docs.get(pid)
                if parent_data:
                    parents.append({
                        "parent_id": pid,
                        "section_title": parent_data["section_title"],
                        "content": parent_data["content"],
                        "metadata": parent_data["metadata"],
                        "matched_child_text": child["text"],
                        "rrf_score": child.get("rrf_score", 0.0),
                        "cross_encoder_score": child.get("cross_encoder_score", 0.0)
                    })
            if len(parents) >= top_n_parents:
                break
        return parents
