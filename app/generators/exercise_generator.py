"""Exercise generation using LLMs."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.pinecone_service import PineconeExerciseService
from app.resources.personalities import personality_loader
from app.core.prompts import ChainOfThoughtPrompts

logger = structlog.get_logger()


class ExerciseGenerator:
    """Generate personalized exercises using LLMs with enhanced chain-of-thought prompting."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL
        self.pinecone_service = PineconeExerciseService()
        self.chain_of_thought = ChainOfThoughtPrompts()

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
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str = "basic",
        exercise_type: str = "initial",
        personality: Optional[str] = None,
        use_enhanced_prompts: bool = True,
    ) -> Dict[str, Any]:
        """Generate a personalized exercise with enhanced chain-of-thought prompting."""
        # Early return for mock exercises
        if self._should_use_mock():
            return self._create_mock_exercise(
                concept, student_profile, life_category, difficulty, exercise_type
            )

        try:
            # Get relevant context from Pinecone
            context_chunks = await self.pinecone_service.get_concept_context(
                concept.get("name", ""),
                student_profile.get("interests", []),
                difficulty,
            )

            # Get similar exercises for reference
            similar_exercises = await self.pinecone_service.find_similar_exercises(
                concept.get("concept_id", ""), student_profile
            )

            # Build unified prompt
            prompt = self._build_prompt(
                concept,
                student_profile,
                life_category,
                difficulty,
                exercise_type,
                context_chunks,
                similar_exercises,
                use_enhanced_prompts,
            )

            # Get system prompt with personality
            system_prompt = self._get_system_prompt(personality, use_enhanced_prompts)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
            exercise_content = json.loads(content)

            # Ensure concept_id is properly set
            concept_id = concept.get("concept_id")
            if not concept_id:
                # Fallback to generate a default concept_id
                concept_id = "default-concept"
                logger.warning("Missing concept_id in concept data, using fallback", concept=concept)

            # Create exercise object
            exercise = {
                "exercise_id": str(uuid.uuid4()),
                "concept_id": concept_id,
                "student_id": student_profile.get("student_id"),
                "type": exercise_type,
                "difficulty": difficulty,
                "content": exercise_content,
                "personalization": {
                    "interests_used": student_profile.get("interests", []),
                    "life_category": life_category,
                    "context": exercise_content.get("personalized_context"),
                    "enhanced_prompting": use_enhanced_prompts,
                },
                "expected_steps": exercise_content.get("expected_steps", []),
                "hints": exercise_content.get("hints", []),
                "created_at": datetime.utcnow().isoformat(),
                "llm_response_raw": content,  # Store raw response for analysis
            }

            logger.info(
                "Generated exercise with enhanced prompting",
                exercise_id=exercise["exercise_id"],
                concept_id=concept.get("concept_id"),
                difficulty=difficulty,
                enhanced_prompts=use_enhanced_prompts,
            )

            return exercise

        except Exception as e:
            logger.error("Exercise generation failed", error=str(e))
            # Fallback to mock exercise on any error
            return self._create_mock_exercise(
                concept, student_profile, life_category, difficulty, exercise_type
            )

    def _get_system_prompt(
        self, personality: Optional[str] = None, enhanced: bool = True
    ) -> str:
        """Unified system prompt generator."""
        base_prompt = """
        ## CORE IDENTITY
        You are an expert educational content creator specializing in authentic, performance-based assessment that connects academic concepts to students' real interests and contexts.

        ## MANDATORY REQUIREMENTS
        You MUST create exercises that:
        1. Present specific, concrete problems requiring numerical/measurable solutions
        2. Connect authentically to student interests through real-world scenarios
        3. Require step-by-step demonstration of understanding
        4. Include clear success criteria and expected solution paths
        5. Provide scaffolded complexity appropriate to difficulty level

        ## FORBIDDEN PRACTICES
        You MUST NEVER:
        1. Create abstract overviews or theoretical discussions instead of concrete problems
        2. Use generic scenarios that don't meaningfully connect to student interests
        3. Accept surface-level responses without deep demonstration of understanding
        4. Create problems that require memorization rather than application
        5. Generate exercises without clear, measurable outcomes

        ## STRUCTURED OUTPUT FORMAT
        Return JSON with:
        - scenario: Authentic real-world context using student interests
        - problem: Specific, concrete challenge with measurable outcome
        - expected_steps: 4-6 logical solution steps
        - success_criteria: Clear performance indicators
        - cognitive_scaffolds: Chunking strategies and complexity management
        - metacognitive_prompts: Questions encouraging self-reflection

        ## THINKING PROCESS
        Before generating content:
        1. Identify authentic connections between concept and student interests
        2. Design specific problem requiring active application
        3. Map cognitive load and chunk information appropriately
        4. Ensure multiple valid solution pathways exist
        5. Create opportunities for student agency and choice within structure"""

        enhanced_block = (
            """
        
        ## ENHANCED CHAIN-OF-THOUGHT PROMPTING
        When creating exercises, follow this enhanced process:
        
        ### Step 1: Analyze and Plan
        - Break down the concept into teachable components
        - Identify student interests that authentically connect
        - Plan the problem structure and expected learning path
        
        ### Step 2: Design with Scaffolding
        - Create clear intermediate questions that build understanding
        - Design self-check opportunities throughout the problem
        - Provide worked example format students should follow
        
        ### Step 3: Include Reflection Components
        - Add metacognitive prompts for self-assessment
        - Include verification steps students should perform
        - Create opportunities for alternative approach consideration
        
        ### Step 4: Verify and Refine
        - Ensure the problem requires deep reasoning, not just recall
        - Check that all steps logically build toward mastery
        - Confirm authentic connection to student interests"""
            if enhanced
            else ""
        )

        prompt = base_prompt + enhanced_block
        return personality_loader.apply_personality_to_prompt(prompt, personality)

    def _build_prompt(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str,
        exercise_type: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        similar_exercises: Optional[List[Dict[str, Any]]] = None,
        enhanced: bool = False,
    ) -> str:
        """Single prompt builder with optional enhanced/context features."""
        interests = student_profile.get("interests", [])

        # Base prompt construction
        prompt = f"""Create a {difficulty} {exercise_type} exercise for this concept:
        
        Concept: {concept.get('name')}
        Content: {concept.get('content', '')}
        Type: {concept.get('type', 'explanation')}
        
        Student Profile:
        - Interests: {', '.join(interests)}
        - Grade Level: {student_profile.get('grade_level', 'high school')}
        - Life Category Focus: {life_category}
        """

        # Add context from vector search if available
        if context_chunks:
            prompt += "\n\nRelevant Context from Knowledge Base:\n"
            for i, chunk in enumerate(context_chunks[:2]):  # Use top 2 chunks
                content = chunk.get("content", "")
                if isinstance(content, str):
                    prompt += f"Context {i+1}: {content[:300]}...\n"
                else:
                    prompt += f"Context {i+1}: {str(content)[:300]}...\n"

        # Add similar exercise patterns if available
        if similar_exercises:
            prompt += "\n\nSimilar Exercise Patterns:\n"
            for i, exercise in enumerate(similar_exercises[:1]):  # Use 1 example
                content = exercise.get("content", "")
                if isinstance(content, str):
                    prompt += f"Example {i+1}: {content[:200]}...\n"
                else:
                    prompt += f"Example {i+1}: {str(content)[:200]}...\n"

        # Add enhanced instructions if requested
        enhanced_instructions = ""
        if enhanced:
            enhanced_instructions = """
        
        ENHANCED REQUIREMENTS:
        - Use chain-of-thought reasoning in your design process
        - Include self-check opportunities throughout the problem
        - Provide worked example format students should follow
        - Add metacognitive prompts for self-assessment"""

        prompt += f"""
        
        Requirements:
        1. Create a scenario that uses one or more student interests
        2. Frame it in the context of their {life_category} goals
        3. The problem should require explaining their complete thought process
        4. Difficulty should be {difficulty}
        5. Include 4-6 expected solution steps
        6. Provide 2-3 progressive hints
        {"7. Use the provided context to ensure accuracy and depth" if context_chunks else ""}
        
        {"For an ADVANCED exercise, add additional complexity like multiple concepts, edge cases, or optimization requirements." if exercise_type == "advanced" else ""}
        {enhanced_instructions}
        
        The exercise should test deep understanding, not just memorization."""

        return prompt

    def _create_mock_exercise(
        self,
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        life_category: str,
        difficulty: str,
        exercise_type: str,
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
                "Verify the result makes sense",
            ],
            "hints": [
                "Start by identifying what you know and what you need to find",
                "Consider how this relates to your interest in " + interests[0],
                "Think about the core principles of " + concept_name,
            ],
            "personalized_context": f"This problem connects {concept_name} to your interest in {interests[0]} for {life_category} applications.",
            "success_criteria": "Student explains all key steps with clear reasoning",
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
                "context": mock_content["personalized_context"],
            },
            "expected_steps": mock_content["expected_steps"],
            "hints": mock_content["hints"],
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Generated mock exercise for testing",
            exercise_id=exercise["exercise_id"],
            concept_id=concept.get("concept_id"),
            difficulty=difficulty,
        )

        return exercise
