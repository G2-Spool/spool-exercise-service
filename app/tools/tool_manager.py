"""Tool manager for coordinating educational tools."""

from typing import Dict, Any, List, Optional
from .calculator_tool import CalculatorTool
from .code_executor import CodeExecutor
from .search_tool import SearchTool
import structlog

logger = structlog.get_logger()


class ToolManager:
    """Manages and coordinates all available educational tools."""
    
    def __init__(self):
        self.calculator = CalculatorTool()
        self.code_executor = CodeExecutor()
        self.search_tool = SearchTool()
        self.tools_enabled = True
        
    def get_available_tools(self) -> Dict[str, str]:
        """Get descriptions of all available tools."""
        return {
            'calculator': self.calculator.get_tool_description(),
            'code_executor': self.code_executor.get_tool_description(),
            'search_tool': self.search_tool.get_tool_description()
        }
    
    def get_tool_prompt_enhancement(self, context: str = "general") -> str:
        """Get prompt enhancement text describing available tools."""
        if not self.tools_enabled:
            return ""
        
        return f"""
        ## Available Tools for Enhanced Analysis

        You have access to the following tools to provide more accurate and comprehensive responses:

        ### 🧮 Calculator Tool
        - **Use for**: Mathematical calculations, equation solving, verification
        - **Functions**: calculate(), solve_quadratic(), verify_solution()
        - **When to use**: Any mathematical problem requiring computation

        ### 💻 Code Executor Tool  
        - **Use for**: Python code execution, algorithm testing, validation
        - **Functions**: execute_code(), run_test_case(), validate_solution()
        - **When to use**: Programming problems, algorithm verification, code examples

        ### 🔍 Search Tool
        - **Use for**: Finding definitions, examples, step-by-step guides
        - **Functions**: search_concept_definitions(), search_examples(), comprehensive_search()
        - **When to use**: Need additional context, examples, or verification methods

        ### Tool Usage Instructions:
        1. **Request tools when needed**: Say "I need to [calculate/execute/search] to provide an accurate answer"
        2. **Show your work**: Demonstrate the tool usage in your response
        3. **Verify results**: Use tools to double-check your reasoning
        4. **Enhance explanations**: Use search results to provide richer context

        **Example**: For a quadratic equation problem, you might:
        1. Search for definitions and examples
        2. Use calculator to solve the equation
        3. Verify the solution using the verification function
        4. Provide step-by-step explanation based on search results
        """
    
    async def use_calculator(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Use calculator tool with specified operation."""
        if not self.tools_enabled:
            return {'success': False, 'error': 'Tools are disabled'}
        
        try:
            if operation == 'calculate':
                return self.calculator.calculate(kwargs.get('expression', ''))
            elif operation == 'solve_quadratic':
                return self.calculator.solve_quadratic(
                    kwargs.get('a', 0), 
                    kwargs.get('b', 0), 
                    kwargs.get('c', 0)
                )
            elif operation == 'verify_solution':
                return self.calculator.verify_solution(
                    kwargs.get('equation', ''),
                    kwargs.get('variable', 'x'),
                    kwargs.get('value', 0)
                )
            else:
                return {'success': False, 'error': f'Unknown calculator operation: {operation}'}
        except Exception as e:
            logger.error("Calculator tool error", operation=operation, error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def use_code_executor(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Use code executor tool with specified operation."""
        if not self.tools_enabled:
            return {'success': False, 'error': 'Tools are disabled'}
        
        try:
            if operation == 'execute_code':
                return self.code_executor.execute_code(
                    kwargs.get('code', ''),
                    kwargs.get('context')
                )
            elif operation == 'run_test_case':
                return self.code_executor.run_test_case(
                    kwargs.get('code', ''),
                    kwargs.get('test_input', ''),
                    kwargs.get('expected_output', '')
                )
            elif operation == 'validate_solution':
                return self.code_executor.validate_solution(
                    kwargs.get('code', ''),
                    kwargs.get('test_cases', [])
                )
            else:
                return {'success': False, 'error': f'Unknown code executor operation: {operation}'}
        except Exception as e:
            logger.error("Code executor tool error", operation=operation, error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def use_search_tool(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Use search tool with specified operation."""
        if not self.tools_enabled:
            return {'success': False, 'error': 'Tools are disabled'}
        
        try:
            if operation == 'search_concept_definitions':
                return await self.search_tool.search_concept_definitions(
                    kwargs.get('concept_name', ''),
                    kwargs.get('limit', 3)
                )
            elif operation == 'search_examples':
                return await self.search_tool.search_examples(
                    kwargs.get('concept_name', ''),
                    kwargs.get('context', ''),
                    kwargs.get('limit', 3)
                )
            elif operation == 'search_step_by_step_guides':
                return await self.search_tool.search_step_by_step_guides(
                    kwargs.get('concept_name', ''),
                    kwargs.get('difficulty', 'basic'),
                    kwargs.get('limit', 2)
                )
            elif operation == 'search_common_mistakes':
                return await self.search_tool.search_common_mistakes(
                    kwargs.get('concept_name', ''),
                    kwargs.get('limit', 3)
                )
            elif operation == 'search_verification_methods':
                return await self.search_tool.search_verification_methods(
                    kwargs.get('concept_name', ''),
                    kwargs.get('limit', 2)
                )
            elif operation == 'comprehensive_search':
                return await self.search_tool.comprehensive_search(
                    kwargs.get('concept_name', ''),
                    kwargs.get('student_interests'),
                    kwargs.get('difficulty', 'basic')
                )
            else:
                return {'success': False, 'error': f'Unknown search operation: {operation}'}
        except Exception as e:
            logger.error("Search tool error", operation=operation, error=str(e))
            return {'success': False, 'error': str(e)}
    
    def create_tool_enhanced_prompt(self, base_prompt: str, concept_name: str, 
                                  student_interests: List[str] = None, 
                                  enable_calculator: bool = True,
                                  enable_code_executor: bool = True,
                                  enable_search: bool = True) -> str:
        """Create enhanced prompt with tool availability information."""
        if not self.tools_enabled:
            return base_prompt
        
        tool_section = "\n## 🛠️ Available Tools\n"
        
        if enable_calculator:
            tool_section += """
### Calculator Tool
- Use for mathematical calculations and equation solving
- Functions: calculate(), solve_quadratic(), verify_solution()
- Example: "Let me calculate this: [use calculator to solve]"
"""
        
        if enable_code_executor:
            tool_section += """
### Code Executor Tool
- Use for Python code execution and validation
- Functions: execute_code(), run_test_case(), validate_solution()
- Example: "Let me test this code: [use code executor to validate]"
"""
        
        if enable_search:
            tool_section += f"""
### Search Tool
- Use for finding definitions, examples, and step-by-step guides
- Functions: search_concept_definitions(), search_examples(), comprehensive_search()
- Example: "Let me search for examples of {concept_name}: [use search tool]"
"""
        
        tool_section += """
### Tool Usage Guidelines:
1. **Request tools explicitly**: State when you need to use a tool
2. **Show your work**: Demonstrate tool usage in your response  
3. **Verify results**: Use tools to double-check your reasoning
4. **Enhance explanations**: Use search results to provide richer context

**Remember**: Always use tools to provide the most accurate and comprehensive response possible.
"""
        
        return base_prompt + tool_section
    
    def get_llm_tool_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get tool capabilities optimized for different LLMs."""
        return {
            "GPT-4": {
                "recommended_tools": ["calculator", "code_executor", "search_tool"],
                "strengths": ["All tools", "Function calling", "Complex reasoning"],
                "optimal_usage": "Use all tools for comprehensive analysis"
            },
            "Claude": {
                "recommended_tools": ["code_executor", "search_tool"],
                "strengths": ["Code reasoning", "Text synthesis"],
                "optimal_usage": "Emphasize code execution and search results synthesis"
            },
            "Gemini": {
                "recommended_tools": ["calculator", "search_tool"],
                "strengths": ["Mathematical reasoning", "Multi-source synthesis"],
                "optimal_usage": "Focus on mathematical calculations and comprehensive search"
            }
        }
    
    async def analyze_problem_and_suggest_tools(self, problem_type: str, content: str) -> Dict[str, Any]:
        """Analyze a problem and suggest appropriate tools."""
        suggested_tools = []
        
        # Check for mathematical content
        math_keywords = ['equation', 'solve', 'calculate', 'formula', 'quadratic', 'algebra', 'geometry']
        if any(keyword in content.lower() for keyword in math_keywords):
            suggested_tools.append('calculator')
        
        # Check for coding content
        code_keywords = ['code', 'program', 'algorithm', 'python', 'function', 'loop', 'if statement']
        if any(keyword in content.lower() for keyword in code_keywords):
            suggested_tools.append('code_executor')
        
        # Always suggest search for additional context
        suggested_tools.append('search_tool')
        
        return {
            'success': True,
            'problem_type': problem_type,
            'suggested_tools': suggested_tools,
            'reasoning': f"Based on content analysis, these tools would be most helpful for {problem_type} problems",
            'tool_descriptions': {tool: self.get_available_tools()[tool] for tool in suggested_tools}
        }
    
    def disable_tools(self):
        """Disable all tools."""
        self.tools_enabled = False
    
    def enable_tools(self):
        """Enable all tools."""
        self.tools_enabled = True 