#!/usr/bin/env python3
"""
Quick test to verify OpenAI API setup is working correctly.
Run this before the comprehensive test to ensure everything is configured properly.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_api_setup():
    """Test that OpenAI API is properly configured."""
    print("🔍 Testing OpenAI API Setup")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if api_key.startswith('test') or api_key == 'your-actual-openai-api-key-here':
        print("❌ OPENAI_API_KEY appears to be a placeholder")
        return False
    
    print(f"✅ API key found (***{api_key[-4:]})")
    
    # Test API connection
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        print("🔄 Testing API connection...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ API Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

async def main():
    """Main test function."""
    success = await test_api_setup()
    
    if success:
        print("\n🎯 API setup verified!")
        print("You can now run the comprehensive test:")
        print("python run_workflow_test.py")
    else:
        print("\n❌ API setup failed!")
        print("Please check your .env file and API key.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 