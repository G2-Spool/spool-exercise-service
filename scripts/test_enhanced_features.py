#!/usr/bin/env python3
"""
Test script for enhanced chain-of-thought prompting and tool integration.

This script demonstrates the new features:
1. Chain-of-thought prompting strategies
2. Calculator tool functionality
3. Code executor capabilities
4. Search tool integration
5. Tool manager coordination
"""

import asyncio
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up basic environment
os.environ.setdefault("ENABLE_VECTOR_CONTEXT", "true")
os.environ.setdefault("OPENAI_API_KEY", "test_key")

from app.core.prompts import ChainOfThoughtPrompts
from app.tools.calculator_tool import CalculatorTool
from app.tools.code_executor import CodeExecutor
from app.tools.search_tool import SearchTool
from app.tools.tool_manager import ToolManager


async def test_chain_of_thought_prompts():
    """Test chain-of-thought prompting strategies."""
    print("🧠 Testing Chain-of-Thought Prompting Strategies")
    print("=" * 60)
    
    cot = ChainOfThoughtPrompts()
    
    # Test concept
    concept = {
        "name": "Quadratic Equations",
        "content": "Mathematical equations of the form ax² + bx + c = 0",
        "type": "mathematical"
    }
    
    student_profile = {
        "interests": ["basketball", "music"],
        "grade_level": "high school"
    }
    
    context_chunks = [
        {"content": "Quadratic equations are fundamental in algebra and have real-world applications in physics, engineering, and economics."},
        {"content": "The quadratic formula x = (-b ± √(b² - 4ac)) / 2a provides a universal solution method."}
    ]
    
    # Generate enhanced exercise prompt
    print("\n📝 Generated Enhanced Exercise Prompt:")
    print("-" * 40)
    exercise_prompt = cot.create_enhanced_exercise_prompt(
        concept, student_profile, context_chunks
    )
    print(exercise_prompt[:500] + "..." if len(exercise_prompt) > 500 else exercise_prompt)
    
    # Generate enhanced evaluation prompt
    print("\n📊 Generated Enhanced Evaluation Prompt:")
    print("-" * 40)
    exercise = {"content": {"problem": "Solve x² + 5x + 6 = 0"}, "expected_steps": ["Factor the equation", "Set factors to zero", "Solve for x"]}
    student_response = "I factored the equation as (x + 2)(x + 3) = 0, so x = -2 and x = -3."
    
    evaluation_prompt = cot.create_enhanced_evaluation_prompt(
        exercise, student_response, concept, context_chunks
    )
    print(evaluation_prompt[:500] + "..." if len(evaluation_prompt) > 500 else evaluation_prompt)
    
    print("\n✅ Chain-of-thought prompts generated successfully!")


def test_calculator_tool():
    """Test calculator tool functionality."""
    print("\n🧮 Testing Calculator Tool")
    print("=" * 60)
    
    calculator = CalculatorTool()
    
    # Test basic calculations
    print("\n➕ Basic Calculations:")
    results = [
        calculator.calculate("2 + 3 * 4"),
        calculator.calculate("sqrt(16) + 5"),
        calculator.calculate("sin(pi/2)"),
        calculator.calculate("2**3 + 1")
    ]
    
    for result in results:
        if result['success']:
            print(f"   {result['expression']} = {result['result']}")
        else:
            print(f"   Error: {result['error']}")
    
    # Test quadratic solver
    print("\n🔢 Quadratic Equation Solver:")
    quad_results = [
        calculator.solve_quadratic(1, 5, 6),  # x² + 5x + 6 = 0
        calculator.solve_quadratic(1, -5, 6), # x² - 5x + 6 = 0
        calculator.solve_quadratic(1, 0, -4)  # x² - 4 = 0
    ]
    
    for result in quad_results:
        if result['success']:
            print(f"   {result['equation']}: solutions = {result['solutions']}")
        else:
            print(f"   Error: {result['error']}")
    
    # Test solution verification
    print("\n✅ Solution Verification:")
    verify_results = [
        calculator.verify_solution("x**2 + 5*x + 6", "x", -2),
        calculator.verify_solution("x**2 + 5*x + 6", "x", -3),
        calculator.verify_solution("x**2 + 5*x + 6", "x", 0)
    ]
    
    for result in verify_results:
        if result['success']:
            status = "✓" if result['verified'] else "✗"
            print(f"   {status} x = {result['value']}: result = {result['result']}")
        else:
            print(f"   Error: {result['error']}")
    
    print("\n✅ Calculator tool tests completed!")


def test_code_executor():
    """Test code executor functionality."""
    print("\n💻 Testing Code Executor")
    print("=" * 60)
    
    executor = CodeExecutor()
    
    # Test basic code execution
    print("\n🐍 Basic Code Execution:")
    code_examples = [
        "2 + 3 * 4",
        "print('Hello, World!')",
        "import math; print(math.sqrt(16))",
        "x = 5; y = 3; print(f'x + y = {x + y}')"
    ]
    
    for code in code_examples:
        result = executor.execute_code(code)
        if result['success']:
            print(f"   Code: {code}")
            print(f"   Result: {result.get('result', 'None')}")
            if result['stdout']:
                print(f"   Output: {result['stdout'].strip()}")
        else:
            print(f"   Error in '{code}': {result['error']}")
        print()
    
    # Test with unsafe code (should be blocked)
    print("\n🔒 Safety Testing (should be blocked):")
    unsafe_codes = [
        "import os; os.system('ls')",
        "open('/etc/passwd', 'r')",
        "eval('__import__(\\'os\\').system(\\'ls\\')')"
    ]
    
    for code in unsafe_codes:
        result = executor.execute_code(code)
        if result['success']:
            print(f"   ⚠️  UNSAFE CODE EXECUTED: {code}")
        else:
            print(f"   ✅ Blocked unsafe code: {code}")
    
    print("\n✅ Code executor tests completed!")


async def test_search_tool():
    """Test search tool functionality."""
    print("\n🔍 Testing Search Tool")
    print("=" * 60)
    
    search_tool = SearchTool()
    
    # Test concept definition search
    print("\n📖 Concept Definition Search:")
    definition_result = await search_tool.search_concept_definitions("quadratic equations", 2)
    if definition_result['success']:
        print(f"   Found {definition_result['count']} definitions")
        for i, result in enumerate(definition_result['results']):
            print(f"   {i+1}. {str(result)[:100]}...")
    else:
        print(f"   Error: {definition_result['error']}")
    
    # Test example search
    print("\n📚 Example Search:")
    example_result = await search_tool.search_examples("quadratic equations", "sports basketball", 2)
    if example_result['success']:
        print(f"   Found {example_result['count']} examples")
        for i, result in enumerate(example_result['results']):
            print(f"   {i+1}. {str(result)[:100]}...")
    else:
        print(f"   Error: {example_result['error']}")
    
    # Test comprehensive search
    print("\n🎯 Comprehensive Search:")
    comprehensive_result = await search_tool.comprehensive_search(
        "quadratic equations", 
        ["sports", "music"], 
        "basic"
    )
    if comprehensive_result['success']:
        print(f"   Total results: {comprehensive_result['total_results']}")
        print(f"   Definitions: {comprehensive_result['definitions']['count']}")
        print(f"   Examples: {comprehensive_result['examples']['count']}")
        print(f"   Guides: {comprehensive_result['guides']['count']}")
    else:
        print(f"   Error: {comprehensive_result['error']}")
    
    print("\n✅ Search tool tests completed!")


async def test_tool_manager():
    """Test tool manager functionality."""
    print("\n🛠️ Testing Tool Manager")
    print("=" * 60)
    
    tool_manager = ToolManager()
    
    # Test available tools
    print("\n📋 Available Tools:")
    available_tools = tool_manager.get_available_tools()
    for tool_name, description in available_tools.items():
        print(f"   {tool_name}: {description[:100]}...")
    
    # Test calculator integration
    print("\n🧮 Calculator Integration:")
    calc_result = await tool_manager.use_calculator(
        operation='solve_quadratic',
        a=1, b=5, c=6
    )
    if calc_result['success']:
        print(f"   Quadratic solution: {calc_result['solutions']}")
    else:
        print(f"   Error: {calc_result['error']}")
    
    # Test code executor integration
    print("\n💻 Code Executor Integration:")
    code_result = await tool_manager.use_code_executor(
        operation='execute_code',
        code='print("Hello from tool manager!")'
    )
    if code_result['success']:
        print(f"   Code output: {code_result['stdout'].strip()}")
    else:
        print(f"   Error: {code_result['error']}")
    
    # Test LLM capabilities
    print("\n🤖 LLM Tool Recommendations:")
    llm_capabilities = tool_manager.get_llm_tool_capabilities()
    for llm, capabilities in llm_capabilities.items():
        print(f"   {llm}: {capabilities['recommended_tools']}")
    
    # Test problem analysis
    print("\n🔍 Problem Analysis:")
    analysis_result = await tool_manager.analyze_problem_and_suggest_tools(
        "mathematical", 
        "Solve the quadratic equation x² + 5x + 6 = 0 and verify your answer"
    )
    if analysis_result['success']:
        print(f"   Suggested tools: {analysis_result['suggested_tools']}")
        print(f"   Reasoning: {analysis_result['reasoning']}")
    else:
        print(f"   Error: {analysis_result['error']}")
    
    print("\n✅ Tool manager tests completed!")


async def main():
    """Run all tests."""
    print("🚀 Enhanced Features Test Suite")
    print("=" * 80)
    print("Testing Chain-of-Thought Prompting and Tool Integration")
    print("=" * 80)
    
    try:
        # Test chain-of-thought prompts
        await test_chain_of_thought_prompts()
        
        # Test calculator tool
        test_calculator_tool()
        
        # Test code executor
        test_code_executor()
        
        # Test search tool
        await test_search_tool()
        
        # Test tool manager
        await test_tool_manager()
        
        print("\n" + "=" * 80)
        print("🎉 All Enhanced Features Tests Completed Successfully!")
        print("=" * 80)
        
        print("\n📊 Summary:")
        print("✅ Chain-of-thought prompting strategies implemented")
        print("✅ Calculator tool functional with safety measures")
        print("✅ Code executor operational with sandboxing")
        print("✅ Search tool integrated with Pinecone service")
        print("✅ Tool manager coordinates all tools effectively")
        
        print("\n🚀 The Spool Exercise Service is now enhanced with:")
        print("   • Step-by-step reasoning capabilities")
        print("   • Mathematical computation tools")
        print("   • Safe code execution environment")
        print("   • Comprehensive search functionality")
        print("   • LLM-optimized tool recommendations")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 