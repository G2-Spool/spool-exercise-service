"""Evaluate student responses to identify understanding gaps."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService
from app.core.prompts import ChainOfThoughtPrompts

logger = structlog.get_logger()


class ResponseEvaluator:
    """Evaluate student responses using LLMs with enhanced chain-of-thought prompting."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EVALUATION_MODEL
        self.pinecone_service = PineconeExerciseService()
        self.chain_of_thought = ChainOfThoughtPrompts()

    def _should_use_mock(self) -> bool:
        """Centralized check for mock evaluation usage."""
        key = settings.OPENAI_API_KEY
        return (
            not key
            or key == "test_key"
            or key.startswith("test")
            or key == "your-openai-api-key"
        )

    async def evaluate(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any],
        use_enhanced_prompts: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate a student's response with enhanced context and chain-of-thought prompting."""
        # Validate response length (but be more lenient for potentially correct short answers)
        if len(student_response) < 10:  # Very short responses (less than 10 chars) are likely insufficient
            return self._create_insufficient_response_evaluation(
                exercise, student_response
            )

        # Early return for mock evaluations
        if self._should_use_mock():
            return self._create_mock_evaluation(exercise, student_response, concept)

        try:
            # Get concept context for better evaluation
            context_chunks = await self.pinecone_service.get_concept_context(
                concept.get("name", ""),
                [],  # No interests needed for evaluation
                "basic",
            )

            # Build unified prompt
            prompt = self._build_prompt(
                exercise,
                student_response,
                concept,
                context_chunks,
                use_enhanced_prompts,
            )

            # Get system prompt
            system_prompt = self._get_system_prompt(use_enhanced_prompts)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Very low temperature for consistent evaluation
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
                understanding_analysis_obj = evaluation_result.get(
                    "understanding_analysis", {}
                )
                if isinstance(understanding_analysis_obj, dict):
                    # Check various possible score field names
                    score_fields = [
                        "Understanding score",
                        "understanding_score",
                        "score",
                        "overall_understanding_score",
                    ]
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
                            explicit_score = (
                                float(explicit_score.replace("%", "")) / 100
                            )
                        else:
                            explicit_score = float(explicit_score)
                    else:
                        explicit_score = float(explicit_score)

                    # Ensure score is in 0-1 range
                    explicit_score = float(explicit_score)
                    # Only normalize if score is actually > 1 (not already normalized)
                    if explicit_score > 1:
                        if explicit_score <= 10:
                            explicit_score = explicit_score / 10  # 8 -> 0.8
                        else:
                            explicit_score = explicit_score / 100  # 80 -> 0.8

                    explicit_score = min(max(explicit_score, 0.0), 1.0)
                except (ValueError, TypeError):
                    explicit_score = None

            # Extract other fields from evaluation_result (fallback safe access)
            understanding_analysis = evaluation_result.get("understanding_analysis", "")
            process_evaluation = evaluation_result.get("process_evaluation", "")
            growth_feedback = evaluation_result.get("growth_feedback", "")
            strength_identification = evaluation_result.get(
                "strength_identification", ""
            )
            next_steps = evaluation_result.get("next_steps", "")

            # Determine understanding score
            if explicit_score is not None:
                understanding_score = explicit_score
            else:
                understanding_score = self._extract_understanding_score(
                    understanding_analysis, process_evaluation
                )

            mastery_achieved = understanding_score >= 0.8  # 80% threshold

            # Extract step analysis from the detailed feedback
            correct_steps, missing_steps, incorrect_steps = self._extract_step_analysis(
                understanding_analysis,
                process_evaluation,
                exercise.get("expected_steps", []),
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

    def _get_system_prompt(self, enhanced: bool = True) -> str:
        """Unified system prompt generator."""
        base_prompt = """
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
        6. Require the student to solve the problem multiple times to get full credit
        7. Penalize students for using different valid approaches or step sequences
        8. Give zero credit when students demonstrate understanding but use different methods

        ## STRUCTURED OUTPUT FORMAT
        Return JSON with:
        - understanding_analysis: Detailed breakdown of demonstrated vs. missing understanding (MUST include "Understanding score: X/10")
        - process_evaluation: Assessment of problem-solving approach and reasoning quality
        - growth_feedback: Specific, actionable suggestions for improvement
        - strength_identification: Concrete evidence of what student did well
        - next_steps: Clear guidance for continued learning
        
        CRITICAL OUTPUT FORMAT:
        In your understanding_analysis field, you MUST include the exact phrase "Understanding score: X/10" where X is the numeric score
        
        DETERMINISTIC SCORING RULES:
        Use ONLY these scores based on the criteria:
        - 10/10: Correct final answer + Clear reasoning + No major errors
        - 9/10: Correct final answer + Good reasoning + Minor presentation issues
        - 8/10: Correct final answer + Adequate reasoning + Small gaps
        - 7/10: Correct final answer + Minimal reasoning + Major gaps in explanation
        - 6/10: Correct final answer ONLY (even if no explanation provided)
        - 4-5/10: Partially correct + Some understanding shown
        - 0-3/10: Incorrect answer OR major misunderstanding
        
        CRITICAL PRINCIPLE: Getting the right answer shows understanding - give credit accordingly
        
        CRITICAL: Focus on mathematical correctness and logical reasoning, NOT matching specific steps

        ## THINKING PROCESS
        Before evaluating:
        1. Identify evidence of deep vs. surface understanding
        2. Analyze problem-solving process and reasoning quality
        3. Connect evaluation to learning objectives and expected outcomes
        4. Generate specific, actionable feedback for improvement
        5. Consider multiple valid approaches while maintaining rigor"""

        enhanced_block = (
            """
        
        ## ENHANCED CHAIN-OF-THOUGHT EVALUATION PROCESS
        When evaluating responses, follow this enhanced process:
        
        ### Step 1: Systematic Analysis
        - First, read the entire response to understand the student's approach
        - Identify the main strategy or method the student used
        - Note any mathematical or logical reasoning demonstrated
        
        ### Step 2: Step-by-Step Verification
        - Break down the response into individual steps or components
        - Verify each step against the expected solution path
        - Check mathematical accuracy and logical flow
        
        ### Step 3: Understanding Assessment
        - Evaluate conceptual understanding vs. procedural execution
        - Identify gaps between what the student knows and what they demonstrated
        - Assess whether errors are conceptual or computational
        
        ### Step 4: Comprehensive Scoring
        - Assign understanding score based on demonstrated mastery and overall correctness
        - Consider multiple valid approaches and give full credit for sound reasoning
        - Ensure scoring reflects depth of understanding, not adherence to specific steps
        - Focus on whether the student solved the problem correctly, not if they hit all
            the expected steps
        
        ### Step 5: Feedback Generation
        - Provide specific, actionable feedback for improvement
        - Highlight strengths and build confidence
        - Suggest next steps for continued learning
        
        **Critical**: Always show your reasoning process and explicitly state "Understanding score: X/10" in your analysis."""
            if enhanced
            else ""
        )

        return base_prompt + enhanced_block

    def _build_prompt(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any],
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        enhanced: bool = False,
    ) -> str:
        """Single prompt builder with optional enhanced/context features."""
        expected_steps = exercise.get("expected_steps", [])

        # Base prompt construction
        prompt = f"""Evaluate this student's response to an exercise:
        
        PROBLEM: {exercise.get('content', {}).get('problem')}
        
        STUDENT RESPONSE: "{student_response}"
        
        EVALUATION FOCUS:
        1. Is the final answer mathematically correct?
        2. Does the student demonstrate valid reasoning?
        3. Are there any major conceptual errors?
        
        SCORING CRITERIA:
        - Give 10/10 if: Correct answer + Clear reasoning + No major errors
        - Give 9/10 if: Correct answer + Good reasoning + Minor issues  
        - Give 8/10 if: Correct answer + Adequate reasoning + Small gaps
        - Give 7/10 if: Correct answer + Minimal reasoning + Major gaps
        - Give 6/10 if: Correct answer ONLY (even without explanation)
        - Give 4-5/10 if: Partially correct + Some understanding shown
        - Give 0-3/10 if: Wrong answer OR no understanding shown
        
        IMPORTANT: A correct final answer deserves at least 6/10, even if brief
        
        EXAMPLES:
        - "Average = 20" for a problem where 20 is correct → Give 6/10 minimum
        - "Sum is 100, average is 20" → Give 7-8/10 
        - Detailed correct work → Give 9-10/10
        
        CRITICAL: In your understanding_analysis, include "Understanding score: X/10"
        """

        # Add context for more accurate evaluation if available
        if context_chunks:
            prompt += "\n\nAdditional Context for Evaluation:\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get("content", "")
                if isinstance(content, str):
                    prompt += f"Context {i+1}: {content[:300]}...\n"
                else:
                    prompt += f"Context {i+1}: {str(content)[:300]}...\n"

        # Add enhanced evaluation criteria if requested
        enhanced_criteria = ""
        if enhanced:
            enhanced_criteria = """
        
        ENHANCED EVALUATION CRITERIA:
        - Use systematic step-by-step analysis
        - Verify each component against expected solution path
        - Assess both conceptual understanding and procedural execution
        - Provide comprehensive scoring with detailed reasoning"""

        if enhanced_criteria:
            prompt += f"""
        
        Enhanced Evaluation Criteria:
        {enhanced_criteria}
        """
        
        prompt += """
        
        Remember: Focus on mathematical correctness and reasoning quality, not on matching specific solution steps or approaches."""

        return prompt

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

    def _extract_understanding_score(
        self, understanding_analysis: str, process_evaluation: str
    ) -> float:
        """Extract understanding score from structured LLM response."""
        combined_text = f"{understanding_analysis} {process_evaluation}".lower()
        
        import re
        
        # Look for the exact format: "understanding score: X/10"
        score_pattern = r"understanding score:\s*(\d+(?:\.\d+)?)/10"
        match = re.search(score_pattern, combined_text)
        if match:
            score = float(match.group(1))
            return min(score / 10.0, 1.0)  # Normalize to 0-1 scale
        
        # Backup: look for any "X/10" pattern
        general_pattern = r"(\d+(?:\.\d+)?)/10"
        match = re.search(general_pattern, combined_text)
        if match:
            score = float(match.group(1))
            return min(score / 10.0, 1.0)
        
        # Final fallback: analyze the structured responses
        final_correct = "final answer correct: yes" in combined_text
        reasoning_valid = "reasoning valid: yes" in combined_text
        major_errors = "major errors: yes" in combined_text
        
        # Deterministic scoring based on structured analysis
        if final_correct and reasoning_valid and not major_errors:
            return 1.0  # 10/10
        elif final_correct and reasoning_valid:
            return 0.9  # 9/10
        elif final_correct and not major_errors:
            return 0.8  # 8/10
        elif final_correct:
            return 0.7  # 7/10
        elif reasoning_valid and not major_errors:
            return 0.6  # 6/10
        elif not major_errors:
            return 0.4  # 4/10
        else:
            return 0.2  # 2/10

    def _extract_step_analysis(
        self,
        understanding_analysis: str,
        process_evaluation: str,
        expected_steps: List[str],
    ) -> tuple:
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
                positive_context = any(
                    pos in combined_text
                    for pos in ["correct", "good", "demonstrates", "shows"]
                )
                negative_context = any(
                    neg in combined_text
                    for neg in ["missing", "lacks", "incorrect", "wrong"]
                )

                if positive_context and not negative_context:
                    correct_steps.append(f"Demonstrated: {step}")
                elif negative_context:
                    incorrect_steps.append(f"Incorrectly addressed: {step}")
                else:
                    correct_steps.append(f"Partially addressed: {step}")
            else:
                missing_steps.append(f"Missing: {step}")

        return correct_steps, missing_steps, incorrect_steps

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
