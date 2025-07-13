"""Exercise generation tool."""

import json
from typing import Dict, Any, List, Optional
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService

logger = structlog.get_logger()


class ExerciseTool:
    """
    LLM-powered tool to generate exercises.
    Returns structured JSON data, not conversational messages.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL
        self.pinecone_service = PineconeExerciseService()

    def _should_use_mock(self) -> bool:
        """Centralized check for mock exercise usage."""
        key = settings.OPENAI_API_KEY
        return (
            not key
            or key == "test_key"
            or key.startswith("test")
            or key == "your-openai-api-key"
        )

    async def generate(
        self, concept: Dict[str, Any], student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a personalized exercise and return a structured JSON object."""
        if self._should_use_mock():
            return self._create_mock_exercise_data(concept, student_profile)

        try:
            context_chunks = await self.pinecone_service.get_concept_context(
                concept.get("name", ""),
                student_profile.get("interests", []),
                student_profile.get("difficulty", "basic"),
            )
            prompt = self._build_exercise_prompt(concept, student_profile, context_chunks)
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

            exercise_data = json.loads(content)

            return {
                "type": "exercise_generated",
                "exercise": {
                    "id": str(uuid.uuid4()),
                    "concept_id": concept.get("id"),
                    "problem": exercise_data.get("problem"),
                    "scenario": exercise_data.get("scenario"),
                    "expected_steps": exercise_data.get("expected_steps", []),
                    "hints": exercise_data.get("hints", []),
                    "difficulty": student_profile.get("difficulty"),
                    "topic": concept.get("name")
                },
                "metadata": {
                    "context_used": bool(context_chunks),
                    "personalization": exercise_data.get("personalization", {})
                }
            }

        except Exception as e:
            logger.error("Exercise tool failed", error=str(e))
            return self._create_mock_exercise_data(concept, student_profile)

    def _get_system_prompt(self) -> str:
        """System prompt for exercise generation LLM - NO personality."""
        return """
        You are an expert educational content creator. Your task is to generate an educational exercise based on the provided details.

        Return a single JSON object with the following structure:
        - "scenario": A real-world context for the problem that uses student interests.
        - "problem": A specific, concrete challenge with a measurable outcome.
        - "expected_steps": An array of 4-6 strings outlining the logical steps to solve the problem.
        - "hints": An array of 2-3 strings containing progressive hints.
        - "personalization": A brief explanation of how the exercise was personalized for the student.

        Focus ONLY on generating accurate, high-quality educational content.
        Do NOT include any conversational elements, greetings, or personality in your response.
        """

    def _build_exercise_prompt(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        context_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Builds the prompt for the exercise generation LLM."""
        interests = student_profile.get("interests", [])
        difficulty = student_profile.get("difficulty", "basic")

        prompt = f"""
        Please create a {difficulty} exercise for the following concept:

        **Concept:** {concept.get('name')}
        **Description:** {concept.get('content', '')}

        **Student Profile:**
        - Interests: {', '.join(interests)}
        - Difficulty Level: {difficulty}

        **Requirements:**
        1. Create a scenario that authentically uses one or more student interests.
        2. The problem should be solvable and appropriate for the specified difficulty.
        3. The exercise must test deep understanding, not just memorization.
        """

        if context_chunks:
            prompt += "\n\n**Relevant Context from Knowledge Base:**\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get("content", "")
                prompt += f"Context {i+1}: {str(content)[:300]}...\n"
        else:
            prompt += "\nNo additional context provided.\n"

        prompt += "\nRespond with a JSON object following the required format."
        return prompt

    def _create_mock_exercise_data(
        self, concept: Dict[str, Any], student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates mock structured data for testing."""
        interests = student_profile.get("interests", ["general activities"])
        concept_name = concept.get("name", "Unknown Concept")
        difficulty = student_profile.get("difficulty", "basic")

        return {
            "type": "exercise_generated",
            "exercise": {
                "id": str(uuid.uuid4()),
                "concept_id": concept.get("id"),
                "problem": f"This is a mock {difficulty} problem about {concept_name}.",
                "scenario": f"Imagine you are using {concept_name} in a project related to {interests[0]}.",
                "expected_steps": ["Step 1", "Step 2", "Step 3"],
                "hints": ["Hint 1", "Hint 2"],
                "difficulty": difficulty,
                "topic": concept_name
            },
            "metadata": {
                "context_used": False,
                "personalization": {"interest_used": interests[0]}
            }
        } 