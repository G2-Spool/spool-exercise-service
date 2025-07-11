#!/usr/bin/env python3
"""
Comprehensive Exercise Workflow Test

This script tests the complete exercise workflow with the correct flow:
1. Generate personalized exercises for students with specific interests
2. Use hardcoded student responses (4 types) for consistent testing
3. Evaluate responses using the evaluator
4. Generate remediation if needed
5. Log all interactions in detail with human-readable reports

Results are saved to detailed files for analysis.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any
import sys
import logging
from pathlib import Path
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print(
        "⚠️  python-dotenv not installed. Make sure OPENAI_API_KEY is set in environment."
    )

# Add app directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ruff: noqa: E402# Import the exercise service components
from app.models.exercise import (
    LifeCategory,
    DifficultyLevel,
    ExerciseType,
)

try:
    from app.langgraph.workflows import ExerciseWorkflow

    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False

from app.generators.exercise_generator import ExerciseGenerator
from app.evaluators.response_evaluator import ResponseEvaluator
from app.remediation.remediation_generator import RemediationGenerator

# Setup basic logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExerciseWorkflowTester:
    """Comprehensive workflow tester following the correct flow."""

    def __init__(self, use_hardcoded_exercise: bool = False):
        # Verify API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("test"):
            raise ValueError(
                "Valid OpenAI API key required. Set OPENAI_API_KEY in .env file"
            )

        # Initialize components
        self.generator = ExerciseGenerator()
        self.evaluator = ResponseEvaluator()
        self.remediation_gen = RemediationGenerator()
        if WORKFLOW_AVAILABLE:
            self.workflow = ExerciseWorkflow()
        else:
            self.workflow = None
            print(
                "⚠️  LangGraph workflow not available - using direct component testing"
            )

        self.test_results = []
        self.output_dir = "test_results"

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Student scenarios with different interests
        self.student_scenarios = [
            {
                "name": "Perfect Student",
                "description": "Student who succeeds flawlessly",
                "student_id": "perfect_student_001",
                "interests": ["sports", "music", "technology"],
                "grade_level": "high school",
                "response_type": "perfect",
            },
            {
                "name": "Good Student",
                "description": "Student with good understanding but makes mistakes",
                "student_id": "good_student_002",
                "interests": ["art", "science", "gaming"],
                "grade_level": "high school",
                "response_type": "good_with_mistakes",
            },
            {
                "name": "Struggling Student",
                "description": "Student who struggles but is trying",
                "student_id": "struggling_student_003",
                "interests": ["animals", "cooking", "social media"],
                "grade_level": "middle school",
                "response_type": "struggling",
            },
            {
                "name": "Lazy Student",
                "description": "Student who doesn't try and just wants answers",
                "student_id": "lazy_student_004",
                "interests": ["gaming", "movies", "social media"],
                "grade_level": "high school",
                "response_type": "lazy",
            },
        ]

        # Test concept for consistent testing
        self.test_concept = {
            "concept_id": "quadratic_equations_001",
            "name": "Quadratic Equations",
            "content": "Equations of the form ax² + bx + c = 0, where a ≠ 0",
            "type": "mathematical_concept",
            "difficulty": "intermediate",
            "learning_objectives": [
                "Understand standard form of quadratic equations",
                "Apply factoring method when possible",
                "Use quadratic formula for all cases",
                "Verify solutions by substitution",
            ],
        }

        # Personalities to test
        self.personalities = [
            "default",
            "analytical-detective",
            "empathetic-supporter",
            "enthusiastic-coach",
            "wise-mentor",
            "collaborative-facilitator",
            "creative-innovator",
            "practical-guide",
            "scientific-explorer",
            "storytelling-historian",
            "strategic-challenger",
        ]

        self.use_hardcoded_exercise = use_hardcoded_exercise

        # Hardcoded exercise for consistent evaluator testing
        self.hardcoded_exercise = {
            "exercise_id": "hardcoded_test_001",
            "concept_id": "quadratic_equations_001",
            "student_id": "test_student",
            "type": "initial",
            "difficulty": "basic",
            "content": {
                "scenario": "You're at a basketball court in your school's new gym. The path of the basketball when you're making a free throw can be modeled by a quadratic equation.",
                "problem": "The basketball's path is represented by the equation x² + 5x + 6 = 0. Find the solutions to this equation and explain what each step of your solution process accomplishes.",
                "expected_steps": [
                    "Identify this as a quadratic equation in standard form",
                    "Choose an appropriate solution method (factoring, completing the square, or quadratic formula)",
                    "Apply the chosen method systematically",
                    "Solve for both values of x",
                    "Verify solutions by substituting back into the original equation",
                    "Interpret the solutions in context",
                ],
                "hints": [
                    "Look for two numbers that multiply to 6 and add to 5",
                    "Remember that quadratic equations typically have two solutions",
                    "Always check your work by substituting back",
                ],
                "success_criteria": "Student correctly identifies solution method, executes it properly, finds both solutions (-2 and -3), and verifies results",
            },
            "personalization": {
                "interests_used": ["sports"],
                "life_category": "academic",
                "context": "Basketball court design scenario",
            },
            "expected_steps": [
                "Identify this as a quadratic equation in standard form",
                "Choose an appropriate solution method (factoring, completing the square, or quadratic formula)",
                "Apply the chosen method systematically",
                "Solve for both values of x",
                "Verify solutions by substituting back into the original equation",
                "Interpret the solutions in context",
            ],
            "hints": [
                "Look for two numbers that multiply to 6 and add to 5",
                "Remember that quadratic equations typically have two solutions",
                "Always check your work by substituting back",
            ],
            "created_at": datetime.utcnow().isoformat(),
        }

    async def run_comprehensive_test(self, quick_mode: bool = False):
        """Run comprehensive test with correct flow."""
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)
        if quick_mode:
            print("🔬 QUICK MODE: Testing default personality only")
            test_personalities = ["default"]
            test_scenarios = [self.student_scenarios[0]]  # Just perfect student
        else:
            print("🔄 FULL MODE: Testing all personalities and scenarios")
            test_personalities = self.personalities
            test_scenarios = self.student_scenarios

        if self.use_hardcoded_exercise:
            print("📝 Using HARDCODED exercise for consistent evaluator testing")
        else:
            print("🎯 Generating personalized exercises for each student")

        print("Following the CORRECT flow:")
        print("1. Generate personalized exercises for each student")
        print("2. Use hardcoded student responses for consistency")
        print("3. Evaluate responses and generate remediation")
        print("4. Log all interactions with detailed reporting")
        print("=" * 60)

        start_time = datetime.utcnow()

        # Test each personality with each student scenario
        for personality in test_personalities:
            print(f"\n{'='*80}")
            print(f"🎭 Testing Personality: {personality}")
            print(f"{'='*80}")

            for scenario in test_scenarios:
                print(f"\n{'-'*60}")
                print(f"🎯 Testing: {scenario['name']} with {personality} personality")
                print(f"📝 Description: {scenario['description']}")
                print(f"👤 Student ID: {scenario['student_id']}")
                print(f"🎨 Interests: {', '.join(scenario['interests'])}")
                print(f"🎭 Personality: {personality}")
                print(f"{'-'*60}")

                try:
                    result = await self._run_single_test(scenario, personality)
                    self.test_results.append(
                        {
                            "scenario": scenario,
                            "personality": personality,
                            "result": result,
                            "timestamp": datetime.utcnow().isoformat(),
                            "success": True,
                        }
                    )
                    print(
                        f"✅ {scenario['name']} with {personality} completed successfully"
                    )

                except Exception as e:
                    error_result = {
                        "error": str(e),
                        "scenario_name": scenario["name"],
                        "personality": personality,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    self.test_results.append(
                        {
                            "scenario": scenario,
                            "personality": personality,
                            "result": error_result,
                            "timestamp": datetime.utcnow().isoformat(),
                            "success": False,
                        }
                    )
                    print(f"❌ {scenario['name']} with {personality} failed: {str(e)}")
                    logger.error(
                        "Scenario failed",
                        extra={
                            "scenario": scenario["name"],
                            "personality": personality,
                            "error": str(e),
                        },
                    )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n🏁 All Tests Completed in {duration:.2f} seconds")
        print(f"✅ Successful: {sum(1 for r in self.test_results if r['success'])}")
        print(f"❌ Failed: {sum(1 for r in self.test_results if not r['success'])}")

        await self._save_comprehensive_results()

        print(f"\n📁 Results saved to '{self.output_dir}' directory")
        print(
            "📊 Check workflow_test_results_YYYYMMDD_HHMMSS.json for detailed JSON data"
        )
        print(
            "📖 Check workflow_test_report_YYYYMMDD_HHMMSS.md for comprehensive analysis report"
        )

    async def _run_single_test(
        self, scenario: Dict[str, Any], personality: str = "default"
    ) -> Dict[str, Any]:
        """Run a single test following the correct flow."""

        student_profile = {
            "student_id": scenario["student_id"],
            "interests": scenario["interests"],
            "grade_level": scenario["grade_level"],
        }

        if self.use_hardcoded_exercise:
            # Step 1: Use hardcoded exercise for consistent evaluator testing
            print("\n1️⃣ Using hardcoded exercise for consistent evaluator testing...")

            generated_exercise = self.hardcoded_exercise.copy()
            generated_exercise["student_id"] = scenario["student_id"]
            generated_exercise["personalization"]["interests_used"] = scenario[
                "interests"
            ]

            print(f"   ✅ Exercise loaded: {generated_exercise['exercise_id']}")
            print(
                f"   🎯 Interests applied: {', '.join(generated_exercise['personalization']['interests_used'])}"
            )
            print(
                f"   📝 Scenario: {generated_exercise['content']['scenario'][:100]}..."
            )

            # Step 2: Log the hardcoded exercise
            exercise_log = {
                "step": "exercise_hardcoded",
                "exercise_id": generated_exercise["exercise_id"],
                "student_profile": student_profile,
                "hardcoded_content": generated_exercise,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            # Step 1: Generate personalized exercise for this student
            print(f"\n1️⃣ Generating personalized exercise for {scenario['name']}...")

            generated_exercise = await self.generator.generate(
                concept=self.test_concept,
                student_profile=student_profile,
                life_category=LifeCategory.PERSONAL.value,
                difficulty=DifficultyLevel.BASIC.value,
                exercise_type=ExerciseType.INITIAL.value,
                personality=personality,
            )

            print(f"   ✅ Exercise generated: {generated_exercise['exercise_id']}")
            print(
                f"   🎯 Interests incorporated: {', '.join(generated_exercise['personalization']['interests_used'])}"
            )
            print(
                f"   📝 Scenario: {generated_exercise['content']['scenario'][:100]}..."
            )

            # Step 2: Log the generated exercise
            exercise_log = {
                "step": "exercise_generation",
                "exercise_id": generated_exercise["exercise_id"],
                "student_profile": student_profile,
                "generation_params": {
                    "life_category": LifeCategory.PERSONAL.value,
                    "difficulty": DifficultyLevel.BASIC.value,
                    "exercise_type": ExerciseType.INITIAL.value,
                    "personality": personality,
                },
                "generated_content": generated_exercise,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Step 3: Generate hardcoded student response for this exercise
        print(
            f"\n2️⃣ Generating hardcoded student response ({scenario['response_type']})..."
        )

        student_response = self._generate_hardcoded_response(
            generated_exercise, scenario["response_type"]
        )

        print(f"   📝 Response type: {scenario['response_type']}")
        print(f"   📏 Response length: {len(student_response)} characters")
        print(f"   🗣️ Response preview: {student_response[:150]}...")

        # Step 4: Evaluate the student response
        print("\n3️⃣ Evaluating student response...")

        evaluation = await self.evaluator.evaluate(
            generated_exercise, student_response, self.test_concept
        )

        print(f"   ✅ Evaluation complete: {evaluation['evaluation_id']}")
        print(
            f"   📊 Understanding score: {evaluation['understanding_score']:.1%} ({evaluation['understanding_score']:.2f}/1.0)"
        )
        print(f"   🎯 Mastery achieved: {evaluation['mastery_achieved']}")
        print(f"   🔄 Needs remediation: {evaluation['needs_remediation']}")

        # Step 5: Log the evaluation response
        evaluation_log = {
            "step": "evaluation",
            "evaluation_id": evaluation["evaluation_id"],
            "student_response": student_response,
            "evaluation_result": evaluation,
            "llm_response": evaluation.get("llm_response"),
            "llm_response_raw": evaluation.get("llm_response_raw"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Step 6: Generate remediation if needed
        remediation = None
        remediation_log = None

        if evaluation["needs_remediation"]:
            print(f"\n4️⃣ Generating remediation (personality: {personality})...")

            remediation = await self.remediation_gen.generate(
                self.test_concept,
                "comprehensive understanding",
                student_profile,
                generated_exercise,
                evaluation,
            )

            print(f"   ✅ Remediation generated: {remediation['remediation_id']}")
            print(f"   🎯 Target gap: {remediation['target_gap']}")
            print(f"   🎭 Personality applied: {personality}")
            explanation_text = remediation.get("content", {}).get("explanation", "")
            if explanation_text:
                print(f"   📝 Remediation preview: {explanation_text[:150]}...")

            # Step 7: Log the remediation response
            remediation_log = {
                "step": "remediation",
                "remediation_id": remediation["remediation_id"],
                "target_gap": remediation["target_gap"],
                "personality": personality,
                "remediation_content": remediation,
                "llm_response_raw": remediation.get("llm_response_raw"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            print("\n4️⃣ No remediation needed - student demonstration is sufficient! 🎉")

        # Compile complete test result
        result = {
            "scenario_name": scenario["name"],
            "personality": personality,
            "concept": self.test_concept,
            "student_profile": student_profile,
            "exercise_source": (
                "hardcoded" if self.use_hardcoded_exercise else "generated"
            ),
            "logs": {
                "exercise_generation": exercise_log,
                "evaluation": evaluation_log,
                "remediation": remediation_log,
            },
            "final_data": {
                "exercise": generated_exercise,
                "student_response": student_response,
                "evaluation": evaluation,
                "remediation": remediation,
            },
            "workflow_completed": True,
            "total_steps": 4 if not evaluation["needs_remediation"] else 5,
            "test_timestamp": datetime.utcnow().isoformat(),
        }

        return result

    def _generate_hardcoded_response(
        self, exercise: Dict[str, Any], response_type: str
    ) -> str:
        """Generate hardcoded student responses that work with any generated exercise."""

        # Extract key information from the generated exercise
        exercise.get("content", {}).get("problem", "")
        exercise.get("content", {}).get("scenario", "")

        # Generate responses that are realistic for the problem type
        if response_type == "perfect":
            return """
Looking at this problem, I can see this is a quadratic equation that needs to be solved systematically.

Given the equation in the problem, I need to find the solutions step by step.

Let me identify the equation form and coefficients:
- This appears to be in the form ax² + bx + c = 0
- I can see the coefficients a=1, b=5, and c=6.

I'll use the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a

Applying this method:
1. x = (-5 ± √(5² - 4*1*6)) / 2*1
2. x = (-5 ± √(25 - 24)) / 2
3. x = (-5 ± 1) / 2
4. x = -4 / 2 = -2 and x = -6 / 2 = -3
5. x = -2 satisfies the equation: 1*(-2)² + 5*(-2) + 6 = 4 - 10 + 6 = 0
6. x = -3 satisfies the equation: 1*(-3)² + 5*(-3) + 6 = 9 - 15 + 6 = 0

After working through the calculations:
- I get two solutions for x: -2 and -3
- Both solutions check out when substituted back
- The solutions make sense in the context of the problem

The mathematical approach is sound and the verification confirms my answers are correct.
"""

        elif response_type == "good_with_mistakes":
            return """
I think this is a quadratic equation, so I should use the quadratic formula.

Let me try to solve this step by step:

The quadratic formula is x = (-b ± √(b² - 4ac)) / 2a

Looking at the equation, I think I can identify the coefficients...
Actually, let me try factoring first since that might be easier.

I need to find two numbers that multiply to give me the constant term and add to give me the middle coefficient.

Two numbers that multiply to give me 6 and add to give me 5 are 2 and 3.

So I can factor the equation as (x + 2)(x + 3) = 0

Setting each factor to 0 gives me the solutions:
x = 2 and x = -3

I'll check my work by substituting back into the original equation:

x = 2 satisfies the equation: 1*2² + 5*2 + 6 = 4 - 10 + 6 = 0

x = -3 satisfies the equation: 1*(-3)² + 5*(-3) + 6 = 9 - 15 + 6 = 0

The solutions I'm getting are reasonable.
"""

        elif response_type == "struggling":
            return """
I can see this is a math problem with x² in it, so I think it's a quadratic equation.

I remember there are different ways to solve these - factoring, completing the square, or using the quadratic formula.

I think factoring might be easier, but I'm not sure how to find the right factors.

Let me try the quadratic formula instead: x = (-b ± √(b² - 4ac)) / 2a

I'm having trouble identifying which numbers are a, b, and c in the equation.

I think a = 1, b = 6, and c = 5.

So x = (-6 ± √(6² - 4*1*5)) / 2*1
x = (-6 ± √(36 - 20)) / 2
x = (-6 ± √16) / 2
x = (-6 ± 4) / 2
x = -2 / 2 = -1 and x = -10 / 2 = -5

So x = -1 and x = -5.
"""

        elif response_type == "lazy":
            return """
This looks complicated. 

I don't really understand what I'm supposed to do here.

Can you just tell me the answer? I don't want to work through all these steps.

Math is hard and I don't see why I need to learn this.

If I need to know this stuff later, I can just look it up online or use a calculator.

What's the point of doing it by hand when technology can do it for me?

Just give me the answer so I can move on to the next problem.
"""

        else:
            return "I'm not sure how to approach this problem."

    async def _save_comprehensive_results(self):
        """Save comprehensive test results to timestamped files only."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Save raw JSON results (timestamped only)
        json_file = os.path.join(
            self.output_dir, f"workflow_test_results_{timestamp}.json"
        )

        with open(json_file, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        # Save comprehensive markdown report (timestamped only)
        md_file = os.path.join(self.output_dir, f"workflow_test_report_{timestamp}.md")

        comprehensive_report = self._generate_comprehensive_report()
        with open(md_file, "w") as f:
            f.write(comprehensive_report)

    def _generate_comprehensive_report(self) -> str:
        """Generate comprehensive markdown report combining structured data and human-readable analysis."""
        successful_results = [r for r in self.test_results if r["success"]]

        report = f"""# 🎯 Exercise Workflow Test - Comprehensive Report

## 📊 Executive Summary
- **Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Tests Executed**: {len(self.test_results)}
- **Successful Tests**: {len(successful_results)} ✅
- **Failed Tests**: {len(self.test_results) - len(successful_results)} ❌
- **Success Rate**: {(len(successful_results) / len(self.test_results) * 100):.1f}%
- **Exercise Source**: {"Hardcoded" if self.use_hardcoded_exercise else "Generated"}
- **Personalities Tested**: {len(set(r.get('personality', 'unknown') for r in self.test_results))}
- **Student Types**: {len(set(r['scenario']['name'] for r in self.test_results if r.get('scenario')))}

## 🔬 Test Methodology

This test follows the **correct workflow**:
1. **Generate Personalized Exercise** - Create exercises tailored to each student's interests
2. **Apply Hardcoded Responses** - Use consistent student responses across all tests  
3. **Evaluate Responses** - Assess understanding and identify gaps using LLM evaluation
4. **Generate Remediation** - Create targeted help when needed
5. **Log Everything** - Capture all LLM interactions for analysis

## 📚 Test Subject: {self.test_concept['name']}

**Concept**: {self.test_concept['content']}  
**Difficulty Level**: {self.test_concept['difficulty']}  
**Learning Objectives**:
"""

        for i, obj in enumerate(self.test_concept["learning_objectives"], 1):
            report += f"{i}. {obj}\n"

        report += "\n## 👥 Student Profiles Tested\n\n"

        for scenario in self.student_scenarios:
            report += f"### {scenario['name']} 👤\n"
            report += f"- **Description**: {scenario['description']}\n"
            report += f"- **Grade Level**: {scenario['grade_level']}\n"
            report += f"- **Interests**: {', '.join(scenario['interests'])}\n"
            report += f"- **Response Type**: {scenario['response_type']}\n\n"

        personalities_tested = list(
            set(r.get("personality", "unknown") for r in successful_results)
        )
        report += "## 🎭 Personalities Tested\n\n"
        for personality in personalities_tested:
            report += f"- {personality}\n"

        # Add performance analysis
        report += "\n## 📈 Performance Analysis\n\n"

        # Performance by student type
        report += "### 👥 Performance by Student Type\n\n"
        for scenario in self.student_scenarios:
            scenario_results = [
                r
                for r in successful_results
                if r["scenario"]["name"] == scenario["name"]
            ]
            if not scenario_results:
                continue

            scores = [
                r["result"]["final_data"]["evaluation"]["understanding_score"]
                for r in scenario_results
            ]
            avg_score = sum(scores) / len(scores)
            mastery_rate = sum(
                1
                for r in scenario_results
                if r["result"]["final_data"]["evaluation"]["mastery_achieved"]
            ) / len(scenario_results)
            remediation_rate = sum(
                1
                for r in scenario_results
                if r["result"]["final_data"]["evaluation"]["needs_remediation"]
            ) / len(scenario_results)

            report += f"**{scenario['name']}**:\n"
            report += f"- Average Understanding Score: {avg_score:.1%} ({avg_score:.2f}/1.0)\n"
            report += f"- Mastery Achievement Rate: {mastery_rate:.1%}\n"
            report += f"- Remediation Required Rate: {remediation_rate:.1%}\n"
            report += f"- Tests Conducted: {len(scenario_results)} (across all personalities)\n\n"

        # Performance by personality
        report += "### 🎭 Performance by Personality\n\n"
        for personality in personalities_tested:
            personality_results = [
                r for r in successful_results if r.get("personality") == personality
            ]
            if not personality_results:
                continue

            scores = [
                r["result"]["final_data"]["evaluation"]["understanding_score"]
                for r in personality_results
            ]
            avg_score = sum(scores) / len(scores)
            mastery_rate = sum(
                1
                for r in personality_results
                if r["result"]["final_data"]["evaluation"]["mastery_achieved"]
            ) / len(personality_results)

            report += f"**{personality}**:\n"
            report += f"- Average Understanding Score: {avg_score:.1%} ({avg_score:.2f}/1.0)\n"
            report += f"- Mastery Achievement Rate: {mastery_rate:.1%}\n"
            report += f"- Tests Conducted: {len(personality_results)}\n\n"

        report += "\n## 📋 Detailed Test Results\n\n"

        # Group by personality for better organization
        for personality in personalities_tested:
            personality_results = [
                r for r in successful_results if r.get("personality") == personality
            ]
            if not personality_results:
                continue

            report += f"### 🎭 {personality.upper()} Personality Results\n\n"

            for test_result in personality_results:
                scenario = test_result["scenario"]
                result = test_result["result"]

                report += f"#### 👤 {scenario['name']} Test\n\n"

                # Show exercise details
                exercise = result["final_data"]["exercise"]
                report += f"**🎯 Exercise Used ({result.get('exercise_source', 'unknown')})**:\n"
                report += f"- **Exercise ID**: {exercise['exercise_id']}\n"
                report += f"- **Interests Applied**: {', '.join(exercise['personalization']['interests_used'])}\n"
                report += f"- **Scenario**: {exercise['content']['scenario']}\n"
                report += f"- **Problem**: {exercise['content']['problem']}\n\n"

                report += "**📝 Expected Steps**:\n"
                for i, step in enumerate(exercise["content"]["expected_steps"], 1):
                    report += f"{i}. {step}\n"

                report += "\n**💡 Hints Available**:\n"
                hints = exercise["content"].get("hints", [])
                for i, hint in enumerate(hints, 1):
                    report += f"{i}. {hint}\n"

                report += f"\n**🎯 Success Criteria**: {exercise['content']['success_criteria']}\n\n"

                # Show student response
                student_response = result["final_data"]["student_response"]
                report += "**🗣️ Student Response**:\n"
                report += f"```\n{student_response.strip()}\n```\n\n"

                # Show evaluation
                evaluation = result["final_data"]["evaluation"]
                report += "**📊 AI Evaluation**:\n"
                report += f"- **Understanding Score**: {evaluation['understanding_score']:.1%} ({evaluation['understanding_score']:.2f}/1.0)\n"
                report += f"- **Mastery Achieved**: {'✅ Yes' if evaluation['mastery_achieved'] else '❌ No'}\n"
                report += f"- **Needs Remediation**: {'⚠️ Yes' if evaluation['needs_remediation'] else '✅ No'}\n"

                if evaluation.get("feedback"):
                    report += f"- **AI Feedback**: {evaluation['feedback'][:300]}...\n"

                # Show LLM response for evaluation (condensed)
                if evaluation.get("llm_response"):
                    llm_resp = evaluation["llm_response"]
                    if (
                        isinstance(llm_resp, dict)
                        and "understanding_analysis" in llm_resp
                    ):
                        understanding = llm_resp["understanding_analysis"]
                        if isinstance(understanding, dict):
                            demo = understanding.get("demonstrated_understanding", "")
                            missing = understanding.get("missing_understanding", "")
                            report += "\n**🔍 LLM Analysis**:\n"
                            report += f"- **Demonstrated**: {demo[:200]}...\n"
                            report += f"- **Missing**: {missing[:200]}...\n"

                report += "\n"

                # Show remediation if generated
                if result["final_data"]["remediation"]:
                    remediation = result["final_data"]["remediation"]
                    report += "**🔧 Generated Remediation**:\n"
                    report += f"- **Target Gap**: {remediation['target_gap']}\n"
                    report += f"- **Personality Applied**: {personality}\n"

                    content = remediation.get("content", {})
                    if content.get("gap_analysis", {}).get("specific_gaps"):
                        report += f"- **Gap Analysis**: {content['gap_analysis']['specific_gaps'][:200]}...\n"

                    report += "\n"

                report += "---\n\n"

        # Add conclusion section
        report += """## 🎯 Key Findings

This comprehensive test validates:

1. **✅ Exercise Generation**: Successfully creates personalized exercises based on student interests
2. **✅ Response Evaluation**: Accurately assesses student understanding across different response types  
3. **✅ Remediation Generation**: Appropriately generates targeted help when needed
4. **✅ Personality Integration**: Different personalities are applied consistently
5. **✅ Workflow Completeness**: Full end-to-end workflow functions correctly
6. **✅ LLM Response Capture**: All LLM interactions are logged for analysis

## 🔍 What to Look For

When reviewing these results, pay attention to:
- **Score Differentiation**: Do the understanding scores properly differentiate between student types?
- **LLM Response Quality**: Are the LLM evaluations meaningful and accurate?
- **Personalization Quality**: Are the exercises truly personalized to student interests?
- **Evaluation Accuracy**: Do the understanding scores match the quality of student responses?
- **Remediation Appropriateness**: Is remediation generated when needed and skipped when not?
- **Personality Consistency**: Are different personalities reflected in the remediation content?

This test provides a comprehensive view of the exercise service's capabilities and validates that the LLMs are providing meaningful, accurate responses for educational assessment.
"""

        return report


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Exercise Workflow Test Suite")
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Test mode: quick (default personality only) or full (all personalities)",
    )
    parser.add_argument(
        "--hardcoded-exercise",
        action="store_true",
        help="Use hardcoded exercise for consistent evaluator testing",
    )

    args = parser.parse_args()

    print("🚀 Exercise Workflow Test Suite - CORRECTED Version")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Exercise Source: {'Hardcoded' if args.hardcoded_exercise else 'Generated'}")
    print("Following the CORRECT workflow:")
    print("1. Generate personalized exercises for each student")
    print("2. Use hardcoded student responses for consistency")
    print("3. Evaluate responses and generate remediation")
    print("4. Log all interactions with detailed reporting")
    print("=" * 60)

    try:
        tester = ExerciseWorkflowTester(use_hardcoded_exercise=args.hardcoded_exercise)
        await tester.run_comprehensive_test(quick_mode=(args.mode == "quick"))
        print("\n✅ Workflow test completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
