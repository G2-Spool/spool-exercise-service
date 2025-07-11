#!/bin/bash

# Script to update AWS Parameter Store with required secrets for Exercise Service

set -e

# Configuration
AWS_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Setting up AWS Parameter Store secrets for Exercise Service${NC}"

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

# Function to create or update parameter
create_or_update_parameter() {
    local param_name="$1"
    local param_value="$2"
    local param_type="$3"
    
    if aws ssm get-parameter --name "$param_name" --region "$AWS_REGION" &> /dev/null; then
        echo -e "${YELLOW}📝 Updating existing parameter: $param_name${NC}"
        aws ssm put-parameter \
            --name "$param_name" \
            --value "$param_value" \
            --type "$param_type" \
            --overwrite \
            --region "$AWS_REGION"
    else
        echo -e "${GREEN}✨ Creating new parameter: $param_name${NC}"
        aws ssm put-parameter \
            --name "$param_name" \
            --value "$param_value" \
            --type "$param_type" \
            --region "$AWS_REGION"
    fi
}

# Prompt for secrets
echo -e "${YELLOW}🔑 Please provide the following secrets:${NC}"
echo -e "${YELLOW}⚠️  These will be stored securely in AWS Parameter Store${NC}"
echo

# OpenAI API Key
read -s -p "OpenAI API Key: " OPENAI_API_KEY
echo

# Pinecone API Key
read -s -p "Pinecone API Key: " PINECONE_API_KEY
echo

# PostgreSQL Database URL
read -s -p "PostgreSQL Database URL: " POSTGRES_URL
echo

# Validation
if [[ -z "$OPENAI_API_KEY" || -z "$PINECONE_API_KEY" || -z "$POSTGRES_URL" ]]; then
    echo -e "${RED}❌ All secrets are required. Please try again.${NC}"
    exit 1
fi

# Create parameters in AWS Parameter Store
echo -e "${GREEN}📤 Storing secrets in AWS Parameter Store...${NC}"

create_or_update_parameter "/spool/openai-api-key" "$OPENAI_API_KEY" "SecureString"
create_or_update_parameter "/spool/pinecone-api-key" "$PINECONE_API_KEY" "SecureString"
create_or_update_parameter "/spool/postgres-url" "$POSTGRES_URL" "SecureString"

# Additional configuration parameters
echo -e "${GREEN}⚙️  Setting up configuration parameters...${NC}"

create_or_update_parameter "/spool/environment" "production" "String"
create_or_update_parameter "/spool/pinecone-index-name" "spool-content" "String"
create_or_update_parameter "/spool/pinecone-environment" "us-east-1-aws" "String"
create_or_update_parameter "/spool/pinecone-namespace" "content" "String"
create_or_update_parameter "/spool/cors-origins" '["*"]' "String"

echo -e "${GREEN}✅ All parameters have been stored successfully!${NC}"

# List created parameters
echo -e "${GREEN}📋 Created/Updated parameters:${NC}"
echo "  • /spool/openai-api-key"
echo "  • /spool/pinecone-api-key"
echo "  • /spool/postgres-url"
echo "  • /spool/environment"
echo "  • /spool/pinecone-index-name"
echo "  • /spool/pinecone-environment"
echo "  • /spool/pinecone-namespace"
echo "  • /spool/cors-origins"

echo -e "${GREEN}🔒 Secrets are now stored securely in AWS Parameter Store${NC}"
echo -e "${YELLOW}⚠️  Remember to set appropriate IAM permissions for your Lambda function to access these parameters${NC}"