import os
import json
from typing import List, Dict, Any, Tuple
import chromadb

# Determine Project Root Directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Strictly lock Database directory to Project Root level
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
SAMPLE_DOCS_DIR = os.path.join(PROJECT_ROOT, "sample_docs")

def get_db_subpath(sub_folder: str) -> str:
    """Returns absolute path inside root project database directory."""
    full_path = os.path.join(DATABASE_DIR, sub_folder)
    os.makedirs(full_path, exist_ok=True)
    return full_path


class NomicEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom ChromaDB Embedding Function utilizing Nomic Embed Text Model.
    Supports Nomic v1/v1.5 via SentenceTransformers with trust_remote_code=True.
    Applies Nomic prefix conventions: 'search_document: ' for docs, 'search_query: ' for queries.
    """
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        self.model_name = model_name
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
            print(f"[OK] Successfully initialized Nomic Embedding Model: {model_name}")
        except Exception as e:
            print(f"[NOTE] SentenceTransformer model '{model_name}' will load on first inference: {e}")

    def __call__(self, input_texts: List[str]) -> List[List[float]]:
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
            except Exception as e:
                raise RuntimeError(f"Could not load SentenceTransformer model {self.model_name}: {e}")
            
        formatted_inputs = []
        for text in input_texts:
            if not text.startswith("search_document:") and not text.startswith("search_query:"):
                formatted_inputs.append(f"search_document: {text}")
            else:
                formatted_inputs.append(text)
                
        embeddings = self.model.encode(formatted_inputs, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()


class ChromaDatabaseBuilder:
    def __init__(
        self,
        sample_docs_dir: str = None,
        vector_db_dir: str = None,
        processed_dir: str = None,
        nomic_model_name: str = "nomic-ai/nomic-embed-text-v1.5"
    ):
        self.sample_docs_dir = sample_docs_dir or SAMPLE_DOCS_DIR
        self.vector_db_dir = vector_db_dir or get_db_subpath("vector_store")
        self.processed_dir = processed_dir or get_db_subpath("processed")
        self.nomic_model_name = nomic_model_name
        
        from backend.data_build.loader import MarkdownDocumentLoader
        self.loader = MarkdownDocumentLoader(sample_docs_dir=self.sample_docs_dir)
        
        os.makedirs(self.sample_docs_dir, exist_ok=True)
        os.makedirs(self.vector_db_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    def reconcile_document_versions(self, all_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Version Reconciliation Engine:
        Groups documents by (doc_id, branch_id). Sorts by effective_date.
        Sets status = "CURRENT" for the latest date version and status = "SUPERSEDED" for older versions.
        """
        groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for doc in all_docs:
            key = (doc["metadata"]["doc_id"], doc["metadata"]["branch_id"])
            if key not in groups:
                groups[key] = []
            groups[key].append(doc)
            
        for key, doc_list in groups.items():
            if len(doc_list) > 1:
                doc_list.sort(key=lambda d: d["metadata"]["effective_date"], reverse=True)
                doc_list[0]["metadata"]["status"] = "CURRENT"
                for older in doc_list[1:]:
                    older["metadata"]["status"] = "SUPERSEDED"
            else:
                doc_list[0]["metadata"]["status"] = "CURRENT"
                
        return all_docs

    def build_chroma_database(self):
        """Processes all Markdown files, reconciles versions, and builds ChromaDB persistent vector index with HNSW."""
        print("[BUILD] Starting ChromaDB Vector Indexing with Nomic HuggingFace Embedding Model...")
        print(f"[BUILD] Source Directory: {self.sample_docs_dir}")
        print(f"[BUILD] Vector Store Path: {self.vector_db_dir}")
        print(f"[BUILD] Processed Parent Store Path: {self.processed_dir}")
        
        if not os.path.exists(self.sample_docs_dir):
            print(f"⚠️ Document directory '{self.sample_docs_dir}' does not exist.")
            return

        file_list = [f for f in os.listdir(self.sample_docs_dir) if f.endswith('.md')]
        if not file_list:
            print(f"⚠️ No markdown files found in {self.sample_docs_dir}")
            return

        print(f"📄 Found {len(file_list)} Markdown files for ingestion.")
        parsed_docs = []
        for file_name in file_list:
            file_path = os.path.join(self.sample_docs_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            meta, parents, children = self.loader.split_into_parents_and_children(text, file_name)
            parsed_docs.append({
                "file_name": file_name,
                "metadata": meta,
                "parents": parents,
                "children": children
            })
            
        # Reconcile document versions
        reconciled_docs = self.reconcile_document_versions(parsed_docs)
        
        parent_store: Dict[str, Any] = {}
        child_ids: List[str] = []
        child_texts: List[str] = []
        child_metadatas: List[Dict[str, Any]] = []

        for doc in reconciled_docs:
            doc_status = doc["metadata"]["status"]
            
            for p in doc["parents"]:
                p["metadata"]["status"] = doc_status
                parent_store[p["parent_id"]] = p
                
            for c in doc["children"]:
                c["metadata"]["status"] = doc_status
                
                clean_meta = {}
                for mk, mv in c["metadata"].items():
                    clean_meta[mk] = str(mv) if mv is not None else ""
                    
                child_ids.append(c["child_id"])
                child_texts.append(c["content"])
                child_metadatas.append(clean_meta)
                
        # Save Parent Store JSON
        parent_store_path = os.path.join(self.processed_dir, "parent_docs.json")
        with open(parent_store_path, 'w', encoding='utf-8') as f:
            json.dump(parent_store, f, indent=2)
        print(f"✅ Saved {len(parent_store)} Parent Sections to {parent_store_path}")

        # Initialize ChromaDB persistent client
        chroma_client = chromadb.PersistentClient(path=self.vector_db_dir)
        nomic_embed_fn = NomicEmbeddingFunction(model_name=self.nomic_model_name)

        collection_name = "nomic_enterprise_child_chunks"
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        # HNSW Index Configuration with Cosine Similarity
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=nomic_embed_fn,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 128,
                "hnsw:M": 16
            }
        )

        if child_ids:
            collection.add(
                ids=child_ids,
                documents=child_texts,
                metadatas=child_metadatas
            )
            print(f"✅ Successfully indexed {len(child_ids)} Child Chunks using HNSW Cosine Index in ChromaDB!")
        else:
            print("⚠️ No child chunks found to index.")
            
        print("🎉 ChromaDB Vector Database Build Complete!")
