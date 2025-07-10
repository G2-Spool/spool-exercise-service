#!/usr/bin/env python3
"""Mock content service to satisfy dependencies for testing."""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Mock Content Service")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mock-content-service"}

@app.get("/api/content/concepts/{concept_id}")
async def get_concept(concept_id: str):
    return {
        "concept_id": concept_id,
        "name": "Quadratic Equations",
        "description": "Solving equations of the form ax² + bx + c = 0",
        "content": "Quadratic equations are polynomial equations of degree 2. They can be solved using factoring, completing the square, or the quadratic formula.",
        "learning_objectives": [
            "Understand the standard form of quadratic equations",
            "Apply factoring method to solve quadratic equations",
            "Use the quadratic formula when factoring is not possible",
            "Verify solutions by substitution"
        ],
        "examples": [
            {
                "equation": "x² + 5x + 6 = 0",
                "solution": "x = -2 or x = -3",
                "method": "factoring"
            },
            {
                "equation": "2x² - 7x + 3 = 0",
                "solution": "x = 3 or x = 1/2",
                "method": "factoring"
            }
        ],
        "difficulty": "intermediate",
        "prerequisites": ["linear_equations", "basic_algebra"]
    }

if __name__ == "__main__":
    print("Starting mock content service on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002) 