#!/usr/bin/env python3
"""
Comprehensive System Test for Exercise Service

This script consolidates all basic system tests including:
- API setup and configuration verification
- Import testing for all dependencies
- Basic functionality testing
- Environment validation
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)


class SystemTester:
    """Comprehensive system testing suite."""

    def __init__(self) -> None:
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    def log_test(self, test_name: str, success: bool, message: str = "") -> None:
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")

        self.test_results.append(
            {"test": test_name, "success": success, "message": message}
        )

        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    async def test_environment_setup(self):
        """Test environment variables and configuration."""
        print("\n🔧 Testing Environment Setup")
        print("=" * 40)

        # Test critical environment variables
        required_vars = [
            ("OPENAI_API_KEY", "OpenAI API Key"),
            ("PINECONE_API_KEY", "Pinecone API Key"),
            ("PINECONE_INDEX_NAME", "Pinecone Index Name"),
        ]

        for var_name, description in required_vars:
            value = os.getenv(var_name)
            if not value:
                self.log_test(
                    f"Environment: {description}", False, f"{var_name} not set"
                )
            elif value.startswith("test") or "placeholder" in value:
                self.log_test(
                    f"Environment: {description}",
                    False,
                    f"{var_name} appears to be placeholder",
                )
            else:
                self.log_test(
                    f"Environment: {description}",
                    True,
                    f"***{value[-4:] if len(value) > 4 else '***'}",
                )

        # Test optional variables
        optional_vars = [
            ("REDIS_URL", "Redis URL"),
            ("CONTENT_SERVICE_URL", "Content Service URL"),
            ("ENVIRONMENT", "Environment"),
        ]

        for var_name, description in optional_vars:
            value = os.getenv(var_name)
            self.log_test(f"Optional: {description}", True, value or "Using default")

    async def test_imports(self):
        """Test all critical imports."""
        print("\n📦 Testing Imports")
        print("=" * 40)

        # Test core dependencies
        core_imports = [
            ("asyncio", "Async I/O"),
            ("json", "JSON handling"),
            ("os", "Operating system interface"),
            ("uuid", "UUID generation"),
            ("datetime", "Date and time utilities"),
        ]

        for module, description in core_imports:
            try:
                __import__(module)
                self.log_test(f"Core Import: {description}", True)
            except ImportError as e:
                self.log_test(f"Core Import: {description}", False, str(e))

        # Test external dependencies
        external_imports = [
            ("fastapi", "FastAPI framework"),
            ("openai", "OpenAI client"),
            ("pinecone", "Pinecone client"),
            ("dotenv", "Environment variables"),
            ("httpx", "HTTP client"),
            ("structlog", "Structured logging"),
        ]

        for module, description in external_imports:
            try:
                __import__(module)
                self.log_test(f"External Import: {description}", True)
            except ImportError as e:
                self.log_test(f"External Import: {description}", False, str(e))

        # Test LangGraph imports
        langgraph_imports = [
            ("langgraph.graph", "StateGraph"),
            ("langgraph.constants", "Constants"),
            ("langgraph.checkpoint.memory", "Memory"),
        ]

        for module, description in langgraph_imports:
            try:
                __import__(module)
                self.log_test(f"LangGraph Import: {description}", True)
            except ImportError as e:
                self.log_test(f"LangGraph Import: {description}", False, str(e))

    async def test_api_connections(self):
        """Test API connections."""
        print("\n🌐 Testing API Connections")
        print("=" * 40)

        # Test OpenAI API
        try:
            from openai import AsyncOpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key.startswith("test"):
                self.log_test("OpenAI API Connection", False, "No valid API key")
            else:
                client = AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test connection"}],
                    max_tokens=5,
                )
                self.log_test(
                    "OpenAI API Connection",
                    True,
                    f"Response: {response.choices[0].message.content}",
                )
        except Exception as e:
            self.log_test("OpenAI API Connection", False, str(e))

        # Test Pinecone API
        try:
            from pinecone import Pinecone

            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                self.log_test("Pinecone API Connection", False, "No API key")
            else:
                pc = Pinecone(api_key=api_key)
                indexes = pc.list_indexes()
                self.log_test(
                    "Pinecone API Connection", True, f"Found {len(indexes)} indexes"
                )
        except Exception as e:
            self.log_test("Pinecone API Connection", False, str(e))

    async def test_service_imports(self):
        """Test service-specific imports."""
        print("\n🔧 Testing Service Imports")
        print("=" * 40)

        # Add app directory to path
        app_path = Path(__file__).parent.parent / "app"
        sys.path.insert(0, str(app_path))

        service_imports = [
            ("app.core.config", "Configuration"),
            ("app.models.exercise", "Exercise Models"),
            ("app.generators.exercise_generator", "Exercise Generator"),
            ("app.evaluators.response_evaluator", "Response Evaluator"),
            ("app.remediation.remediation_generator", "Remediation Generator"),
            ("app.services.pinecone_service", "Pinecone Service"),
        ]

        for module, description in service_imports:
            try:
                __import__(module)
                self.log_test(f"Service Import: {description}", True)
            except ImportError as e:
                self.log_test(f"Service Import: {description}", False, str(e))

    async def run_all_tests(self):
        """Run all system tests."""
        print("🚀 Exercise Service System Test Suite")
        print("=" * 50)

        await self.test_environment_setup()
        await self.test_imports()
        await self.test_api_connections()
        await self.test_service_imports()

        print("\n📊 Test Results Summary")
        print("=" * 30)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(
            f"📈 Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%"
        )

        if self.failed_tests > 0:
            print(
                f"\n⚠️  {self.failed_tests} tests failed. Please address these issues before proceeding."
            )
            return False
        else:
            print("\n🎉 All tests passed! System is ready for operation.")
            return True


async def main() -> None:
    """Main entry point."""
    tester = SystemTester()
    success = await tester.run_all_tests()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
