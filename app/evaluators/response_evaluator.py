"""Evaluate student responses to identify understanding gaps."""

import json
from typing import Dict, Any, List
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService

logger = structlog.get_logger()


class ResponseEvaluator:
    """Evaluate student responses using LLMs."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EVALUATION_MODEL
        self.pinecone_service = PineconeExerciseService()

    async def evaluate(
        self, exercise: Dict[str, Any], student_response: str, concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a student's response with enhanced context."""
        try:
            # Get concept context for better evaluation
            context_chunks = await self.pinecone_service.get_concept_context(
                concept.get("name", ""),
                [],  # No interests needed for evaluation
                "basic"
            )
            
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

            # Create enhanced prompt with context if available, otherwise use standard prompt
            if context_chunks:
                prompt = self._create_enhanced_evaluation_prompt(
                    exercise, student_response, concept, context_chunks
                )
            else:
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

            # Retain full raw response for downstream logging/analysis
            raw_llm_response = content
            
            # Use explicit numeric score if provided by the LLM
            explicit_score = evaluation_result.get("understanding_score")
            
            # Also check nested understanding_analysis for score
            if explicit_score is None:
                understanding_analysis_obj = evaluation_result.get("understanding_analysis", {})
                if isinstance(understanding_analysis_obj, dict):
                    # Check various possible score field names
                    score_fields = ["Understanding score", "understanding_score", "score", "overall_understanding_score"]
                    for field in score_fields:
                        if field in understanding_analysis_obj:
                            explicit_score = understanding_analysis_obj[field]
                            break
            
            if explicit_score is not None:
                try:
                    # Handle string scores like "7/10" or "70%"
                    if isinstance(explicit_score, str):
                        explicit_score = explicit_score.strip()
                        if "/" in explicit_score:
                            # Handle "7/10" format
                            parts = explicit_score.split("/")
                            if len(parts) == 2:
                                numerator = float(parts[0])
                                denominator = float(parts[1])
                                explicit_score = numerator / denominator
                        elif "%" in explicit_score:
                            # Handle "70%" format
                            explicit_score = float(explicit_score.replace("%", "")) / 100
                        else:
                            explicit_score = float(explicit_score)
                    else:
                        explicit_score = float(explicit_score)
                    
                    # Ensure score is in 0-1 range
                    explicit_score = float(explicit_score)
                    if explicit_score > 1:
                        explicit_score = explicit_score / 10 if explicit_score <= 10 else explicit_score / 100
                    
                    explicit_score = min(max(explicit_score, 0.0), 1.0)
                except (ValueError, TypeError):
                    explicit_score = None
            
            # Extract other fields from evaluation_result (fallback safe access)
            understanding_analysis = evaluation_result.get("understanding_analysis", "")
            process_evaluation = evaluation_result.get("process_evaluation", "")
            growth_feedback = evaluation_result.get("growth_feedback", "")
            strength_identification = evaluation_result.get("strength_identification", "")
            next_steps = evaluation_result.get("next_steps", "")

            # Determine understanding score
            if explicit_score is not None:
                understanding_score = explicit_score
            else:
                understanding_score = self._extract_understanding_score(understanding_analysis, process_evaluation)
            
            mastery_achieved = understanding_score >= 0.8  # 80% threshold
            
            # Extract step analysis from the detailed feedback
            correct_steps, missing_steps, incorrect_steps = self._extract_step_analysis(
                understanding_analysis, process_evaluation, exercise.get("expected_steps", [])
            )

            # Create evaluation object
            evaluation = {
                "evaluation_id": str(uuid.uuid4()),
                "exercise_id": exercise.get("exercise_id"),
                "student_response": student_response,
                "competency_map": {
                    "correct_steps": correct_steps,
                    "missing_steps": missing_steps,
                    "incorrect_steps": incorrect_steps,
                    "partial_steps": [],
                },
                "understanding_score": understanding_score,
                "mastery_achieved": mastery_achieved,
                "feedback": f"{growth_feedback}\n\nStrengths: {strength_identification}\n\nNext Steps: {next_steps}",
                "needs_remediation": not mastery_achieved,
                "understanding_gaps": missing_steps,
                "llm_response": evaluation_result,  # full parsed JSON
                "llm_response_raw": raw_llm_response,
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

    def _extract_understanding_score(self, understanding_analysis: str, process_evaluation: str) -> float:
        """Extract understanding score from LLM analysis."""
        combined_text = f"{understanding_analysis} {process_evaluation}".lower()
        
        # Look for explicit score mentions
        import re
        score_patterns = [
            r'score[:\s]*(\d+(?:\.\d+)?)',
            r'understanding[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[/\s]*(?:out of|/)?\s*(?:10|1\.0|1)',
            r'(\d+(?:\.\d+)?)%'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, combined_text)
            if match:
                score = float(match.group(1))
                # Normalize to 0-1 scale
                if score > 1:
                    score = score / 100 if score <= 100 else score / 10
                return min(score, 1.0)
        
        # Fallback: analyze quality indicators
        positive_indicators = ['correct', 'accurate', 'good', 'excellent', 'demonstrates', 'shows', 'understands']
        negative_indicators = ['incorrect', 'wrong', 'missing', 'lacks', 'fails', 'confused', 'unclear']
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in combined_text)
        negative_count = sum(1 for indicator in negative_indicators if indicator in combined_text)
        
        if positive_count > negative_count:
            return 0.8 + (positive_count - negative_count) * 0.05
        elif negative_count > positive_count:
            return max(0.2, 0.7 - (negative_count - positive_count) * 0.1)
        else:
            return 0.6

    def _extract_step_analysis(self, understanding_analysis: str, process_evaluation: str, expected_steps: List[str]) -> tuple:
        """Extract step analysis from LLM feedback."""
        combined_text = f"{understanding_analysis} {process_evaluation}".lower()
        
        correct_steps = []
        missing_steps = []
        incorrect_steps = []
        
        # Analyze each expected step
        for step in expected_steps:
            step_lower = step.lower()
            key_words = step_lower.split()[:3]  # First 3 words as key indicators
            
            # Check if step is mentioned positively
            step_mentioned = any(word in combined_text for word in key_words)
            
            if step_mentioned:
                # Look for positive or negative context
                positive_context = any(pos in combined_text for pos in ['correct', 'good', 'demonstrates', 'shows'])
                negative_context = any(neg in combined_text for neg in ['missing', 'lacks', 'incorrect', 'wrong'])
                
                if positive_context and not negative_context:
                    correct_steps.append(f"Demonstrated: {step}")
                elif negative_context:
                    incorrect_steps.append(f"Incorrectly addressed: {step}")
                else:
                    correct_steps.append(f"Partially addressed: {step}")
            else:
                missing_steps.append(f"Missing: {step}")
        
        return correct_steps, missing_steps, incorrect_steps

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
        - understanding_analysis: Detailed breakdown of demonstrated vs. missing understanding (include overall understanding score 0-10)
        - process_evaluation: Assessment of problem-solving approach and reasoning quality
        - growth_feedback: Specific, actionable suggestions for improvement
        - strength_identification: Concrete evidence of what student did well
        - next_steps: Clear guidance for continued learning
        
        CRITICAL: In your understanding_analysis, explicitly state "Understanding score: X/10" where X is the numeric score.

        ## THINKING PROCESS
        Before evaluating:
        1. Identify evidence of deep vs. surface understanding
        2. Analyze problem-solving process and reasoning quality
        3. Connect evaluation to learning objectives and expected outcomes
        4. Generate specific, actionable feedback for improvement
        5. Consider multiple valid approaches while maintaining rigor
        """

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

    def _create_enhanced_evaluation_prompt(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any],
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """Create enhanced evaluation prompt with context."""
        expected_steps = exercise.get("expected_steps", [])
        
        prompt = f"""Evaluate this student's response to an exercise:
        
        Concept Being Tested: {concept.get('name')}
        
        Exercise Scenario: {exercise.get('content', {}).get('scenario')}
        Exercise Problem: {exercise.get('content', {}).get('problem')}
        
        Expected Solution Steps:
        {chr(10).join(f"{i+1}. {step}" for i, step in enumerate(expected_steps))}
        
        Student's Response:
        "{student_response}"
        """
        
        # Add context for more accurate evaluation
        if context_chunks:
            prompt += "\n\nAdditional Context for Evaluation:\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get('content', '')
                if isinstance(content, str):
                    prompt += f"Context {i+1}: {content[:300]}...\n"
                else:
                    prompt += f"Context {i+1}: {str(content)[:300]}...\n"
        
        prompt += """
        Evaluation Criteria:
        1. Has the student demonstrated understanding of each expected step?
        2. Is their reasoning logically sound?
        3. Did they identify the key concepts?
        4. Are there any misconceptions or knowledge gaps?
        5. Is the explanation complete and clear?
        6. Use the provided context to verify accuracy
        
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
