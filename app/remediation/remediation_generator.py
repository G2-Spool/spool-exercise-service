"""Generate targeted remediation for understanding gaps."""

import json
from typing import Dict, Any, List
from datetime import datetime
import uuid
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RemediationGenerator:
    """Generate personalized remediation content."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GENERATION_MODEL
    
    async def generate(
        self,
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        original_exercise: Dict[str, Any],
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate remediation for a specific understanding gap."""
        try:
            prompt = self._create_remediation_prompt(
                concept, target_gap, student_profile, original_exercise, evaluation
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            remediation_content = json.loads(response.choices[0].message.content)
            
            # Create remediation object
            remediation = {
                "remediation_id": str(uuid.uuid4()),
                "evaluation_id": evaluation.get("evaluation_id"),
                "exercise_id": original_exercise.get("exercise_id"),
                "student_id": student_profile.get("student_id"),
                "target_gap": target_gap,
                "content": remediation_content,
                "personalized_context": remediation_content.get("personalized_context"),
                "practice_problems": remediation_content.get("practice_problems", []),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Generated remediation",
                remediation_id=remediation["remediation_id"],
                target_gap=target_gap
            )
            
            return remediation
            
        except Exception as e:
            logger.error("Remediation generation failed", error=str(e))
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for remediation generation."""
        return """You are an expert educational tutor specializing in providing 
        targeted remediation for specific understanding gaps.
        
        Your remediation should:
        1. Focus on the FIRST identified gap only
        2. Provide a clear, step-by-step explanation
        3. Use analogies from the student's interests
        4. Include visual or concrete examples
        5. Break down complex ideas into simpler parts
        6. Provide 1-2 simple practice problems
        7. Build confidence while addressing the misconception
        
        Return your response as a JSON object with these fields:
        - explanation: Clear explanation addressing the gap
        - visual_aid: Description of a helpful visual/diagram
        - analogy: An analogy using student interests
        - step_by_step: Array of steps to understand this concept
        - practice_problems: Array of 1-2 simple problems
        - personalized_context: How this connects to their interests
        - key_insight: The main takeaway in one sentence"""
    
    def _create_remediation_prompt(
        self,
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        original_exercise: Dict[str, Any],
        evaluation: Dict[str, Any]
    ) -> str:
        """Create prompt for remediation generation."""
        interests = student_profile.get("interests", [])
        
        prompt = f"""Create targeted remediation for this specific gap:
        
        Concept: {concept.get('name')}
        Target Gap: {target_gap}
        
        Original Exercise Context:
        {original_exercise.get('content', {}).get('scenario')}
        
        Student's Interests: {', '.join(interests)}
        
        What the student missed or misunderstood:
        {target_gap}
        
        Other context from evaluation:
        - Understanding score: {evaluation.get('understanding_score', 0)}
        - Correct steps: {', '.join(evaluation.get('competency_map', {}).get('correct_steps', [])[:2])}
        
        Create remediation that:
        1. Addresses ONLY this specific gap
        2. Uses their interests to explain the concept
        3. Provides a clear, memorable explanation
        4. Includes a visual or concrete example
        5. Gives them a simple practice problem to verify understanding
        
        Remember: Focus on building understanding, not just correcting the error."""
        
        return prompt