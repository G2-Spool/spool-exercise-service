# Spool Exercise Service

Exercise generation, evaluation, and remediation service with LangGraph orchestration for the Spool platform.

## Overview

The Exercise Service is responsible for:

- **Dynamic Exercise Generation**: Create personalized exercises based on student interests
- **Response Evaluation**: Analyze student explanations to identify understanding gaps
- **Remediation Content**: Generate targeted help for specific misconceptions
- **LangGraph Orchestration**: Coordinate complex LLM workflows for adaptive learning
- **Interest Integration**: Personalize all content using student interest profiles

## Architecture

```
Exercise Request → LangGraph Orchestration → Exercise Generation
                           ↓
                  Response Evaluation
                           ↓
                    Gap Analysis
                           ↓
                 Remediation Generation
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker
- OpenAI API key
- Access to Content Service
- Access to Student Profile Service

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Run locally:
```bash
uvicorn app.main:app --reload --port 8003
```

### Docker

```bash
# Build
docker build -t spool-exercise-service .

# Run
docker run -p 8003:8003 spool-exercise-service
```

## API Endpoints

### Health Check
```
GET /health
```

### Exercise Generation
```
POST /api/exercise/generate
  - Generate initial exercise for a concept
  - Body: {
      "concept_id": "string",
      "student_id": "string",
      "student_interests": ["array"],
      "life_category": "personal|career|social|philanthropic",
      "difficulty": "basic|intermediate|advanced"
    }

POST /api/exercise/generate-advanced
  - Generate advanced exercise after initial completion
  - Body: {
      "concept_id": "string",
      "student_id": "string",
      "previous_exercise_id": "string"
    }
```

### Exercise Evaluation
```
POST /api/exercise/evaluate
  - Evaluate student's thought process explanation
  - Body: {
      "exercise_id": "string",
      "student_response": "string",
      "student_id": "string"
    }
  - Returns: {
      "evaluation_id": "string",
      "mastery_achieved": boolean,
      "competency_map": {
        "correct_steps": ["array"],
        "missing_steps": ["array"],
        "incorrect_steps": ["array"]
      },
      "feedback": "string",
      "needs_remediation": boolean
    }
```

### Remediation
```
POST /api/exercise/remediation/generate
  - Generate targeted remediation for gaps
  - Body: {
      "evaluation_id": "string",
      "focus_gap": "string"
    }

GET /api/exercise/remediation/{remediation_id}
  - Get remediation content
```

### Progress Tracking
```
GET /api/exercise/history/{student_id}
  - Get student's exercise history

GET /api/exercise/mastery/{student_id}/{concept_id}
  - Check mastery status for a concept
```

## LangGraph Workflows

### Exercise Generation Workflow
```python
Start → Extract Concept → Personalize Context → Generate Exercise → Validate → End
```

### Evaluation Workflow
```python
Start → Parse Response → Extract Steps → Compare to Solution → Identify Gaps → Generate Feedback → End
```

### Remediation Workflow
```python
Start → Analyze Gap → Generate Explanation → Create Practice → Validate Understanding → End
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key
- `LANGCHAIN_API_KEY`: LangChain API key (optional)
- `CONTENT_SERVICE_URL`: URL of content service
- `PROFILE_SERVICE_URL`: URL of profile service
- `REDIS_URL`: Redis connection for caching
- `EVALUATION_MODEL`: Model for evaluation (default: gpt-4o)
- `GENERATION_MODEL`: Model for generation (default: gpt-4o)
- `MAX_RETRIES`: Max retries for LLM calls
- `EXERCISE_CACHE_TTL`: Cache TTL in seconds

## Data Models

### Exercise Structure
```python
{
  "exercise_id": "uuid",
  "concept_id": "uuid",
  "student_id": "uuid",
  "type": "initial|advanced",
  "content": {
    "scenario": "string",
    "problem": "string",
    "hints": ["array"],
    "expected_steps": ["array"]
  },
  "personalization": {
    "interests_used": ["array"],
    "life_category": "string"
  },
  "created_at": "datetime"
}
```

### Evaluation Structure
```python
{
  "evaluation_id": "uuid",
  "exercise_id": "uuid",
  "student_response": "string",
  "analysis": {
    "identified_steps": ["array"],
    "competency_map": {
      "correct": ["array"],
      "missing": ["array"],
      "incorrect": ["array"]
    },
    "understanding_score": 0.0-1.0
  },
  "mastery_achieved": boolean,
  "feedback": "string"
}
```

### Remediation Structure
```python
{
  "remediation_id": "uuid",
  "evaluation_id": "uuid",
  "target_gap": "string",
  "content": {
    "explanation": "string",
    "examples": ["array"],
    "practice_problems": ["array"]
  },
  "personalized_context": "string"
}
```

## LangGraph Implementation

### State Management
```python
class ExerciseState(TypedDict):
    concept: dict
    student_profile: dict
    exercise_type: str
    generated_exercise: dict
    student_response: str
    evaluation: dict
    remediation: dict
```

### Node Functions
- `fetch_concept`: Get concept from content service
- `fetch_student_profile`: Get student interests
- `generate_exercise`: Create personalized exercise
- `evaluate_response`: Analyze student explanation
- `identify_gaps`: Find understanding gaps
- `generate_remediation`: Create targeted help

### Edge Logic
- Conditional edges based on mastery achievement
- Retry logic for failed generations
- Fallback paths for error handling

## Monitoring

### Metrics
- Exercise generation time
- Evaluation accuracy
- Remediation effectiveness
- Student progress rates
- LLM token usage

### Logging
Structured JSON logging with:
- Exercise generation details
- Evaluation results
- Remediation tracking
- Error analysis

## Development

### Testing
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests
pytest
```

### Code Quality
```bash
# Linting
ruff check app

# Type checking
mypy app

# Format code
black app
```

## Deployment

### AWS ECS
```bash
# Build and push to ECR
./scripts/build-and-push.sh

# Deploy to ECS
./scripts/deploy-ecs.sh
```

### Required Resources
- ECS task with 1GB memory minimum
- Redis for caching
- Access to other microservices

## Troubleshooting

### Common Issues

1. **Exercise Generation Timeout**
   - Check OpenAI API limits
   - Increase timeout settings
   - Enable caching

2. **Evaluation Accuracy**
   - Review prompt templates
   - Check solution step definitions
   - Validate competency mapping

3. **Remediation Not Helping**
   - Analyze gap identification
   - Review personalization logic
   - Check student profile data

## License

Copyright © 2024 Spool. All rights reserved.