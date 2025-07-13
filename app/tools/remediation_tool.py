"""Remediation generation tool."""

import json
from typing import Dict, Any, List, Optional
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService

logger = structlog.get_logger()


class RemediationTool:
    """
    LLM-powered tool to generate remediation content.
    Returns structured JSON data, not conversational messages.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL
        self.pinecone_service = PineconeExerciseService()

    def _should_use_mock(self) -> bool:
        """Centralized check for mock remediation usage."""
        key = settings.OPENAI_API_KEY
        return (
            not key
            or key == "test_key"
            or key.startswith("test")
            or key == "your-openai-api-key"
        )

    async def generate(
        self,
        evaluation: Dict[str, Any],
        exercise: Dict[str, Any],
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate remediation content and return a structured JSON object."""
        if self._should_use_mock():
            return self._create_mock_remediation_data(evaluation, concept)

        try:
            target_gaps = evaluation.get("analysis", {}).get("weaknesses", [])
            context_chunks = await self.pinecone_service.get_remediation_examples(
                ", ".join(target_gaps),
                concept.get("name", ""),
                student_profile.get("interests", []),
            )
            prompt = self._build_remediation_prompt(
                evaluation, exercise, concept, student_profile, context_chunks
            )
            system_prompt = self._get_system_prompt()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.TEMPERATURE,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")

            remediation_data = json.loads(content)

            return {
                "type": "remediation_generated",
                "remediation": {
                    "id": str(uuid.uuid4()),
                    "target_gaps": remediation_data.get("target_gaps", []),
                    "explanations": remediation_data.get("explanations", []),
                    "examples": remediation_data.get("examples", []),
                    "practice_problems": remediation_data.get("practice_problems", []),
                },
                "teaching_strategy": remediation_data.get("teaching_strategy", {}),
                "metadata": {"context_used": bool(context_chunks)},
            }

        except Exception as e:
            logger.error("Remediation tool failed", error=str(e))
            return self._create_mock_remediation_data(evaluation, concept)

    def _get_system_prompt(self) -> str:
        """System prompt for remediation LLM - NO personality."""
        return """
        You are a remediation specialist. Your task is to generate targeted learning materials to address specific knowledge gaps identified in a student's evaluation.

        Return a single JSON object with the following structure:
        - "target_gaps": An array of strings listing the specific gaps this remediation addresses.
        - "explanations": An array of strings providing clear, concise explanations for each gap.
        - "examples": An array of objects, where each object contains a "problem" and "solution" for a worked example.
        - "practice_problems": An array of objects, where each object contains a "problem" and "hint" for new practice.
        - "teaching_strategy": An object containing "approach", "key_concepts", and "common_mistakes" to guide the instruction.

        Focus ONLY on generating accurate, high-quality educational content.
        Do NOT include any conversational elements, greetings, or personality in your response.
        """

    def _build_remediation_prompt(
        self,
        evaluation: Dict[str, Any],
        exercise: Dict[str, Any],
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        context_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Builds the prompt for the remediation generation LLM."""
        analysis = evaluation.get("analysis", {})
        prompt = f"""
        Please create remediation content for a student based on their evaluation.

        **Concept:** {concept.get('name')}
        **Original Problem:** {exercise.get('problem')}
        **Student's Score:** {evaluation.get('evaluation', {}).get('understanding_score')}

        **Identified Weaknesses to Address:**
        - {", ".join(analysis.get('weaknesses', ['N/A']))}

        **Identified Missing Steps:**
        - {", ".join(analysis.get('missing_steps', ['N/A']))}

        **Student Profile:**
        - Interests: {", ".join(student_profile.get('interests', []))}
        """

        if context_chunks:
            prompt += "\n\n**Relevant Examples and Explanations from Knowledge Base:**\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get("content", "")
                prompt += f"Context {i+1}: {str(content)[:400]}...\n"
        else:
            prompt += "\nNo additional context provided.\n"

        prompt += "\nRespond with a JSON object following the required format."
        return prompt

    def _create_mock_remediation_data(
        self, evaluation: Dict[str, Any], concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates mock structured data for testing."""
        gaps = evaluation.get("analysis", {}).get("weaknesses", ["a specific area"])
        return {
            "type": "remediation_generated",
            "remediation": {
                "id": str(uuid.uuid4()),
                "target_gaps": gaps,
                "explanations": [f"Here is a mock explanation for {gaps[0]}."],
                "examples": [{"problem": "Mock example problem", "solution": "Mock solution"}],
                "practice_problems": [{"problem": "Mock practice problem", "hint": "Mock hint"}],
            },
            "teaching_strategy": {"approach": "Mock approach"},
            "metadata": {"context_used": False},
        } 