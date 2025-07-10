"""Generate remediation content for learning gaps."""

import json
from typing import Dict, Any
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RemediationGenerator:
    """Generate remediation content using LLMs."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL

    async def generate(
        self,
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        original_exercise: Dict[str, Any],
        evaluation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate remediation content for a specific gap."""
        try:
            # Check if using test key or no key - create mock remediation
            if (
                not settings.OPENAI_API_KEY
                or settings.OPENAI_API_KEY == "test_key"
                or settings.OPENAI_API_KEY.startswith("test")
                or settings.OPENAI_API_KEY == "your-openai-api-key"
            ):
                return self._create_mock_remediation(
                    concept, target_gap, student_profile, original_exercise, evaluation
                )

            prompt = self._create_remediation_prompt(
                concept, target_gap, student_profile, original_exercise, evaluation
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
            remediation_content = json.loads(content)

            # Create remediation object
            remediation = {
                "remediation_id": str(uuid.uuid4()),
                "evaluation_id": evaluation.get("evaluation_id"),
                "exercise_id": original_exercise.get("exercise_id"),
                "student_id": student_profile.get("student_id"),
                "target_gap": target_gap,
                "content": remediation_content,
                "personalized_context": remediation_content.get(
                    "personalized_context", ""
                ),
                "practice_problems": remediation_content.get("practice_problems", []),
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "Generated remediation",
                remediation_id=remediation["remediation_id"],
                target_gap=target_gap,
            )

            return remediation

        except Exception as e:
            logger.error("Remediation generation failed", error=str(e))
            # Fallback to mock remediation on any error
            return self._create_mock_remediation(
                concept, target_gap, student_profile, original_exercise, evaluation
            )

    def _create_mock_remediation(
        self,
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        original_exercise: Dict[str, Any],
        evaluation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a mock remediation for testing purposes."""
        interests = student_profile.get("interests", ["general activities"])
        concept_name = concept.get("name", "the concept")

        mock_content = {
            "explanation": f"Let's work on {target_gap}. {concept_name} is a fundamental concept that builds on identifying key problem components.",
            "step_by_step_guide": [
                "Step 1: Take time to clearly read and understand what the problem is asking",
                "Step 2: Identify the key information given and what you need to find",
                f"Step 3: Choose the appropriate method for {concept_name}",
                "Step 4: Work through the solution systematically",
                "Step 5: Always verify your answer makes sense",
            ],
            "examples": [
                {
                    "problem": f"Here's a simple example of {concept_name}",
                    "solution": "Step-by-step solution would be provided here",
                    "context": f"This connects to your interest in {interests[0]}",
                }
            ],
            "practice_problems": [
                {
                    "problem": f"Practice problem focusing on {target_gap}",
                    "difficulty": "easier",
                    "hint": f"Remember to focus on {target_gap.lower()}",
                }
            ],
            "personalized_context": f"Since you're interested in {interests[0]}, here's how {concept_name} applies in that area...",
            "key_insights": [
                f"The most important thing about {target_gap} is to take it step by step",
                "Always start by clearly identifying what you know and what you need to find",
                f"Practice makes perfect - the more you work with {concept_name}, the easier it becomes",
            ],
        }

        remediation = {
            "remediation_id": str(uuid.uuid4()),
            "evaluation_id": evaluation.get("evaluation_id"),
            "exercise_id": original_exercise.get("exercise_id"),
            "student_id": student_profile.get("student_id"),
            "target_gap": target_gap,
            "content": mock_content,
            "personalized_context": mock_content["personalized_context"],
            "practice_problems": mock_content["practice_problems"],
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Generated mock remediation for testing",
            remediation_id=remediation["remediation_id"],
            target_gap=target_gap,
        )

        return remediation

    def _get_system_prompt(self) -> str:
        """Get system prompt for remediation generation."""
        return """You are an expert educational content creator specializing in 
        generating targeted remediation content for specific learning gaps.
        
        Your remediation should:
        1. Reframe the gap as an opportunity for expanded enactment within 
            their assemblage of interests, tools, and contexts
        2. Break down complex concepts into manageable steps as aligned with their
            attempted solution as is reasonable
        3. Provide clear explanations with various examples that match the correct
            solution path
        4. Include practice opportunities that strengthen performance within their
            assemblage of interests, tools, and contexts
        5. Connect new performances to their existing ways of engaging with the
            student's interests and context
        6. Build confidence by validating current performances and expanding their
            repertoire while addressing misconceptions and assemblage gaps
        
        Return your response as a JSON object with these fields:
        - explanation: Clear explanation of the concept/gap
        - step_by_step_guide: Array of specific steps to follow
        - examples: Array of worked examples
        - practice_problems: Array of practice problems
        - personalized_context: How this connects to student interests
        - key_insights: Most important takeaways"""

    def _create_remediation_prompt(
        self,
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        original_exercise: Dict[str, Any],
        evaluation: Dict[str, Any],
    ) -> str:
        """Create prompt for remediation generation."""
        interests = student_profile.get("interests", [])

        prompt = f"""Create targeted remediation content for this learning gap:
        
        Concept: {concept.get('name')}
        Specific Gap: {target_gap}
        
        Student Profile:
        - Interests: {', '.join(interests)}
        - Current Understanding Score: {evaluation.get('understanding_score', 0)}
        
        Original Exercise Context:
        {original_exercise.get('content', {}).get('scenario', '')}
        
        Student's Response Issues:
        - Missing Steps: {evaluation.get('competency_map', {}).get('missing_steps', [])}
        - Incorrect Steps: {evaluation.get('competency_map', {}).get('incorrect_steps', [])}
        
        Create remediation that:
        1. Specifically addresses "{target_gap}"
        2. Uses their interests: {', '.join(interests)}
        3. Builds on what they did correctly
        4. Provides scaffolded practice
        5. Rebuilds confidence
        
        Make it encouraging and accessible."""

        return prompt
