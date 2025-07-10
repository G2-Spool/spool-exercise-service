"""LangGraph workflow definitions."""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import structlog

from app.langgraph.state import ExerciseState
from app.langgraph.nodes import WorkflowNodes
from app.core.config import settings

logger = structlog.get_logger()


class ExerciseWorkflow:
    """Main workflow for exercise generation and evaluation."""

    def __init__(self) -> None:
        self.nodes = WorkflowNodes()
        self.graph = self._build_graph()
        self.memory = MemorySaver()

    def _build_graph(self) -> Any:
        """Build the exercise workflow graph."""
        workflow = StateGraph(ExerciseState)

        # Add nodes
        workflow.add_node("fetch_concept", self.nodes.fetch_concept)
        workflow.add_node("fetch_profile", self.nodes.fetch_student_profile)
        workflow.add_node("generate_exercise", self.nodes.generate_exercise)
        workflow.add_node("validate_exercise", self.nodes.validate_exercise)
        workflow.add_node("evaluate_response", self.nodes.evaluate_response)
        workflow.add_node("generate_remediation", self.nodes.generate_remediation)
        workflow.add_node("check_retry", self.nodes.check_retry)

        # Define edges for exercise generation flow
        workflow.add_edge("fetch_concept", "fetch_profile")
        workflow.add_edge("fetch_profile", "generate_exercise")
        workflow.add_edge("generate_exercise", "validate_exercise")

        # Conditional edge from validation
        workflow.add_conditional_edges(
            "validate_exercise",
            self._should_retry_generation,
            {"retry": "check_retry", "success": END, "error": END},
        )

        # Conditional edge from retry check
        workflow.add_conditional_edges(
            "check_retry",
            self._check_retry_status,
            {"retry": "generate_exercise", "stop": END},
        )

        # Evaluation flow edges
        workflow.add_conditional_edges(
            "evaluate_response",
            self._check_remediation_needed,
            {"remediate": "generate_remediation", "complete": END, "error": END},
        )

        # Set entry point
        workflow.set_entry_point("fetch_concept")

        return workflow.compile()

    def _should_retry_generation(self, state: ExerciseState) -> str:
        """Determine if we should retry exercise generation."""
        if state.get("error"):
            if state.get("retry_count", 0) < settings.MAX_RETRIES:
                return "retry"
            return "error"
        return "success"

    def _check_retry_status(self, state: ExerciseState) -> str:
        """Check if we should continue retrying."""
        if state.get("workflow_status") == "retrying":
            return "retry"
        return "stop"

    def _check_remediation_needed(self, state: ExerciseState) -> str:
        """Check if remediation is needed."""
        if state.get("error"):
            return "error"
        if state.get("needs_remediation"):
            return "remediate"
        return "complete"

    async def generate_exercise(
        self,
        concept_id: str,
        student_id: str,
        student_interests: List[str],
        life_category: str,
        difficulty: str = "basic",
        exercise_type: str = "initial",
    ) -> Dict[str, Any]:
        """Run exercise generation workflow."""
        initial_state = {
            "concept_id": concept_id,
            "student_id": student_id,
            "student_interests": student_interests,
            "life_category": life_category,
            "difficulty": difficulty,
            "exercise_type": exercise_type,
            "workflow_status": "started",
        }

        try:
            # Run the workflow
            result = await self.graph.ainvoke(
                initial_state,
                config={
                    "configurable": {"thread_id": f"exercise_{concept_id}_{student_id}"}
                },
            )

            if result.get("error"):
                raise Exception(result["error"])

            return {
                "success": True,
                "exercise": result.get("exercise"),
                "exercise_id": result.get("exercise_id"),
            }

        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def evaluate_exercise(
        self,
        exercise_id: str,
        student_response: str,
        exercise_data: Dict[str, Any],
        concept_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run evaluation workflow."""
        # Reconstruct student profile from exercise data
        student_profile = {
            "student_id": exercise_data.get("student_id"),
            "interests": exercise_data.get("personalization", {}).get(
                "interests_used", []
            ),
            "learning_style": "visual",
            "grade_level": "high_school",
            "previous_concepts": [],
        }

        initial_state = {
            "exercise_id": exercise_id,
            "student_response": student_response,
            "exercise": exercise_data,
            "concept_data": concept_data,
            "student_profile": student_profile,
            "workflow_status": "evaluating",
        }

        try:
            # Start from evaluation node
            workflow = StateGraph(ExerciseState)
            workflow.add_node("evaluate_response", self.nodes.evaluate_response)
            workflow.add_node("generate_remediation", self.nodes.generate_remediation)

            workflow.add_conditional_edges(
                "evaluate_response",
                self._check_remediation_needed,
                {"remediate": "generate_remediation", "complete": END, "error": END},
            )

            workflow.set_entry_point("evaluate_response")
            compiled = workflow.compile()

            result = await compiled.ainvoke(initial_state)

            if result.get("error"):
                raise Exception(result["error"])

            return {
                "success": True,
                "evaluation": result.get("evaluation"),
                "remediation": (
                    result.get("remediation_content")
                    if result.get("needs_remediation")
                    else None
                ),
            }

        except Exception as e:
            logger.error("Evaluation workflow failed", error=str(e))
            return {"success": False, "error": str(e)}
