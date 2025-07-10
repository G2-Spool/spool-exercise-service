"""Exercise evaluation routes."""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
import structlog

from app.models.exercise import StudentResponse, EvaluateResponse, Evaluation
from app.langgraph.workflows import ExerciseWorkflow
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_response(
    response_data: StudentResponse, request: Request
) -> EvaluateResponse:
    """Evaluate a student's response to an exercise."""
    try:
        # Get exercise from cache
        cache = request.app.state.redis_cache
        exercise_data = await cache.get(f"exercise:{response_data.exercise_id}")

        if not exercise_data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        exercise = json.loads(exercise_data)

        # Get concept data (mock for now)
        concept = {
            "concept_id": exercise["concept_id"],
            "name": "Sample Concept",
            "content": "Concept content",
        }

        # Run evaluation workflow
        workflow: ExerciseWorkflow = request.app.state.workflow

        result = await workflow.evaluate_exercise(
            exercise_id=response_data.exercise_id,
            student_response=response_data.response_text,
            exercise_data=exercise,
            concept_data=concept,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Evaluation failed")
            )

        # Convert to Evaluation model
        eval_data = result["evaluation"]
        evaluation = Evaluation(
            evaluation_id=eval_data["evaluation_id"],
            exercise_id=eval_data["exercise_id"],
            student_id=response_data.student_id,
            student_response=eval_data["student_response"],
            competency_map=eval_data["competency_map"],
            understanding_score=eval_data["understanding_score"],
            mastery_achieved=eval_data["mastery_achieved"],
            feedback=eval_data["feedback"],
            needs_remediation=eval_data["needs_remediation"],
            first_gap=(
                eval_data["competency_map"]["missing_steps"][0]
                if eval_data["competency_map"]["missing_steps"]
                else None
            ),
        )

        # Cache the evaluation
        await cache.set(
            f"evaluation:{evaluation.evaluation_id}",
            evaluation.model_dump_json(),
            ttl=settings.CACHE_TTL,
        )

        # Determine next action
        if evaluation.mastery_achieved:
            next_action = "complete"
            message = "Excellent! You've mastered this concept. Ready for the advanced exercise?"
        elif evaluation.needs_remediation:
            next_action = "remediate"
            message = "Let's work on understanding this concept better."
        else:
            next_action = "continue"
            message = "Good progress! Try addressing the missing steps."

        # Store remediation if needed
        if result.get("remediation"):
            await cache.set(
                f"remediation:{evaluation.evaluation_id}",
                json.dumps(result["remediation"]),
                ttl=settings.CACHE_TTL,
            )

        return EvaluateResponse(
            evaluation=evaluation, next_action=next_action, message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Response evaluation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Evaluation failed")


@router.get("/evaluation/{evaluation_id}")
async def get_evaluation(evaluation_id: str, request: Request) -> Dict[str, Any]:
    """Get evaluation details."""
    try:
        cache = request.app.state.redis_cache
        eval_data = await cache.get(f"evaluation:{evaluation_id}")

        if not eval_data:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        return dict(json.loads(eval_data))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get evaluation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve evaluation")
