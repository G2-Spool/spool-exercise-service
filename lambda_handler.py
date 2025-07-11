"""AWS Lambda handler for Exercise Service."""

import json
import os
from typing import Dict, Any

from mangum import Mangum
from app.main import app

# Set environment to production for Lambda
os.environ["ENVIRONMENT"] = "production"

# Create the Lambda handler
handler = Mangum(app, lifespan="off")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        HTTP response dictionary
    """
    try:
        # Use mangum to handle the ASGI app
        return handler(event, context)
    except Exception as e:
        # Log error and return 500 response
        print(f"Lambda handler error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }