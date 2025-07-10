# Exercise Service Scripts

This directory contains streamlined testing and development scripts for the spool-exercise-service. The scripts have been consolidated to eliminate redundancy while preserving all essential functionality.

## 📁 Script Overview

### 🔧 Core Testing Scripts

#### `test_system.py`
**Comprehensive system testing suite**
- **Purpose**: Validates environment setup, imports, API connections, and service configuration
- **Consolidates**: API setup, imports testing, basic functionality validation
- **Use Case**: Run first to ensure your development environment is properly configured

```bash
# Run complete system test
python test_system.py

# Expected output: Pass/fail status for all core dependencies
```

#### `test_pinecone.py`
**Complete Pinecone vector search testing**
- **Purpose**: Tests all Pinecone functionality including vector search, context retrieval, and service integration
- **Consolidates**: 5 previous Pinecone test scripts with overlapping functionality
- **Use Case**: Validate vector search capabilities and educational context enhancement

```bash
# Run comprehensive Pinecone tests
python test_pinecone.py

# Tests: Configuration, connection, vector search, concept searches, interest integration, service integration
```

#### `test_workflow.py`
**End-to-end workflow testing with realistic scenarios**
- **Purpose**: Tests complete exercise workflow with 4 different student personas
- **Features**: Real API calls, detailed result analysis, comprehensive reporting
- **Use Case**: Validate the entire exercise generation → evaluation → remediation workflow

```bash
# Run complete workflow test
python test_workflow.py

# Output: Detailed JSON and Markdown reports in test_results/ directory
```

### 🎭 Development & Support Scripts

#### `mock_services.py`
**Mock services for testing without dependencies**
- **Purpose**: Provides mock content service and exercise service endpoints
- **Features**: Realistic API responses, configurable ports, CORS support
- **Use Case**: Test exercise service when other services are not available

```bash
# Run both mock services (ports 8001 & 8003)
python mock_services.py both

# Run only mock content service (port 8001)
python mock_services.py content

# Run only mock exercise service (port 8003)
python mock_services.py simple
```

## 🚀 Quick Start Guide

### 1. Environment Setup
```bash
# Ensure you have a .env file with required variables:
OPENAI_API_KEY=your-actual-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=spool-textbook-embeddings
REDIS_URL=redis://localhost:6379
CONTENT_SERVICE_URL=http://localhost:8001
```

### 2. Run System Check
```bash
python test_system.py
```
This validates your environment setup and dependencies.

### 3. Test Pinecone Integration
```bash
python test_pinecone.py
```
This verifies vector search capabilities.

### 4. Run Workflow Test
```bash
python test_workflow.py
```
This tests the complete exercise generation workflow.

## 📊 Test Results

### System Test Output
- ✅/❌ Environment variables validation
- ✅/❌ Import testing for all dependencies
- ✅/❌ API connection verification
- ✅/❌ Service component imports
- 📈 Overall success rate percentage

### Pinecone Test Output
- ✅/❌ Configuration and connection tests
- ✅/❌ Vector search functionality
- ✅/❌ Concept-based searches across mathematics
- ✅/❌ Interest-based contextual searches
- ✅/❌ Service integration with exercise components
- 💡 Enhanced exercise generation demonstrations

### Workflow Test Output
- 📁 `test_results/` directory with timestamped results
- 📊 `workflow_test_results.json` - Raw test data
- 📖 `workflow_test_report.md` - Human-readable analysis
- 🎯 Success rates for different student personas
- 📈 Understanding scores and mastery achievement rates

## 🔍 Troubleshooting

### Common Issues

**Environment Variables Missing**
```bash
# Error: OPENAI_API_KEY not set
# Solution: Create/update .env file with valid API keys
```

**Import Errors**
```bash
# Error: Import "pinecone" could not be resolved
# Solution: Install dependencies with pip install -r requirements.txt
```

**API Connection Failures**
```bash
# Error: OpenAI API Connection failed
# Solution: Verify API key is valid and has sufficient credits
```

**Pinecone Index Not Found**
```bash
# Error: Index 'spool-textbook-embeddings' not found
# Solution: Verify index name in environment variables or create index
```

### Development Tips

1. **Run tests in sequence**: System → Pinecone → Workflow
2. **Use mock services** when developing without full infrastructure
3. **Check test_results/** for detailed analysis after workflow tests
4. **Monitor API usage** during comprehensive testing

## 🧹 Cleanup Results

### Removed Redundant Scripts
The following 13 scripts were consolidated to eliminate redundancy:

**Pinecone Testing (5 scripts → 1)**
- ❌ `test_comprehensive_pinecone.py`
- ❌ `test_enhanced_exercise_demo.py`
- ❌ `test_fresh_pinecone.py`
- ❌ `test_direct_pinecone.py`
- ❌ `test_pinecone_integration.py`
- ✅ **→ `test_pinecone.py`**

**Basic Testing (4 scripts → 1)**
- ❌ `test_api_setup.py`
- ❌ `test_imports.py`
- ❌ `simple_test.py`
- ❌ `debug_test.py`
- ✅ **→ `test_system.py`**

**Workflow Testing (2 scripts → 1)**
- ❌ `comprehensive_workflow_test.py`
- ❌ `run_workflow_test.py`
- ✅ **→ `test_workflow.py`**

**Mock Services (2 scripts → 1)**
- ❌ `mock_content_service.py`
- ❌ `simple_server.py`
- ✅ **→ `mock_services.py`**

### Benefits of Consolidation
- 📉 **Reduced from 13 to 4 scripts** (69% reduction)
- 🔄 **Eliminated redundant functionality**
- 📖 **Improved maintainability** with single-responsibility scripts
- 🚀 **Streamlined developer experience**
- 📊 **Better organized testing workflows**

## 📋 Script Responsibilities

| Script | Purpose | Dependencies | Output |
|--------|---------|--------------|---------|
| `test_system.py` | Environment & basic functionality | Core Python packages | Console status |
| `test_pinecone.py` | Vector search testing | Pinecone, OpenAI | Console status |
| `test_workflow.py` | End-to-end workflow | All exercise components | JSON + Markdown reports |
| `mock_services.py` | Development support | FastAPI, uvicorn | Running web services |

Each script is designed to be run independently and provides clear, actionable feedback about the system state. 