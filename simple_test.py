#!/usr/bin/env python3
"""Simple test to verify what's failing in the HTTP endpoint."""

import os
import httpx
import asyncio
import json

# Set environment variables
os.environ['OPENAI_API_KEY'] = 'test_key_placeholder'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['CONTENT_SERVICE_URL'] = 'http://localhost:8002'
os.environ['ENVIRONMENT'] = 'development'

async def test_exercise_endpoint():
    """Test the exercise generation endpoint directly."""
    
    url = "http://localhost:8003/api/exercise/generate"
    
    payload = {
        "concept_id": "math_algebra_quadratic",
        "student_id": "student_123",
        "student_interests": ["sports", "gaming", "music"],
        "life_category": "career",
        "difficulty": "basic"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=30.0
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code != 200:
                # Try to get more details from the server logs
                print("Checking health endpoint...")
                health_response = await client.get("http://localhost:8003/health")
                print(f"Health status: {health_response.status_code}")
                print(f"Health response: {health_response.text}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_exercise_endpoint()) 