#!/usr/bin/env python3
"""
Comprehensive Exercise Workflow Test with ChatAgent Integration

This script tests the complete exercise workflow through the ChatAgent endpoint:
1. Generate personalized exercises for students with specific interests
2. Use hardcoded student responses for consistent testing
3. Evaluate responses through the chat interface
4. Request remediation if needed
5. Log all interactions and generate detailed reports

Results are saved to detailed files for analysis.
"""

import sys
from pathlib import Path

# Add app directory to path before any app imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import argparse
import uuid
import httpx
import time
import subprocess
import signal

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Make sure OPENAI_API_KEY is set in environment.")

from app.models.chat import ChatRequest, ChatResponse

# Set default test environment variables
os.environ.setdefault("ENABLE_VECTOR_CONTEXT", "true")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("PINECONE_INDEX_NAME", "spool-content")
os.environ.setdefault("PINECONE_ENVIRONMENT", "us-east-1-aws")
os.environ.setdefault("CONTENT_SERVICE_SEARCH_URL", "http://localhost:8002/api/content/search")
os.environ.setdefault("MIN_RESPONSE_LENGTH", "20")

# ruff: noqa: E402
# Import the exercise service components
from app.models.exercise import (
    LifeCategory,
    DifficultyLevel,
    ExerciseType,
)

# Setup basic logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExerciseWorkflowTester:
    """Comprehensive workflow tester using ChatAgent endpoint."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        # Verify API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("test"):
            raise ValueError("Valid OpenAI API key required. Set OPENAI_API_KEY in .env file")

        self.base_url = base_url.rstrip('/')
        self.chat_endpoint = f"{self.base_url}/api/chat"  # Add /api prefix for FastAPI endpoints
        self.test_results = []
        self.output_dir = "test_results"
        self.mock_service_process = None

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize mock content service
        self._setup_mock_content_service()

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

        # Student scenarios with different interests
        self.student_scenarios = [
            {
                "name": "Perfect Student",
                "description": "Student who succeeds flawlessly",
                "student_id": "perfect_student_001",
                "interests": ["sports", "music", "technology"],
                "grade_level": "high school",
                "response_type": "perfect",
                "personality_type": "enthusiastic-coach"
            },
            {
                "name": "Good Student",
                "description": "Student with good understanding but makes mistakes",
                "student_id": "good_student_002",
                "interests": ["art", "science", "gaming"],
                "grade_level": "high school",
                "response_type": "good_with_mistakes",
                "personality_type": "empathetic-supporter"
            },
            {
                "name": "Struggling Student",
                "description": "Student who struggles but is trying",
                "student_id": "struggling_student_003",
                "interests": ["animals", "cooking", "social media"],
                "grade_level": "middle school",
                "response_type": "struggling",
                "personality_type": "wise-mentor"
            },
            {
                "name": "Lazy Student",
                "description": "Student who doesn't try and just wants answers",
                "student_id": "lazy_student_004",
                "interests": ["gaming", "movies", "social media"],
                "grade_level": "high school",
                "response_type": "lazy",
                "personality_type": "strategic-challenger"
            },
        ]

        # Update student profiles with consistent session IDs
        for scenario in self.student_scenarios:
            scenario["session_id"] = str(uuid.uuid4())

    async def send_chat_request(
        self, 
        session_id: str, 
        message: str = "", 
        action: Optional[str] = None,
        student_profile: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> ChatResponse:
        """Send a chat request to the ChatAgent endpoint with retries for transient errors."""
        request = ChatRequest(
            session_id=session_id,
            message=message,
            action=action,
            student_profile=student_profile or {}
        )

        last_error = None
        max_retries = 3
        backoff_factor = 1.5

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.chat_endpoint,
                        json=request.model_dump(),  # Use model_dump() instead of dict() for Pydantic v2
                        timeout=timeout * (backoff_factor ** attempt)  # Increase timeout with each retry
                    )
                    response.raise_for_status()
                    return ChatResponse(**response.json())
            
            except httpx.ReadTimeout as e:
                last_error = f"Request timed out after {timeout * (backoff_factor ** attempt):.1f}s"
                if attempt < max_retries - 1:
                    await asyncio.sleep(attempt * backoff_factor)  # Exponential backoff
                    continue
                raise Exception(f"Chat request failed after {max_retries} attempts: {last_error}") from e
            
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code if e.response else "unknown"
                last_error = f"HTTP error {status_code}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(attempt * backoff_factor)
                    continue
                raise Exception(f"Chat request failed after {max_retries} attempts: {last_error}") from e
            
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(attempt * backoff_factor)
                    continue
                raise Exception(f"Chat request failed after {max_retries} attempts: {last_error}") from e
        
        # If we get here without returning, all retries failed
        raise Exception(f"Chat request failed after {max_retries} attempts: {last_error}")

    # Setup mock content service
    def _setup_mock_content_service(self):
        """Start the mock content service for testing."""
        print("\n🚀 Starting Mock Content Service for Pinecone Integration Testing...")
        
        # Check if service is already running
        if self._is_service_running():
            print("   ✅ Mock content service already running")
            return
        
        try:
            # Start the mock content service
            script_path = Path(__file__).parent / "mock_content_service.py"
            self.mock_service_process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            print("   ⏳ Waiting for mock content service to start...")
            max_attempts = 10
            for attempt in range(max_attempts):
                if self._is_service_running():
                    print("   ✅ Mock content service started successfully!")
                    return
                time.sleep(1)
            
            # If we get here, service failed to start
            if self.mock_service_process.poll() is not None:
                stdout, stderr = self.mock_service_process.communicate()
                print(f"   ❌ Mock service failed to start:")
                print(f"      stdout: {stdout}")
                print(f"      stderr: {stderr}")
            else:
                print("   ❌ Mock service took too long to start")
                self._cleanup_mock_service()
            
        except Exception as e:
            print(f"   ❌ Failed to start mock content service: {str(e)}")
            self._cleanup_mock_service()

    def _is_service_running(self) -> bool:
        """Check if the mock content service is running."""
        try:
            import httpx
            response = httpx.get("http://localhost:8002/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def _cleanup_mock_service(self):
        """Clean up the mock content service."""
        if self.mock_service_process:
            try:
                print("\n🧹 Cleaning up mock content service...")
                self.mock_service_process.terminate()
                try:
                    self.mock_service_process.wait(timeout=5)
                    print("   ✅ Mock service stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("   ⚠️  Forcing mock service shutdown...")
                    self.mock_service_process.kill()
                    self.mock_service_process.wait()
                    print("   ✅ Mock service force stopped")
            except Exception as e:
                print(f"   ⚠️  Error stopping mock service: {str(e)}")
            finally:
                self.mock_service_process = None

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self._cleanup_mock_service()

    async def run_comprehensive_test(self, quick_mode: bool = False):
        """Run comprehensive test using the ChatAgent endpoint with parallel execution."""
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)

        if quick_mode:
            print("🔬 QUICK MODE: Testing one student")
            test_scenarios = [self.student_scenarios[0]]  # Just perfect student
        else:
            print("🔄 FULL MODE: Testing all scenarios in parallel")
            test_scenarios = self.student_scenarios

        print("\nFollowing the ChatAgent workflow:")
        print("1. Generate personalized exercises")
        print("2. Submit hardcoded student responses")
        print("3. Evaluate responses through chat")
        print("4. Request remediation if needed")
        print("5. Log all interactions")
        print("=" * 60)

        start_time = datetime.utcnow()

        # Run all scenario tests in parallel
        tasks = [self._run_single_test(scenario) for scenario in test_scenarios]
        results = await asyncio.gather(*tasks)

        # Process results
        for scenario, result in zip(test_scenarios, results):
            try:
                self.test_results.append({
                    "scenario": scenario,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True
                })
                print(f"✅ {scenario['name']} completed successfully")

            except Exception as e:
                error_result = {
                    "error": str(e),
                    "scenario_name": scenario["name"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.test_results.append({
                    "scenario": scenario,
                    "result": error_result,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False
                })
                print(f"❌ {scenario['name']} failed: {str(e)}")
                logger.error("Scenario failed", 
                    extra={
                        "scenario": scenario["name"],
                        "error": str(e)
                    }
                )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n🏁 All Tests Completed in {duration:.2f} seconds")
        print(f"✅ Successful: {sum(1 for r in self.test_results if r['success'])}")
        print(f"❌ Failed: {sum(1 for r in self.test_results if not r['success'])}")

        await self._save_comprehensive_results()
        
        print(f"\n📁 Results saved to '{self.output_dir}' directory")
        print("📊 Check workflow_test_results_YYYYMMDD_HHMMSS.json for detailed data")
        print("📖 Check workflow_test_report_YYYYMMDD_HHMMSS.md for analysis report")
        
        # Clean up mock service
        self._cleanup_mock_service()

    async def _run_single_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test through the ChatAgent workflow with retries."""
        session_id = scenario["session_id"]
        student_profile = {
            "student_id": scenario["student_id"],
            "interests": scenario["interests"],
            "grade_level": scenario["grade_level"],
            "personality_type": scenario["personality_type"]
        }

        print(f"\n🎯 Testing {scenario['name']}...")
        
        # Step 1: Generate exercise with retry
        exercise_data = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   1️⃣ Generating personalized exercise (attempt {attempt + 1})...")
                exercise_response = await self.send_chat_request(
                    session_id=session_id,
                    action="generate_exercise",
                    student_profile=student_profile
                )
                exercise_data = exercise_response.data
                if not exercise_data:
                    raise ValueError("No exercise data received from server")
                print(f"      ✅ Exercise generated")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"      ⚠️ Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)  # Brief delay before retry
        
        if not exercise_data:
            raise Exception("Failed to generate exercise after all retries")

        # Step 2: Submit hardcoded response
        print(f"   2️⃣ Submitting {scenario['response_type']} response...")
        hardcoded_response = self._generate_hardcoded_response(
            exercise_data.get("exercise", {}),
            scenario["response_type"]
        )
        
        evaluation_response = await self.send_chat_request(
            session_id=session_id,
            message=hardcoded_response,
            action="submit_answer"
        )
        
        evaluation_data = evaluation_response.data
        print(f"      ✅ Response evaluated")

        # Step 3: Request remediation if needed
        remediation_data = None
        if "request_remediation" in evaluation_response.available_actions:
            print("   3️⃣ Requesting remediation...")
            remediation_response = await self.send_chat_request(
                session_id=session_id,
                action="request_remediation"
            )
            
            remediation_data = remediation_response.data
            print(f"      ✅ Remediation generated")
        else:
            print("   3️⃣ No remediation needed!")

        # Compile test results
        result = {
            "scenario_name": scenario["name"],
            "session_id": session_id,
            "student_profile": student_profile,
            "workflow_data": {
                "exercise": exercise_data,
                "student_response": hardcoded_response,
                "evaluation": evaluation_data,
                "remediation": remediation_data
            },
            "test_details": {
                "response_type": scenario["response_type"],
                "remediation_requested": remediation_data is not None
            },
            "workflow_completed": True,
            "total_steps": 3 if not remediation_data else 4,
            "test_timestamp": datetime.utcnow().isoformat()
        }

        return result

    def _generate_hardcoded_response(
        self, exercise: Dict[str, Any], response_type: str
    ) -> str:
        """Generate hardcoded student responses that work with any generated exercise."""

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

I'm not sure if this is right though, and I don't know how to check my work.
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
        """Save comprehensive test results to timestamped files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Save raw JSON results
        json_file = os.path.join(self.output_dir, f"workflow_test_results_{timestamp}.json")
        with open(json_file, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        # Save comprehensive markdown report
        md_file = os.path.join(self.output_dir, f"workflow_test_report_{timestamp}.md")
        report = self._generate_comprehensive_report()
        with open(md_file, "w") as f:
            f.write(report)

    def _generate_comprehensive_report(self) -> str:
        """Generate a comprehensive markdown report of test results."""
        successful_results = [r for r in self.test_results if r["success"]]

        report = f"""# 🎯 Exercise Workflow Test - Comprehensive Report

## 📊 Executive Summary
- **Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Total Tests Executed**: {len(self.test_results)}
- **Successful Tests**: {len(successful_results)} ✅
- **Failed Tests**: {len(self.test_results) - len(successful_results)} ❌
- **Success Rate**: {(len(successful_results) / len(self.test_results) * 100):.1f}%
- **Student Types**: {len(set(r['scenario']['name'] for r in self.test_results if r.get('scenario')))}

## 🔬 Test Methodology

This test follows the ChatAgent workflow:
1. **Generate Personalized Exercise** - Create exercises tailored to each student's interests
2. **Submit Student Response** - Use consistent hardcoded responses across all tests
3. **Evaluate Response** - Assess understanding through the chat interface
4. **Generate Remediation** - Create targeted help when needed through chat
5. **Log Everything** - Capture all interactions for analysis

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
            report += f"- **Response Type**: {scenario['response_type']}\n"
            report += f"- **Personality**: {scenario['personality_type']}\n\n"

        # Add performance analysis
        report += "\n## 📈 Performance Analysis\n\n"

        # Performance by student type
        report += "### 👥 Performance by Student Type\n\n"
        for scenario in self.student_scenarios:
            scenario_results = [
                r for r in successful_results
                if r["scenario"]["name"] == scenario["name"]
            ]
            if not scenario_results:
                continue

            report += f"**{scenario['name']}**:\n"
            report += f"- Tests Completed Successfully: {len(scenario_results)}\n"
            report += f"- Response Type: {scenario['response_type']}\n"
            
            remediation_count = sum(
                1 for r in scenario_results
                if r["result"]["workflow_data"]["remediation"] is not None
            )
            report += f"- Remediation Required: {remediation_count}/{len(scenario_results)}\n\n"

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test complete exercise workflow with ChatAgent"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with one student",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the exercise service API",
    )

    args = parser.parse_args()

    # Run tests
    try:
        tester = ExerciseWorkflowTester(base_url=args.base_url)
        asyncio.run(tester.run_comprehensive_test(quick_mode=args.quick))
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
