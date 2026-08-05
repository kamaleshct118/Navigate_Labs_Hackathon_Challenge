import os
import json
import re
from typing import Dict, Any, List, Tuple, Set, Optional
from backend.data_build.chroma_builder import get_kb_subpath

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

        processed_dir = get_kb_subpath("processed")
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
        Dynamic Parameter Extraction supporting Single & Multi-Region Comparisons.
        """
        taxonomy = cls._load_dynamic_metadata_taxonomy()
        params = {}
        q_lower = query.lower()

        matched_regions = []
        for region in taxonomy["regions"]:
            reg_clean = region.lower().replace("-", " ")
            parts = reg_clean.split()
            if any(p in q_lower for p in parts if len(p) > 1) or reg_clean in q_lower:
                matched_regions.append(region)

        if len(matched_regions) == 1:
            params["region"] = matched_regions[0]
        elif len(matched_regions) > 1:
            params["multi_regions"] = matched_regions  # Cross-Branch Comparison Mode!

        # Dynamic Branch Matching
        for branch_id in taxonomy["branch_ids"]:
            b_clean = branch_id.lower().replace("-", " ")
            if b_clean in q_lower or branch_id.lower() in q_lower:
                params["branch_id"] = branch_id
                break

        # Dynamic Department Matching
        for dept in taxonomy["departments"]:
            dept_clean = dept.lower()
            if dept_clean in q_lower or any(word in q_lower for word in dept_clean.split() if len(word) > 2):
                params["department"] = dept
                break

        return params

    @staticmethod
    def classify_intent(query: str, params: Dict[str, Any]) -> str:
        q_lower = query.lower()
        
        # Scenario 5: High-Risk Legal / Anti-Bribery / Subpoena / Audit Escalation
        escalation_keywords = [
            "subpoena", "bribe", "bribery", "kickback", "investigation",
            "regulatory audit", "foreign official", "fcpa", "law enforcement", "prosecutor"
        ]
        if any(k in q_lower for k in escalation_keywords):
            return "ESCALATE"

        # Scenario 4: Multi-Hop SOP Workflow
        multihop_keywords = [
            "stolen laptop", "lost laptop", "lost phone", "data breach",
            "gdpr notification", "report breach", "security incident"
        ]
        if any(k in q_lower for k in multihop_keywords):
            return "MULTI_HOP"

        # Check if query is an explicit Comparison Query (Version Comparison OR Cross-Branch Comparison)
        is_comparison_query = any(w in q_lower for w in ["difference", "compare", "versus", "vs", "what changed", "between"])

        # Scenario 2: Vague / Location-Ambiguous Query without specified region/branch AND not a comparison query
        ambiguous_location_topics = [
            "pto", "vacation", "annual leave", "paid time off", "remote work",
            "work hours", "holiday", "stipend", "equipment allowance"
        ]
        has_location_topic = any(t in q_lower for t in ambiguous_location_topics)
        has_region_param = "region" in params or "branch_id" in params or "multi_regions" in params
        
        if has_location_topic and not has_region_param and not is_comparison_query:
            return "CLARIFY"

        # Default: ANSWER_DIRECT (Handles both Version Comparisons & Cross-Branch Comparisons!)
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
        if "multi_regions" in params:
            return False, None

        if len(regions) > 1 and "region" not in params:
            region_list = ", ".join(list(regions))
            return True, f"Conflict detected across multiple regional jurisdictions ({region_list}). User location context is required."

        if len(versions) > 1 and len(doc_ids) == 1:
            return True, f"Version conflict detected within document {list(doc_ids)[0]} ({', '.join(list(versions))}). Reconciling to latest CURRENT version."

        return False, None
