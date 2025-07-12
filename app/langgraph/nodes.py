"""Node functions for LangGraph workflows."""

import httpx
import structlog

from app.core.config import settings
from app.langgraph.state import ExerciseState
from app.generators.exercise_generator import ExerciseGenerator
from app.evaluators.response_evaluator import ResponseEvaluator
from app.remediation.remediation_generator import RemediationGenerator

logger = structlog.get_logger()


class WorkflowNodes:
    """Collection of node functions for exercise workflows."""

    def __init__(self) -> None:
        self.exercise_gen = ExerciseGenerator()
        self.evaluator = ResponseEvaluator()
        self.remediation_gen = RemediationGenerator()

    async def fetch_concept(self, state: ExerciseState) -> ExerciseState:
        """Fetch concept data from content service."""
        try:
            # For local development, use mock data when content service is unavailable
            if settings.ENVIRONMENT == "development":
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(
                            f"{settings.CONTENT_SERVICE_URL}/api/content/concepts/{state['concept_id']}"
                        )
                        response.raise_for_status()
                        state["concept_data"] = response.json()
                except Exception:
                    # Fallback to mock data for development
                    logger.info("Content service unavailable, using mock concept data")
                    state["concept_data"] = self._create_mock_concept(state["concept_id"])
            else:
                # Production: require real content service
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{settings.CONTENT_SERVICE_URL}/api/content/concepts/{state['concept_id']}"
                    )
                    response.raise_for_status()
                    state["concept_data"] = response.json()

            state["workflow_status"] = "concept_fetched"

            logger.info(
                "Fetched concept data",
                concept_id=state["concept_id"],
                concept_name=state["concept_data"].get("name"),
                is_mock=settings.ENVIRONMENT == "development" and "mock" in state["concept_data"].get("source", ""),
            )

        except Exception as e:
            logger.error("Failed to fetch concept", error=str(e))
            state["error"] = f"Failed to fetch concept: {str(e)}"
            state["workflow_status"] = "error"

        return state

    def _create_mock_concept(self, concept_id: str) -> dict:
        """Create mock concept data for development."""
        return {
            "concept_id": concept_id,
            "name": "Mathematical Problem Solving",
            "description": "Learn systematic approaches to solving mathematical problems, including breaking down complex problems into manageable steps.",
            "subject": "Mathematics",
            "difficulty": "intermediate",
            "learning_objectives": [
                "Break down complex problems into smaller, manageable parts",
                "Apply systematic problem-solving strategies",
                "Verify solutions for accuracy and reasonableness",
                "Communicate mathematical reasoning clearly"
            ],
            "prerequisite_concepts": ["basic_algebra", "mathematical_reasoning"],
            "key_terms": ["problem decomposition", "systematic approach", "verification", "mathematical reasoning"],
            "examples": [
                "Word problems involving multiple steps",
                "Optimization problems",
                "Logic puzzles"
            ],
            "source": "mock_data_for_development",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

    async def fetch_student_profile(self, state: ExerciseState) -> ExerciseState:
        """Fetch student profile (mock for now)."""
        # In production, this would call the profile service
        state["student_profile"] = {
            "student_id": state["student_id"],
            "interests": state["student_interests"],
            "learning_style": "visual",
            "grade_level": "high_school",
            "previous_concepts": [],
        }
        state["workflow_status"] = "profile_fetched"

        return state

    async def generate_exercise(self, state: ExerciseState) -> ExerciseState:
        """Generate personalized exercise."""
        try:
            exercise = await self.exercise_gen.generate(
                concept=state["concept_data"],
                student_profile=state["student_profile"],
                life_category=state["life_category"],
                difficulty=state["difficulty"],
                exercise_type=state.get("exercise_type", "initial"),
            )

            state["exercise"] = exercise
            state["exercise_id"] = exercise["exercise_id"]
            state["workflow_status"] = "exercise_generated"

            logger.info(
                "Generated exercise",
                exercise_id=exercise["exercise_id"],
                concept_id=state["concept_id"],
            )

        except Exception as e:
            logger.error("Failed to generate exercise", error=str(e))
            state["error"] = f"Failed to generate exercise: {str(e)}"
            state["workflow_status"] = "error"

        return state

    async def evaluate_response(self, state: ExerciseState) -> ExerciseState:
        """Evaluate student's response."""
        try:
            evaluation = await self.evaluator.evaluate(
                exercise=state["exercise"],
                student_response=state["student_response"],
                concept=state["concept_data"],
            )

            state["evaluation"] = evaluation
            state["competency_map"] = evaluation["competency_map"]
            state["understanding_score"] = evaluation["understanding_score"]
            state["mastery_achieved"] = evaluation["mastery_achieved"]
            state["needs_remediation"] = evaluation["needs_remediation"]

            if state["needs_remediation"]:
                # Set target_gap for remediation
                if evaluation["competency_map"]["missing_steps"]:
                    # Use the first missing step if available
                    state["target_gap"] = evaluation["competency_map"]["missing_steps"][0]
                elif evaluation["competency_map"]["incorrect_steps"]:
                    # Use the first incorrect step if available
                    state["target_gap"] = evaluation["competency_map"]["incorrect_steps"][0]
                else:
                    # Fallback to a general understanding gap
                    state["target_gap"] = "Overall understanding of the concept needs improvement"

            state["workflow_status"] = "response_evaluated"

            logger.info(
                "Evaluated response",
                exercise_id=state["exercise_id"],
                mastery_achieved=state["mastery_achieved"],
                score=state["understanding_score"],
            )

        except Exception as e:
            logger.error("Failed to evaluate response", error=str(e))
            state["error"] = f"Failed to evaluate response: {str(e)}"
            state["workflow_status"] = "error"

        return state

    async def generate_remediation(self, state: ExerciseState) -> ExerciseState:
        """Generate remediation content for identified gaps."""
        try:
            remediation = await self.remediation_gen.generate(
                concept=state["concept_data"],
                target_gap=state["target_gap"],
                student_profile=state["student_profile"],
                original_exercise=state["exercise"],
                evaluation=state["evaluation"],
            )

            state["remediation_content"] = remediation
            state["workflow_status"] = "remediation_generated"

            logger.info(
                "Generated remediation",
                exercise_id=state["exercise_id"],
                target_gap=state["target_gap"],
            )

        except Exception as e:
            logger.error("Failed to generate remediation", error=str(e))
            state["error"] = f"Failed to generate remediation: {str(e)}"
            state["workflow_status"] = "error"

        return state

    async def validate_exercise(self, state: ExerciseState) -> ExerciseState:
        """Validate generated exercise."""
        exercise = state.get("exercise")

        if not exercise:
            state["error"] = "No exercise to validate"
            state["workflow_status"] = "error"
            return state

        # Check required fields in content
        content_fields = ["scenario", "problem"]
        content = exercise.get("content", {})
        missing_content_fields = [
            f for f in content_fields if f not in content
        ]

        # Check required fields at exercise level
        exercise_fields = ["expected_steps", "hints"]
        missing_exercise_fields = [
            f for f in exercise_fields if f not in exercise
        ]

        missing_fields = missing_content_fields + missing_exercise_fields

        if missing_fields:
            state["error"] = f"Missing required fields: {missing_fields}"
            state["workflow_status"] = "error"
        else:
            state["workflow_status"] = "exercise_validated"

        return state

    async def check_retry(self, state: ExerciseState) -> ExerciseState:
        """Check if we should retry on error."""
        if state.get("error") and state.get("retry_count", 0) < settings.MAX_RETRIES:
            state["retry_count"] = state.get("retry_count", 0) + 1
            state["error"] = None  # Clear error for retry
            state["workflow_status"] = "retrying"

        return state
