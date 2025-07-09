#!/usr/bin/env python3
"""Debug script to test exercise generation with detailed error reporting."""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.langgraph.workflows import ExerciseWorkflow
from app.langgraph.nodes import WorkflowNodes
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_exercise_generation():
    """Test exercise generation with detailed error reporting."""
    
    print("🔧 Debug: Testing Exercise Generation")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"OpenAI API Key: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
    print(f"Content Service URL: {settings.CONTENT_SERVICE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print("-" * 50)
    
    # Test 1: Check if we can create workflow
    try:
        print("1. Creating workflow...")
        workflow = ExerciseWorkflow()
        print("✅ Workflow created successfully")
    except Exception as e:
        print(f"❌ Failed to create workflow: {e}")
        return
    
    # Test 2: Test individual nodes
    try:
        print("2. Testing workflow nodes...")
        nodes = WorkflowNodes()
        print("✅ Workflow nodes created successfully")
    except Exception as e:
        print(f"❌ Failed to create nodes: {e}")
        return
    
    # Test 3: Test exercise generation
    try:
        print("3. Testing exercise generation...")
        
        result = await workflow.generate_exercise(
            concept_id="test_concept",
            student_id="test_student",
            student_interests=["gaming", "music"],
            life_category="career",
            difficulty="basic",
            exercise_type="initial"
        )
        
        print(f"Result: {result}")
        
        if result.get("success"):
            print("✅ Exercise generated successfully!")
            print(f"Exercise ID: {result.get('exercise_id')}")
        else:
            print(f"❌ Exercise generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception during exercise generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exercise_generation()) 