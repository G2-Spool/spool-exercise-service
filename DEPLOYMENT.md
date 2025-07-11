# AWS Lambda Deployment Guide

This guide provides step-by-step instructions for deploying the Spool Exercise Service to AWS Lambda with API Gateway integration.

## 🏗️ Architecture Overview

```
Amplify Frontend → API Gateway → Lambda Function → RDS PostgreSQL
                       ↓
                Parameter Store (Secrets)
                       ↓
                Pinecone Vector DB
```

## 📋 Prerequisites

### AWS Resources Required
- **VPC** with private subnets for Lambda
- **RDS PostgreSQL** database instance
- **Security Groups** configured for Lambda-to-RDS communication
- **SSL Certificate** (optional, for custom domain)
- **AWS CLI** configured with appropriate permissions

### IAM Permissions Required
Your AWS user/role needs permissions for:
- Lambda functions (create, update, invoke)
- API Gateway (create, deploy, manage)
- CloudFormation (create, update, delete stacks)
- Parameter Store (read, write parameters)
- VPC (describe subnets, security groups)
- IAM (create execution roles)

## 🚀 Deployment Steps

### Step 1: Configure AWS Parameter Store

First, set up the required secrets in AWS Parameter Store:

```bash
./deploy/update-parameters.sh
```

This script will prompt you for:
- OpenAI API Key
- Pinecone API Key
- PostgreSQL Database URL
- Other configuration parameters

### Step 2: Deploy the Lambda Function

Run the deployment script:

```bash
./deploy/deploy.sh
```

The script will prompt you for:
- **VPC ID**: Your VPC identifier
- **Subnet IDs**: Comma-separated list of private subnet IDs
- **RDS Security Group ID**: Security group that allows Lambda access to RDS
- **Custom Domain Name**: (Optional) Your custom domain
- **SSL Certificate ARN**: (Optional) SSL certificate for custom domain

### Step 3: Verify Deployment

The deployment script will automatically:
1. Create a CloudFormation stack
2. Deploy the Lambda function
3. Configure API Gateway
4. Run a health check

## 🔧 Configuration Details

### Environment Variables

The Lambda function uses these environment variables:
- `ENVIRONMENT=production`
- `AWS_REGION=us-east-1`
- `CORS_ORIGINS=["*"]`

### Parameter Store Keys

The following parameters are automatically loaded in production:
- `/spool/openai-api-key` - OpenAI API key
- `/spool/pinecone-api-key` - Pinecone API key
- `/spool/postgres-url` - PostgreSQL connection string
- `/spool/environment` - Environment setting
- `/spool/pinecone-index-name` - Pinecone index name
- `/spool/cors-origins` - CORS configuration

### Database Configuration

The service connects to PostgreSQL using:
- Connection pooling (2-10 connections)
- 60-second command timeout
- Automatic retry logic
- Health check monitoring

## 🌐 API Endpoints

After deployment, these endpoints will be available:

### Base URL
```
https://your-api-id.execute-api.us-east-1.amazonaws.com/production
```

### Health Check
```
GET /health
```

### Exercise Generation
```
POST /api/exercise/generate
```

### Response Evaluation
```
POST /api/exercise/evaluate
```

### Remediation
```
POST /api/exercise/remediate
```

## 🔍 Monitoring and Logs

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/spool-exercise-service-exercise-service --follow
```

### Health Monitoring
The `/health` endpoint provides status for:
- Redis cache
- LangGraph workflow
- Database connection (production only)

### Metrics
Prometheus metrics are available at `/metrics` (non-production only).

## 🐛 Troubleshooting

### Common Issues

1. **Lambda timeout**: Increase timeout in CloudFormation template
2. **Database connection failed**: Check VPC configuration and security groups
3. **Parameter Store access denied**: Verify IAM permissions
4. **Cold start issues**: Consider provisioned concurrency

### Debugging Steps

1. Check CloudWatch logs for detailed error messages
2. Verify Parameter Store parameters are correctly set
3. Test database connectivity from Lambda
4. Validate API Gateway configuration

### Health Check Failures

If health checks fail:
1. Check Lambda function logs
2. Verify environment variables
3. Test Parameter Store access
4. Validate database connection

## 🔄 Updates and Maintenance

### Code Updates
```bash
# Update Lambda function code only
aws lambda update-function-code \
    --function-name spool-exercise-service-exercise-service \
    --zip-file fileb://lambda-deployment.zip
```

### Configuration Updates
```bash
# Update CloudFormation stack
aws cloudformation update-stack \
    --stack-name spool-exercise-service \
    --template-body file://cloudformation/lambda-deployment.yaml
```

### Parameter Updates
```bash
# Update individual parameter
aws ssm put-parameter \
    --name "/spool/openai-api-key" \
    --value "new-api-key" \
    --type "SecureString" \
    --overwrite
```

## 🏷️ Resource Tagging

All resources are tagged with:
- `Environment: production`
- `Service: exercise-service`

## 💰 Cost Optimization

- Lambda is billed per request and execution time
- API Gateway charges per request
- RDS costs depend on instance type and storage
- Parameter Store has no additional charges for standard parameters

## 🔐 Security Best Practices

1. **Secrets Management**: All secrets stored in Parameter Store
2. **Network Security**: Lambda in private subnets
3. **IAM Least Privilege**: Minimal required permissions
4. **Encryption**: Data encrypted at rest and in transit
5. **CORS**: Properly configured for frontend access

## 📞 Support

For deployment issues:
1. Check CloudWatch logs
2. Review CloudFormation events
3. Verify Parameter Store configuration
4. Test health endpoints

---

**Next Steps**: After successful deployment, integrate the API Gateway endpoint with your Amplify frontend application.