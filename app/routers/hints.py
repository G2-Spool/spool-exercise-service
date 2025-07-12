"""Hint generation routes."""

import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
import structlog

from app.generators.exercise_generator import ExerciseGenerator

router = APIRouter()
logger = structlog.get_logger()


@router.post("/hint")
async def get_hint(request_data: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Generate a contextual hint for the current exercise step."""
    try:
        exercise_id = request_data.get("exerciseId")
        current_step = request_data.get("currentStep", 0)
        chat_context = request_data.get("chatContext", [])

        if not exercise_id:
            raise HTTPException(status_code=400, detail="Exercise ID is required")

        # Get exercise from cache
        cache = request.app.state.redis_cache
        exercise_data = await cache.get(f"exercise:{exercise_id}")

        if not exercise_data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        exercise = json.loads(exercise_data)

        # Generate contextual hint using LLM
        exercise_gen = ExerciseGenerator()
        
        # Create hint generation prompt
        hint_prompt = f"""
        Generate a helpful hint for this exercise based on the student's current progress:
        
        Exercise: {exercise.get('content', {}).get('problem', '')}
        Expected Steps: {', '.join(exercise.get('expected_steps', []))}
        Current Step Number: {current_step + 1}
        
        Student's Progress So Far:
        {chr(10).join(chat_context) if chat_context else 'No progress recorded yet'}
        
        Provide a specific, encouraging hint that guides them toward the next logical step without giving away the answer.
        Focus on helping them think through the problem rather than providing the solution.
        
        Return JSON with:
        - hint: The specific guidance text
        - step_number: The step this hint addresses
        - encouragement: A brief encouraging message
        """

        # Check if we should use mock (for testing)
        if exercise_gen._should_use_mock():
            # Generate mock hint based on current step
            expected_steps = exercise.get('expected_steps', [])
            if current_step < len(expected_steps):
                hint_text = f"Think about: {expected_steps[current_step]}"
            else:
                hint_text = "You're making good progress! Consider reviewing your approach and checking if you've addressed all parts of the problem."
                
            return {
                "hint": hint_text,
                "stepNumber": current_step + 1,
                "encouragement": "You've got this! Take it one step at a time."
            }

        # For production, use LLM to generate contextual hint
        try:
            from openai import AsyncOpenAI
            from app.core.config import settings
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.GENERATION_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful educational tutor who provides encouraging, specific hints that guide students toward understanding without giving away answers."
                    },
                    {"role": "user", "content": hint_prompt}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
                
            hint_data = json.loads(content)
            
            return {
                "hint": hint_data.get("hint", "Think about what information you have and what you need to find."),
                "stepNumber": hint_data.get("step_number", current_step + 1),
                "encouragement": hint_data.get("encouragement", "You're doing great! Keep thinking through it step by step.")
            }
            
        except Exception as e:
            logger.error("LLM hint generation failed", error=str(e))
            # Fallback to exercise-based hint
            expected_steps = exercise.get('expected_steps', [])
            if current_step < len(expected_steps):
                hint_text = f"Consider this approach: {expected_steps[current_step]}"
            else:
                hint_text = "Review your work so far. Have you addressed all parts of the problem?"
                
            return {
                "hint": hint_text,
                "stepNumber": current_step + 1,
                "encouragement": "Keep going! You're on the right track."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Hint generation failed", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate hint: {str(e)}"
        )


@router.post("/adaptive-hint")
async def get_adaptive_hint(request_data: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """Generate an adaptive hint that considers student's learning style and previous hint effectiveness."""
    try:
        exercise_id = request_data.get("exerciseId")
        hint_history = request_data.get("hintHistory", [])
        student_profile = request_data.get("studentProfile", {})
        
        if not exercise_id:
            raise HTTPException(status_code=400, detail="Exercise ID is required")

        # Get exercise from cache
        cache = request.app.state.redis_cache
        exercise_data = await cache.get(f"exercise:{exercise_id}")

        if not exercise_data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        exercise = json.loads(exercise_data)

        # Analyze hint effectiveness and adapt approach
        learning_style = student_profile.get("learning_style", "balanced")
        interests = student_profile.get("interests", [])
        
        # Create adaptive hint based on learning style
        if learning_style == "visual":
            hint_approach = "Try drawing a diagram or making a visual representation of the problem."
        elif learning_style == "kinesthetic":
            hint_approach = "Think about this problem as if you were physically working through it step by step."
        elif learning_style == "auditory":
            hint_approach = "Try explaining this problem out loud to yourself, step by step."
        else:
            hint_approach = "Break this down into logical steps, one at a time."

        # Connect to student interests if possible
        interest_connection = ""
        if interests:
            interest_connection = f" Think about how this relates to your interest in {interests[0]}."

        return {
            "hint": f"{hint_approach}{interest_connection}",
            "stepNumber": len(hint_history) + 1,
            "learningStyle": learning_style,
            "encouragement": "This approach is tailored to how you learn best!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Adaptive hint generation failed", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate adaptive hint: {str(e)}"
        ) 