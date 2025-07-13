from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    action: Optional[str] = None  # "generate_exercise", "submit_answer", etc.
    student_profile: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    message: str
    session_state: Dict[str, Any]
    available_actions: List[str]
    data: Dict[str, Any] = {}  # Exercise data, evaluation results, etc. 