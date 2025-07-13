import json
from datetime import datetime
from typing import Dict, Any, cast

from app.core.dependencies import get_redis_cache


class SessionManager:
    """Manage chat sessions and state using Redis."""

    def __init__(self):
        # self.cache is now an awaitable, must be awaited in methods
        pass

    async def get_cache(self) -> Any: # Return Any to satisfy mypy for now
        return await get_redis_cache()

    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get session state from cache."""
        cache = await self.get_cache()
        state_json = await cache.get(f"session:{session_id}")
        if not state_json:
            return self._create_initial_state(session_id)
        return json.loads(state_json)

    async def update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """Update session state in the cache."""
        current_state = await self.get_session_state(session_id)
        current_state.update(updates)

        cache = await self.get_cache()
        await cache.set(
            f"session:{session_id}",
            json.dumps(current_state),
            ttl=3600  # 1 hour
        )
        return current_state

    def _create_initial_state(self, session_id: str) -> Dict[str, Any]:
        """Create a default initial state for a new session."""
        return {
            "session_id": session_id,
            "phase": "initialization",  # initialization, exercise, evaluation, remediation
            "current_exercise": None,
            "current_evaluation": None,
            "history": [],
            "personality_type": "encouraging", # Default personality
            "created_at": datetime.utcnow().isoformat(),
            "student_profile": None,
        } 