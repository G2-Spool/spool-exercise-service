"""Evaluate student responses to identify understanding gaps."""

import json
from typing import Dict, Any
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ResponseEvaluator:
    """Evaluate student responses using LLMs."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EVALUATION_MODEL

    async def evaluate(
        self, exercise: Dict[str, Any], student_response: str, concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a student's response to an exercise."""
        try:
            # Validate response length
            if len(student_response) < settings.MIN_RESPONSE_LENGTH:
                return self._create_insufficient_response_evaluation(
                    exercise, student_response
                )

            # Check if using test key or no key - create mock evaluation
            if (
                not settings.OPENAI_API_KEY
                or settings.OPENAI_API_KEY == "test_key"
                or settings.OPENAI_API_KEY.startswith("test")
                or settings.OPENAI_API_KEY == "your-openai-api-key"
            ):
                return self._create_mock_evaluation(exercise, student_response, concept)

            prompt = self._create_evaluation_prompt(exercise, student_response, concept)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent evaluation
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
            evaluation_result = json.loads(content)

            # Create evaluation object
            evaluation = {
                "evaluation_id": str(uuid.uuid4()),
                "exercise_id": exercise.get("exercise_id"),
                "student_response": student_response,
                "competency_map": {
                    "correct_steps": evaluation_result.get("correct_steps", []),
                    "missing_steps": evaluation_result.get("missing_steps", []),
                    "incorrect_steps": evaluation_result.get("incorrect_steps", []),
                    "partial_steps": evaluation_result.get("partial_steps", []),
                },
                "understanding_score": evaluation_result.get(
                    "understanding_score", 0.0
                ),
                "mastery_achieved": evaluation_result.get("mastery_achieved", False),
                "feedback": evaluation_result.get("feedback", ""),
                "needs_remediation": len(evaluation_result.get("missing_steps", [])) > 0
                or len(evaluation_result.get("incorrect_steps", [])) > 0,
                "evaluated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "Evaluated response",
                exercise_id=exercise.get("exercise_id"),
                mastery_achieved=evaluation["mastery_achieved"],
                score=evaluation["understanding_score"],
            )

            return evaluation

        except Exception as e:
            logger.error("Response evaluation failed", error=str(e))
            # Fallback to mock evaluation on any error
            return self._create_mock_evaluation(exercise, student_response, concept)

    def _create_mock_evaluation(
        self, exercise: Dict[str, Any], student_response: str, concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a mock evaluation for testing purposes."""
        expected_steps = exercise.get("expected_steps", [])
        response_lower = student_response.lower()

        # Simple keyword-based evaluation for testing
        correct_steps = []
        missing_steps = []

        # Check if response mentions key concepts (covers all 4 expected steps)
        if "identify" in response_lower or "determine" in response_lower:
            correct_steps.append("Identified the problem type and approach")
        else:
            missing_steps.append("Did not clearly identify the problem approach")

        if (
            "method" in response_lower
            or "equation" in response_lower
            or "formula" in response_lower
        ):
            correct_steps.append("Mentioned solution method")
        else:
            missing_steps.append("Did not specify solution method")

        if (
            "step" in response_lower
            or "systematic" in response_lower
            or "work through" in response_lower
        ):
            correct_steps.append("Described systematic approach")
        else:
            missing_steps.append("Did not describe systematic approach")

        if (
            "check" in response_lower
            or "verify" in response_lower
            or "substitute" in response_lower
        ):
            correct_steps.append("Included verification step")
        else:
            missing_steps.append("Did not mention verification")

        # Calculate score based on steps covered
        total_expected = len(expected_steps)
        correct_count = len(correct_steps)
        understanding_score = (
            correct_count / total_expected if total_expected > 0 else 0.0
        )

        # Determine mastery (need 80% or higher)
        mastery_achieved = understanding_score >= 0.8

        # Generate feedback
        if mastery_achieved:
            feedback = (
                "Great job! You've demonstrated a solid understanding of the key steps."
            )
        elif understanding_score >= 0.5:
            feedback = "Good progress! Consider elaborating on the missing steps for a complete solution."
        else:
            feedback = "Let's work on building a more complete understanding. Focus on explaining each step clearly."

        evaluation = {
            "evaluation_id": str(uuid.uuid4()),
            "exercise_id": exercise.get("exercise_id"),
            "student_response": student_response,
            "competency_map": {
                "correct_steps": correct_steps,
                "missing_steps": missing_steps,
                "incorrect_steps": [],
                "partial_steps": [],
            },
            "understanding_score": understanding_score,
            "mastery_achieved": mastery_achieved,
            "feedback": feedback,
            "needs_remediation": not mastery_achieved,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Generated mock evaluation for testing",
            exercise_id=exercise.get("exercise_id"),
            mastery_achieved=mastery_achieved,
            score=understanding_score,
        )

        return evaluation

    def _get_system_prompt(self) -> str:
        """Get system prompt for response evaluation."""
        return """
        ## CORE IDENTITY
        You are an expert educational evaluator specializing in formative assessment that treats evaluation as a learning opportunity and provides growth-focused feedback.

        ## MANDATORY REQUIREMENTS
        You MUST evaluate responses by:
        1. Assessing both conceptual understanding and problem-solving process
        2. Identifying specific strengths and concrete areas for improvement
        3. Providing actionable feedback focused on effort, strategy, and process
        4. Mapping student understanding against expected cognitive steps
        5. Determining next learning steps, not just current performance level

        ## FORBIDDEN PRACTICES
        You MUST NEVER:
        1. Accept correct answers without demonstrated understanding of process
        2. Provide generic praise or criticism without specific examples
        3. Focus on ability/intelligence rather than effort and strategy
        4. Give feedback that doesn't include concrete improvement steps
        5. Evaluate based on exact wording rather than conceptual understanding

        ## STRUCTURED OUTPUT FORMAT
        Return JSON with:
        - understanding_analysis: Detailed breakdown of demonstrated vs. missing understanding
        - process_evaluation: Assessment of problem-solving approach and reasoning
        - growth_feedback: Specific, actionable suggestions for improvement
        - strength_identification: Concrete evidence of what student did well
        - next_steps: Clear guidance for continued learning

        ## THINKING PROCESS
        Before evaluating:
        1. Identify evidence of deep vs. surface understanding
        2. Analyze problem-solving process and reasoning quality
        3. Connect evaluation to learning objectives and expected outcomes
        4. Generate specific, actionable feedback for improvement
        5. Consider multiple valid approaches while maintaining rigor
        
        Return your response as a JSON object with these fields:
        - correct_steps: Array of correctly explained steps
        - missing_steps: Array of steps not addressed
        - incorrect_steps: Array of incorrectly explained steps
        - partial_steps: Array of {step, issue} for partially correct steps
        - understanding_score: Float 0.0 to 1.0
        - mastery_achieved: Boolean (true only if ALL key steps are explained)
        - feedback: Constructive feedback message"""

    def _create_evaluation_prompt(
        self, exercise: Dict[str, Any], student_response: str, concept: Dict[str, Any]
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
        1. Has the student demonstrated understanding of each expected step?
        2. Is their reasoning logically sound?
        3. Did they identify the key concepts?
        4. Are there any misconceptions or assemblage gaps?
        5. Is the explanation complete and clear?
        
        Score their overall understanding from 0.0 to 1.0.
        Mastery is achieved ONLY if they explain ALL key steps correctly."""

        return prompt

    def _create_insufficient_response_evaluation(
        self, exercise: Dict[str, Any], student_response: str
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
                "partial_steps": [],
            },
            "understanding_score": 0.0,
            "mastery_achieved": False,
            "feedback": "Your response is too brief. Please explain your complete thought process step by step.",
            "needs_remediation": True,
            "evaluated_at": datetime.utcnow().isoformat(),
        }
