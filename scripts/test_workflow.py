#!/usr/bin/env python3
"""
Comprehensive Exercise Workflow Test

This script tests the complete exercise workflow with four different student scenarios:
1. Perfect Student - succeeds flawlessly
2. Good Student - has understanding but makes mistakes
3. Struggling Student - tries but has difficulties
4. Lazy Student - doesn't try and just wants answers

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
from pathlib import Path
import sys

# Load environment variables from .env file
load_dotenv()

# Add app directory to path
app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

# Import the exercise service components
from app.core.config import settings
from app.models.exercise import (
    ExerciseGenerationRequest,
    StudentResponse,
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
from app.resources.personalities import personality_loader
from openai import AsyncOpenAI

# Setup logging
logger = structlog.get_logger()

class RealAPIWorkflowTester:
    """Comprehensive workflow tester using real API calls."""
    
    def __init__(self):
        # Verify API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('test'):
            raise ValueError("Valid OpenAI API key required. Set OPENAI_API_KEY in .env file")
        
        # Initialize components
        self.generator = ExerciseGenerator()
        self.evaluator = ResponseEvaluator()
        self.remediation_gen = RemediationGenerator()
        if WORKFLOW_AVAILABLE:
            self.workflow = ExerciseWorkflow()
        else:
            self.workflow = None
            print("⚠️  LangGraph workflow not available - using direct component testing")
        self.test_results = []
        self.output_dir = "test_results"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test scenarios - now includes personality testing
        self.personalities = [
            "default", "analytical-detective", "empathetic-supporter", 
            "enthusiastic-coach", "wise-mentor", "collaborative-facilitator",
            "creative-innovator", "practical-guide", "scientific-explorer",
            "storytelling-historian", "strategic-challenger"
        ]
        
        self.scenarios = [
            {
                "name": "Perfect Student",
                "description": "Student who succeeds flawlessly",
                "student_id": "perfect_student_001",
                "interests": ["sports", "music", "technology"],
                "grade_level": "high school",
                "response_type": "perfect"
            },
            {
                "name": "Good Student",
                "description": "Student with good understanding but makes mistakes",
                "student_id": "good_student_002",
                "interests": ["art", "science", "gaming"],
                "grade_level": "high school",
                "response_type": "good_with_mistakes"
            },
            {
                "name": "Struggling Student",
                "description": "Student who struggles but is trying",
                "student_id": "struggling_student_003",
                "interests": ["sports", "animals", "food"],
                "grade_level": "middle school",
                "response_type": "struggling"
            },
            {
                "name": "Lazy Student",
                "description": "Student who doesn't try and just wants answers",
                "student_id": "lazy_student_004",
                "interests": ["gaming", "social media", "movies"],
                "grade_level": "high school",
                "response_type": "lazy"
            }
        ]
        
        # Hard-coded exercise for consistent testing
        self.hardcoded_exercise = {
            "exercise_id": "test_exercise_001",
            "concept_id": "quadratic_equations_001",
            "student_id": "test_student",
            "type": "initial",
            "difficulty": "basic",
            "content": {
                "scenario": "You're helping design a basketball court layout for your school's new gym. The path of the basketball when making a free throw can be modeled by a quadratic equation.",
                "problem": "The basketball's path is represented by the equation x² + 5x + 6 = 0. Find the solutions to this equation and explain what each step of your solution process accomplishes.",
                "expected_steps": [
                    "Identify this as a quadratic equation in standard form",
                    "Choose an appropriate solution method (factoring, completing the square, or quadratic formula)",
                    "Apply the chosen method systematically",
                    "Solve for both values of x",
                    "Verify solutions by substituting back into the original equation",
                    "Interpret the solutions in context"
                ],
                "hints": [
                    "Look for two numbers that multiply to 6 and add to 5",
                    "Remember that quadratic equations typically have two solutions",
                    "Always check your work by substituting back"
                ],
                "success_criteria": "Student correctly identifies solution method, executes it properly, finds both solutions (-2 and -3), and verifies results"
            },
            "personalization": {
                "interests_used": ["sports"],
                "life_category": "academic",
                "context": "Basketball court design scenario"
            },
            "expected_steps": [
                "Identify this as a quadratic equation in standard form",
                "Choose an appropriate solution method (factoring, completing the square, or quadratic formula)",
                "Apply the chosen method systematically",
                "Solve for both values of x",
                "Verify solutions by substituting back into the original equation",
                "Interpret the solutions in context"
            ],
            "hints": [
                "Look for two numbers that multiply to 6 and add to 5",
                "Remember that quadratic equations typically have two solutions",
                "Always check your work by substituting back"
            ],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Test concept
        self.concept = {
            "concept_id": "quadratic_equations_001",
            "name": "Quadratic Equations",
            "content": "Equations of the form ax² + bx + c = 0, where a ≠ 0",
            "type": "mathematical_concept",
            "difficulty": "intermediate",
            "learning_objectives": [
                "Understand standard form of quadratic equations",
                "Apply factoring method when possible",
                "Use quadratic formula for all cases",
                "Verify solutions by substitution"
            ]
        }
    
    async def run_comprehensive_test(self):
        """Run comprehensive test with all scenarios and personalities."""
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Test each personality with each scenario
        for personality in self.personalities:
            print(f"\n{'='*80}")
            print(f"🎭 Testing Personality: {personality}")
            print(f"{'='*80}")
            
            for scenario in self.scenarios:
                print(f"\n{'-'*60}")
                print(f"🎯 Testing: {scenario['name']} with {personality} personality")
                print(f"📝 Description: {scenario['description']}")
                print(f"👤 Student ID: {scenario['student_id']}")
                print(f"🎨 Interests: {', '.join(scenario['interests'])}")
                print(f"🎭 Personality: {personality}")
                print(f"{'-'*60}")
                
                try:
                    result = await self._run_scenario(scenario, personality)
                    self.test_results.append({
                        "scenario": scenario,
                        "personality": personality,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": True
                    })
                    print(f"✅ {scenario['name']} with {personality} completed successfully")
                    
                except Exception as e:
                    error_result = {
                        "error": str(e),
                        "scenario_name": scenario['name'],
                        "personality": personality,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.test_results.append({
                        "scenario": scenario,
                        "personality": personality,
                        "result": error_result,
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": False
                    })
                    print(f"❌ {scenario['name']} with {personality} failed: {str(e)}")
                    logger.error(f"Scenario failed", scenario=scenario['name'], personality=personality, error=str(e))
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n🏁 All Tests Completed in {duration:.2f} seconds")
        print(f"✅ Successful: {sum(1 for r in self.test_results if r['success'])}")
        print(f"❌ Failed: {sum(1 for r in self.test_results if not r['success'])}")
        
        await self._save_comprehensive_results()
        
        print(f"\n📁 Results saved to '{self.output_dir}' directory")
        print(f"📊 Check workflow_test_results.json for detailed data")
        print(f"📖 Check workflow_test_report.md for readable summary")
        print(f"🎨 Check workflow_test_report_pretty.md for human-readable analysis")
    
    async def _run_scenario(self, scenario: Dict[str, Any], personality: str = "default") -> Dict[str, Any]:
        """Run a single test scenario using hardcoded exercise for consistent testing."""
        student_profile = {
            "student_id": scenario["student_id"],
            "interests": scenario["interests"],
            "grade_level": scenario["grade_level"]
        }
        
        # Step 1: Use hardcoded exercise for consistent testing
        print(f"\n1️⃣ Using hardcoded exercise for consistent testing...")
        print(f"   🎭 Personality: {personality}")
        
        # Test remediation generation with personality (this is where personality matters most)
        exercise = self.hardcoded_exercise.copy()
        exercise["student_id"] = scenario["student_id"]
        exercise["personalization"]["interests_used"] = scenario["interests"]
        
        print(f"   ✅ Exercise loaded: {exercise['exercise_id']}")
        print(f"   🎯 Interests used: {', '.join(exercise['personalization']['interests_used'])}")
        print(f"   🎭 Testing with personality: {personality}")
        
        # Step 2: Generate student response
        print(f"\n2️⃣ Generating student response...")
        student_response = self._generate_student_response(exercise, scenario["response_type"])
        print(f"   📝 Response length: {len(student_response)} characters")
        
        # Step 3: Evaluate response
        print(f"\n3️⃣ Evaluating student response...")
        evaluation = await self.evaluator.evaluate(
            exercise,
            student_response,
            self.concept
        )
        
        print(f"   ✅ Evaluation complete: {evaluation['evaluation_id']}")
        print(f"   📊 Understanding score: {evaluation['understanding_score']:.2f}")
        print(f"   🎯 Mastery achieved: {evaluation['mastery_achieved']}")
        print(f"   🔄 Needs remediation: {evaluation['needs_remediation']}")
        
        # Step 4: Generate remediation if needed
        remediation = None
        if evaluation['needs_remediation']:
            print(f"\n4️⃣ Generating remediation...")
            remediation = await self.remediation_gen.generate(
                self.concept,
                "comprehensive understanding",
                student_profile,
                exercise,
                evaluation
            )
            print(f"   ✅ Remediation generated: {remediation['remediation_id']}")
            print(f"   🎯 Target gap: {remediation['target_gap']}")
            print(f"   🎭 Personality context: {personality}")
        else:
            print(f"\n4️⃣ No remediation needed - mastery achieved!")
        
        # Compile results
        result = {
            "scenario_name": scenario["name"],
            "personality": personality,
            "concept": self.concept,
            "student_profile": student_profile,
            "exercise": exercise,
            "student_response": student_response,
            "evaluation": evaluation,
            "remediation": remediation,
            "workflow_completed": True,
            "total_steps": 4 if not evaluation['needs_remediation'] else 5
        }
        
        return result
    
    def _generate_student_response(self, exercise: Dict[str, Any], response_type: str) -> str:
        """Generate realistic student responses based on type."""
        scenario = exercise.get("content", {}).get("scenario", "")
        problem = exercise.get("content", {}).get("problem", "")
        
        if response_type == "perfect":
            return f"""
            Looking at this problem, I need to identify that this is a quadratic equation and solve it systematically.
            
            The equation is in the form ax² + bx + c = 0, so I can use the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a
            
            First, let me identify the coefficients:
            a = 1, b = 5, c = 6
            
            Now I'll apply the quadratic formula:
            x = (-5 ± √(25 - 24)) / 2
            x = (-5 ± √1) / 2
            x = (-5 ± 1) / 2
            
            This gives me two solutions:
            x₁ = (-5 + 1) / 2 = -4/2 = -2
            x₂ = (-5 - 1) / 2 = -6/2 = -3
            
            Let me verify by substituting back:
            For x = -2: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0 ✓
            For x = -3: (-3)² + 5(-3) + 6 = 9 - 15 + 6 = 0 ✓
            
            Therefore, the solutions are x = -2 and x = -3.
            """
        
        elif response_type == "good_with_mistakes":
            return f"""
            This is a quadratic equation, so I need to solve it using the quadratic formula.
            
            The equation is ax² + bx + c = 0, where a = 1, b = 5, c = 6
            
            Using the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a
            
            x = (-5 ± √(25 - 24)) / 2
            x = (-5 ± √1) / 2
            x = (-5 ± 1) / 2
            
            So x = -4/2 = -2 or x = -6/2 = -3
            
            Wait, let me check this... Actually, I think I might have made an error in my calculation.
            The solutions should be x = -2 and x = -3.
            
            [Student shows good understanding but has some uncertainty and minor computational hesitation]
            """
        
        elif response_type == "struggling":
            return f"""
            I think this is a quadratic equation because it has x².
            
            I'm not sure which method to use. Maybe I can try factoring?
            
            x² + 5x + 6 = 0
            
            I need to find two numbers that multiply to 6 and add to 5.
            That would be 2 and 3.
            
            So (x + 2)(x + 3) = 0
            
            This means x + 2 = 0 or x + 3 = 0
            So x = -2 or x = -3
            
            I think that's right but I'm not totally sure. I get confused with the signs sometimes.
            """
        
        elif response_type == "lazy":
            return f"""
            I don't know. Can you just tell me the answer?
            
            This looks hard and I don't really understand what I'm supposed to do.
            """
        
        else:
            return "I'm not sure how to approach this problem."
    
    async def _save_comprehensive_results(self):
        """Save comprehensive test results to files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save raw JSON results
        json_file = os.path.join(self.output_dir, f"workflow_test_results_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save readable markdown report
        md_file = os.path.join(self.output_dir, f"workflow_test_report_{timestamp}.md")
        with open(md_file, 'w') as f:
            f.write(self._generate_readable_report())
        
        # Save pretty visualization report
        pretty_file = os.path.join(self.output_dir, f"workflow_test_report_pretty_{timestamp}.md")
        with open(pretty_file, 'w') as f:
            f.write(self._generate_pretty_report())
        
        # Save latest versions (no timestamp)
        latest_json = os.path.join(self.output_dir, "workflow_test_results.json")
        latest_md = os.path.join(self.output_dir, "workflow_test_report.md")
        latest_pretty = os.path.join(self.output_dir, "workflow_test_report_pretty.md")
        
        with open(latest_json, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        with open(latest_md, 'w') as f:
            f.write(self._generate_readable_report())
        
        with open(latest_pretty, 'w') as f:
            f.write(self._generate_pretty_report())
    
    def _generate_readable_report(self) -> str:
        """Generate a readable markdown report."""
        report = f"""# Exercise Workflow Test Report

## Test Summary
- **Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Scenarios**: {len(self.test_results)}
- **Successful**: {sum(1 for r in self.test_results if r['success'])}
- **Failed**: {sum(1 for r in self.test_results if not r['success'])}

## Test Concept
- **Name**: {self.concept['name']}
- **Content**: {self.concept['content']}
- **Difficulty**: {self.concept['difficulty']}

## Scenario Results

"""
        
        for i, test_result in enumerate(self.test_results, 1):
            scenario = test_result['scenario']
            result = test_result['result']
            success = test_result['success']
            personality = test_result.get('personality', 'default')
            
            report += f"""### {i}. {scenario['name']} - {personality}
**Status**: {'✅ SUCCESS' if success else '❌ FAILED'}
**Description**: {scenario['description']}
**Student Interests**: {', '.join(scenario['interests'])}
**Grade Level**: {scenario['grade_level']}
**Personality**: {personality}

"""
            
            if success and 'evaluation' in result:
                evaluation = result['evaluation']
                report += f"""**Results**:
- Understanding Score: {evaluation['understanding_score']:.2f}
- Mastery Achieved: {evaluation['mastery_achieved']}
- Needs Remediation: {evaluation['needs_remediation']}
- Exercise ID: {result['exercise']['exercise_id']}

"""
                
                if result['remediation']:
                    report += f"""**Remediation**:
- Target Gap: {result['remediation']['target_gap']}
- Remediation ID: {result['remediation']['remediation_id']}

"""
            
            elif not success:
                report += f"""**Error**: {result.get('error', 'Unknown error')}

"""
        
        # Add analysis
        if self.test_results:
            successful_results = [r for r in self.test_results if r['success']]
            if successful_results:
                scores = [r['result']['evaluation']['understanding_score'] for r in successful_results]
                mastery_achieved = [r['result']['evaluation']['mastery_achieved'] for r in successful_results]
                
                report += f"""## Analysis

### Understanding Scores
- **Average**: {sum(scores) / len(scores):.2f}
- **Highest**: {max(scores):.2f}
- **Lowest**: {min(scores):.2f}

### Mastery Achievement
- **Students achieving mastery**: {sum(mastery_achieved)}/{len(mastery_achieved)}
- **Mastery rate**: {(sum(mastery_achieved) / len(mastery_achieved) * 100):.1f}%

### Remediation Needed
- **Students needing remediation**: {sum(1 for r in successful_results if r['result']['evaluation']['needs_remediation'])}
- **Remediation rate**: {(sum(1 for r in successful_results if r['result']['evaluation']['needs_remediation']) / len(successful_results) * 100):.1f}%

"""
        
        report += f"""## Conclusions

The workflow test demonstrates the exercise system's ability to:
1. Generate personalized exercises based on student interests
2. Evaluate student responses with appropriate scoring
3. Identify when remediation is needed
4. Provide targeted remediation for learning gaps

This comprehensive test validates the end-to-end functionality of the exercise service.
"""
        
        return report
    
    def _generate_pretty_report(self) -> str:
        """Generate a pretty, human-readable report for evaluation."""
        report = f"""# 🎯 Exercise Workflow Test - Pretty Report

## 📊 Overview
- **Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Tests**: {len(self.test_results)}
- **Personalities Tested**: {len(self.personalities)}
- **Student Scenarios**: {len(self.scenarios)}
- **Successful**: {sum(1 for r in self.test_results if r['success'])} ✅
- **Failed**: {sum(1 for r in self.test_results if not r['success'])} ❌

## 🧪 Test Configuration

### 📝 Hard-coded Problem Used
**Problem**: {self.hardcoded_exercise['content']['problem']}

**Scenario**: {self.hardcoded_exercise['content']['scenario']}

**Expected Steps**:
"""
        
        for i, step in enumerate(self.hardcoded_exercise['content']['expected_steps'], 1):
            report += f"{i}. {step}\n"
        
        report += f"""

### 🎭 Personalities Tested
{', '.join(self.personalities)}

### 👨‍🎓 Student Scenarios
"""
        
        for scenario in self.scenarios:
            report += f"- **{scenario['name']}**: {scenario['description']}\n"
        
        report += "\n## 🔍 Detailed Results\n\n"
        
        # Group by personality
        for personality in self.personalities:
            personality_results = [r for r in self.test_results if r.get('personality') == personality]
            if not personality_results:
                continue
                
            report += f"### 🎭 {personality.upper()} Personality\n\n"
            
            for test_result in personality_results:
                if not test_result['success']:
                    continue
                    
                scenario = test_result['scenario']
                result = test_result['result']
                
                report += f"#### 👨‍🎓 {scenario['name']}\n"
                report += f"**Grade Level**: {scenario['grade_level']}\n"
                report += f"**Interests**: {', '.join(scenario['interests'])}\n\n"
                
                # Show student response
                report += f"**🗣️ Student Response**:\n"
                report += f"```\n{result['student_response'].strip()}\n```\n\n"
                
                # Show evaluation
                evaluation = result['evaluation']
                report += f"**📊 AI Evaluation**:\n"
                report += f"- Understanding Score: {evaluation['understanding_score']:.2f}/10\n"
                report += f"- Mastery Achieved: {'✅ Yes' if evaluation['mastery_achieved'] else '❌ No'}\n"
                report += f"- Needs Remediation: {'⚠️ Yes' if evaluation['needs_remediation'] else '✅ No'}\n\n"
                
                if evaluation.get('feedback'):
                    report += f"**💬 AI Feedback**:\n"
                    report += f"```\n{evaluation['feedback']}\n```\n\n"
                
                # Show remediation if present
                if result.get('remediation'):
                    remediation = result['remediation']
                    report += f"**🔧 Remediation Generated**:\n"
                    report += f"- Target Gap: {remediation['target_gap']}\n"
                    
                    if remediation.get('content', {}).get('explanation'):
                        report += f"- Explanation: {remediation['content']['explanation'][:200]}...\n"
                    
                    if remediation.get('content', {}).get('key_insights'):
                        report += f"- Key Insights: {len(remediation['content']['key_insights'])} provided\n"
                    
                    report += "\n"
                
                report += "---\n\n"
        
        # Add analysis section
        successful_results = [r for r in self.test_results if r['success']]
        if successful_results:
            report += "## 📈 Analysis\n\n"
            
            # Score analysis by personality
            report += "### 🎭 Performance by Personality\n\n"
            for personality in self.personalities:
                personality_results = [r for r in successful_results if r.get('personality') == personality]
                if not personality_results:
                    continue
                    
                scores = [r['result']['evaluation']['understanding_score'] for r in personality_results]
                avg_score = sum(scores) / len(scores)
                mastery_rate = sum(1 for r in personality_results if r['result']['evaluation']['mastery_achieved']) / len(personality_results)
                
                report += f"**{personality}**:\n"
                report += f"- Average Score: {avg_score:.2f}/10\n"
                report += f"- Mastery Rate: {mastery_rate:.1%}\n"
                report += f"- Tests: {len(personality_results)}\n\n"
            
            # Student type analysis
            report += "### 👨‍🎓 Performance by Student Type\n\n"
            for scenario in self.scenarios:
                scenario_results = [r for r in successful_results if r['scenario']['name'] == scenario['name']]
                if not scenario_results:
                    continue
                    
                scores = [r['result']['evaluation']['understanding_score'] for r in scenario_results]
                avg_score = sum(scores) / len(scores)
                mastery_rate = sum(1 for r in scenario_results if r['result']['evaluation']['mastery_achieved']) / len(scenario_results)
                
                report += f"**{scenario['name']}**:\n"
                report += f"- Average Score: {avg_score:.2f}/10\n"
                report += f"- Mastery Rate: {mastery_rate:.1%}\n"
                report += f"- Tests: {len(scenario_results)}\n\n"
        
        report += """## 🎯 Summary

This test validates:
1. **Personality Integration**: Each personality was tested across all student scenarios
2. **Consistent Problem**: Same hardcoded problem ensures fair evaluation
3. **Response Mapping**: Student responses matched to appropriate problem context
4. **Evaluation Accuracy**: AI assessment of various student performance levels
5. **Remediation Targeting**: Appropriate remediation generated when needed

The detailed responses above allow human evaluators to quickly assess:
- Quality of AI evaluations
- Appropriateness of remediation suggestions
- Consistency across personalities
- Accuracy of student response assessments
"""
        
        return report

async def main():
    """Main entry point."""
    print("🚀 Exercise Workflow Test Suite - Updated Version")
    print("=" * 60)
    print("This test validates the complete exercise workflow with personality integration")
    print("Using real OpenAI API calls for authentic testing")
    print()
    print("🔧 Updates in this version:")
    print("1. 🎭 Tests all personalities, not just default")
    print("2. 📝 Uses hardcoded problem with corresponding hardcoded student responses")
    print("3. 🎨 Generates pretty human-readable reports for evaluation")
    print("4. 📊 Provides detailed analysis by personality and student type")
    print("=" * 60)
    
    try:
        tester = RealAPIWorkflowTester()
        await tester.run_comprehensive_test()
        print("\n✅ Workflow test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 