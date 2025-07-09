"""Exercise data models."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ExerciseType(str, Enum):
    """Types of exercises."""

    INITIAL = "initial"
    ADVANCED = "advanced"
    REMEDIATION = "remediation"
    PRACTICE = "practice"


class DifficultyLevel(str, Enum):
    """Exercise difficulty levels."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LifeCategory(str, Enum):
    """Life categories for personalization."""

    PERSONAL = "personal"
    CAREER = "career"
    SOCIAL = "social"
    PHILANTHROPIC = "philanthropic"


class MasteryStatus(str, Enum):
    """Student mastery status for a concept."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    NEEDS_REVIEW = "needs_review"


class Exercise(BaseModel):
    """Exercise model."""

    exercise_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_id: str
    student_id: str
    type: ExerciseType
    difficulty: DifficultyLevel
    content: Dict[str, Any]
    personalization: Dict[str, Any]
    expected_steps: List[str]
    hints: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExerciseGenerationRequest(BaseModel):
    """Request to generate an exercise."""

    concept_id: str
    student_id: str
    student_interests: List[str]
    life_category: LifeCategory
    difficulty: DifficultyLevel = DifficultyLevel.BASIC
    previous_exercise_id: Optional[str] = None


class StudentResponse(BaseModel):
    """Student's response to an exercise."""

    exercise_id: str
    student_id: str
    response_text: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_seconds: Optional[int] = None


class CompetencyMap(BaseModel):
    """Competency analysis of student response."""

    correct_steps: List[str] = Field(default_factory=list)
    missing_steps: List[str] = Field(default_factory=list)
    incorrect_steps: List[str] = Field(default_factory=list)
    partial_steps: List[Dict[str, str]] = Field(default_factory=list)


class Evaluation(BaseModel):
    """Evaluation of student response."""

    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exercise_id: str
    student_id: str
    student_response: str
    competency_map: CompetencyMap
    understanding_score: float = Field(ge=0.0, le=1.0)
    mastery_achieved: bool
    feedback: str
    needs_remediation: bool
    first_gap: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Remediation(BaseModel):
    """Remediation content for understanding gaps."""

    remediation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_id: str
    exercise_id: str
    student_id: str
    target_gap: str
    content: Dict[str, Any]
    personalized_context: str
    practice_problems: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExerciseHistory(BaseModel):
    """Student's exercise history for a concept."""

    student_id: str
    concept_id: str
    exercises: List[Exercise]
    evaluations: List[Evaluation]
    mastery_status: MasteryStatus
    last_attempt: Optional[datetime] = None
    total_attempts: int = 0
    average_score: float = 0.0


class GenerateExerciseResponse(BaseModel):
    """Response from exercise generation."""

    exercise: Exercise
    message: str = "Exercise generated successfully"


class EvaluateResponse(BaseModel):
    """Response from exercise evaluation."""

    evaluation: Evaluation
    next_action: str  # "continue", "remediate", "complete"
    message: str
