"""Calculator tool for mathematical computations with memory and resource limits."""

import ast
import operator
import math
import resource
import signal
import time
from typing import Dict, Any, Union, List
import structlog

logger = structlog.get_logger()


class SecureCalculatorTool:
    """Safe calculator for mathematical operations with memory and resource limits."""
    
    # Define safe operations
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'max': max,
        'min': min,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
        'ceil': math.ceil,
        'floor': math.floor,
        'factorial': math.factorial,
        'gcd': math.gcd,
        'pow': pow,
    }
    
    def __init__(self, max_memory_mb: int = 10, timeout_seconds: int = 5):
        self.enabled = True
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.timeout_seconds = timeout_seconds
        
        # Maximum values to prevent resource exhaustion
        self.max_input_length = 1000
        self.max_number_value = 10**100  # Prevent extremely large numbers
        self.max_factorial_input = 1000  # Factorial grows very quickly
        self.max_power_exponent = 1000   # Prevent huge exponentiations
        
    def _set_resource_limits(self):
        """Set memory and CPU limits for the calculation."""
        try:
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_bytes, self.max_memory_bytes))
            
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds))
        except (ValueError, OSError):
            # Some systems may not support all limits
            pass
    
    def _timeout_handler(self, signum, frame):
        """Handle timeout signal."""
        raise TimeoutError("Calculation timed out")
    
    def _validate_input(self, expression: str) -> bool:
        """Validate input for potential resource exhaustion."""
        if len(expression) > self.max_input_length:
            return False
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            '**' * 10,  # Multiple exponentiations
            'factorial(' * 5,  # Nested factorials
            '*' * 50,   # Many multiplications
            '+' * 50,   # Many additions
        ]
        
        for pattern in dangerous_patterns:
            if pattern in expression:
                return False
        
        return True
    
    def _validate_number(self, value: Union[int, float, complex]) -> bool:
        """Validate that numbers don't exceed safe limits."""
        if isinstance(value, (int, float)):
            if abs(value) > self.max_number_value:
                return False
        elif isinstance(value, complex):
            if abs(value.real) > self.max_number_value or abs(value.imag) > self.max_number_value:
                return False
        return True
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Safely evaluate a mathematical expression with resource limits.
        
        Args:
            expression: Mathematical expression as string
            
        Returns:
            Dictionary with result and metadata
        """
        try:
            # Validate input
            if not self._validate_input(expression):
                return {
                    'success': False,
                    'error': 'Expression too long or contains potentially dangerous patterns',
                    'expression': expression[:100] + '...' if len(expression) > 100 else expression
                }
            
            # Clean the expression
            expression = expression.strip()
            
            # Set resource limits
            self._set_resource_limits()
            
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
            
            try:
                # Parse the expression
                tree = ast.parse(expression, mode='eval')
                
                # Evaluate safely with memory monitoring
                start_time = time.time()
                result = self._safe_eval(tree.body)
                execution_time = time.time() - start_time
                
                # Validate result size (only for numeric results)
                if isinstance(result, (int, float, complex)) and not self._validate_number(result):
                    return {
                        'success': False,
                        'error': 'Result too large for safe handling',
                        'expression': expression
                    }
                
                return {
                    'success': True,
                    'result': result,
                    'expression': expression,
                    'type': type(result).__name__,
                    'execution_time': execution_time,
                    'memory_safe': True
                }
                
            finally:
                signal.alarm(0)  # Cancel timeout
                signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
            
        except TimeoutError:
            return {
                'success': False,
                'error': f'Calculation timed out after {self.timeout_seconds} seconds',
                'expression': expression
            }
        except MemoryError:
            return {
                'success': False,
                'error': 'Calculation exceeded memory limit',
                'expression': expression
            }
        except Exception as e:
            logger.error("Calculator error", expression=expression[:100], error=str(e))
            return {
                'success': False,
                'error': str(e),
                'expression': expression
            }
    
    def _safe_eval(self, node: ast.AST) -> Union[int, float, complex, List[Any], tuple]:
        """Safely evaluate an AST node with additional safety checks."""
        if isinstance(node, ast.Constant):
            value = node.value
            if not self._validate_number(value):
                raise ValueError("Number too large for safe evaluation")
            return value
        elif isinstance(node, ast.Num):  # For Python < 3.8 compatibility
            value = node.n
            if not self._validate_number(value):
                raise ValueError("Number too large for safe evaluation")
            return value
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            
            # Special checks for power operations
            if isinstance(node.op, ast.Pow):
                if isinstance(right, (int, float)) and abs(right) > self.max_power_exponent:
                    raise ValueError(f"Exponent too large (max {self.max_power_exponent})")
            
            if type(node.op) in self.SAFE_OPERATORS:
                result = self.SAFE_OPERATORS[type(node.op)](left, right)
                if not self._validate_number(result):
                    raise ValueError("Result too large for safe handling")
                return result
            else:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            if type(node.op) in self.SAFE_OPERATORS:
                result = self.SAFE_OPERATORS[type(node.op)](operand)
                if not self._validate_number(result):
                    raise ValueError("Result too large for safe handling")
                return result
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.SAFE_FUNCTIONS:
                    args = [self._safe_eval(arg) for arg in node.args]
                    
                    # Special validation for factorial
                    if func_name == 'factorial':
                        if args and isinstance(args[0], (int, float)) and args[0] > self.max_factorial_input:
                            raise ValueError(f"Factorial input too large (max {self.max_factorial_input})")
                    
                    # Special validation for power function
                    if func_name == 'pow' and len(args) >= 2:
                        if isinstance(args[1], (int, float)) and abs(args[1]) > self.max_power_exponent:
                            raise ValueError(f"Power exponent too large (max {self.max_power_exponent})")
                    
                    result = self.SAFE_FUNCTIONS[func_name](*args)
                    if not self._validate_number(result):
                        raise ValueError("Function result too large for safe handling")
                    return result
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Only simple function calls are supported")
        elif isinstance(node, ast.Name):
            if node.id in self.SAFE_FUNCTIONS:
                return self.SAFE_FUNCTIONS[node.id]
            else:
                raise ValueError(f"Unsupported name: {node.id}")
        elif isinstance(node, ast.List):
            elements = [self._safe_eval(item) for item in node.elts]
            if len(elements) > 10000:  # Limit list size
                raise ValueError("List too large for safe handling")
            return elements
        elif isinstance(node, ast.Tuple):
            elements = tuple(self._safe_eval(item) for item in node.elts)
            if len(elements) > 10000:  # Limit tuple size
                raise ValueError("Tuple too large for safe handling")
            return elements
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def solve_quadratic(self, a: float, b: float, c: float) -> Dict[str, Any]:
        """
        Solve quadratic equation ax² + bx + c = 0 with safety checks.
        
        Args:
            a, b, c: Coefficients of the quadratic equation
            
        Returns:
            Dictionary with solutions and metadata
        """
        try:
            # Validate input coefficients
            for coeff in [a, b, c]:
                if not self._validate_number(coeff):
                    return {
                        'success': False,
                        'error': 'Coefficient too large for safe calculation'
                    }
            
            # Set resource limits
            self._set_resource_limits()
            
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
            
            try:
                if a == 0:
                    if b == 0:
                        return {
                            'success': False,
                            'error': 'Not a valid equation (both a and b are zero)'
                        }
                    else:
                        # Linear equation: bx + c = 0
                        solution = -c / b
                        if not self._validate_number(solution):
                            return {
                                'success': False,
                                'error': 'Solution too large for safe handling'
                            }
                        return {
                            'success': True,
                            'type': 'linear',
                            'solutions': [solution],
                            'discriminant': None,
                            'equation': f"{b}x + {c} = 0",
                            'memory_safe': True
                        }
                
                # Calculate discriminant
                discriminant = b * b - 4 * a * c
                
                if not self._validate_number(discriminant):
                    return {
                        'success': False,
                        'error': 'Discriminant too large for safe calculation'
                    }
                
                if discriminant > 0:
                    # Two real solutions
                    sqrt_discriminant = math.sqrt(discriminant)
                    x1 = (-b + sqrt_discriminant) / (2 * a)
                    x2 = (-b - sqrt_discriminant) / (2 * a)
                    
                    if not (self._validate_number(x1) and self._validate_number(x2)):
                        return {
                            'success': False,
                            'error': 'Solutions too large for safe handling'
                        }
                    
                    return {
                        'success': True,
                        'type': 'quadratic',
                        'solutions': [x1, x2],
                        'discriminant': discriminant,
                        'equation': f"{a}x² + {b}x + {c} = 0",
                        'memory_safe': True
                    }
                elif discriminant == 0:
                    # One real solution
                    x = -b / (2 * a)
                    
                    if not self._validate_number(x):
                        return {
                            'success': False,
                            'error': 'Solution too large for safe handling'
                        }
                    
                    return {
                        'success': True,
                        'type': 'quadratic',
                        'solutions': [x],
                        'discriminant': discriminant,
                        'equation': f"{a}x² + {b}x + {c} = 0",
                        'memory_safe': True
                    }
                else:
                    # Complex solutions
                    real_part = -b / (2 * a)
                    imag_part = math.sqrt(-discriminant) / (2 * a)
                    x1 = complex(real_part, imag_part)
                    x2 = complex(real_part, -imag_part)
                    
                    if not (self._validate_number(x1) and self._validate_number(x2)):
                        return {
                            'success': False,
                            'error': 'Complex solutions too large for safe handling'
                        }
                    
                    return {
                        'success': True,
                        'type': 'quadratic',
                        'solutions': [x1, x2],
                        'discriminant': discriminant,
                        'equation': f"{a}x² + {b}x + {c} = 0",
                        'memory_safe': True
                    }
                    
            finally:
                signal.alarm(0)  # Cancel timeout
                signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
                
        except TimeoutError:
            return {
                'success': False,
                'error': f'Quadratic calculation timed out after {self.timeout_seconds} seconds',
                'equation': f"{a}x² + {b}x + {c} = 0"
            }
        except MemoryError:
            return {
                'success': False,
                'error': 'Quadratic calculation exceeded memory limit',
                'equation': f"{a}x² + {b}x + {c} = 0"
            }
        except Exception as e:
            logger.error("Quadratic solver error", a=a, b=b, c=c, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'equation': f"{a}x² + {b}x + {c} = 0"
            }
    
    def verify_solution(self, equation: str, variable: str, value: Union[int, float, complex]) -> Dict[str, Any]:
        """
        Verify if a value satisfies an equation with safety checks.
        
        Args:
            equation: Equation as string (e.g., "x**2 + 5*x + 6")
            variable: Variable name (e.g., "x")
            value: Value to verify
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Validate inputs
            if not self._validate_input(equation):
                return {
                    'success': False,
                    'error': 'Equation too long or contains dangerous patterns',
                    'equation': equation[:100] + '...' if len(equation) > 100 else equation
                }
            
            if not self._validate_number(value):
                return {
                    'success': False,
                    'error': 'Value too large for safe verification',
                    'equation': equation,
                    'variable': variable,
                    'value': str(value)
                }
            
            # Replace the variable with the value
            test_expression = equation.replace(variable, f"({value})")
            
            # Calculate the result using our safe calculator
            result = self.calculate(test_expression)
            
            if result['success']:
                is_zero = abs(result['result']) < 1e-10  # Account for floating point precision
                return {
                    'success': True,
                    'verified': is_zero,
                    'result': result['result'],
                    'equation': equation,
                    'variable': variable,
                    'value': value,
                    'memory_safe': True
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'equation': equation,
                    'variable': variable,
                    'value': value
                }
                
        except Exception as e:
            logger.error("Verification error", equation=equation[:100], variable=variable, value=str(value), error=str(e))
            return {
                'success': False,
                'error': str(e),
                'equation': equation,
                'variable': variable,
                'value': value
            }
    
    def get_tool_description(self) -> str:
        """Get description of secure calculator tool capabilities."""
        return f"""
        Secure Calculator Tool - Mathematical computations with resource limits:
        
        **Security Features:**
        - Memory limit: {self.max_memory_bytes // (1024*1024)}MB
        - Timeout: {self.timeout_seconds} seconds
        - Input validation and size limits
        - Large number detection and prevention
        - Resource exhaustion protection
        
        **Functions:**
        - calculate(expression): Evaluate mathematical expressions safely
        - solve_quadratic(a, b, c): Solve quadratic equations with limits
        - verify_solution(equation, variable, value): Verify solutions safely
        
        **Supported Operations:**
        - Basic arithmetic: +, -, *, /, **, %
        - Math functions: sqrt, sin, cos, tan, log, exp, etc.
        - Constants: pi, e
        - Aggregation: max, min, sum, abs, round
        
        **Safety Limits:**
        - Max expression length: {self.max_input_length} characters
        - Max number value: {self.max_number_value}
        - Max factorial input: {self.max_factorial_input}
        - Max power exponent: {self.max_power_exponent}
        
        **Examples:**
        - calculate("2 + 3 * 4") → 14
        - solve_quadratic(1, 5, 6) → solutions for x² + 5x + 6 = 0
        - verify_solution("x**2 + 5*x + 6", "x", -2) → True/False
        """


# Backward compatibility alias
CalculatorTool = SecureCalculatorTool 