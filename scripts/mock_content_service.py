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
        "concept_id": "probability_independent_001",
        "content": "Independent events are events where the outcome of one event does not affect the probability of another event occurring. For example, when flipping a coin twice, the result of the first flip doesn't change the probability of getting heads or tails on the second flip. Each flip has a 1/2 probability of being heads, regardless of previous results.",
        "score": 0.95,
        "book": "Introduction to Probability",
        "subject": "Mathematics",
        "concept_name": "Understanding Independent Events",
        "concept_type": "explanation",
        "chapter_title": "Independent Events",
        "section_title": "Core Concepts"
    },
    {
        "concept_id": "probability_independent_002",
        "content": "To calculate the probability of multiple independent events all occurring, multiply their individual probabilities together. This is called the multiplication rule for independent events. If event A has probability P(A) and event B has probability P(B), then P(A and B) = P(A) × P(B). For example, the probability of rolling a 6 on a die AND flipping heads on a coin is (1/6) × (1/2) = 1/12.",
        "score": 0.92,
        "book": "Probability Rules and Applications",
        "subject": "Mathematics",
        "concept_name": "Multiplication Rule for Independent Events",
        "concept_type": "explanation",
        "chapter_title": "Calculating Probabilities",
        "section_title": "Multiplication Rule"
    },
    {
        "concept_id": "probability_sports_001",
        "content": "In sports, independent events can model situations like free throw shooting. If a basketball player has a 75% free throw percentage, each shot is independent of previous shots. The probability of making 3 consecutive free throws is 0.75 × 0.75 × 0.75 = 0.421875, or about 42.2%. This helps coaches understand streaks and performance expectations.",
        "score": 0.89,
        "book": "Statistics in Sports",
        "subject": "Applied Probability",
        "concept_name": "Sports Applications of Independent Events",
        "concept_type": "application",
        "chapter_title": "Performance Analysis",
        "section_title": "Free Throw Probability"
    },
    {
        "concept_id": "probability_example_001",
        "content": "Example: What's the probability of rolling two dice and getting a 4 on the first die AND a 6 on the second die? Since the dice rolls are independent, we multiply: P(4 on first) × P(6 on second) = (1/6) × (1/6) = 1/36 ≈ 0.0278 or about 2.78%. Each die has 6 equally likely outcomes, so each specific number has a 1/6 probability.",
        "score": 0.94,
        "book": "Step-by-Step Probability",
        "subject": "Mathematics",
        "concept_name": "Dice Rolling Example",
        "concept_type": "example",
        "chapter_title": "Worked Examples",
        "section_title": "Dice Probability"
    }
]

# Mock remediation examples
MOCK_REMEDIATION_EXAMPLES = [
    {
        "concept_id": "remediation_probability_001",
        "content": "When students struggle with independent events, they often confuse them with dependent events or forget to multiply probabilities. Help them identify independence by asking: 'Does the first event change what can happen in the second event?' Use concrete examples like coin flips or dice rolls. Common mistakes include adding probabilities instead of multiplying them, or thinking that previous outcomes affect future ones (the gambler's fallacy).",
        "score": 0.96,
        "book": "Teaching Probability Concepts",
        "subject": "Mathematical Pedagogy",
        "concept_name": "Teaching Strategies for Independent Events",
        "concept_type": "explanation",
        "chapter_title": "Common Student Difficulties",
        "section_title": "Independence vs Dependence"
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