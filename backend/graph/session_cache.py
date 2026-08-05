import time
from typing import Dict, Any, Optional, List, Tuple

class SessionCacheStore:
    """
    In-Memory Session Cache Layer for Multi-Turn Conversational Policy Disambiguation.
    Persists pending user queries across clarification turns using thread_id / session_id.
    """
    def __init__(self, ttl_seconds: int = 1800):  # 30-minute session TTL
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.sessions:
            return None
            
        session_data = self.sessions[session_id]
        if time.time() - session_data["last_updated"] > self.ttl_seconds:
            del self.sessions[session_id]
            return None
            
        return session_data

    def set_pending_clarification(self, session_id: str, original_query: str, options_offered: list):
        """Caches pending query when CLARIFY intent is triggered."""
        self.sessions[session_id] = {
            "pending_query": original_query,
            "options_offered": options_offered,
            "last_updated": time.time()
        }

    def resolve_pending_clarification(self, session_id: str, new_user_input: str) -> Tuple[str, bool]:
        """
        Merges new user response (e.g. 'US-NY' or 'New York') into the cached original query.
        Returns (merged_full_query, is_resolved_from_cache).
        """
        session_data = self.get_session(session_id)
        if not session_data or "pending_query" not in session_data:
            return new_user_input, False

        pending_query = session_data["pending_query"]
        merged_query = f"{pending_query} for {new_user_input}"
        
        # Clear resolved pending session state
        del self.sessions[session_id]
        return merged_query, True

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


# Singleton Session Cache Store Instance
session_cache = SessionCacheStore()
