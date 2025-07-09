"""Exercise generation routes."""

import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
import structlog

from app.core.config import settings

from app.models.exercise import (
    ExerciseGenerationRequest,
    GenerateExerciseResponse,
    Exercise,
    ExerciseHistory,
    MasteryStatus,
)
from app.langgraph.workflows import ExerciseWorkflow

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=GenerateExerciseResponse)
async def generate_exercise(request_data: ExerciseGenerationRequest, request: Request):
    """Generate a personalized exercise for a concept."""
    try:
        workflow: ExerciseWorkflow = request.app.state.workflow

        result = await workflow.generate_exercise(
            concept_id=request_data.concept_id,
            student_id=request_data.student_id,
            student_interests=request_data.student_interests,
            life_category=request_data.life_category.value,
            difficulty=request_data.difficulty.value,
            exercise_type="initial",
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Exercise generation failed"),
            )

        # Convert to Exercise model
        exercise_data = result["exercise"]
        exercise = Exercise(
            exercise_id=exercise_data["exercise_id"],
            concept_id=exercise_data["concept_id"],
            student_id=exercise_data["student_id"],
            type=exercise_data["type"],
            difficulty=exercise_data["difficulty"],
            content=exercise_data["content"],
            personalization=exercise_data["personalization"],
            expected_steps=exercise_data["expected_steps"],
            hints=exercise_data["hints"],
        )

        # Cache the exercise
        cache = request.app.state.redis_cache
        await cache.set(
            f"exercise:{exercise.exercise_id}",
            exercise.model_dump_json(),
            ttl=settings.EXERCISE_CACHE_TTL,
        )

        return GenerateExerciseResponse(exercise=exercise)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exercise generation failed", error=str(e))
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Exercise generation failed: {str(e)}"
        )


@router.post("/generate-advanced", response_model=GenerateExerciseResponse)
async def generate_advanced_exercise(request_data: Dict[str, Any], request: Request):
    """Generate an advanced exercise after initial completion."""
    try:
        # Get original exercise from cache
        cache = request.app.state.redis_cache
        original_exercise_data = await cache.get(
            f"exercise:{request_data['previous_exercise_id']}"
        )

        if not original_exercise_data:
            raise HTTPException(status_code=404, detail="Previous exercise not found")

        original_exercise = json.loads(original_exercise_data)

        # Generate advanced exercise
        workflow: ExerciseWorkflow = request.app.state.workflow

        result = await workflow.generate_exercise(
            concept_id=request_data["concept_id"],
            student_id=request_data["student_id"],
            student_interests=original_exercise["personalization"]["interests_used"],
            life_category=original_exercise["personalization"]["life_category"],
            difficulty="advanced",
            exercise_type="advanced",
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Advanced exercise generation failed"),
            )

        # Convert to Exercise model
        exercise_data = result["exercise"]
        exercise = Exercise(
            exercise_id=exercise_data["exercise_id"],
            concept_id=exercise_data["concept_id"],
            student_id=exercise_data["student_id"],
            type="advanced",
            difficulty="advanced",
            content=exercise_data["content"],
            personalization=exercise_data["personalization"],
            expected_steps=exercise_data["expected_steps"],
            hints=exercise_data["hints"],
        )

        # Cache the exercise
        await cache.set(
            f"exercise:{exercise.exercise_id}",
            exercise.model_dump_json(),
            ttl=settings.EXERCISE_CACHE_TTL,
        )

        return GenerateExerciseResponse(
            exercise=exercise, message="Advanced exercise generated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Advanced exercise generation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Advanced exercise generation failed"
        )


@router.get("/history/{student_id}", response_model=List[ExerciseHistory])
async def get_exercise_history(
    student_id: str, request: Request, concept_id: Optional[str] = None
):
    """Get student's exercise history."""
    try:
        # In production, this would query a database
        # For now, return mock data
        return []

    except Exception as e:
        logger.error("Failed to get exercise history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/mastery/{student_id}/{concept_id}")
async def check_mastery_status(student_id: str, concept_id: str, request: Request):
    """Check mastery status for a concept."""
    try:
        # In production, this would check the database
        # For now, return mock data
        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "mastery_status": MasteryStatus.NOT_STARTED.value,
            "attempts": 0,
            "last_attempt": None,
        }

    except Exception as e:
        logger.error("Failed to check mastery status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check mastery")
