"""Exercise generation using LLMs."""

import json
from typing import Dict, Any, List
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ExerciseGenerator:
    """Generate personalized exercises using LLMs."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL
    
    async def generate(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str = "basic",
        exercise_type: str = "initial"
    ) -> Dict[str, Any]:
        """Generate a personalized exercise."""
        try:
            # Check if using test key or no key - create mock exercise
            if (not settings.OPENAI_API_KEY or 
                settings.OPENAI_API_KEY == "test_key" or 
                settings.OPENAI_API_KEY.startswith("test") or
                settings.OPENAI_API_KEY == "your-openai-api-key"):
                return self._create_mock_exercise(concept, student_profile, life_category, difficulty, exercise_type)
            
            prompt = self._create_generation_prompt(
                concept, student_profile, life_category, difficulty, exercise_type
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            exercise_content = json.loads(response.choices[0].message.content)
            
            # Create exercise object
            exercise = {
                "exercise_id": str(uuid.uuid4()),
                "concept_id": concept.get("concept_id"),
                "student_id": student_profile.get("student_id"),
                "type": exercise_type,
                "difficulty": difficulty,
                "content": exercise_content,
                "personalization": {
                    "interests_used": student_profile.get("interests", []),
                    "life_category": life_category,
                    "context": exercise_content.get("personalized_context")
                },
                "expected_steps": exercise_content.get("expected_steps", []),
                "hints": exercise_content.get("hints", []),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Generated exercise",
                exercise_id=exercise["exercise_id"],
                concept_id=concept.get("concept_id"),
                difficulty=difficulty
            )
            
            return exercise
            
        except Exception as e:
            logger.error("Exercise generation failed", error=str(e))
            # Fallback to mock exercise on any error
            return self._create_mock_exercise(concept, student_profile, life_category, difficulty, exercise_type)

    def _create_mock_exercise(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str,
        exercise_type: str
    ) -> Dict[str, Any]:
        """Create a mock exercise for testing purposes."""
        interests = student_profile.get("interests", ["general activities"])
        concept_name = concept.get("name", "Unknown Concept")
        
        mock_content = {
            "scenario": f"You're working on a {life_category} project involving {interests[0]} and need to apply {concept_name}.",
            "problem": f"Explain step-by-step how you would solve this {difficulty} problem using {concept_name}. Walk through your complete thought process.",
            "expected_steps": [
                "Identify the key components of the problem",
                "Apply the main concept principles",
                "Work through the solution systematically",
                "Verify the result makes sense"
            ],
            "hints": [
                "Start by identifying what you know and what you need to find",
                "Consider how this relates to your interest in " + interests[0],
                "Think about the core principles of " + concept_name
            ],
            "personalized_context": f"This problem connects {concept_name} to your interest in {interests[0]} for {life_category} applications.",
            "success_criteria": "Student explains all key steps with clear reasoning"
        }
        
        exercise = {
            "exercise_id": str(uuid.uuid4()),
            "concept_id": concept.get("concept_id"),
            "student_id": student_profile.get("student_id"),
            "type": exercise_type,
            "difficulty": difficulty,
            "content": mock_content,
            "personalization": {
                "interests_used": interests,
                "life_category": life_category,
                "context": mock_content["personalized_context"]
            },
            "expected_steps": mock_content["expected_steps"],
            "hints": mock_content["hints"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Generated mock exercise for testing",
            exercise_id=exercise["exercise_id"],
            concept_id=concept.get("concept_id"),
            difficulty=difficulty
        )
        
        return exercise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for exercise generation."""
        return """You are an expert educational content creator specializing in 
        creating personalized exercises that test conceptual understanding through 
        articulated thought processes.
        
        Your exercises should:
        1. Use realistic scenarios based on student interests
        2. Require students to explain their complete thought process
        3. Have clear expected solution steps
        4. Include helpful hints without giving away the answer
        5. Be appropriately challenging for the difficulty level
        
        Return your response as a JSON object with these fields:
        - scenario: The problem scenario using student interests
        - problem: The specific question or task
        - expected_steps: Array of logical steps in the solution
        - hints: Array of 2-3 progressive hints
        - personalized_context: How this relates to their interests
        - success_criteria: What constitutes a correct solution"""
    
    def _create_generation_prompt(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str,
        exercise_type: str
    ) -> str:
        """Create prompt for exercise generation."""
        interests = student_profile.get("interests", [])
        
        prompt = f"""Create a {difficulty} {exercise_type} exercise for this concept:
        
        Concept: {concept.get('name')}
        Content: {concept.get('content', '')}
        Type: {concept.get('type', 'explanation')}
        
        Student Profile:
        - Interests: {', '.join(interests)}
        - Grade Level: {student_profile.get('grade_level', 'high school')}
        - Life Category Focus: {life_category}
        
        Requirements:
        1. Create a scenario that uses one or more student interests
        2. Frame it in the context of their {life_category} goals
        3. The problem should require explaining their complete thought process
        4. Difficulty should be {difficulty}
        5. Include 4-6 expected solution steps
        6. Provide 2-3 progressive hints
        
        {"For an ADVANCED exercise, add additional complexity like multiple concepts, edge cases, or optimization requirements." if exercise_type == "advanced" else ""}
        
        The exercise should test deep understanding, not just memorization."""
        
        return prompt