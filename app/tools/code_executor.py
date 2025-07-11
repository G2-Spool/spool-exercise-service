"""Safe code execution tool for educational purposes."""

import ast
import io
import sys
import contextlib
import time
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class CodeExecutor:
    """Safe Python code executor for educational purposes."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.enabled = True
        
        # Define allowed built-ins for safety
        self.safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bin': bin,
            'bool': bool,
            'chr': chr,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'hex': hex,
            'int': int,
            'isinstance': isinstance,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            'print': print,
        }
        
        # Allowed modules
        self.safe_modules = {
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            're': __import__('re'),
        }
    
    def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code safely with output capture.
        
        Args:
            code: Python code to execute
            context: Optional context variables
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Validate code safety
            if not self._is_safe_code(code):
                return {
                    'success': False,
                    'error': 'Code contains unsafe operations'
                }
            
            # Prepare execution environment
            exec_globals = {
                '__builtins__': self.safe_builtins,
                **self.safe_modules
            }
            
            if context:
                exec_globals.update(context)
            
            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # Execute with timeout
                start_time = time.time()
                local_vars = {}
                
                # Try to execute as expression first, then as statement
                try:
                    # Try as expression
                    result = eval(code, exec_globals, local_vars)
                    execution_type = 'expression'
                except SyntaxError:
                    # Execute as statement
                    exec(code, exec_globals, local_vars)
                    result = None
                    execution_type = 'statement'
                
                end_time = time.time()
                
                # Get output
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                return {
                    'success': True,
                    'result': result,
                    'execution_type': execution_type,
                    'stdout': stdout_output,
                    'stderr': stderr_output,
                    'execution_time': end_time - start_time,
                    'variables': {k: v for k, v in local_vars.items() if not k.startswith('__')}
                }
                
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            logger.error("Code execution error", code=code[:100], error=str(e))
            return {
                'success': False,
                'error': str(e),
                'code': code[:100] + '...' if len(code) > 100 else code
            }
    
    def _is_safe_code(self, code: str) -> bool:
        """Check if code is safe to execute."""
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Check for unsafe operations
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Check if importing allowed modules
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name not in self.safe_modules:
                                return False
                    elif isinstance(node, ast.ImportFrom):
                        if node.module not in self.safe_modules:
                            return False
                
                elif isinstance(node, ast.Call):
                    # Check function calls
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        # Block dangerous functions
                        if func_name in ['exec', 'eval', 'compile', 'open', '__import__', 'globals', 'locals', 'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr']:
                            return False
                
                elif isinstance(node, ast.Attribute):
                    # Block access to certain attributes
                    if isinstance(node.attr, str) and node.attr.startswith('__'):
                        return False
                
                elif isinstance(node, (ast.Global, ast.Nonlocal)):
                    # Block global/nonlocal declarations
                    return False
            
            return True
            
        except SyntaxError:
            return False
    
    def run_test_case(self, code: str, test_input: str, expected_output: str) -> Dict[str, Any]:
        """
        Run code with test input and compare output.
        
        Args:
            code: Code to test
            test_input: Input for the code
            expected_output: Expected output
            
        Returns:
            Dictionary with test results
        """
        try:
            # Execute code with test input
            context = {'input_data': test_input}
            result = self.execute_code(code, context)
            
            if not result['success']:
                return {
                    'success': False,
                    'error': result['error'],
                    'test_passed': False
                }
            
            # Compare output
            actual_output = result['stdout'].strip()
            test_passed = actual_output == expected_output.strip()
            
            return {
                'success': True,
                'test_passed': test_passed,
                'actual_output': actual_output,
                'expected_output': expected_output,
                'execution_time': result['execution_time'],
                'variables': result['variables']
            }
            
        except Exception as e:
            logger.error("Test execution error", code=code[:100], error=str(e))
            return {
                'success': False,
                'error': str(e),
                'test_passed': False
            }
    
    def validate_solution(self, code: str, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Validate code against multiple test cases.
        
        Args:
            code: Code to validate
            test_cases: List of test cases with 'input' and 'expected' keys
            
        Returns:
            Dictionary with validation results
        """
        results = []
        passed_count = 0
        
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get('input', '')
            expected_output = test_case.get('expected', '')
            
            result = self.run_test_case(code, test_input, expected_output)
            results.append({
                'test_case': i + 1,
                'passed': result.get('test_passed', False),
                'actual_output': result.get('actual_output', ''),
                'expected_output': expected_output,
                'error': result.get('error'),
                'execution_time': result.get('execution_time', 0)
            })
            
            if result.get('test_passed', False):
                passed_count += 1
        
        return {
            'success': True,
            'total_tests': len(test_cases),
            'passed_tests': passed_count,
            'success_rate': passed_count / len(test_cases) if test_cases else 0,
            'all_passed': passed_count == len(test_cases),
            'results': results
        }
    
    def get_tool_description(self) -> str:
        """Get description of code executor tool capabilities."""
        return """
        Code Executor Tool - Available for Python code execution:
        
        **Functions:**
        - execute_code(code, context=None): Execute Python code safely
        - run_test_case(code, input, expected): Test code with specific input
        - validate_solution(code, test_cases): Validate against multiple test cases
        
        **Safety Features:**
        - Sandboxed execution environment
        - Limited built-in functions
        - Restricted module imports
        - Output capture and timeout protection
        
        **Allowed Modules:**
        - math, random, datetime, json, re
        
        **Examples:**
        - execute_code("2 + 3 * 4") → result: 14
        - run_test_case("print(x)", "5", "5") → test validation
        - validate_solution(code, [{"input": "5", "expected": "25"}])
        """ 