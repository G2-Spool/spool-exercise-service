#!/usr/bin/env python3
"""
Mock Services for Exercise Service Testing

This script provides mock services that can be used during testing:
- Mock Content Service (port 8001)
- Mock Simple Server (port 8003)
- Health check endpoints
- Basic API simulation

Use this when you need to test the exercise service without running full dependencies.
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime


class MockServices:
    """Mock services for testing."""

    def __init__(self) -> None:
        self.content_app = self._create_content_service()
        self.simple_app = self._create_simple_service()

    def _create_content_service(self) -> FastAPI:
        """Create mock content service."""
        app = FastAPI(title="Mock Content Service", version="1.0.0")

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "mock-content-service",
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.get("/api/content/concepts/{concept_id}")
        async def get_concept(concept_id: str):
            """Get concept information."""
            # Mock concept data
            mock_concepts = {
                "quadratic_equations_001": {
                    "concept_id": concept_id,
                    "name": "Quadratic Equations",
                    "description": "Solving equations of the form ax² + bx + c = 0",
                    "content": "Quadratic equations are polynomial equations of degree 2. They can be solved using factoring, completing the square, or the quadratic formula.",
                    "learning_objectives": [
                        "Understand the standard form of quadratic equations",
                        "Apply factoring method to solve quadratic equations",
                        "Use the quadratic formula when factoring is not possible",
                        "Verify solutions by substitution",
                    ],
                    "examples": [
                        {
                            "equation": "x² + 5x + 6 = 0",
                            "solution": "x = -2 or x = -3",
                            "method": "factoring",
                        },
                        {
                            "equation": "2x² - 7x + 3 = 0",
                            "solution": "x = 3 or x = 1/2",
                            "method": "factoring",
                        },
                    ],
                    "difficulty": "intermediate",
                    "prerequisites": ["linear_equations", "basic_algebra"],
                },
                "linear_equations": {
                    "concept_id": concept_id,
                    "name": "Linear Equations",
                    "description": "Solving equations of the form ax + b = 0",
                    "content": "Linear equations are first-degree polynomial equations with one variable.",
                    "learning_objectives": [
                        "Understand linear equations",
                        "Solve linear equations using algebraic methods",
                        "Apply linear equations to real-world problems",
                    ],
                    "examples": [
                        {
                            "equation": "2x + 3 = 7",
                            "solution": "x = 2",
                            "method": "algebraic",
                        }
                    ],
                    "difficulty": "basic",
                    "prerequisites": ["basic_algebra"],
                },
            }

            if concept_id in mock_concepts:
                return mock_concepts[concept_id]
            else:
                # Return generic concept for unknown IDs
                return {
                    "concept_id": concept_id,
                    "name": f"Concept {concept_id}",
                    "description": f"Mock concept for {concept_id}",
                    "content": f"This is a mock concept for testing purposes: {concept_id}",
                    "learning_objectives": [
                        "Understand the concept",
                        "Apply the concept to problems",
                        "Verify understanding",
                    ],
                    "examples": [
                        {
                            "problem": "Example problem",
                            "solution": "Example solution",
                            "method": "example method",
                        }
                    ],
                    "difficulty": "intermediate",
                    "prerequisites": ["basic_knowledge"],
                }

        @app.post("/api/content/search")
        async def search_content(query: Dict[str, Any]):
            """Mock content search endpoint."""
            search_query = query.get("query", "")
            limit = query.get("limit", 5)

            # Mock search results
            mock_results = [
                {
                    "content_id": "mock_content_1",
                    "title": f"Mock Content for: {search_query}",
                    "content": f"This is mock content related to {search_query}. It provides educational context and examples.",
                    "relevance_score": 0.85,
                    "content_type": "educational_material",
                    "source": "Mock Textbook",
                    "subject": "Mathematics",
                    "chapter": "Chapter 1",
                },
                {
                    "content_id": "mock_content_2",
                    "title": f"Additional Context for: {search_query}",
                    "content": f"More detailed information about {search_query} with practical examples and applications.",
                    "relevance_score": 0.78,
                    "content_type": "educational_material",
                    "source": "Mock Textbook",
                    "subject": "Mathematics",
                    "chapter": "Chapter 2",
                },
            ]

            return {
                "query": search_query,
                "results": mock_results[:limit],
                "total_results": len(mock_results),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.get("/api/content/vector-search")
        async def vector_search(concept: str, interests: str = "", limit: int = 3):
            """Mock vector search endpoint."""
            # Mock vector search results
            mock_results = [
                {
                    "chunk_id": "chunk_1",
                    "content": f"Educational content about {concept} with practical applications in {interests}",
                    "score": 0.92,
                    "metadata": {
                        "book": "Advanced Mathematics",
                        "subject": "Mathematics",
                        "chapter": "Quadratic Equations",
                        "page": 145,
                    },
                },
                {
                    "chunk_id": "chunk_2",
                    "content": f"Additional examples and explanations for {concept}",
                    "score": 0.87,
                    "metadata": {
                        "book": "Math Fundamentals",
                        "subject": "Mathematics",
                        "chapter": "Algebraic Methods",
                        "page": 67,
                    },
                },
            ]

            return {
                "concept": concept,
                "interests": interests,
                "results": mock_results[:limit],
                "total_results": len(mock_results),
                "timestamp": datetime.utcnow().isoformat(),
            }

        return app

    def _create_simple_service(self) -> FastAPI:
        """Create simple mock exercise service."""
        app = FastAPI(title="Mock Exercise Service", version="1.0.0")

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        async def root():
            return {
                "message": "Mock Exercise Service is running",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "mock-exercise-service",
            }

        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "mock-exercise-service",
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.post("/api/exercise/generate")
        async def generate_exercise(request: Dict[str, Any]):
            """Mock exercise generation endpoint."""
            concept_id = request.get("concept_id", "unknown")
            student_id = request.get("student_id", "unknown")
            interests = request.get("student_interests", [])

            # Mock exercise response
            mock_exercise = {
                "exercise_id": f"mock_exercise_{concept_id}_{student_id}",
                "concept_id": concept_id,
                "student_id": student_id,
                "content": {
                    "scenario": f"Mock scenario incorporating {', '.join(interests[:2])}",
                    "problem": f"Mock problem for {concept_id}",
                    "instructions": "Solve this mock problem step by step",
                    "expected_steps": [
                        "Step 1: Identify the problem type",
                        "Step 2: Apply the appropriate method",
                        "Step 3: Solve systematically",
                        "Step 4: Verify the solution",
                    ],
                },
                "difficulty": request.get("difficulty", "basic"),
                "life_category": request.get("life_category", "academic"),
                "personalization": {
                    "interests_used": interests[:2],
                    "context": "Mock personalized context",
                },
                "created_at": datetime.utcnow().isoformat(),
            }

            return mock_exercise

        @app.post("/api/exercise/evaluate")
        async def evaluate_response(request: Dict[str, Any]):
            """Mock response evaluation endpoint."""
            exercise_id = request.get("exercise_id", "unknown")
            student_response = request.get("student_response", "")

            # Mock evaluation based on response length and content
            response_length = len(student_response)
            has_keywords = any(
                keyword in student_response.lower()
                for keyword in ["formula", "solve", "equation", "steps"]
            )

            if response_length < 50:
                understanding_score = 0.3
                mastery_achieved = False
            elif response_length < 100:
                understanding_score = 0.6
                mastery_achieved = False
            else:
                understanding_score = 0.8 if has_keywords else 0.5
                mastery_achieved = understanding_score >= 0.8

            mock_evaluation = {
                "evaluation_id": f"mock_eval_{exercise_id}",
                "exercise_id": exercise_id,
                "understanding_score": understanding_score,
                "mastery_achieved": mastery_achieved,
                "needs_remediation": not mastery_achieved,
                "feedback": "Mock feedback based on response analysis",
                "competency_map": {
                    "correct_steps": ["Step 1", "Step 2"] if has_keywords else [],
                    "missing_steps": (
                        ["Step 3", "Step 4"] if not mastery_achieved else []
                    ),
                    "incorrect_steps": [],
                },
                "evaluated_at": datetime.utcnow().isoformat(),
            }

            return mock_evaluation

        return app


async def run_content_service() -> None:
    """Run mock content service."""
    print("🚀 Starting Mock Content Service on port 8001...")
    mock_services = MockServices()

    config = uvicorn.Config(
        app=mock_services.content_app, host="0.0.0.0", port=8001, log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_simple_service() -> None:
    """Run mock simple exercise service."""
    print("🚀 Starting Mock Exercise Service on port 8003...")
    mock_services = MockServices()

    config = uvicorn.Config(
        app=mock_services.simple_app, host="0.0.0.0", port=8003, log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_both_services() -> None:
    """Run both mock services concurrently."""
    print("🚀 Starting Both Mock Services...")
    print("   📡 Mock Content Service on port 8001")
    print("   🎯 Mock Exercise Service on port 8003")

    mock_services = MockServices()

    # Create server configs
    content_config = uvicorn.Config(
        app=mock_services.content_app, host="0.0.0.0", port=8001, log_level="info"
    )

    simple_config = uvicorn.Config(
        app=mock_services.simple_app, host="0.0.0.0", port=8003, log_level="info"
    )

    # Run both servers concurrently
    content_server = uvicorn.Server(content_config)
    simple_server = uvicorn.Server(simple_config)

    await asyncio.gather(content_server.serve(), simple_server.serve())


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        service_type = sys.argv[1].lower()

        if service_type == "content":
            asyncio.run(run_content_service())
        elif service_type == "simple":
            asyncio.run(run_simple_service())
        elif service_type == "both":
            asyncio.run(run_both_services())
        else:
            print("Usage: python mock_services.py [content|simple|both]")
            print("  content - Run mock content service on port 8001")
            print("  simple  - Run mock exercise service on port 8003")
            print("  both    - Run both services concurrently")
            sys.exit(1)
    else:
        # Default: run both services
        asyncio.run(run_both_services())


if __name__ == "__main__":
    main()
