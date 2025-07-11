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
        "concept_id": "quadratic_001",
        "content": "Quadratic equations are polynomial equations of degree 2. They have the general form ax² + bx + c = 0 where a ≠ 0. These equations are fundamental in algebra and appear frequently in physics, engineering, and other mathematical applications.",
        "score": 0.95,
        "book": "Algebra Fundamentals",
        "subject": "Mathematics",
        "concept_name": "Quadratic Equations Basics",
        "concept_type": "explanation",
        "chapter_title": "Polynomial Equations",
        "section_title": "Introduction to Quadratic Equations"
    },
    {
        "concept_id": "quadratic_002", 
        "content": "To solve quadratic equations, we can use several methods: factoring, completing the square, or the quadratic formula. The quadratic formula x = (-b ± √(b² - 4ac)) / 2a works for all quadratic equations and is especially useful when factoring is difficult.",
        "score": 0.92,
        "book": "Algebra Problem Solving",
        "subject": "Mathematics", 
        "concept_name": "Quadratic Solution Methods",
        "concept_type": "explanation",
        "chapter_title": "Solving Equations",
        "section_title": "Quadratic Formula"
    },
    {
        "concept_id": "quadratic_sports_001",
        "content": "Quadratic equations model projectile motion in sports. When a basketball player shoots a free throw, the ball follows a parabolic path described by a quadratic equation. The trajectory depends on initial velocity, angle, and gravity.",
        "score": 0.89,
        "book": "Mathematics in Sports",
        "subject": "Applied Mathematics",
        "concept_name": "Projectile Motion in Sports",
        "concept_type": "application",
        "chapter_title": "Physics of Sports",
        "section_title": "Ball Trajectories"
    },
    {
        "concept_id": "quadratic_music_001",
        "content": "Musical acoustics uses quadratic equations to model sound wave interactions and resonance frequencies. When designing concert halls or audio equipment, engineers use quadratic relationships to optimize sound quality and minimize distortion.",
        "score": 0.87,
        "book": "Mathematical Music Theory",
        "subject": "Applied Mathematics",
        "concept_name": "Sound Wave Mathematics",
        "concept_type": "application", 
        "chapter_title": "Acoustic Engineering",
        "section_title": "Resonance and Frequency"
    },
    {
        "concept_id": "quadratic_technology_001",
        "content": "In computer graphics and game development, quadratic equations are used for collision detection, curve rendering, and physics simulations. Bezier curves, which are quadratic functions, create smooth animations and realistic movement patterns.",
        "score": 0.85,
        "book": "Mathematics in Computer Science",
        "subject": "Computational Mathematics",
        "concept_name": "Quadratic Functions in Graphics",
        "concept_type": "application",
        "chapter_title": "Computer Graphics Math",
        "section_title": "Curves and Collisions"
    },
    {
        "concept_id": "quadratic_example_001",
        "content": "Example: Solve x² + 5x + 6 = 0. We can factor this as (x + 2)(x + 3) = 0, giving us solutions x = -2 and x = -3. We can verify by substituting back: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0 ✓",
        "score": 0.94,
        "book": "Step-by-Step Algebra",
        "subject": "Mathematics",
        "concept_name": "Quadratic Factoring Example",
        "concept_type": "example",
        "chapter_title": "Worked Examples",
        "section_title": "Factoring Practice"
    }
]

# Mock remediation examples
MOCK_REMEDIATION_EXAMPLES = [
    {
        "concept_id": "remediation_001",
        "content": "When students struggle with quadratic equations, break down the solution process into clear steps: 1) Identify the standard form ax² + bx + c = 0, 2) Choose the best solution method (factoring, completing the square, or quadratic formula), 3) Apply the method systematically, 4) Check your answers by substituting back into the original equation.",
        "score": 0.96,
        "book": "Teaching Algebra Effectively",
        "subject": "Mathematical Pedagogy",
        "concept_name": "Quadratic Equation Teaching Strategy",
        "concept_type": "explanation",
        "chapter_title": "Common Student Difficulties",
        "section_title": "Systematic Problem Solving"
    },
    {
        "concept_id": "remediation_002",
        "content": "Common mistakes with quadratic equations include: forgetting to set the equation equal to zero, arithmetic errors in the quadratic formula, and not checking both solutions. Use visual aids like graphs to help students understand that quadratic equations typically have two solutions.",
        "score": 0.93,
        "book": "Algebra Teaching Guide",
        "subject": "Mathematical Education",
        "concept_name": "Common Quadratic Mistakes",
        "concept_type": "explanation",
        "chapter_title": "Error Analysis",
        "section_title": "Student Misconceptions"
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
            filters = body.get("filters", {})
            
            print(f"🔍 Mock Content Service: Searching for '{query}' (limit: {limit})")
            
            # Select appropriate mock content based on query
            if "remediation" in query.lower() or "examples" in query.lower():
                available_chunks = MOCK_REMEDIATION_EXAMPLES
            else:
                available_chunks = MOCK_CONTENT_CHUNKS
            
            # Filter by query keywords
            relevant_chunks = []
            query_lower = query.lower()
            
            for chunk in available_chunks:
                # Simple keyword matching
                content_lower = chunk["content"].lower()
                name_lower = chunk["concept_name"].lower()
                
                relevance_score = 0
                if "quadratic" in query_lower and "quadratic" in content_lower:
                    relevance_score += 0.3
                if "sports" in query_lower and "sports" in content_lower:
                    relevance_score += 0.2
                if "music" in query_lower and "music" in content_lower:
                    relevance_score += 0.2
                if "technology" in query_lower and "technology" in content_lower:
                    relevance_score += 0.2
                if "applications" in query_lower and "application" in chunk["concept_type"]:
                    relevance_score += 0.2
                if "basic" in query_lower and "basics" in name_lower:
                    relevance_score += 0.2
                
                if relevance_score > 0:
                    # Adjust score based on relevance
                    adjusted_chunk = chunk.copy()
                    adjusted_chunk["score"] = min(chunk["score"] + relevance_score, 1.0)
                    relevant_chunks.append(adjusted_chunk)
            
            # Sort by score and limit results
            relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
            results = relevant_chunks[:limit]
            
            print(f"✅ Mock Content Service: Returning {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result['concept_name']} (score: {result['score']:.2f})")
            
            return results
            
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
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_mock_server()) 