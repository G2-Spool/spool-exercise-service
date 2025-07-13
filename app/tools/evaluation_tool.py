"""Evaluation tool for student responses."""

import json
from typing import Dict, Any, List, Optional
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService

logger = structlog.get_logger()


class EvaluationTool:
    """
    LLM-powered tool to evaluate student responses.
    Returns structured JSON data, not conversational messages.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EVALUATION_MODEL
        self.pinecone_service = PineconeExerciseService()

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
        """
        Evaluate a student's response and return a structured JSON object.
        """
        if self._should_use_mock():
            return self._create_mock_evaluation_data(exercise, student_response)

        try:
            context_chunks = await self.pinecone_service.get_concept_context(
                concept.get("name", ""), [], "basic"
            )
            prompt = self._build_evaluation_prompt(
                exercise, student_response, context_chunks
            )
            system_prompt = self._get_system_prompt()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")

            evaluation_data = json.loads(content)

            # Standardize the output structure
            return {
                "type": "evaluation_completed",
                "evaluation": {
                    "id": str(uuid.uuid4()),
                    "understanding_score": evaluation_data.get("understanding_score", 0.0),
                    "mastery_achieved": evaluation_data.get("mastery_achieved", False),
                    "needs_remediation": not evaluation_data.get("mastery_achieved", False),
                },
                "analysis": {
                    "strengths": evaluation_data.get("strengths", []),
                    "weaknesses": evaluation_data.get("weaknesses", []),
                    "next_steps": evaluation_data.get("next_steps", []),
                    "detailed_feedback": evaluation_data.get("detailed_feedback", ""),
                    "correct_steps": evaluation_data.get("correct_steps", []),
                    "missing_steps": evaluation_data.get("missing_steps", []),
                    "incorrect_steps": evaluation_data.get("incorrect_steps", []),
                },
                "metadata": {
                    "evaluation_time": "now",
                    "llm_response_raw": content,
                }
            }
        except Exception as e:
            logger.error("Evaluation tool failed", error=str(e))
            return self._create_mock_evaluation_data(exercise, student_response)

    def _get_system_prompt(self) -> str:
        """System prompt for evaluation LLM - NO personality."""
        return """
        You are an educational assessment specialist. Evaluate student responses objectively.

        Return JSON with:
        - understanding_score: Float from 0.0 to 1.0
        - mastery_achieved: Boolean (true if score >= 0.8)
        - strengths: Array of strings identifying what the student did well.
        - weaknesses: Array of strings identifying areas for improvement.
        - next_steps: Array of strings with actionable recommendations.
        - detailed_feedback: A paragraph explaining the evaluation.
        - correct_steps: Array of strings listing the steps the student got right.
        - missing_steps: Array of strings listing the steps the student missed.
        - incorrect_steps: Array of strings listing the steps the student got wrong.

        Focus ONLY on objective assessment. Do NOT include conversational elements or personality.
        The final answer's correctness is important, but showing the reasoning is key.
        """

    def _build_evaluation_prompt(
        self,
        exercise: Dict[str, Any],
        student_response: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Builds the prompt for the evaluation LLM."""
        prompt = f"""
        Please evaluate the following student response based on the exercise.

        **Exercise Problem:**
        {exercise.get('content', {}).get('problem')}

        **Expected Steps/Solution:**
        {exercise.get('expected_steps', [])}

        **Student's Response:**
        "{student_response}"

        **Evaluation Criteria:**
        1. Assess conceptual understanding.
        2. Analyze the problem-solving process.
        3. Determine mathematical correctness.
        4. Identify specific strengths and weaknesses.
        5. Provide a score from 0.0 to 1.0.

        **Additional Context from Knowledge Base:**
        """
        if context_chunks:
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get("content", "")
                prompt += f"Context {i+1}: {str(content)[:300]}...\n"
        else:
            prompt += "No additional context provided.\n"

        prompt += "\nRespond with a JSON object following the required format."
        return prompt

    def _create_mock_evaluation_data(
        self, exercise: Dict[str, Any], student_response: str
    ) -> Dict[str, Any]:
        """Creates mock structured data for testing."""
        score = 0.7 if "correct" in student_response.lower() else 0.3
        mastery = score >= 0.8
        return {
            "type": "evaluation_completed",
            "evaluation": {
                "id": str(uuid.uuid4()),
                "understanding_score": score,
                "mastery_achieved": mastery,
                "needs_remediation": not mastery,
            },
            "analysis": {
                "strengths": ["Good attempt."],
                "weaknesses": ["Some steps were missing."],
                "next_steps": ["Review the concept of XYZ."],
                "detailed_feedback": "This is a mock evaluation. Your response was partially correct.",
                "correct_steps": ["Identified the problem."],
                "missing_steps": ["Did not show all work."],
                "incorrect_steps": [],
            },
            "metadata": {"evaluation_time": "mock_time"},
        } 