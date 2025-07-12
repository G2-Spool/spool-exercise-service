#!/bin/bash

# Automated deployment script for spool-exercise-service
# This script provides the necessary inputs to the deployment script automatically

echo "Starting automated deployment..."

# Make the deployment script executable
chmod +x ./deploy/deploy.sh

# Run the deployment script with automated inputs
{
    echo "vpc-e5a7949f"                    # VPC ID
    echo "subnet-1b789f7d,subnet-0fb16901" # Subnet IDs
    echo "sg-b969c293"                     # RDS Security Group ID
    echo ""                                # Custom Domain Name (empty)
    echo ""                                # SSL Certificate ARN (empty)
} | ./deploy/deploy.sh

echo "Deployment completed!"
