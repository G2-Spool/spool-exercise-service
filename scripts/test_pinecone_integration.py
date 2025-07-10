"""Test Pinecone integration for exercise service."""

import asyncio
import os
from app.services.pinecone_service import PineconeExerciseService
from app.generators.exercise_generator import ExerciseGenerator
from app.evaluators.response_evaluator import ResponseEvaluator
from app.remediation.remediation_generator import RemediationGenerator
from app.core.config import settings


async def test_pinecone_integration():
    """Test basic Pinecone integration with all components."""
    print("Testing Pinecone Integration for Exercise Service")
    print("=" * 50)
    
    # Test data
    concept = {
        "concept_id": "test-concept-1",
        "name": "quadratic equations",
        "content": "A quadratic equation is a polynomial equation of degree 2",
        "type": "explanation"
    }
    
    student_profile = {
        "student_id": "test-student-1",
        "interests": ["sports", "music"],
        "grade_level": "high school"
    }
    
    # Test 1: PineconeExerciseService
    print("\n1. Testing PineconeExerciseService...")
    service = PineconeExerciseService()
    
    try:
        context = await service.get_concept_context(
            concept["name"],
            student_profile["interests"],
            "basic"
        )
        print(f"✓ Found {len(context)} context chunks")
        
        similar_exercises = await service.find_similar_exercises(
            concept["concept_id"],
            student_profile
        )
        print(f"✓ Found {len(similar_exercises)} similar exercises")
        
        remediation_examples = await service.get_remediation_examples(
            "problem solving approach",
            concept["name"],
            student_profile["interests"]
        )
        print(f"✓ Found {len(remediation_examples)} remediation examples")
        
    except Exception as e:
        print(f"✗ PineconeExerciseService error: {e}")
    
    # Test 2: ExerciseGenerator with Pinecone
    print("\n2. Testing ExerciseGenerator with Pinecone...")
    generator = ExerciseGenerator()
    
    try:
        exercise = await generator.generate(
            concept,
            student_profile,
            "academic",
            "basic",
            "initial"
        )
        print(f"✓ Generated exercise: {exercise['exercise_id']}")
        print(f"  - Type: {exercise['type']}")
        print(f"  - Difficulty: {exercise['difficulty']}")
        print(f"  - Personalized: {len(exercise['personalization']['interests_used'])} interests used")
        
    except Exception as e:
        print(f"✗ ExerciseGenerator error: {e}")
    
    # Test 3: ResponseEvaluator with Pinecone
    print("\n3. Testing ResponseEvaluator with Pinecone...")
    evaluator = ResponseEvaluator()
    
    try:
        # Mock exercise for evaluation
        mock_exercise = {
            "exercise_id": "test-exercise-1",
            "content": {
                "scenario": "Test scenario",
                "problem": "Test problem"
            },
            "expected_steps": [
                "Step 1: Identify the problem",
                "Step 2: Apply the method",
                "Step 3: Solve systematically",
                "Step 4: Verify the answer"
            ]
        }
        
        test_response = "I need to identify what type of problem this is and then apply the quadratic formula step by step."
        
        evaluation = await evaluator.evaluate(
            mock_exercise,
            test_response,
            concept
        )
        print(f"✓ Evaluated response: {evaluation['evaluation_id']}")
        print(f"  - Understanding score: {evaluation['understanding_score']}")
        print(f"  - Mastery achieved: {evaluation['mastery_achieved']}")
        print(f"  - Needs remediation: {evaluation['needs_remediation']}")
        
    except Exception as e:
        print(f"✗ ResponseEvaluator error: {e}")
    
    # Test 4: RemediationGenerator with Pinecone
    print("\n4. Testing RemediationGenerator with Pinecone...")
    remediation_gen = RemediationGenerator()
    
    try:
        # Mock evaluation for remediation
        mock_evaluation = {
            "evaluation_id": "test-eval-1",
            "understanding_score": 0.6,
            "competency_map": {
                "missing_steps": ["Did not verify the answer"],
                "incorrect_steps": []
            }
        }
        
        remediation = await remediation_gen.generate(
            concept,
            "verification process",
            student_profile,
            mock_exercise,
            mock_evaluation
        )
        print(f"✓ Generated remediation: {remediation['remediation_id']}")
        print(f"  - Target gap: {remediation['target_gap']}")
        print(f"  - Practice problems: {len(remediation['practice_problems'])}")
        
    except Exception as e:
        print(f"✗ RemediationGenerator error: {e}")
    
    print("\n" + "=" * 50)
    print("Integration test completed!")
    print(f"Vector context enabled: {settings.ENABLE_VECTOR_CONTEXT}")
    print(f"Content service URL: {settings.CONTENT_SERVICE_SEARCH_URL}")


if __name__ == "__main__":
    asyncio.run(test_pinecone_integration()) 