"""Remediation routes."""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
import structlog


router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate")
async def generate_remediation(request_data: Dict[str, Any], request: Request):
    """Generate remediation for a specific gap."""
    try:
        evaluation_id = request_data.get("evaluation_id")

        # Check if remediation already exists
        cache = request.app.state.redis_cache
        remediation_data = await cache.get(f"remediation:{evaluation_id}")

        if remediation_data:
            return json.loads(remediation_data)

        # Get evaluation data
        eval_data = await cache.get(f"evaluation:{evaluation_id}")
        if not eval_data:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # evaluation = json.loads(eval_data)  # Unused variable

        # If remediation wasn't generated during evaluation, generate now
        # This is a fallback - normally remediation is generated with evaluation

        return {
            "remediation_id": "mock-remediation-id",
            "evaluation_id": evaluation_id,
            "message": "Remediation content would be generated here",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Remediation generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Remediation generation failed")


@router.get("/{remediation_id}")
async def get_remediation(remediation_id: str, request: Request):
    """Get remediation content."""
    try:
        # Try by remediation ID first
        cache = request.app.state.redis_cache
        remediation_data = await cache.get(f"remediation:{remediation_id}")

        if not remediation_data:
            # Try by evaluation ID (remediation might be stored with evaluation)
            remediation_data = await cache.get(f"remediation:eval_{remediation_id}")

        if not remediation_data:
            raise HTTPException(status_code=404, detail="Remediation not found")

        return json.loads(remediation_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get remediation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve remediation")


@router.post("/complete/{remediation_id}")
async def mark_remediation_complete(
    remediation_id: str, request_data: Dict[str, Any], request: Request
):
    """Mark remediation as completed."""
    try:
        student_id = request_data.get("student_id")
        understood = request_data.get("understood", True)

        # In production, this would update the database
        # For now, just log and return success

        logger.info(
            "Remediation completed",
            remediation_id=remediation_id,
            student_id=student_id,
            understood=understood,
        )

        return {
            "status": "completed",
            "remediation_id": remediation_id,
            "message": "Remediation marked as complete",
            "next_step": "return_to_exercise" if understood else "additional_help",
        }

    except Exception as e:
        logger.error("Failed to mark remediation complete", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to update remediation status"
        )
