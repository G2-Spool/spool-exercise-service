"""Simple Lambda function test."""

def lambda_handler(event, context):
    """Simple Lambda handler for testing."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": '{"message": "Hello from Lambda!", "event": "received"}'
    }