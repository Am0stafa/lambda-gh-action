import json
import logging
import time
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def validate_parameters(query_params: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validates the incoming query parameters.
    Returns (is_valid, error_message)
    """
    if not query_params:
        return False, "No query parameters provided ya dodo"
    
    name = query_params.get('name', '').strip()
    age_str = query_params.get('age', '')
    
    if not name:
        return False, "Name parameter is required ya dodo"
    
    if age_str:
        try:
            age = int(age_str)
            if age < 0 or age > 150:
                return False, "Age must be between 0 and 150"
        except ValueError:
            return False, "Age must be a valid number"
    
    return True, None

def log_request_metrics(event: Dict[str, Any], start_time: float) -> None:
    """
    Logs various metrics about the request
    """
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    logger.info({
        "requestId": event.get('requestContext', {}).get('requestId', 'N/A'),
        "httpMethod": event.get('requestContext', {}).get('http', {}).get('method', 'N/A'),
        "path": event.get('requestContext', {}).get('http', {}).get('path', 'N/A'),
        "duration": f"{duration:.2f}ms",
        "timestamp": datetime.utcnow().isoformat(),
        "sourceIp": event.get('requestContext', {}).get('http', {}).get('sourceIp', 'N/A')
    })

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function
    """
    start_time = time.time()
    
    try:
        # Log the raw event for debugging
        logger.debug(f"Received event: {json.dumps(event)}")
        
        # Extract query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Validate parameters
        is_valid, error_message = validate_parameters(query_params)
        
        if not is_valid:
            logger.warning(f"Validation failed: {error_message}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': error_message,
                    'status': 'failed'
                })
            }
        
        # Process valid request
        name = query_params.get('name')
        age = query_params.get('age')
        
        # Log successful processing
        logger.info(f"Processing request for name: {name}, age: {age}")
        
        # Simulate different status codes based on age
        status_code = 200
        if age and int(age) < 18:
            logger.info("Underage user detected")
            status_code = 202
        
        response_body = {
            'message': f"Hello {name}!",
            'age_provided': age,
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        # Log metrics before returning
        log_request_metrics(event, start_time)
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'X-Custom-Header': 'Lambda Demo'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'status': 'error'
            })
        }