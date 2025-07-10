#!/usr/bin/env python3
"""
Simple runner script for the comprehensive workflow test.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import structlog
        import openai
        from langgraph.graph import StateGraph
        print("✅ All required dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install structlog openai langgraph")
        return False

def setup_test_environment():
    """Setup test environment with real API configurations."""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Set defaults only if not already set in .env
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('GENERATION_MODEL', 'gpt-4o')
    os.environ.setdefault('EVALUATION_MODEL', 'gpt-4o')
    os.environ.setdefault('CONTENT_SERVICE_URL', 'http://localhost:8001')
    os.environ.setdefault('PROFILE_SERVICE_URL', 'http://localhost:8002')
    os.environ.setdefault('MAX_RETRIES', '3')
    os.environ.setdefault('CACHE_TTL', '3600')
    os.environ.setdefault('EXERCISE_CACHE_TTL', '3600')
    os.environ.setdefault('TEMPERATURE', '0.7')
    os.environ.setdefault('MAX_TOKENS', '2000')
    os.environ.setdefault('MIN_RESPONSE_LENGTH', '10')
    os.environ.setdefault('WORKFLOW_TIMEOUT', '300')
    
    # Verify OpenAI API key is loaded
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key.startswith('test'):
        print("❌ ERROR: No valid OpenAI API key found!")
        print("   Create a .env file in this directory with:")
        print("   OPENAI_API_KEY=your-actual-openai-api-key-here")
        print("   ENVIRONMENT=development")
        return False
    else:
        print(f"✅ OpenAI API key loaded (***{api_key[-4:]})")
    
    print("✅ Test environment configured for real API calls")
    return True

async def run_test():
    """Run the comprehensive workflow test."""
    try:
        from comprehensive_workflow_test import WorkflowTestSuite
        
        print("🚀 Starting Comprehensive Exercise Workflow Test")
        print("=" * 60)
        
        test_suite = WorkflowTestSuite()
        await test_suite.run_comprehensive_test()
        
        print("\n✅ Test completed successfully!")
        print("Check the 'test_results' directory for detailed output files.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point."""
    print("Exercise Workflow Test Runner")
    print("=" * 40)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not setup_test_environment():
        sys.exit(1)
    
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 