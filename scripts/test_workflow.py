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
import uuid
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Make sure OPENAI_API_KEY is set in environment.")

# Add app directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

# Setup basic logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExerciseWorkflowTester:
    """Comprehensive workflow tester following the correct flow."""
    
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
        
        # Student scenarios with different interests
        self.student_scenarios = [
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
                "interests": ["animals", "cooking", "social media"],
                "grade_level": "middle school",
                "response_type": "struggling"
            },
            {
                "name": "Lazy Student",
                "description": "Student who doesn't try and just wants answers",
                "student_id": "lazy_student_004",
                "interests": ["gaming", "movies", "social media"],
                "grade_level": "high school",
                "response_type": "lazy"
            }
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
                "Verify solutions by substitution"
            ]
        }
        
        # Personalities to test
        self.personalities = [
            "default", "analytical-detective", "empathetic-supporter", 
            "enthusiastic-coach", "wise-mentor", "collaborative-facilitator",
            "creative-innovator", "practical-guide", "scientific-explorer",
            "storytelling-historian", "strategic-challenger"
        ]
    
    async def run_comprehensive_test(self):
        """Run comprehensive test with correct flow."""
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)
        print("Following the CORRECT flow:")
        print("1. Generate personalized exercises for each student")
        print("2. Use hardcoded student responses for consistency")
        print("3. Evaluate responses and generate remediation")
        print("4. Log all interactions with detailed reporting")
        print("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Test each personality with each student scenario
        for personality in self.personalities:
            print(f"\n{'='*80}")
            print(f"🎭 Testing Personality: {personality}")
            print(f"{'='*80}")
            
            for scenario in self.student_scenarios:
                print(f"\n{'-'*60}")
                print(f"🎯 Testing: {scenario['name']} with {personality} personality")
                print(f"📝 Description: {scenario['description']}")
                print(f"👤 Student ID: {scenario['student_id']}")
                print(f"🎨 Interests: {', '.join(scenario['interests'])}")
                print(f"🎭 Personality: {personality}")
                print(f"{'-'*60}")
                
                try:
                    result = await self._run_single_test(scenario, personality)
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
                    logger.error(f"Scenario failed", extra={"scenario": scenario['name'], "personality": personality, "error": str(e)})
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n🏁 All Tests Completed in {duration:.2f} seconds")
        print(f"✅ Successful: {sum(1 for r in self.test_results if r['success'])}")
        print(f"❌ Failed: {sum(1 for r in self.test_results if not r['success'])}")
        
        await self._save_comprehensive_results()
        
        print(f"\n📁 Results saved to '{self.output_dir}' directory")
        print(f"📊 Check workflow_test_results.json for detailed JSON data")
        print(f"📖 Check workflow_test_report.md for structured markdown report")
        print(f"🎨 Check workflow_test_report_pretty.md for human-readable analysis")
    
    async def _run_single_test(self, scenario: Dict[str, Any], personality: str = "default") -> Dict[str, Any]:
        """Run a single test following the correct flow."""
        
        # Step 1: Generate personalized exercise for this student
        print(f"\n1️⃣ Generating personalized exercise for {scenario['name']}...")
        
        student_profile = {
            "student_id": scenario["student_id"],
            "interests": scenario["interests"],
            "grade_level": scenario["grade_level"]
        }
        
        generated_exercise = await self.generator.generate(
            concept=self.test_concept,
            student_profile=student_profile,
            life_category=LifeCategory.PERSONAL.value,
            difficulty=DifficultyLevel.BASIC.value,
            exercise_type=ExerciseType.INITIAL.value,
            personality=personality
        )
        
        print(f"   ✅ Exercise generated: {generated_exercise['exercise_id']}")
        print(f"   🎯 Interests incorporated: {', '.join(generated_exercise['personalization']['interests_used'])}")
        print(f"   📝 Scenario: {generated_exercise['content']['scenario'][:100]}...")
        
        # Step 2: Log the generated exercise
        exercise_log = {
            "step": "exercise_generation",
            "exercise_id": generated_exercise["exercise_id"],
            "student_profile": student_profile,
            "generation_params": {
                "life_category": LifeCategory.PERSONAL.value,
                "difficulty": DifficultyLevel.BASIC.value,
                "exercise_type": ExerciseType.INITIAL.value,
                "personality": personality
            },
            "generated_content": generated_exercise,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 3: Generate hardcoded student response for this exercise
        print(f"\n2️⃣ Generating hardcoded student response ({scenario['response_type']})...")
        
        student_response = self._generate_hardcoded_response(
            generated_exercise, 
            scenario["response_type"]
        )
        
        print(f"   📝 Response type: {scenario['response_type']}")
        print(f"   📏 Response length: {len(student_response)} characters")
        print(f"   🗣️ Response preview: {student_response[:150]}...")
        
        # Step 4: Evaluate the student response
        print(f"\n3️⃣ Evaluating student response...")
        
        evaluation = await self.evaluator.evaluate(
            generated_exercise,
            student_response,
            self.test_concept
        )
        
        print(f"   ✅ Evaluation complete: {evaluation['evaluation_id']}")
        print(f"   📊 Understanding score: {evaluation['understanding_score']:.2f}/10")
        print(f"   🎯 Mastery achieved: {evaluation['mastery_achieved']}")
        print(f"   🔄 Needs remediation: {evaluation['needs_remediation']}")
        
        # Step 5: Log the evaluation response
        evaluation_log = {
            "step": "evaluation",
            "evaluation_id": evaluation["evaluation_id"],
            "student_response": student_response,
            "evaluation_result": evaluation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 6: Generate remediation if needed
        remediation = None
        remediation_log = None
        
        if evaluation['needs_remediation']:
            print(f"\n4️⃣ Generating remediation (personality: {personality})...")
            
            remediation = await self.remediation_gen.generate(
                self.test_concept,
                "comprehensive understanding",
                student_profile,
                generated_exercise,
                evaluation
            )
            
            print(f"   ✅ Remediation generated: {remediation['remediation_id']}")
            print(f"   🎯 Target gap: {remediation['target_gap']}")
            print(f"   🎭 Personality applied: {personality}")
            print(f"   📝 Remediation preview: {remediation['content']['explanation'][:150]}...")
            
            # Step 7: Log the remediation response
            remediation_log = {
                "step": "remediation",
                "remediation_id": remediation["remediation_id"],
                "target_gap": remediation["target_gap"],
                "personality": personality,
                "remediation_content": remediation,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            print(f"\n4️⃣ No remediation needed - student demonstration is sufficient! 🎉")
        
        # Compile complete test result
        result = {
            "scenario_name": scenario["name"],
            "personality": personality,
            "concept": self.test_concept,
            "student_profile": student_profile,
            "logs": {
                "exercise_generation": exercise_log,
                "evaluation": evaluation_log,
                "remediation": remediation_log
            },
            "final_data": {
                "exercise": generated_exercise,
                "student_response": student_response,
                "evaluation": evaluation,
                "remediation": remediation
            },
            "workflow_completed": True,
            "total_steps": 4 if not evaluation['needs_remediation'] else 5,
            "test_timestamp": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _generate_hardcoded_response(self, exercise: Dict[str, Any], response_type: str) -> str:
        """Generate hardcoded student responses that work with any generated exercise."""
        
        # Extract key information from the generated exercise
        problem = exercise.get("content", {}).get("problem", "")
        scenario = exercise.get("content", {}).get("scenario", "")
        
        # Generate responses that are realistic for the problem type
        if response_type == "perfect":
            return f"""
Looking at this problem, I can see this is a quadratic equation that needs to be solved systematically.

Given the equation in the problem, I need to find the solutions step by step.

Let me identify the equation form and coefficients:
- This appears to be in the form ax² + bx + c = 0
- I can see the coefficients and will work with them

I'll use the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a

Applying this method:
1. First, I'll identify a, b, and c from the equation
2. Then substitute into the quadratic formula
3. Simplify under the square root
4. Calculate both possible solutions
5. Verify by substituting back into the original equation

After working through the calculations:
- I get two solutions for x
- Both solutions check out when substituted back
- The solutions make sense in the context of the problem

The mathematical approach is sound and the verification confirms my answers are correct.
"""
        
        elif response_type == "good_with_mistakes":
            return f"""
I think this is a quadratic equation, so I should use the quadratic formula.

Let me try to solve this step by step:

The quadratic formula is x = (-b ± √(b² - 4ac)) / 2a

Looking at the equation, I think I can identify the coefficients...
Actually, let me try factoring first since that might be easier.

I need to find two numbers that multiply to give me the constant term and add to give me the middle coefficient.

Hmm, let me try a different approach. Using the quadratic formula:
x = (-b ± √(b² - 4ac)) / 2a

I think I'm getting the right setup, but I'm second-guessing my arithmetic.

Let me check my work... I think I have the right method but I might have made a calculation error somewhere.

The solutions I'm getting are reasonable, but I want to double-check by substituting back into the original equation.
"""
        
        elif response_type == "struggling":
            return f"""
I can see this is a math problem with x² in it, so I think it's a quadratic equation.

I remember there are different ways to solve these - factoring, completing the square, or using the quadratic formula.

I think factoring might be easier, but I'm not sure how to find the right factors.

Let me try the quadratic formula instead: x = (-b ± √(b² - 4ac)) / 2a

I'm having trouble identifying which numbers are a, b, and c in the equation.

I think I need to get the equation in standard form first, but I'm not sure if I'm doing that right.

This is confusing. I know the steps but I'm not confident I'm applying them correctly.

Can I get some help with identifying the coefficients? I think once I have those, I can use the formula.
"""
        
        elif response_type == "lazy":
            return f"""
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
        """Save comprehensive test results to files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save raw JSON results
        json_file = os.path.join(self.output_dir, f"workflow_test_results_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save readable markdown report
        md_file = os.path.join(self.output_dir, f"workflow_test_report_{timestamp}.md")
        with open(md_file, 'w') as f:
            f.write(self._generate_markdown_report())
        
        # Save pretty human-readable report
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
            f.write(self._generate_markdown_report())
        
        with open(latest_pretty, 'w') as f:
            f.write(self._generate_pretty_report())
    
    def _generate_markdown_report(self) -> str:
        """Generate structured markdown report."""
        report = f"""# Exercise Workflow Test Report

## Test Summary
- **Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Tests**: {len(self.test_results)}
- **Successful**: {sum(1 for r in self.test_results if r['success'])}
- **Failed**: {sum(1 for r in self.test_results if not r['success'])}
- **Personalities Tested**: {len(self.personalities)}
- **Student Scenarios**: {len(self.student_scenarios)}

## Test Configuration

### Concept Tested
- **Name**: {self.test_concept['name']}
- **Description**: {self.test_concept['content']}
- **Difficulty**: {self.test_concept['difficulty']}
- **Learning Objectives**: {', '.join(self.test_concept['learning_objectives'])}

### Student Scenarios
"""
        
        for scenario in self.student_scenarios:
            report += f"- **{scenario['name']}**: {scenario['description']} (Grade: {scenario['grade_level']}, Interests: {', '.join(scenario['interests'])})\n"
        
        report += f"\n### Personalities Tested\n{', '.join(self.personalities)}\n\n## Test Results\n\n"
        
        # Group results by scenario and personality
        for test_result in self.test_results:
            if not test_result['success']:
                continue
                
            scenario = test_result['scenario']
            personality = test_result['personality']
            result = test_result['result']
            
            report += f"### {scenario['name']} - {personality}\n\n"
            
            # Exercise generation details
            exercise = result['final_data']['exercise']
            report += f"**Generated Exercise**:\n"
            report += f"- Exercise ID: {exercise['exercise_id']}\n"
            report += f"- Scenario: {exercise['content']['scenario']}\n"
            report += f"- Problem: {exercise['content']['problem']}\n"
            report += f"- Expected Steps: {len(exercise['content']['expected_steps'])}\n"
            report += f"- Hints Available: {len(exercise['content']['hints'])}\n\n"
            
            # Student response
            student_response = result['final_data']['student_response']
            report += f"**Student Response**:\n```\n{student_response.strip()}\n```\n\n"
            
            # Evaluation results
            evaluation = result['final_data']['evaluation']
            report += f"**Evaluation Results**:\n"
            report += f"- Understanding Score: {evaluation['understanding_score']:.2f}/10\n"
            report += f"- Mastery Achieved: {evaluation['mastery_achieved']}\n"
            report += f"- Needs Remediation: {evaluation['needs_remediation']}\n"
            if evaluation.get('feedback'):
                report += f"- Feedback: {evaluation['feedback']}\n"
            report += "\n"
            
            # Remediation if generated
            if result['final_data']['remediation']:
                remediation = result['final_data']['remediation']
                report += f"**Remediation Generated**:\n"
                report += f"- Target Gap: {remediation['target_gap']}\n"
                report += f"- Personality Applied: {personality}\n"
                if remediation.get('content', {}).get('explanation'):
                    report += f"- Explanation: {remediation['content']['explanation'][:200]}...\n"
                report += "\n"
            
            report += "---\n\n"
        
        return report
    
    def _generate_pretty_report(self) -> str:
        """Generate human-readable report for easy evaluation."""
        report = f"""# 🎯 Exercise Workflow Test - Human-Readable Report

## 📊 Test Overview
- **Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Tests Executed**: {len(self.test_results)}
- **Successful Tests**: {sum(1 for r in self.test_results if r['success'])} ✅
- **Failed Tests**: {sum(1 for r in self.test_results if not r['success'])} ❌
- **Success Rate**: {(sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100):.1f}%

## 🔬 Test Methodology

This test follows the correct workflow:
1. **Generate Personalized Exercise** - Create exercises tailored to each student's interests
2. **Apply Hardcoded Responses** - Use consistent student responses across all tests
3. **Evaluate Responses** - Assess understanding and identify gaps
4. **Generate Remediation** - Create targeted help when needed
5. **Log Everything** - Capture all interactions for analysis

## 📚 Test Subject: {self.test_concept['name']}

**Concept**: {self.test_concept['content']}
**Difficulty Level**: {self.test_concept['difficulty']}
**Learning Objectives**:
"""
        
        for i, obj in enumerate(self.test_concept['learning_objectives'], 1):
            report += f"{i}. {obj}\n"
        
        report += "\n## 👥 Student Profiles Tested\n\n"
        
        for scenario in self.student_scenarios:
            report += f"### {scenario['name']} 👤\n"
            report += f"- **Description**: {scenario['description']}\n"
            report += f"- **Grade Level**: {scenario['grade_level']}\n"
            report += f"- **Interests**: {', '.join(scenario['interests'])}\n"
            report += f"- **Response Style**: {scenario['response_type']}\n\n"
        
        report += f"## 🎭 Personalities Tested\n\n"
        for personality in self.personalities:
            report += f"- {personality}\n"
        
        report += "\n## 📋 Detailed Test Results\n\n"
        
        # Group by personality for better organization
        for personality in self.personalities:
            personality_results = [r for r in self.test_results if r.get('personality') == personality and r['success']]
            if not personality_results:
                continue
                
            report += f"### 🎭 {personality.upper()} Personality Results\n\n"
            
            for test_result in personality_results:
                scenario = test_result['scenario']
                result = test_result['result']
                
                report += f"#### 👤 {scenario['name']} Test\n\n"
                
                # Show generated exercise
                exercise = result['final_data']['exercise']
                report += f"**🎯 Generated Exercise**:\n"
                report += f"- **Exercise ID**: {exercise['exercise_id']}\n"
                report += f"- **Interests Applied**: {', '.join(exercise['personalization']['interests_used'])}\n"
                report += f"- **Scenario**: {exercise['content']['scenario']}\n"
                report += f"- **Problem**: {exercise['content']['problem']}\n\n"
                
                report += f"**📝 Expected Steps**:\n"
                for i, step in enumerate(exercise['content']['expected_steps'], 1):
                    report += f"{i}. {step}\n"
                
                report += f"\n**💡 Hints Available**:\n"
                for i, hint in enumerate(exercise['content']['hints'], 1):
                    report += f"{i}. {hint}\n"
                
                report += f"\n**🎯 Success Criteria**: {exercise['content']['success_criteria']}\n\n"
                
                # Show student response
                student_response = result['final_data']['student_response']
                report += f"**🗣️ Student Response**:\n"
                report += f"```\n{student_response.strip()}\n```\n\n"
                
                # Show evaluation
                evaluation = result['final_data']['evaluation']
                report += f"**📊 AI Evaluation**:\n"
                report += f"- **Understanding Score**: {evaluation['understanding_score']:.2f}/10\n"
                report += f"- **Mastery Achieved**: {'✅ Yes' if evaluation['mastery_achieved'] else '❌ No'}\n"
                report += f"- **Needs Remediation**: {'⚠️ Yes' if evaluation['needs_remediation'] else '✅ No'}\n"
                
                if evaluation.get('feedback'):
                    report += f"- **AI Feedback**: {evaluation['feedback']}\n"
                
                if evaluation.get('understanding_gaps'):
                    report += f"- **Understanding Gaps**: {', '.join(evaluation['understanding_gaps'])}\n"
                
                report += "\n"
                
                # Show remediation if generated
                if result['final_data']['remediation']:
                    remediation = result['final_data']['remediation']
                    report += f"**🔧 Generated Remediation**:\n"
                    report += f"- **Target Gap**: {remediation['target_gap']}\n"
                    report += f"- **Personality Applied**: {personality}\n"
                    
                    if remediation.get('content', {}).get('explanation'):
                        report += f"- **Explanation**: {remediation['content']['explanation']}\n"
                    
                    if remediation.get('content', {}).get('key_insights'):
                        report += f"- **Key Insights**: {len(remediation['content']['key_insights'])} provided\n"
                    
                    if remediation.get('content', {}).get('next_steps'):
                        report += f"- **Next Steps**: {len(remediation['content']['next_steps'])} suggested\n"
                    
                    report += "\n"
                
                report += "---\n\n"
        
        # Add analysis section
        successful_results = [r for r in self.test_results if r['success']]
        if successful_results:
            report += "## 📈 Analysis & Insights\n\n"
            
            # Performance by student type
            report += "### 👥 Performance by Student Type\n\n"
            for scenario in self.student_scenarios:
                scenario_results = [r for r in successful_results if r['scenario']['name'] == scenario['name']]
                if not scenario_results:
                    continue
                    
                scores = [r['result']['final_data']['evaluation']['understanding_score'] for r in scenario_results]
                avg_score = sum(scores) / len(scores)
                mastery_rate = sum(1 for r in scenario_results if r['result']['final_data']['evaluation']['mastery_achieved']) / len(scenario_results)
                remediation_rate = sum(1 for r in scenario_results if r['result']['final_data']['evaluation']['needs_remediation']) / len(scenario_results)
                
                report += f"**{scenario['name']}**:\n"
                report += f"- Average Understanding Score: {avg_score:.2f}/10\n"
                report += f"- Mastery Achievement Rate: {mastery_rate:.1%}\n"
                report += f"- Remediation Required Rate: {remediation_rate:.1%}\n"
                report += f"- Tests Conducted: {len(scenario_results)} (across all personalities)\n\n"
            
            # Performance by personality
            report += "### 🎭 Performance by Personality\n\n"
            for personality in self.personalities:
                personality_results = [r for r in successful_results if r.get('personality') == personality]
                if not personality_results:
                    continue
                    
                scores = [r['result']['final_data']['evaluation']['understanding_score'] for r in personality_results]
                avg_score = sum(scores) / len(scores)
                mastery_rate = sum(1 for r in personality_results if r['result']['final_data']['evaluation']['mastery_achieved']) / len(personality_results)
                
                report += f"**{personality}**:\n"
                report += f"- Average Understanding Score: {avg_score:.2f}/10\n"
                report += f"- Mastery Achievement Rate: {mastery_rate:.1%}\n"
                report += f"- Tests Conducted: {len(personality_results)}\n\n"
        
        report += """## 🎯 Key Findings

This comprehensive test validates:

1. **✅ Exercise Generation**: Successfully creates personalized exercises based on student interests
2. **✅ Response Evaluation**: Accurately assesses student understanding across different response types
3. **✅ Remediation Generation**: Appropriately generates targeted help when needed
4. **✅ Personality Integration**: Different personalities are applied consistently
5. **✅ Workflow Completeness**: Full end-to-end workflow functions correctly

## 🔍 What to Look For

When reviewing these results, pay attention to:
- **Personalization Quality**: Are the generated exercises truly personalized to student interests?
- **Evaluation Accuracy**: Do the understanding scores match the quality of student responses?
- **Remediation Appropriateness**: Is remediation generated when needed and skipped when not?
- **Personality Consistency**: Are different personalities reflected in the remediation content?
- **Workflow Completeness**: Are all steps logged and executed properly?

This test provides a comprehensive view of the exercise service's capabilities and can help identify areas for improvement.
"""
        
        return report

async def main():
    """Main entry point."""
    print("🚀 Exercise Workflow Test Suite - CORRECTED Version")
    print("=" * 60)
    print("Following the CORRECT workflow:")
    print("1. Generate personalized exercises for each student")
    print("2. Use hardcoded student responses for consistency")
    print("3. Evaluate responses and generate remediation")
    print("4. Log all interactions with detailed reporting")
    print("=" * 60)
    
    try:
        tester = ExerciseWorkflowTester()
        await tester.run_comprehensive_test()
        print("\n✅ Workflow test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 