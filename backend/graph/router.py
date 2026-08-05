import os
import json
import re
from typing import Dict, Any, List, Tuple, Set, Optional
from backend.data_build.chroma_builder import get_db_subpath

class ComplianceQueryRouter:
    """
    Dynamic Intent Classifier & Policy Contradiction Engine for Enterprise Compliance.
    Extracts branches, regions, and departments DYNAMICALLY from ingested document metadata store (parent_docs.json).
    Supports Cross-Branch Comparisons (e.g. US-NY vs EU-London) and Version Comparisons (v1.0 vs v2.0).
    """
    
    _metadata_cache = None

    @classmethod
    def _load_dynamic_metadata_taxonomy(cls) -> Dict[str, Set[str]]:
        """Dynamically inspects parent_docs.json to discover all active regions, branch_ids, and departments."""
        if cls._metadata_cache is not None:
            return cls._metadata_cache

        processed_dir = get_db_subpath("processed")
        parent_store_path = os.path.join(processed_dir, "parent_docs.json")

        taxonomy = {
            "regions": set(),
            "branch_ids": set(),
            "departments": set()
        }

        if os.path.exists(parent_store_path):
            try:
                with open(parent_store_path, 'r', encoding='utf-8') as f:
                    parent_docs = json.load(f)
                    for parent_id, p_data in parent_docs.items():
                        meta = p_data.get("metadata", {})
                        if meta.get("region"):
                            taxonomy["regions"].add(meta["region"])
                        if meta.get("branch_id"):
                            taxonomy["branch_ids"].add(meta["branch_id"])
                        if meta.get("department"):
                            taxonomy["departments"].add(meta["department"])
            except Exception as e:
                print(f"⚠️ Warning loading dynamic metadata taxonomy: {e}")

        cls._metadata_cache = taxonomy
        return taxonomy

    @classmethod
    def extract_parameters(cls, query: str) -> Dict[str, Any]:
        """
        Dynamic Parameter Extraction using LLM to map user query to active taxonomy.
        """
        taxonomy = cls._load_dynamic_metadata_taxonomy()
        from backend.graph.nodes import call_nvidia_llm
        
        system_prompt = (
            "You are an enterprise compliance parameter extractor. Analyze the query and the available taxonomy. "
            "Output ONLY a raw JSON object containing the extracted parameters. Do not output markdown blocks or extra text."
        )
        
        user_prompt = f"""
QUERY: "{query}"

AVAILABLE TAXONOMY:
- regions: {list(taxonomy['regions'])}
- branch_ids: {list(taxonomy['branch_ids'])}
- departments: {list(taxonomy['departments'])}

INSTRUCTIONS:
1. If the user mentions one or more regions from the taxonomy, add them to a list. If exactly 1 region is found, set "region": "Name". If >1 are found, set "multi_regions": ["Name1", "Name2"].
2. If the user mentions a branch_id from the taxonomy, set "branch_id": "Name".
3. If the user mentions a department from the taxonomy, set "department": "Name".
4. If the user explicitly asks to compare versions (e.g. "old vs new", "what changed", "difference") or regions, set "is_comparison": true.

OUTPUT FORMAT:
Return exactly valid JSON. Example: {{"region": "US", "is_comparison": false}}
"""
        try:
            result = call_nvidia_llm(system_prompt, user_prompt)
            if result:
                clean_result = result.replace("```json", "").replace("```", "").strip()
                params = json.loads(clean_result)
                print(f"🧠 [LLM Extractor] Parsed Params: {params}")
                return params
        except Exception as e:
            print(f"⚠️ [LLM Extractor] Failed or invalid JSON: {e}")
            
        return {}

    @staticmethod
    def classify_intent(query: str, params: Dict[str, Any]) -> str:
        from backend.graph.nodes import call_nvidia_llm
        
        system_prompt = (
            "You are an enterprise compliance intent router. Your job is to classify the user's query into one of four distinct routing nodes. "
            "You must output ONLY the exact node name and nothing else."
        )
        
        user_prompt = f"""Analyze this query and extracted metadata:
QUERY: "{query}"
EXTRACTED PARAMS: {json.dumps(params)}

CATEGORIES:
1. ESCALATE: The query involves high-risk legal matters, bribery, corruption, regulatory subpoenas (e.g., SEC), or whistleblowing.
2. MULTI_HOP: The query involves a complex situation requiring cross-department procedures, such as lost/stolen company devices, data breaches, or employee termination/offboarding.
3. CLARIFY: The query asks about HR/location-dependent policies (like PTO, vacation, remote work) BUT the EXTRACTED PARAMS do not contain a region/branch. (If they do specify a location or ask to compare, do NOT use CLARIFY).
4. ANSWER_DIRECT: Default node for standard policy questions, version comparisons, or location-specific HR questions.

Which category does this query belong to? Output EXACTLY one of: ESCALATE, MULTI_HOP, CLARIFY, ANSWER_DIRECT."""

        result = call_nvidia_llm(system_prompt, user_prompt)
        
        if result:
            result_upper = result.strip().upper()
            for intent in ["ESCALATE", "MULTI_HOP", "CLARIFY", "ANSWER_DIRECT"]:
                if intent in result_upper:
                    print(f"🧠 [LLM Router] Dynamically classified '{query}' -> {intent}")
                    return intent
                    
        print(f"⚠️ [LLM Router] Failed to classify or defaulted -> ANSWER_DIRECT")
        return "ANSWER_DIRECT"

    @staticmethod
    def detect_contradictions(retrieved_docs: List[Dict[str, Any]], params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Contradiction Detection Engine:
        Evaluates retrieved policy chunks for regional or version conflicts.
        Suppresses CLARIFY if query is an explicit comparison query!
        """
        if not retrieved_docs or len(retrieved_docs) < 2:
            return False, None

        regions = set()
        versions = set()
        doc_ids = set()

        for doc in retrieved_docs:
            meta = doc.get("metadata", {})
            if meta.get("region"):
                regions.add(meta["region"])
            if meta.get("version"):
                versions.add(meta["version"])
            if meta.get("doc_id"):
                doc_ids.add(meta["doc_id"])

        # If user explicitly asked for a comparison or provided multi_regions, do NOT trigger CLARIFY conflict!
        if "multi_regions" in params or "is_comparison" in params:
            return False, None

        if len(regions) > 1 and "region" not in params:
            region_list = ", ".join(list(regions))
            return True, f"Conflict detected across multiple regional jurisdictions ({region_list}). User location context is required."

        if len(versions) > 1 and len(doc_ids) == 1:
            return True, f"Version conflict detected within document {list(doc_ids)[0]} ({', '.join(list(versions))}). Reconciling to latest CURRENT version."

        return False, None
