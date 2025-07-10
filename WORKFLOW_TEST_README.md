# Comprehensive Exercise Workflow Test

This test suite provides a complete evaluation of the exercise workflow system with four different student personas. It simulates the entire process from exercise generation to evaluation and remediation.

## Test Scenarios

### 1. Perfect Student
- **Profile**: Methodical, thorough, demonstrates complete understanding
- **Response Style**: Systematic step-by-step approach, proper verification
- **Expected Outcome**: High understanding score (>0.8), mastery achieved

### 2. Good Student with Mistakes
- **Profile**: Generally understands concepts but makes calculation errors
- **Response Style**: Shows good process but has gaps in execution
- **Expected Outcome**: Moderate understanding score (0.5-0.8), some remediation needed

### 3. Struggling Student
- **Profile**: Trying hard but lacks clarity on methods
- **Response Style**: Shows effort but confusion about approaches
- **Expected Outcome**: Low understanding score (<0.5), needs significant remediation

### 4. Lazy Student
- **Profile**: Wants answers without effort, minimal engagement
- **Response Style**: Asks for answers directly, shows no work
- **Expected Outcome**: Very low understanding score (<0.3), needs remediation

## Running the Test

### Step 1: Test API Setup (Recommended)
First, verify your OpenAI API key is working:
```bash
cd spool-exercise-service
python test_api_setup.py
```

### Step 2: Run the Comprehensive Test

#### Option 1: Using the Runner Script (Recommended)
```bash
cd spool-exercise-service
python run_workflow_test.py
```

#### Option 2: Direct Execution
```bash
cd spool-exercise-service
python comprehensive_workflow_test.py
```

#### Option 3: Using Python Module
```bash
cd spool-exercise-service
python -m comprehensive_workflow_test
```

## Prerequisites

The test requires the following packages:
- `structlog` - For structured logging
- `openai` - For OpenAI API integration (REQUIRED - makes real API calls)
- `langgraph` - For workflow orchestration
- `python-dotenv` - For loading environment variables from .env file

Install with:
```bash
pip install structlog openai langgraph python-dotenv
```

### Environment Setup

**IMPORTANT**: This test makes real OpenAI API calls and requires a valid API key.

1. Create a `.env` file in the `spool-exercise-service` directory:
```bash
# .env
OPENAI_API_KEY=your-actual-openai-api-key-here
ENVIRONMENT=development
GENERATION_MODEL=gpt-4o
EVALUATION_MODEL=gpt-4o
TEMPERATURE=0.7
MAX_TOKENS=2000
MIN_RESPONSE_LENGTH=50
MAX_RETRIES=3
WORKFLOW_TIMEOUT=300
```

2. Make sure your OpenAI API key has sufficient credits for the test (~$0.05-0.15 per run).

## Test Output

The test generates several output files in the `test_results/` directory:

### 1. Scenario Files
- `scenario_1_perfect_student_[timestamp].json` - Detailed results for perfect student
- `scenario_2_good_student_with_mistakes_[timestamp].json` - Results for good student with mistakes
- `scenario_3_struggling_student_[timestamp].json` - Results for struggling student
- `scenario_4_lazy_student_[timestamp].json` - Results for lazy student

### 2. Summary Files
- `comprehensive_summary_[timestamp].json` - JSON summary with analytics
- `readable_report_[timestamp].txt` - Human-readable analysis report

## Understanding the Results

### Key Metrics
- **Understanding Score**: 0.0-1.0 scale measuring comprehension
- **Mastery Achieved**: Boolean indicating if student met mastery criteria
- **Needs Remediation**: Boolean indicating if additional help is needed
- **Competency Map**: Detailed breakdown of correct/missing/incorrect steps

### Sample Output Structure
```json
{
  "scenario": {
    "name": "Perfect Student",
    "description": "Student who succeeds flawlessly",
    "student_id": "perfect_student_001",
    "interests": ["mathematics", "problem-solving", "physics"]
  },
  "exercise": {
    "exercise_id": "uuid",
    "content": {
      "scenario": "Career-focused quadratic equation problem",
      "problem": "Step-by-step solution required",
      "expected_steps": ["identify", "method", "solve", "verify"],
      "hints": ["progressive hints"]
    }
  },
  "evaluation": {
    "understanding_score": 0.95,
    "mastery_achieved": true,
    "needs_remediation": false,
    "competency_map": {
      "correct_steps": ["All major steps"],
      "missing_steps": [],
      "incorrect_steps": []
    },
    "feedback": "Excellent work! Complete understanding demonstrated."
  },
  "timing": {
    "duration_seconds": 2.5
  }
}
```

## Analysis Features

### Performance Distribution
- Average understanding scores across all scenarios
- Mastery achievement rates
- Remediation trigger rates

### Workflow Insights
- Differentiation between student types
- Evaluation accuracy assessment
- Remediation system effectiveness

### Recommendations
- Automatic suggestions for system improvements
- Difficulty calibration recommendations
- Mastery criteria adjustments

## Customization

### Adding New Scenarios
1. Add new scenario to the `scenarios` list in `run_comprehensive_test()`
2. Create a corresponding response generator method
3. Define student profile and interests

### Modifying Student Responses
Edit the response generator methods:
- `_generate_perfect_response()`
- `_generate_good_with_mistakes_response()`
- `_generate_struggling_response()`
- `_generate_lazy_response()`

### Changing Test Concept
Modify the `concept_data` dictionary in `_run_scenario()` to test different subject areas.

## Interpreting Results

### Successful Test Indicators
- ✅ Perfect student achieves >0.8 understanding score
- ✅ Struggling student scores <0.5 but shows effort recognition
- ✅ Lazy student receives appropriate low score
- ✅ Remediation triggers for appropriate students
- ✅ Feedback is constructive and specific

### Potential Issues
- ❌ All students receive similar scores (poor differentiation)
- ❌ Perfect student doesn't achieve mastery (criteria too strict)
- ❌ Lazy student achieves high score (evaluation too lenient)
- ❌ No remediation triggered (system not identifying gaps)

## Troubleshooting

### Common Issues
1. **Import Errors**: Install missing dependencies with `pip install structlog openai langgraph python-dotenv`
2. **Missing API Key**: Ensure `OPENAI_API_KEY` is set in `.env` file
3. **API Rate Limits**: OpenAI may throttle requests; test will retry automatically
4. **Insufficient Credits**: Check your OpenAI account has sufficient API credits
5. **Permission Errors**: Ensure write permissions for `test_results/` directory
6. **Timeout Errors**: Increase `WORKFLOW_TIMEOUT` environment variable for slower connections

### Environment Variables
The test loads from `.env` file, but you can override:
- `OPENAI_API_KEY`: Your OpenAI API key (REQUIRED)
- `ENVIRONMENT`: Test environment (default: 'development')
- `GENERATION_MODEL`: Model for exercise generation (default: 'gpt-4o')
- `EVALUATION_MODEL`: Model for response evaluation (default: 'gpt-4o')
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `WORKFLOW_TIMEOUT`: Timeout in seconds (default: 300)
- `TEMPERATURE`: OpenAI temperature setting (default: 0.7)

## Expected Runtime

- **Total Duration**: 30-90 seconds (with real API calls)
- **Per Scenario**: 5-20 seconds
- **API Call Overhead**: 2-5 seconds per exercise generation + evaluation
- **Cost**: Approximately $0.05-0.15 per full test run

## Use Cases

### Quality Assurance
- Validate exercise generation quality
- Verify evaluation accuracy
- Test remediation triggering

### Development Testing
- Regression testing after system changes
- Performance benchmarking
- Integration testing

### Educational Analysis
- Understanding student response patterns
- Calibrating difficulty levels
- Improving feedback quality

## Next Steps

After running the test:
1. Review the readable report for high-level insights
2. Examine individual scenario files for detailed analysis
3. Compare results across multiple test runs
4. Use insights to refine the exercise system
5. Adjust parameters based on recommendations

---

For questions or issues, refer to the main service documentation or contact the development team. 