import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_client_ip(event: Dict[str, Any]) -> Optional[str]:
    """Extract client IP from various possible locations in the event"""
    try:
        # Try to get IP from API Gateway
        if 'requestContext' in event:
            if 'http' in event['requestContext']:
                # HTTP API Gateway v2
                return event['requestContext']['http'].get('sourceIp')
            elif 'identity' in event['requestContext']:
                # REST API Gateway v1
                return event['requestContext']['identity'].get('sourceIp')
        
        # If headers are present, check for X-Forwarded-For
        headers = event.get('headers', {})
        if headers and 'x-forwarded-for' in headers:
            return headers['x-forwarded-for'].split(',')[0].strip()
        
        return None
    except Exception as e:
        logger.error(f"Error extracting client IP: {str(e)}")
        return None

def validate_request(event: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate if the request is coming from API Gateway
    Returns: (is_valid: bool, error_message: str)
    """
    try:
        # Check if request came from API Gateway
        if 'requestContext' not in event:
            return False, "Request not from API Gateway"
        
        # Verify required API Gateway context
        request_context = event.get('requestContext', {})
        if not request_context.get('http') and not request_context.get('apiId'):
            return False, "Invalid API Gateway request context"
        
        return True, ""
    except Exception as e:
        logger.error(f"Error validating request: {str(e)}")
        return False, "Error validating request"

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to process API Gateway requests and extract client IP
    """
    logger.info("Processing new request")
    logger.debug(f"Event: {json.dumps(event)}")
    
    try:
        # Validate request source
        is_valid, error_message = validate_request(event)
        if not is_valid:
            logger.warning(f"Invalid request: {error_message}")
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': error_message,
                    'status': 'failed',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Extract client IP
        client_ip = get_client_ip(event)
        if not client_ip:
            logger.warning("Could not extract client IP")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Could not determine client IP',
                    'status': 'failed',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Process the request
        response_data = {
            'message': 'Request processed successfully',
            'client_ip': client_ip,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id if context else 'local-test',
            'status': 'success'
        }
        
        # Add API Gateway specific information if available
        if 'requestContext' in event and 'http' in event['requestContext']:
            response_data['method'] = event['requestContext']['http'].get('method')
            response_data['path'] = event['requestContext']['http'].get('path')
        
        logger.info(f"Successfully processed request from IP: {client_ip}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Custom-Header': 'API Gateway Request'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'status': 'failed',
                'timestamp': datetime.utcnow().isoformat()
            })
        }