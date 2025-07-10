# Spool Exercise Service

AI-powered exercise generation, evaluation, and remediation service for the Spool educational platform.

**Status:** ✅ Enhanced with Pinecone Vector Search Integration

## Overview

The Exercise Service is responsible for:

- **Exercise Generation**: Create personalized exercises based on student profiles and interests
- **Response Evaluation**: Evaluate student responses and identify understanding gaps
- **Remediation**: Generate targeted remediation content for learning gaps
- **Vector Context**: **NEW** - Enhanced content generation using Pinecone vector search for relevant educational context

## 🚀 New Features

### Pinecone Vector Search Integration

The service now integrates with Pinecone vector database to provide:

- **Enhanced Exercise Generation**: Uses relevant educational content from the knowledge base
- **Context-Aware Evaluation**: More accurate assessment using educational references
- **Targeted Remediation**: Examples and explanations pulled from similar concepts
- **Intelligent Fallback**: Gracefully falls back to standard prompts if vector search fails

### Configuration

Add these environment variables for Pinecone integration:

```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=spool-content
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_NAMESPACE=content
PINECONE_TOP_K=5

# Content Service Integration
CONTENT_SERVICE_SEARCH_URL=http://localhost:8002/api/content/search
ENABLE_VECTOR_CONTEXT=true
```

### Testing the Integration

Run the integration test:

```bash
python test_pinecone_integration.py
```

This will test all components with and without Pinecone context.

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Pinecone account (optional but recommended)
- Content service running (for vector search)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Run the service:
```bash
uvicorn app.main:app --reload --port 8003
```

## API Endpoints

### Exercise Generation
```
POST /api/exercise/generate
```
**Enhanced**: Now includes context from Pinecone vector search

### Response Evaluation
```
POST /api/exercise/evaluate
```
**Enhanced**: More accurate evaluation using educational context

### Remediation
```
POST /api/exercise/remediate
```
**Enhanced**: Targeted examples and explanations from knowledge base

### Workflow Testing
```
POST /api/exercise/workflow
```
Complete workflow test with enhanced context

## Architecture

### Enhanced Processing Flow

```
Student Request → Vector Search → Enhanced Prompt → LLM → Response
                      ↓
                 Knowledge Base
                 (Pinecone)
```

### Fallback Strategy

1. **Primary**: Use enhanced prompts with Pinecone context
2. **Fallback**: Standard prompts if vector search fails
3. **Mock**: Test responses if no API keys configured

## Development

### Running Tests

```bash
# Basic tests
pytest tests/

# Integration test
python test_pinecone_integration.py

# Workflow test
python comprehensive_workflow_test.py
```

### Service Dependencies

- **Content Service**: Provides vector search capabilities
- **OpenAI API**: For exercise generation and evaluation
- **Pinecone**: For vector search and context retrieval

## Deployment

### Environment Variables

Production deployment requires:

```bash
ENVIRONMENT=production
OPENAI_API_KEY=from_aws_parameter_store
PINECONE_API_KEY=from_aws_parameter_store
CONTENT_SERVICE_SEARCH_URL=https://content-service-url/api/content/search
```

### AWS Parameter Store

Keys are automatically loaded from AWS Parameter Store in production:
- `/spool/openai-api-key`
- `/spool/pinecone-api-key`

## Monitoring

Monitor the enhanced features:

- Vector search success rates
- Context retrieval latency
- Fallback activation frequency
- Enhanced vs standard prompt usage

## Contributing

When adding new features:

1. Test with vector context enabled
2. Ensure graceful fallback to standard prompts
3. Update integration tests
4. Document new configuration options

---

**Enhanced with Pinecone Vector Search** - Providing smarter, more contextual educational content generation.