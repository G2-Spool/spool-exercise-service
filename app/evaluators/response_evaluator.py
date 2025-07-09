"""Evaluate student responses to identify understanding gaps."""

import json
from typing import Dict, Any, List
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ResponseEvaluator:
    """Evaluate student responses using LLMs."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EVALUATION_MODEL
    
    async def evaluate(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a student's response to an exercise."""
        try:
            # Validate response length
            if len(student_response) < settings.MIN_RESPONSE_LENGTH:
                return self._create_insufficient_response_evaluation(exercise, student_response)
            
            prompt = self._create_evaluation_prompt(exercise, student_response, concept)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent evaluation
                response_format={"type": "json_object"}
            )
            
            evaluation_result = json.loads(response.choices[0].message.content)
            
            # Create evaluation object
            evaluation = {
                "evaluation_id": str(uuid.uuid4()),
                "exercise_id": exercise.get("exercise_id"),
                "student_response": student_response,
                "competency_map": {
                    "correct_steps": evaluation_result.get("correct_steps", []),
                    "missing_steps": evaluation_result.get("missing_steps", []),
                    "incorrect_steps": evaluation_result.get("incorrect_steps", []),
                    "partial_steps": evaluation_result.get("partial_steps", [])
                },
                "understanding_score": evaluation_result.get("understanding_score", 0.0),
                "mastery_achieved": evaluation_result.get("mastery_achieved", False),
                "feedback": evaluation_result.get("feedback", ""),
                "needs_remediation": len(evaluation_result.get("missing_steps", [])) > 0 or 
                                   len(evaluation_result.get("incorrect_steps", [])) > 0,
                "evaluated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Evaluated response",
                exercise_id=exercise.get("exercise_id"),
                mastery_achieved=evaluation["mastery_achieved"],
                score=evaluation["understanding_score"]
            )
            
            return evaluation
            
        except Exception as e:
            logger.error("Response evaluation failed", error=str(e))
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for response evaluation."""
        return """You are an expert educational evaluator specializing in assessing 
        student understanding through their articulated thought processes.
        
        Your evaluation should:
        1. Compare the student's explanation against expected solution steps
        2. Identify which steps were correctly explained
        3. Identify missing or incorrect reasoning
        4. Assess overall conceptual understanding (0.0 to 1.0)
        5. Determine if mastery has been achieved (requires explaining ALL key steps)
        6. Provide constructive feedback
        
        Be strict about requiring complete explanations but understanding of different 
        valid approaches. Focus on conceptual understanding, not exact wording.
        
        Return your response as a JSON object with these fields:
        - correct_steps: Array of correctly explained steps
        - missing_steps: Array of steps not addressed
        - incorrect_steps: Array of incorrectly explained steps
        - partial_steps: Array of {step, issue} for partially correct steps
        - understanding_score: Float 0.0 to 1.0
        - mastery_achieved: Boolean (true only if ALL key steps are explained)
        - feedback: Constructive feedback message"""
    
    def _create_evaluation_prompt(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any]
    ) -> str:
        """Create prompt for response evaluation."""
        expected_steps = exercise.get("expected_steps", [])
        
        prompt = f"""Evaluate this student's response to an exercise:
        
        Concept Being Tested: {concept.get('name')}
        
        Exercise Scenario: {exercise.get('content', {}).get('scenario')}
        Exercise Problem: {exercise.get('content', {}).get('problem')}
        
        Expected Solution Steps:
        {chr(10).join(f"{i+1}. {step}" for i, step in enumerate(expected_steps))}
        
        Student's Response:
        "{student_response}"
        
        Evaluation Criteria:
        1. Has the student explained each expected step?
        2. Is their reasoning logically sound?
        3. Did they identify the key concepts?
        4. Are there any misconceptions?
        5. Is the explanation complete and clear?
        
        Score their overall understanding from 0.0 to 1.0.
        Mastery is achieved ONLY if they explain ALL key steps correctly."""
        
        return prompt
    
    def _create_insufficient_response_evaluation(
        self,
        exercise: Dict[str, Any],
        student_response: str
    ) -> Dict[str, Any]:
        """Create evaluation for insufficient response."""
        return {
            "evaluation_id": str(uuid.uuid4()),
            "exercise_id": exercise.get("exercise_id"),
            "student_response": student_response,
            "competency_map": {
                "correct_steps": [],
                "missing_steps": exercise.get("expected_steps", []),
                "incorrect_steps": [],
                "partial_steps": []
            },
            "understanding_score": 0.0,
            "mastery_achieved": False,
            "feedback": "Your response is too brief. Please explain your complete thought process step by step.",
            "needs_remediation": True,
            "evaluated_at": datetime.utcnow().isoformat()
        }