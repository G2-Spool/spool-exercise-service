# System Prompt Architecture Documentation

## Overview

This document describes the refactored system prompt architecture for the Spool Exercise Service. The architecture was completely refactored to eliminate code duplication, centralize fallback logic, and provide a consistent, maintainable approach to prompt generation across all three core generators.

## Architecture Components

### Core Generators

The system consists of three main generators, each with a unified prompt generation architecture:

1. **Exercise Generator** (`app/generators/exercise_generator.py`)
   - Generates personalized educational exercises
   - Integrates with Pinecone for context-aware content
   - Supports teaching personality injection

2. **Response Evaluator** (`app/evaluators/response_evaluator.py`)
   - Evaluates student responses to exercises
   - Provides formative assessment feedback
   - Supports enhanced chain-of-thought evaluation

3. **Remediation Generator** (`app/remediation/remediation_generator.py`)
   - Generates targeted remediation content
   - Addresses specific learning gaps
   - Provides scaffolded practice opportunities

## Refactored Architecture

### 1. Centralized Fallback Logic

**Before:** Scattered conditional checks throughout each generator
**After:** Centralized `_should_use_mock()` method in each class

```python
def _should_use_mock(self) -> bool:
    """Centralized check for mock response usage."""
    key = settings.OPENAI_API_KEY
    return not key or key == "test_key" or key.startswith("test") or key == "your-openai-api-key"
```

**Benefits:**
- Consistent mock logic across all generators
- Single point of maintenance for fallback conditions
- Early returns prevent unnecessary processing
- Easier testing and debugging

### 2. Unified System Prompt Generation

**Before:** Multiple system prompt methods with duplicated logic
**After:** Single `_get_system_prompt()` method with conditional enhanced features

#### Exercise Generator
```python
def _get_system_prompt(self, personality: Optional[str] = None, enhanced: bool = True) -> str:
    """Unified system prompt generator."""
    base_prompt = """
    ## CORE IDENTITY
    You are an expert educational content creator...
    """
    
    enhanced_block = """
    ## ENHANCED CHAIN-OF-THOUGHT PROMPTING
    When creating exercises, follow this enhanced process...
    """ if enhanced else ""
    
    prompt = base_prompt + enhanced_block
    return personality_loader.apply_personality_to_prompt(prompt, personality)
```

#### Response Evaluator
```python
def _get_system_prompt(self, enhanced: bool = True) -> str:
    """Unified system prompt generator."""
    base_prompt = """
    ## CORE IDENTITY
    You are an expert educational evaluator...
    """
    
    enhanced_block = """
    ## ENHANCED CHAIN-OF-THOUGHT EVALUATION PROCESS
    When evaluating responses, follow this enhanced process...
    """ if enhanced else ""
    
    return base_prompt + enhanced_block
```

#### Remediation Generator
```python
def _get_system_prompt(self) -> str:
    """Get system prompt for remediation generation."""
    return """
    ## CORE IDENTITY
    You are an expert educational remediation specialist...
    """
```

**Benefits:**
- Reduced code duplication
- Consistent prompt structure
- Easy to modify and maintain
- Clear separation of base and enhanced features

### 3. Consolidated Prompt Building

**Before:** Multiple specialized prompt methods (e.g., `_create_generation_prompt()`, `_create_enhanced_generation_prompt()`)
**After:** Single `_build_prompt()` method with optional parameters

#### Exercise Generator
```python
def _build_prompt(
    self,
    concept: Dict[str, Any],
    student_profile: Dict[str, Any],
    life_category: str,
    difficulty: str,
    exercise_type: str,
    context_chunks: Optional[List[Dict[str, Any]]] = None,
    similar_exercises: Optional[List[Dict[str, Any]]] = None,
    enhanced: bool = False,
) -> str:
    """Single prompt builder with optional enhanced/context features."""
    # Base prompt construction
    prompt = f"""Create a {difficulty} {exercise_type} exercise..."""
    
    # Add context if available
    if context_chunks:
        prompt += "\n\nRelevant Context from Knowledge Base:\n"
        # Add context chunks
    
    # Add enhanced instructions if requested
    if enhanced:
        prompt += "\n\nENHANCED REQUIREMENTS:\n..."
    
    return prompt
```

#### Response Evaluator
```python
def _build_prompt(
    self,
    exercise: Dict[str, Any],
    student_response: str,
    concept: Dict[str, Any],
    context_chunks: Optional[List[Dict[str, Any]]] = None,
    enhanced: bool = False,
) -> str:
    """Single prompt builder with optional enhanced/context features."""
    # Base prompt construction
    prompt = f"""Evaluate this student's response..."""
    
    # Add context if available
    if context_chunks:
        prompt += "\n\nAdditional Context for Evaluation:\n"
        # Add context chunks
    
    # Add enhanced criteria if requested
    if enhanced:
        prompt += "\n\nENHANCED EVALUATION CRITERIA:\n..."
    
    return prompt
```

#### Remediation Generator
```python
def _build_prompt(
    self,
    concept: Dict[str, Any],
    target_gap: str,
    student_profile: Dict[str, Any],
    original_exercise: Dict[str, Any],
    evaluation: Dict[str, Any],
    remediation_examples: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Single prompt builder with optional enhanced/context features."""
    # Base prompt construction
    prompt = f"""Create targeted remediation content..."""
    
    # Add examples if available
    if remediation_examples:
        prompt += "\n\nRelevant Examples and Explanations:\n"
        # Add examples
    
    return prompt
```

**Benefits:**
- Single method handles all prompt variations
- Conditional logic for optional features
- Consistent parameter handling
- Easier to test and maintain

### 4. Enhanced Features Handling

**Before:** Unclear distinction between "enhanced" and "chain-of-thought" features
**After:** Single boolean parameter controls enhanced features

```python
# Usage examples
system_prompt = self._get_system_prompt(personality, use_enhanced_prompts)
prompt = self._build_prompt(..., enhanced=use_enhanced_prompts)
```

**Benefits:**
- Clear definition of enhanced features
- Consistent parameter naming
- Easy to enable/disable enhanced features
- Simplified method signatures

### 5. Personality Integration

**Before:** Personality injection scattered throughout prompt generation
**After:** Clean personality injection at the end of system prompt generation

```python
def _get_system_prompt(self, personality: Optional[str] = None, enhanced: bool = True) -> str:
    # Build complete prompt first
    prompt = base_prompt + enhanced_block
    
    # Apply personality at the end
    return personality_loader.apply_personality_to_prompt(prompt, personality)
```

**Benefits:**
- Cleaner code structure
- Consistent personality application
- Easy to modify personality logic
- Clear separation of concerns

## Method Reduction Summary

### Exercise Generator
**Before:** 6 methods
- `_get_enhanced_system_prompt()`
- `_create_generation_prompt()`
- `_create_enhanced_generation_prompt()`
- `_create_mock_exercise()`
- `generate()`
- `__init__()`

**After:** 5 methods
- `_get_system_prompt()`
- `_build_prompt()`
- `_should_use_mock()`
- `_create_mock_exercise()`
- `generate()`
- `__init__()`

### Response Evaluator
**Before:** 8 methods
- `_get_system_prompt()`
- `_get_enhanced_system_prompt()`
- `_create_evaluation_prompt()`
- `_create_enhanced_evaluation_prompt()`
- `_create_mock_evaluation()`
- `_create_insufficient_response_evaluation()`
- `evaluate()`
- `__init__()`

**After:** 6 methods
- `_get_system_prompt()`
- `_build_prompt()`
- `_should_use_mock()`
- `_create_mock_evaluation()`
- `_create_insufficient_response_evaluation()`
- `evaluate()`
- `__init__()`

### Remediation Generator
**Before:** 6 methods
- `_get_system_prompt()`
- `_create_remediation_prompt()`
- `_create_enhanced_remediation_prompt()`
- `_create_mock_remediation()`
- `generate()`
- `__init__()`

**After:** 5 methods
- `_get_system_prompt()`
- `_build_prompt()`
- `_should_use_mock()`
- `_create_mock_remediation()`
- `generate()`
- `__init__()`

## Type Safety Improvements

### Optional Parameters

All optional parameters now use proper type annotations:

```python
def _build_prompt(
    self,
    # ... required parameters ...
    context_chunks: Optional[List[Dict[str, Any]]] = None,
    similar_exercises: Optional[List[Dict[str, Any]]] = None,
    enhanced: bool = False,
) -> str:
```

### Benefits
- Better IDE support
- Clearer method signatures
- Runtime type checking
- Improved code documentation

## Testing Strategy

### Mock Response Testing

The centralized `_should_use_mock()` method makes testing easier:

```python
def test_should_use_mock():
    # Test various API key scenarios
    assert generator._should_use_mock() == True  # when key is None
    assert generator._should_use_mock() == True  # when key is "test_key"
    assert generator._should_use_mock() == False # when key is valid
```

### Prompt Generation Testing

The unified prompt methods are easier to test:

```python
def test_build_prompt():
    # Test base prompt
    prompt = generator._build_prompt(concept, profile, "personal", "basic", "initial")
    assert "basic" in prompt
    
    # Test enhanced prompt
    enhanced_prompt = generator._build_prompt(..., enhanced=True)
    assert "ENHANCED" in enhanced_prompt
```

## Performance Considerations

### Reduced Method Calls

The refactored architecture reduces the number of method calls:

**Before:**
```python
# Multiple method calls with duplicated logic
if enhanced and context:
    prompt = self._create_enhanced_generation_prompt(...)
elif context:
    prompt = self._create_enhanced_generation_prompt(...)
else:
    prompt = self._create_generation_prompt(...)
```

**After:**
```python
# Single method call with conditional logic
prompt = self._build_prompt(..., enhanced=enhanced)
```

### Memory Efficiency

- Reduced code duplication saves memory
- Fewer method objects created
- Cleaner string concatenation

## Maintenance Benefits

### Code Consistency

All three generators now follow the same pattern:
1. Check for mock usage
2. Build prompt with optional features
3. Get system prompt with conditional enhancements
4. Make API call or return mock response

### Easy Feature Addition

Adding new features is now simpler:
1. Add parameter to `_build_prompt()`
2. Add conditional logic for the feature
3. Update system prompt if needed

### Debugging

The unified structure makes debugging easier:
- Consistent logging points
- Predictable execution flow
- Clear separation of concerns

## Future Enhancements

### Planned Improvements

1. **Template System**: Move prompt templates to configuration files
2. **Caching**: Implement prompt caching for frequently used combinations
3. **Validation**: Add prompt validation before sending to API
4. **Metrics**: Track prompt effectiveness and usage patterns

### Extensibility

The new architecture supports easy extension:
- New generators can follow the same pattern
- New enhanced features can be added with minimal code changes
- Personality system can be expanded without affecting core logic

## Best Practices

### When to Use Enhanced Features

- **Exercise Generation**: Use enhanced features for complex problem-solving exercises
- **Response Evaluation**: Use enhanced features for detailed formative assessment
- **Remediation**: Enhanced features are optional for remediation generation

### Parameter Guidelines

- Always use `Optional` type annotations for optional parameters
- Use descriptive parameter names (`enhanced` instead of `use_enhanced`)
- Provide sensible defaults for all optional parameters

### Error Handling

- Always implement fallback mechanisms
- Use centralized error handling patterns
- Log appropriate information for debugging

## Conclusion

The refactored system prompt architecture provides:
- **Maintainability**: Consistent structure across all generators
- **Flexibility**: Easy to add new features and modify existing ones
- **Reliability**: Centralized fallback logic and error handling
- **Performance**: Reduced code duplication and method calls
- **Type Safety**: Proper type annotations throughout

This architecture forms the foundation for future AI capabilities and ensures the system can scale effectively while maintaining code quality and developer productivity. 