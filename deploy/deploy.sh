#!/bin/bash

# Spool Exercise Service Lambda Deployment Script
# This script deploys the Exercise Service to AWS Lambda with API Gateway

set -e

# Configuration
STACK_NAME="spool-exercise-service"
AWS_REGION="us-east-1"
ENVIRONMENT="production"
LAMBDA_FUNCTION_NAME="$STACK_NAME-exercise-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Spool Exercise Service to AWS Lambda${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get current AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}📋 Using AWS Account: $AWS_ACCOUNT_ID${NC}"

# Prompt for required parameters
echo -e "${YELLOW}📝 Please provide the following information:${NC}"
read -p "VPC ID: " VPC_ID
read -p "Subnet IDs (comma-separated): " SUBNET_IDS
read -p "RDS Security Group ID: " RDS_SECURITY_GROUP_ID
read -p "Custom Domain Name (optional): " DOMAIN_NAME
read -p "SSL Certificate ARN (optional): " CERTIFICATE_ARN

# Convert comma-separated subnets to proper format
SUBNET_LIST=$(echo "$SUBNET_IDS" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//')

# Create deployment package
echo -e "${GREEN}📦 Creating deployment package...${NC}"
rm -rf dist/
mkdir -p dist/
cp -r app/ dist/
cp lambda_handler.py dist/
cp requirements.txt dist/

# Install dependencies
echo -e "${GREEN}📥 Installing dependencies...${NC}"
cd dist/
pip install -r requirements.txt -t .
cd ..

# Create ZIP file
echo -e "${GREEN}🗜️  Creating ZIP file...${NC}"
cd dist/
zip -r ../lambda-deployment.zip . -x "*.pyc" "*/__pycache__/*"
cd ..

# Deploy CloudFormation stack
echo -e "${GREEN}☁️  Deploying CloudFormation stack...${NC}"
aws cloudformation deploy \
    --template-file cloudformation/lambda-deployment.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        VpcId="$VPC_ID" \
        SubnetIds="$SUBNET_LIST" \
        RDSSecurityGroupId="$RDS_SECURITY_GROUP_ID" \
        DomainName="$DOMAIN_NAME" \
        CertificateArn="$CERTIFICATE_ARN" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

# Update Lambda function code
echo -e "${GREEN}🔄 Updating Lambda function code...${NC}"
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file fileb://lambda-deployment.zip \
    --region "$AWS_REGION"

# Wait for update to complete
echo -e "${GREEN}⏳ Waiting for Lambda function update to complete...${NC}"
aws lambda wait function-updated \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION"

# Get API Gateway endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`APIGatewayEndpoint`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🔗 API Gateway Endpoint: $API_ENDPOINT${NC}"

# Test the deployment
echo -e "${GREEN}🧪 Testing deployment...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT/health")
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed. HTTP Status: $HTTP_STATUS${NC}"
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${GREEN}📊 Monitor logs with: aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow${NC}"

# Clean up
rm -rf dist/
rm -f lambda-deployment.zip

echo -e "${GREEN}🧹 Cleaned up temporary files${NC}"