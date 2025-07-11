"""Calculator tool for mathematical computations."""

import ast
import operator
import math
from typing import Dict, Any, Union, List
import structlog

logger = structlog.get_logger()


class CalculatorTool:
    """Safe calculator for mathematical operations."""
    
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
    
    def __init__(self):
        self.enabled = True
        
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Safely evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression as string
            
        Returns:
            Dictionary with result and metadata
        """
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate safely
            result = self._safe_eval(tree.body)
            
            return {
                'success': True,
                'result': result,
                'expression': expression,
                'type': type(result).__name__
            }
            
        except Exception as e:
            logger.error("Calculator error", expression=expression, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'expression': expression
            }
    
    def _safe_eval(self, node: ast.AST) -> Union[int, float, complex, List[Any], tuple]:
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # For Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            if type(node.op) in self.SAFE_OPERATORS:
                return self.SAFE_OPERATORS[type(node.op)](left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            if type(node.op) in self.SAFE_OPERATORS:
                return self.SAFE_OPERATORS[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.SAFE_FUNCTIONS:
                    args = [self._safe_eval(arg) for arg in node.args]
                    return self.SAFE_FUNCTIONS[func_name](*args)
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
            return [self._safe_eval(item) for item in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._safe_eval(item) for item in node.elts)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def solve_quadratic(self, a: float, b: float, c: float) -> Dict[str, Any]:
        """
        Solve quadratic equation ax² + bx + c = 0.
        
        Args:
            a, b, c: Coefficients of the quadratic equation
            
        Returns:
            Dictionary with solutions and metadata
        """
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
                    return {
                        'success': True,
                        'type': 'linear',
                        'solutions': [solution],
                        'discriminant': None,
                        'equation': f"{b}x + {c} = 0"
                    }
            
            # Calculate discriminant
            discriminant = b * b - 4 * a * c
            
            if discriminant > 0:
                # Two real solutions
                sqrt_discriminant = math.sqrt(discriminant)
                x1 = (-b + sqrt_discriminant) / (2 * a)
                x2 = (-b - sqrt_discriminant) / (2 * a)
                return {
                    'success': True,
                    'type': 'quadratic',
                    'solutions': [x1, x2],
                    'discriminant': discriminant,
                    'equation': f"{a}x² + {b}x + {c} = 0"
                }
            elif discriminant == 0:
                # One real solution
                x = -b / (2 * a)
                return {
                    'success': True,
                    'type': 'quadratic',
                    'solutions': [x],
                    'discriminant': discriminant,
                    'equation': f"{a}x² + {b}x + {c} = 0"
                }
            else:
                # Complex solutions
                real_part = -b / (2 * a)
                imag_part = math.sqrt(-discriminant) / (2 * a)
                x1 = complex(real_part, imag_part)
                x2 = complex(real_part, -imag_part)
                return {
                    'success': True,
                    'type': 'quadratic',
                    'solutions': [x1, x2],
                    'discriminant': discriminant,
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
        Verify if a value satisfies an equation.
        
        Args:
            equation: Equation as string (e.g., "x**2 + 5*x + 6")
            variable: Variable name (e.g., "x")
            value: Value to verify
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Replace the variable with the value
            test_expression = equation.replace(variable, f"({value})")
            
            # Calculate the result
            result = self.calculate(test_expression)
            
            if result['success']:
                is_zero = abs(result['result']) < 1e-10  # Account for floating point precision
                return {
                    'success': True,
                    'verified': is_zero,
                    'result': result['result'],
                    'equation': equation,
                    'variable': variable,
                    'value': value
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
            logger.error("Verification error", equation=equation, variable=variable, value=value, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'equation': equation,
                'variable': variable,
                'value': value
            }
    
    def get_tool_description(self) -> str:
        """Get description of calculator tool capabilities."""
        return """
        Calculator Tool - Available for mathematical computations:
        
        **Functions:**
        - calculate(expression): Evaluate mathematical expressions
        - solve_quadratic(a, b, c): Solve quadratic equations
        - verify_solution(equation, variable, value): Verify solutions
        
        **Supported Operations:**
        - Basic arithmetic: +, -, *, /, **, %
        - Math functions: sqrt, sin, cos, tan, log, exp, etc.
        - Constants: pi, e
        - Aggregation: max, min, sum, abs, round
        
        **Examples:**
        - calculate("2 + 3 * 4") → 14
        - solve_quadratic(1, 5, 6) → solutions for x² + 5x + 6 = 0
        - verify_solution("x**2 + 5*x + 6", "x", -2) → True/False
        """ 