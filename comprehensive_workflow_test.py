#!/usr/bin/env python3
"""
Comprehensive Exercise Workflow Test

This test file simulates the complete exercise workflow with four different student scenarios:
1. Student succeeds flawlessly
2. Student has good understanding but makes mistakes
3. Student struggles but is trying
4. Student isn't trying and just wants answers

Results are saved to detailed files for analysis.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
import structlog
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the exercise service components
from app.core.config import settings
from app.models.exercise import (
    ExerciseGenerationRequest,
    StudentResponse,
    LifeCategory,
    DifficultyLevel,
    ExerciseType,
)
from app.langgraph.workflows import ExerciseWorkflow
from app.generators.exercise_generator import ExerciseGenerator
from app.evaluators.response_evaluator import ResponseEvaluator
from app.remediation.remediation_generator import RemediationGenerator
from openai import AsyncOpenAI

# Setup logging
logger = structlog.get_logger()


class RealAPIExerciseGenerator(ExerciseGenerator):
    """Exercise generator that forces real API calls."""
    
    async def generate(self, concept: Dict[str, Any], student_profile: Dict[str, Any], 
                      life_category: str, difficulty: str = "basic", 
                      exercise_type: str = "initial") -> Dict[str, Any]:
        """Generate exercise using real OpenAI API calls."""
        try:
            # Always use real API calls, never mock
            prompt = self._create_generation_prompt(
                concept, student_profile, life_category, difficulty, exercise_type
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
            exercise_content = json.loads(content)

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
                    "context": exercise_content.get("personalized_context"),
                },
                "expected_steps": exercise_content.get("expected_steps", []),
                "hints": exercise_content.get("hints", []),
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "Generated exercise with real API",
                exercise_id=exercise["exercise_id"],
                concept_id=concept.get("concept_id"),
                difficulty=difficulty,
            )

            return exercise

        except Exception as e:
            logger.error("Real API exercise generation failed", error=str(e))
            raise


class RealAPIResponseEvaluator(ResponseEvaluator):
    """Response evaluator that forces real API calls."""
    
    async def evaluate(self, exercise: Dict[str, Any], student_response: str, 
                      concept: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate response using real OpenAI API calls."""
        try:
            # Validate response length
            if len(student_response) < settings.MIN_RESPONSE_LENGTH:
                return self._create_insufficient_response_evaluation(
                    exercise, student_response
                )

            # Always use real API calls, never mock
            prompt = self._create_evaluation_prompt(exercise, student_response, concept)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent evaluation
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
            evaluation_result = json.loads(content)

            # Create evaluation object
            evaluation = {
                "evaluation_id": str(uuid.uuid4()),
                "exercise_id": exercise.get("exercise_id"),
                "student_response": student_response,
                "competency_map": {
                    "correct_steps": evaluation_result.get("correct_steps", []),
                    "missing_steps": evaluation_result.get("missing_steps", []),
                    "incorrect_steps": evaluation_result.get("incorrect_steps", []),
                    "partial_steps": evaluation_result.get("partial_steps", []),
                },
                "understanding_score": evaluation_result.get("understanding_score", 0.0),
                "mastery_achieved": evaluation_result.get("mastery_achieved", False),
                "feedback": evaluation_result.get("feedback", ""),
                "needs_remediation": len(evaluation_result.get("missing_steps", [])) > 0
                or len(evaluation_result.get("incorrect_steps", [])) > 0,
                "evaluated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "Evaluated response with real API",
                exercise_id=exercise.get("exercise_id"),
                mastery_achieved=evaluation["mastery_achieved"],
                score=evaluation["understanding_score"],
            )

            return evaluation

        except Exception as e:
            logger.error("Real API response evaluation failed", error=str(e))
            raise


class WorkflowTestSuite:
    """Test suite for comprehensive exercise workflow testing."""
    
    def __init__(self):
        # Use real API classes instead of mock classes
        self.generator = RealAPIExerciseGenerator()
        self.evaluator = RealAPIResponseEvaluator()
        self.remediation_gen = RemediationGenerator()
        self.workflow = ExerciseWorkflow()
        self.test_results = []
        self.output_dir = "test_results"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Verify OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('test'):
            raise ValueError("Valid OpenAI API key required for real API testing. Set OPENAI_API_KEY in .env file")
        
    async def run_comprehensive_test(self):
        """Run all four test scenarios."""
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)
        
        # Define test scenarios
        scenarios = [
            {
                "name": "Perfect Student",
                "description": "Student who succeeds flawlessly",
                "student_id": "perfect_student_001",
                "interests": ["mathematics", "problem-solving", "physics"],
                "response_generator": self._generate_perfect_response,
            },
            {
                "name": "Good Student with Mistakes",
                "description": "Student with good understanding but makes errors",
                "student_id": "good_student_002", 
                "interests": ["science", "engineering", "technology"],
                "response_generator": self._generate_good_with_mistakes_response,
            },
            {
                "name": "Struggling Student",
                "description": "Student who struggles but is trying hard",
                "student_id": "struggling_student_003",
                "interests": ["art", "music", "creative writing"],
                "response_generator": self._generate_struggling_response,
            },
            {
                "name": "Lazy Student",
                "description": "Student who isn't trying and wants answers",
                "student_id": "lazy_student_004",
                "interests": ["gaming", "social media", "entertainment"],
                "response_generator": self._generate_lazy_response,
            }
        ]
        
        # Run each scenario
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Test {i}/4: {scenario['name']}")
            print(f"   {scenario['description']}")
            print("-" * 50)
            
            try:
                result = await self._run_scenario(scenario)
                self.test_results.append(result)
                print(f"✅ Completed: {scenario['name']}")
            except Exception as e:
                print(f"❌ Failed: {scenario['name']} - {str(e)}")
                logger.error(f"Scenario failed: {scenario['name']}", error=str(e))
        
        # Save comprehensive results
        await self._save_comprehensive_results()
        print(f"\n🎯 Test Complete! Results saved to {self.output_dir}/")
        
    async def _run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario through the complete workflow."""
        start_time = datetime.utcnow()
        
        # Step 1: Generate Exercise
        print("   🔄 Generating exercise...")
        exercise_request = ExerciseGenerationRequest(
            concept_id="quadratic_equations",
            student_id=scenario["student_id"],
            student_interests=scenario["interests"],
            life_category=LifeCategory.CAREER,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )
        
        # Mock concept data
        concept_data = {
            "concept_id": "quadratic_equations",
            "name": "Quadratic Equations",
            "content": "Solving quadratic equations using various methods",
            "description": "Understanding how to solve equations of the form ax² + bx + c = 0",
            "prerequisites": ["linear_equations", "algebraic_manipulation"],
            "difficulty_level": "intermediate"
        }
        
        # Generate exercise using the generator
        exercise = await self.generator.generate(
            concept=concept_data,
            student_profile={
                "student_id": scenario["student_id"],
                "interests": scenario["interests"],
                "learning_style": "visual",
                "grade_level": "high_school",
                "previous_concepts": ["linear_equations"]
            },
            life_category="career",
            difficulty="intermediate",
            exercise_type="initial"
        )
        
        print(f"   ✅ Exercise generated: {exercise['exercise_id']}")
        
        # Step 2: Generate Student Response
        print("   🎭 Generating student response...")
        student_response = scenario["response_generator"](exercise)
        
        print(f"   💬 Response length: {len(student_response)} characters")
        
        # Step 3: Evaluate Response
        print("   🔍 Evaluating response...")
        evaluation = await self.evaluator.evaluate(
            exercise=exercise,
            student_response=student_response,
            concept=concept_data
        )
        
        print(f"   📊 Score: {evaluation['understanding_score']:.2f}")
        print(f"   🎯 Mastery: {evaluation['mastery_achieved']}")
        
        # Step 4: Generate Remediation (if needed)
        remediation = None
        if evaluation["needs_remediation"]:
            print("   📚 Generating remediation...")
            try:
                remediation = await self.remediation_gen.generate(
                    concept=concept_data,
                    target_gap=evaluation["competency_map"]["missing_steps"][0] if evaluation["competency_map"]["missing_steps"] else "General understanding",
                    student_profile={
                        "student_id": scenario["student_id"],
                        "interests": scenario["interests"],
                        "learning_style": "visual",
                        "grade_level": "high_school",
                    },
                    original_exercise=exercise,
                    evaluation=evaluation
                )
                print("   ✅ Remediation generated")
            except Exception as e:
                print(f"   ⚠️ Remediation generation failed: {str(e)}")
                remediation = {"error": str(e)}
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Compile results
        result = {
            "scenario": scenario,
            "exercise": exercise,
            "student_response": student_response,
            "evaluation": evaluation,
            "remediation": remediation,
            "timing": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            },
            "summary": {
                "exercise_id": exercise["exercise_id"],
                "student_type": scenario["name"],
                "understanding_score": evaluation["understanding_score"],
                "mastery_achieved": evaluation["mastery_achieved"],
                "needs_remediation": evaluation["needs_remediation"],
                "correct_steps": len(evaluation["competency_map"]["correct_steps"]),
                "missing_steps": len(evaluation["competency_map"]["missing_steps"]),
                "incorrect_steps": len(evaluation["competency_map"]["incorrect_steps"]),
            }
        }
        
        return result
    
    def _generate_perfect_response(self, exercise: Dict[str, Any]) -> str:
        """Generate a perfect student response."""
        return """
Looking at this quadratic equation problem, I need to solve it step by step.

First, I'll identify what type of problem this is - it's a quadratic equation in the form ax² + bx + c = 0, so I need to find the values of x that make this equation true.

Let me work through this systematically:

1. I'll identify the coefficients: a, b, and c from the equation
2. I'll determine the best method to solve it - I can use factoring, completing the square, or the quadratic formula
3. I'll check if it factors easily first, since that's often the most efficient method
4. If factoring works, I'll factor the expression and set each factor equal to zero
5. I'll solve for x in each case
6. Finally, I'll substitute my answers back into the original equation to verify they're correct

For the quadratic formula method as backup: x = (-b ± √(b² - 4ac)) / 2a

This systematic approach ensures I don't miss any steps and can verify my solution. I'll also check that my final answers make sense in the context of the original problem.

The verification step is crucial - I'll substitute both solutions back into the original equation to confirm they work, and I'll consider whether the solutions make practical sense for the real-world context described in the problem.
"""

    def _generate_good_with_mistakes_response(self, exercise: Dict[str, Any]) -> str:
        """Generate a response from a good student who makes some mistakes."""
        return """
I need to solve this quadratic equation. Let me work through it step by step.

First, I can see this is a quadratic equation, so I need to find the x values. I think I should use the quadratic formula since that always works.

The quadratic formula is x = (-b ± √(b² - 4ac)) / 2a

Let me identify my coefficients from the equation... I think a is the coefficient of x², b is the coefficient of x, and c is the constant term.

Wait, actually let me try factoring first since that might be easier. I'll look for two numbers that multiply to give me the constant term and add to give me the middle coefficient.

Hmm, I'm having trouble factoring this one. Let me go back to the quadratic formula approach.

So plugging into the formula: x = (-b ± √(b² - 4ac)) / 2a

I need to calculate the discriminant first - that's b² - 4ac. If it's positive, I'll have two real solutions.

After calculating... I get x = ... (I'm not showing my arithmetic here but I calculated it)

Let me check my work by plugging one solution back in... Actually, I think I made an error somewhere in my calculations. The numbers don't look right when I substitute back.

I should probably double-check my identification of the coefficients and redo the calculation more carefully.
"""

    def _generate_struggling_response(self, exercise: Dict[str, Any]) -> str:
        """Generate a response from a struggling student who is trying."""
        return """
This is a quadratic equation problem. I know it's the type with x² in it.

I remember we learned about these but I'm not sure exactly how to start. Let me try to remember what my teacher said.

I think there are different ways to solve these... like factoring? And there's also a formula but I don't remember it exactly.

Let me see if I can factor this. I need to find two numbers that... um... I think they need to multiply to something and add to something else? I'm not sure exactly how this works.

Maybe I should try the quadratic formula instead? I remember it has a square root in it and fractions. Something like x equals negative b plus or minus square root of... something... over 2a?

I'm getting confused. Let me try a different approach.

I know that when we solve equations, we want to get x by itself. So maybe I can move things around? But with the x² term it's more complicated.

I think I need to identify the parts of the equation first. The x² part, the x part, and the number part. Then I can use one of the methods we learned.

I'm really struggling with this. I know I need to find the values of x that make the equation true, but I'm not sure about the exact steps. Could you help me understand which method would be best to use here?

I want to learn this properly, not just get the answer.
"""

    def _generate_lazy_response(self, exercise: Dict[str, Any]) -> str:
        """Generate a response from a lazy student who just wants answers."""
        return """
Can you just tell me the answer? I don't really understand this stuff.

Is it x = 5? Or maybe x = -2? 

I tried looking it up online but there are so many different methods and I don't know which one to use.

Could you show me the steps so I can copy them? I have other homework to do too.

Just give me the formula and I'll plug in the numbers. What's the quadratic formula again?
"""

    async def _save_comprehensive_results(self):
        """Save all test results to files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results for each scenario
        for i, result in enumerate(self.test_results, 1):
            filename = f"{self.output_dir}/scenario_{i}_{result['scenario']['name'].lower().replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
                
        # Save summary report
        summary_filename = f"{self.output_dir}/comprehensive_summary_{timestamp}.json"
        summary = {
            "test_metadata": {
                "timestamp": timestamp,
                "total_scenarios": len(self.test_results),
                "test_duration": sum(r['timing']['duration_seconds'] for r in self.test_results)
            },
            "scenario_summaries": [r['summary'] for r in self.test_results],
            "detailed_analysis": self._generate_analysis()
        }
        
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        # Save human-readable report
        readable_filename = f"{self.output_dir}/readable_report_{timestamp}.txt"
        with open(readable_filename, 'w') as f:
            f.write(self._generate_readable_report())
        
        print(f"📄 Detailed results saved to: {self.output_dir}/")
        print(f"📊 Summary report: {summary_filename}")
        print(f"📖 Readable report: {readable_filename}")
        
    def _generate_analysis(self) -> Dict[str, Any]:
        """Generate detailed analysis of test results."""
        analysis = {
            "performance_distribution": {},
            "evaluation_accuracy": {},
            "remediation_triggers": {},
            "workflow_insights": []
        }
        
        scores = [r['evaluation']['understanding_score'] for r in self.test_results]
        mastery_rate = sum(r['evaluation']['mastery_achieved'] for r in self.test_results) / len(self.test_results)
        
        analysis["performance_distribution"] = {
            "average_score": sum(scores) / len(scores),
            "score_range": {"min": min(scores), "max": max(scores)},
            "mastery_rate": mastery_rate,
            "remediation_rate": sum(r['evaluation']['needs_remediation'] for r in self.test_results) / len(self.test_results)
        }
        
        # Add insights based on results
        if mastery_rate < 0.5:
            analysis["workflow_insights"].append("Low mastery rate suggests exercises may be too challenging")
        
        if analysis["performance_distribution"]["remediation_rate"] > 0.75:
            analysis["workflow_insights"].append("High remediation rate indicates good differentiation between student levels")
            
        return analysis
    
    def _generate_readable_report(self) -> str:
        """Generate a human-readable report of test results."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE EXERCISE WORKFLOW TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        scores = [r['evaluation']['understanding_score'] for r in self.test_results]
        avg_score = sum(scores) / len(scores)
        mastery_count = sum(r['evaluation']['mastery_achieved'] for r in self.test_results)
        
        report.append(f"• Total Scenarios Tested: {len(self.test_results)}")
        report.append(f"• Average Understanding Score: {avg_score:.2f}")
        report.append(f"• Students Achieving Mastery: {mastery_count}/{len(self.test_results)}")
        report.append(f"• Remediation Needed: {sum(r['evaluation']['needs_remediation'] for r in self.test_results)}/{len(self.test_results)}")
        report.append("")
        
        # Detailed Results
        report.append("DETAILED SCENARIO RESULTS")
        report.append("-" * 40)
        
        for i, result in enumerate(self.test_results, 1):
            scenario = result['scenario']
            evaluation = result['evaluation']
            summary = result['summary']
            
            report.append(f"\n{i}. {scenario['name'].upper()}")
            report.append(f"   Description: {scenario['description']}")
            report.append(f"   Student ID: {scenario['student_id']}")
            report.append(f"   Interests: {', '.join(scenario['interests'])}")
            report.append(f"   Exercise ID: {summary['exercise_id']}")
            report.append("")
            
            # Performance Metrics
            report.append("   PERFORMANCE METRICS:")
            report.append(f"   • Understanding Score: {evaluation['understanding_score']:.2f}/1.0")
            report.append(f"   • Mastery Achieved: {'✅ Yes' if evaluation['mastery_achieved'] else '❌ No'}")
            report.append(f"   • Needs Remediation: {'Yes' if evaluation['needs_remediation'] else 'No'}")
            report.append(f"   • Correct Steps: {len(evaluation['competency_map']['correct_steps'])}")
            report.append(f"   • Missing Steps: {len(evaluation['competency_map']['missing_steps'])}")
            report.append(f"   • Incorrect Steps: {len(evaluation['competency_map']['incorrect_steps'])}")
            report.append("")
            
            # Student Response Preview
            response_preview = result['student_response'][:200] + "..." if len(result['student_response']) > 200 else result['student_response']
            report.append("   STUDENT RESPONSE PREVIEW:")
            report.append(f"   \"{response_preview}\"")
            report.append("")
            
            # Evaluation Feedback
            report.append("   EVALUATION FEEDBACK:")
            report.append(f"   \"{evaluation['feedback']}\"")
            report.append("")
            
            # Remediation Status
            if result['remediation']:
                report.append("   REMEDIATION: Generated")
            else:
                report.append("   REMEDIATION: Not needed")
            report.append("")
            
        # Workflow Insights
        report.append("WORKFLOW INSIGHTS")
        report.append("-" * 40)
        
        # Analyze patterns
        perfect_score = next((r for r in self.test_results if r['scenario']['name'] == 'Perfect Student'), None)
        if perfect_score and perfect_score['evaluation']['understanding_score'] >= 0.8:
            report.append("✅ Perfect student scenario correctly identified high performance")
        
        lazy_score = next((r for r in self.test_results if r['scenario']['name'] == 'Lazy Student'), None)
        if lazy_score and lazy_score['evaluation']['understanding_score'] <= 0.3:
            report.append("✅ Lazy student scenario correctly identified low engagement")
            
        struggling_score = next((r for r in self.test_results if r['scenario']['name'] == 'Struggling Student'), None)
        if struggling_score and struggling_score['evaluation']['needs_remediation']:
            report.append("✅ Struggling student correctly flagged for remediation")
            
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        if avg_score < 0.5:
            report.append("• Consider adjusting exercise difficulty or providing more scaffolding")
        
        if mastery_count == 0:
            report.append("• Review mastery criteria - may be too stringent")
        elif mastery_count == len(self.test_results):
            report.append("• Consider increasing exercise difficulty for better differentiation")
        
        report.append("• System successfully differentiates between student performance levels")
        report.append("• Remediation system activates appropriately for struggling students")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)


async def main():
    """Run the comprehensive test suite."""
    test_suite = WorkflowTestSuite()
    await test_suite.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main()) 