#!/usr/bin/env python3
"""
Mock Content Service for Testing

This script creates a simple mock content service that returns realistic 
vector search results for testing the Pinecone integration in the exercise workflow.
"""

import json
from typing import Dict, List, Any
import asyncio
from datetime import datetime

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available - mock content service disabled")

# Mock educational content chunks
MOCK_CONTENT_CHUNKS = [
    {
        "concept_id": "linear_systems_001",
        "content": "A system of linear equations consists of two or more linear equations with the same variables. The goal is to find a common solution that satisfies all equations simultaneously. These systems are crucial for modeling real-world problems in fields like economics, engineering, and computer science.",
        "score": 0.95,
        "book": "Linear Algebra Essentials",
        "subject": "Mathematics",
        "concept_name": "Introduction to Systems of Linear Equations",
        "concept_type": "explanation",
        "chapter_title": "Linear Systems",
        "section_title": "Core Concepts"
    },
    {
        "concept_id": "linear_systems_002",
        "content": "There are three primary methods for solving systems of linear equations: substitution, elimination, and graphing. The substitution method involves solving one equation for one variable and substituting that expression into the other equation. The elimination method involves adding or subtracting the equations to eliminate one variable.",
        "score": 0.92,
        "book": "Linear Algebra Problem Solving",
        "subject": "Mathematics",
        "concept_name": "Methods for Solving Linear Systems",
        "concept_type": "explanation",
        "chapter_title": "Solving Systems",
        "section_title": "Substitution and Elimination"
    },
    {
        "concept_id": "linear_systems_sports_001",
        "content": "In sports analytics, systems of linear equations are used to model team performance and player statistics. For example, you could create a system to determine how many 2-point and 3-point shots a basketball team made based on their total shots and total points.",
        "score": 0.89,
        "book": "Mathematics in Sports",
        "subject": "Applied Mathematics",
        "concept_name": "Sports Analytics with Linear Systems",
        "concept_type": "application",
        "chapter_title": "Statistical Modeling",
        "section_title": "Performance Metrics"
    },
    {
        "concept_id": "linear_systems_example_001",
        "content": "Example: Solve the system: 1) x + y = 10, 2) x - y = 4. Using elimination, add the two equations: (x + y) + (x - y) = 10 + 4, which simplifies to 2x = 14, so x = 7. Substitute x = 7 into the first equation: 7 + y = 10, which gives y = 3. The solution is (7, 3).",
        "score": 0.94,
        "book": "Step-by-Step Linear Algebra",
        "subject": "Mathematics",
        "concept_name": "Solving a Linear System by Elimination",
        "concept_type": "example",
        "chapter_title": "Worked Examples",
        "section_title": "Elimination Method Practice"
    }
]

# Mock remediation examples
MOCK_REMEDIATION_EXAMPLES = [
    {
        "concept_id": "remediation_linear_systems_001",
        "content": "When students struggle with systems of linear equations, it's often due to calculation errors or choosing the wrong method. Encourage them to check their work by substituting the final x and y values back into both original equations. Visualizing the problem by graphing the lines can also help build intuition.",
        "score": 0.96,
        "book": "Teaching Linear Algebra",
        "subject": "Mathematical Pedagogy",
        "concept_name": "Teaching Strategies for Linear Systems",
        "concept_type": "explanation",
        "chapter_title": "Common Student Difficulties",
        "section_title": "Verification and Visualization"
    }
]

def create_mock_app():
    """Create a mock FastAPI application."""
    if not FASTAPI_AVAILABLE:
        return None
    
    app = FastAPI(title="Mock Content Service", version="1.0.0")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "mock-content-service"}
    
    @app.post("/api/content/search")
    async def search_content(request: Request):
        """Mock content search endpoint."""
        try:
            body = await request.json()
            query = body.get("query", "")
            limit = body.get("limit", 3)
            
            print(f"🔍 Mock Content Service: Searching for '{query}' (limit: {limit})")
            
            # Select appropriate mock content based on query
            if "remediation" in query.lower() or "examples" in query.lower():
                results = MOCK_REMEDIATION_EXAMPLES
            else:
                results = MOCK_CONTENT_CHUNKS
            
            print(f"✅ Mock Content Service: Returning {len(results)} results")
            
            return results[:limit]
            
        except Exception as e:
            print(f"❌ Mock Content Service Error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Search failed", "detail": str(e)}
            )
    
    return app

async def run_mock_server():
    """Run the mock content service."""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available - cannot run mock content service")
        return
    
    print("🚀 Starting Mock Content Service on http://localhost:8002")
    print("   This will provide realistic vector search results for testing")
    print("   Press Ctrl+C to stop")
    
    app = create_mock_app()
    if app:
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8002,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    else:
        print("❌ Mock app could not be created. Shutting down.")

if __name__ == "__main__":
    asyncio.run(run_mock_server()) 