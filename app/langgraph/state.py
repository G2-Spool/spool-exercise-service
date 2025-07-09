"""State definitions for LangGraph workflows."""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class ExerciseState(TypedDict, total=False):
    """State for exercise generation and evaluation workflows."""

    # Input data
    concept_id: str
    student_id: str
    student_interests: List[str]
    life_category: str
    difficulty: str
    exercise_type: str

    # Fetched data
    concept_data: Dict[str, Any]
    student_profile: Dict[str, Any]

    # Generated content
    exercise: Dict[str, Any]
    exercise_id: str

    # Student interaction
    student_response: str
    response_time: datetime

    # Evaluation
    evaluation: Dict[str, Any]
    competency_map: Dict[str, List[str]]
    understanding_score: float
    mastery_achieved: bool

    # Remediation
    needs_remediation: bool
    target_gap: str
    remediation_content: Dict[str, Any]

    # Workflow control
    error: Optional[str]
    retry_count: int
    workflow_status: str
