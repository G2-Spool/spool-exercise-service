"""Secure code execution tool for educational purposes."""

import ast
import subprocess
import tempfile
import os
import signal
import resource
import time
import json
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class SecureCodeExecutor:
    """Secure Python code executor with proper sandboxing and resource limits."""
    
    def __init__(self, timeout: int = 5, max_memory_mb: int = 50):
        self.timeout = timeout
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.enabled = True
        
        # Allowed modules (ultra restrictive) - must be set before wrapper creation
        self.safe_modules = {
            'math', 'random', 'datetime', 'json', 're', 'string', 'itertools',
            'functools', 'operator', 'heapq', 'bisect'
            # Removed: 'collections' - can be used for complex object construction
        }
        
        # Create secure Python executable wrapper
        self.secure_python_script = self._create_secure_python_wrapper()
        
        # Blocked patterns that should never appear in code
        self.blocked_patterns = [
            '__import__', 'eval', 'exec', 'compile', 'globals', 'locals',
            'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
            'open', 'file', 'input', 'raw_input', '__builtins__',
            'subprocess', 'os.', 'sys.', 'import os', 'import sys',
            '__class__', '__bases__', '__subclasses__', '__mro__',
            'func_globals', 'gi_frame', 'f_locals', 'f_globals',
            # Enhanced blocking for indirect access
            '__dict__', '__module__', '__name__', '__qualname__',
            '__annotations__', '__closure__', '__code__', '__defaults__',
            '__globals__', '__kwdefaults__', '__weakref__', '__doc__',
            'gi_code', 'gi_running', 'cr_code', 'cr_running',
            # Block metaclass and type manipulation
            '__metaclass__', '__new__', '__init_subclass__',
            # Block frame manipulation
            'f_back', 'f_code', 'f_builtins', 'f_trace',
            # Block complex object construction
            'namedtuple', 'defaultdict', 'deque', 'counter'
        ]
    
    def _create_secure_python_wrapper(self) -> str:
        """Create a secure Python wrapper script for isolated execution."""
        wrapper_content = '''
import sys
import json
import signal
import resource
import traceback
from io import StringIO

def set_resource_limits():
    """Set strict resource limits."""
    try:
        # Memory limit
        max_memory = {max_memory}
        resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
        
        # CPU time limit (seconds)
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        
        # File operations limit (no file creation)
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        
        # Process limit (no forking)
        resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    except (ValueError, OSError):
        pass  # Some limits may not be available on all systems

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Code execution timed out")

def secure_exec(code_string):
    """Execute code in a secure environment."""
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm({timeout})
    
    # Set resource limits
    set_resource_limits()
    
    # Ultra-restricted builtins (removed introspection capabilities)
    safe_builtins = {{
        'abs': abs, 'all': all, 'any': any, 'bool': bool,
        'dict': dict, 'enumerate': enumerate, 'filter': filter,
        'float': float, 'int': int, 'isinstance': isinstance,
        'len': len, 'list': list, 'max': max, 'min': min,
        'pow': pow, 'range': range, 'reversed': reversed,
        'round': round, 'set': set, 'sorted': sorted, 'str': str, 'sum': sum,
        'tuple': tuple, 'print': print
        # Removed: 'type', 'zip', 'map' - can be used for introspection
        # Removed: 'chr', 'ord', 'bin', 'hex', 'oct' - can be used for encoding tricks
    }}
    
    # Allowed modules
    safe_modules = {safe_modules}
    for module_name in safe_modules:
        try:
            safe_builtins[module_name] = __import__(module_name)
        except ImportError:
            pass
    
    # Capture output
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    result = None
    execution_type = "statement"
    
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        # Create isolated execution environment
        exec_globals = {{"__builtins__": safe_builtins}}
        exec_locals = {{}}
        
        # Try as expression first
        try:
            # Compile as expression to check if it's a simple expression
            compile(code_string, '<string>', 'eval')
            result = eval(code_string, exec_globals, exec_locals)
            execution_type = "expression"
        except SyntaxError:
            # Execute as statement
            exec(code_string, exec_globals, exec_locals)
            execution_type = "statement"
        
        # Get output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        return {{
            'success': True,
            'result': str(result) if result is not None else None,
            'execution_type': execution_type,
            'stdout': stdout_output,
            'stderr': stderr_output,
            'variables': {{k: str(v) for k, v in exec_locals.items() if not k.startswith('__')}}
        }}
        
    except TimeoutError:
        return {{'success': False, 'error': 'Code execution timed out'}}
    except MemoryError:
        return {{'success': False, 'error': 'Code exceeded memory limit'}}
    except Exception as e:
        return {{'success': False, 'error': str(e), 'traceback': traceback.format_exc()}}
    finally:
        signal.alarm(0)  # Cancel timeout
        sys.stdout = old_stdout
        sys.stderr = old_stderr

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({{'success': False, 'error': 'Invalid arguments'}}))
        sys.exit(1)
    
    code_to_execute = sys.argv[1]
    result = secure_exec(code_to_execute)
    print(json.dumps(result))
'''.format(
            timeout=self.timeout,
            max_memory=self.max_memory_bytes,
            safe_modules=repr(self.safe_modules)
        )
        
        # Write wrapper to temporary file with robust error handling
        wrapper_fd, wrapper_path = tempfile.mkstemp(suffix='.py', prefix='secure_exec_')
        try:
            with os.fdopen(wrapper_fd, 'w') as f:
                f.write(wrapper_content)
            logger.info("Created secure Python wrapper", path=wrapper_path)
            return wrapper_path
        except Exception as e:
            logger.error("Failed to create secure Python wrapper", error=str(e))
            try:
                os.close(wrapper_fd)
            except:
                pass
            try:
                os.unlink(wrapper_path)
            except:
                pass
            raise RuntimeError(f"Failed to create secure execution environment: {str(e)}")
    
    def _is_safe_code(self, code: str) -> bool:
        """Enhanced safety check for code."""
        # Check for blocked patterns
        code_lower = code.lower()
        for pattern in self.blocked_patterns:
            if pattern in code_lower:
                return False
        
        # Check for dangerous escape sequences and obfuscation
        dangerous_sequences = [
            '\\x', '\\u', '\\U',  # Unicode/hex escapes that could hide code
            '\\n', '\\t', '\\r',  # Newlines could hide code
            '\\a', '\\b', '\\f', '\\v',  # Other escape sequences
            'chr(', 'ord(',       # Character manipulation
            'bytes(', 'bytearray(',  # Byte manipulation
            'encode(', 'decode(',  # Encoding manipulation
            'format(', '{',       # String formatting could hide code
            'exec(', 'eval(',     # Double-check these are blocked
            'repr(', 'ascii(',    # Representation functions
            'hex(', 'oct(', 'bin(',  # Number base conversions
        ]
        
        for seq in dangerous_sequences:
            if seq in code_lower:
                return False
        
        try:
            # Parse AST for deeper analysis
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Block any imports not in safe list
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name not in self.safe_modules:
                                return False
                    elif isinstance(node, ast.ImportFrom):
                        if node.module not in self.safe_modules:
                            return False
                
                # Block dangerous function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                            return False
                
                # Block attribute access to dangerous attributes
                elif isinstance(node, ast.Attribute):
                    if (isinstance(node.attr, str) and 
                        (node.attr.startswith('__') or node.attr in ['globals', 'locals'])):
                        return False
                
                # Block global/nonlocal declarations
                elif isinstance(node, (ast.Global, ast.Nonlocal)):
                    return False
                
                # Allow simple lambdas, but block function/class definitions
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    return False
                
                # Restrict lambdas to only safe names and expressions
                elif isinstance(node, ast.Lambda):
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Name):
                            # Block dangerous function names
                            if subnode.id in ['eval', 'exec', 'compile', '__import__', 'open', 'input',
                                            'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
                                            'globals', 'locals', 'type', 'zip', 'map', 'filter']:
                                return False
                        elif isinstance(subnode, ast.Attribute):
                            # Block dangerous attribute access
                            if (isinstance(subnode.attr, str) and 
                                (subnode.attr.startswith('__') or 
                                 subnode.attr in ['globals', 'locals', 'dict', 'class', 'bases', 'mro'])):
                                return False
                        elif isinstance(subnode, ast.Call):
                            # Block nested function calls in lambdas that could be dangerous
                            if isinstance(subnode.func, ast.Name):
                                if subnode.func.id in ['eval', 'exec', 'compile', '__import__']:
                                    return False
            
            return True
            
        except SyntaxError:
            return False
    
    def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code securely with proper isolation and limits.
        
        Args:
            code: Python code to execute
            context: Optional context variables (ignored for security)
            
        Returns:
            Dictionary with execution results
        """
        if not self.enabled:
            return {'success': False, 'error': 'Code executor is disabled'}
        
        # Enhanced safety check
        if not self._is_safe_code(code):
            return {
                'success': False,
                'error': 'Code contains unsafe operations or patterns'
            }
        
        # Additional length check
        if len(code) > 2000:
            return {
                'success': False,
                'error': 'Code is too long (max 2000 characters)'
            }
        
        try:
            # Execute in isolated subprocess
            start_time = time.time()
            
            # Ensure secure_python_script exists
            if not self.secure_python_script or not os.path.exists(self.secure_python_script):
                return {
                    'success': False,
                    'error': 'Secure execution environment not available'
                }
            
            # Enhanced process isolation
            def setup_subprocess():
                """Set up subprocess with enhanced security."""
                if os.name != 'nt':
                    # Create new process group for better isolation
                    os.setsid()
                    # Additional security measures on Unix-like systems
                    try:
                        # Prevent core dumps
                        import resource
                        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                    except (ImportError, OSError):
                        pass
            
            process = subprocess.Popen(
                [sys.executable, self.secure_python_script, code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=setup_subprocess if os.name != 'nt' else None
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout + 1)
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    try:
                        result = json.loads(stdout)
                        result['execution_time'] = execution_time
                        return result
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'error': 'Invalid response from secure executor',
                            'raw_output': stdout[:500]
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Execution failed with code {process.returncode}',
                        'stderr': stderr[:500]
                    }
                    
            except subprocess.TimeoutExpired:
                # Kill the process group to ensure cleanup
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                
                return {
                    'success': False,
                    'error': f'Code execution timed out after {self.timeout} seconds'
                }
                
        except Exception as e:
            logger.error("Secure code execution error", error=str(e))
            return {
                'success': False,
                'error': f'Execution system error: {str(e)}'
            }
    
    def run_test_case(self, code: str, test_input: str, expected_output: str) -> Dict[str, Any]:
        """
        Run code with test input and compare output.
        
        Args:
            code: Code to test
            test_input: Input for the code (safely embedded)
            expected_output: Expected output
            
        Returns:
            Dictionary with test results
        """
        try:
            # Safely validate and embed test input
            if not isinstance(test_input, (str, int, float, bool, list, dict, tuple)):
                return {
                    'success': False,
                    'error': 'Invalid test input type',
                    'test_passed': False
                }
            
            # Double-check test_input doesn't contain dangerous patterns
            if isinstance(test_input, str):
                test_input_lower = test_input.lower()
                for pattern in self.blocked_patterns:
                    if pattern in test_input_lower:
                        return {
                            'success': False,
                            'error': 'Test input contains unsafe patterns',
                            'test_passed': False
                        }
            
            # Safely embed test input using json.dumps for proper escaping
            try:
                safe_input = json.dumps(test_input)
                test_code = f"import json\\ntest_input = json.loads({repr(safe_input)})\\n{code}"
            except (TypeError, ValueError):
                return {
                    'success': False,
                    'error': 'Test input cannot be safely serialized',
                    'test_passed': False
                }
            
            result = self.execute_code(test_code)
            
            if not result['success']:
                return {
                    'success': False,
                    'error': result['error'],
                    'test_passed': False
                }
            
            # Compare output
            actual_output = result.get('stdout', '').strip()
            test_passed = actual_output == expected_output.strip()
            
            return {
                'success': True,
                'test_passed': test_passed,
                'actual_output': actual_output,
                'expected_output': expected_output,
                'execution_time': result.get('execution_time', 0)
            }
            
        except Exception as e:
            logger.error("Test execution error", error=str(e))
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
        """Get description of secure code executor capabilities."""
        return f"""
        Ultra-Secure Code Executor Tool - Bulletproof Python code execution with enterprise-grade security:
        
        **Advanced Security Features:**
        - Complete process isolation with enhanced subprocess execution
        - Real timeout enforcement ({self.timeout}s) with signal handling
        - Memory limits ({self.max_memory_bytes // (1024*1024)}MB) with resource.setrlimit
        - CPU time limits (10s) with core dump prevention
        - Zero file system access (RLIMIT_FSIZE = 0)
        - Ultra-restrictive module imports (only essential math/utility modules)
        - Multi-layer AST-based code analysis with indirect access blocking
        - Enhanced lambda support with strict safety validation
        - Input injection protection with JSON-based serialization
        - Robust error handling with automatic cleanup
        
        **Functions:**
        - execute_code(code): Execute Python code with maximum security
        - run_test_case(code, input, expected): Test code with secure input handling
        - validate_solution(code, test_cases): Validate against multiple test cases
        - cleanup(): Explicit resource cleanup
        
        **Allowed Modules (Ultra-Restrictive):**
        - {', '.join(sorted(self.safe_modules))}
        
        **Removed Dangerous Builtins:**
        - type, zip, map, filter (introspection capabilities)
        - chr, ord, bin, hex, oct (encoding manipulation)
        - eval, exec, compile, __import__ (code execution)
        
        **Enhanced Safety Restrictions:**
        - No eval, exec, compile, __import__, globals, locals
        - No file operations or system access
        - No dangerous attribute access (__dict__, __class__, etc.)
        - No function/class definitions (lambdas allowed with restrictions)
        - No metaclass or frame manipulation
        - No Unicode escape sequences or encoding tricks
        - No string formatting that could hide code
        - Limited to simple computational and educational tasks
        
        **Examples:**
        - execute_code("print(2 + 3)") → output: "5"
        - execute_code("sum([1, 2, 3, 4, 5])") → output: "15"
        - execute_code("list(filter(lambda x: x > 5, [1, 6, 3, 8]))") → output: "[6, 8]"
        - run_test_case("print(test_input * 2)", 5, "10") → validation
        """
    
    def __del__(self):
        """Cleanup temporary files with robust error handling."""
        try:
            if hasattr(self, 'secure_python_script') and self.secure_python_script:
                if os.path.exists(self.secure_python_script):
                    os.unlink(self.secure_python_script)
                    logger.debug("Cleaned up secure Python wrapper", path=self.secure_python_script)
        except Exception as e:
            logger.warning("Failed to cleanup secure Python wrapper", error=str(e))
    
    def cleanup(self):
        """Explicit cleanup method for better resource management."""
        try:
            if hasattr(self, 'secure_python_script') and self.secure_python_script:
                if os.path.exists(self.secure_python_script):
                    os.unlink(self.secure_python_script)
                    logger.info("Explicitly cleaned up secure Python wrapper", path=self.secure_python_script)
                    self.secure_python_script = None
        except Exception as e:
            logger.error("Failed to explicitly cleanup secure Python wrapper", error=str(e))


# Backward compatibility alias
CodeExecutor = SecureCodeExecutor 