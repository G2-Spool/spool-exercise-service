"""Example usage of the personality system."""

from .personality_loader import personality_loader


def demonstrate_personality_system() -> None:
    """Demonstrate how the personality system works."""

    print("=== Personality System Demo ===\n")

    # List all available personalities
    personalities = personality_loader.list_available_personalities()
    print(f"Available personalities: {personalities}\n")

    # Example base system prompt (simplified)
    base_prompt = """
    ## CORE IDENTITY
    You are an expert educational content creator.
    
    ## REQUIREMENTS
    You MUST create exercises that connect to student interests.
    """

    # Demonstrate different personalities
    for personality in [
        "default",
        "enthusiastic-coach",
        "wise-mentor",
        "analytical-detective",
    ]:
        print(f"--- {personality.upper()} PERSONALITY ---")
        enhanced_prompt = personality_loader.apply_personality_to_prompt(
            base_prompt, personality
        )
        # Show just the first 200 characters to keep output manageable
        print(enhanced_prompt[:200] + "...\n")


if __name__ == "__main__":
    demonstrate_personality_system()

# Example usage in the generator classes:
"""
# In ExerciseGenerator.generate():
exercise_generator = ExerciseGenerator()
exercise = await exercise_generator.generate(
    concept=concept,
    student_profile=student_profile,
    life_category="career",
    difficulty="basic",
    exercise_type="initial",
    personality="enthusiastic-coach"  # <-- Add personality parameter
)

# In ResponseEvaluator.evaluate():
evaluator = ResponseEvaluator()
evaluation = await evaluator.evaluate(
    exercise=exercise,
    student_response=response,
    concept=concept,
    personality="analytical-detective"  # <-- Add personality parameter
)

# In RemediationGenerator.generate():
remediation_generator = RemediationGenerator()
remediation = await remediation_generator.generate(
    concept=concept,
    target_gap=gap,
    student_profile=student_profile,
    original_exercise=exercise,
    evaluation=evaluation,
    personality="empathetic-supporter"  # <-- Add personality parameter
)
"""
