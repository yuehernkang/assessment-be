import json

def lambda_handler(event, context):
    auth_token = event.get('identitySource', [None])[0]
    
    if not auth_token:
        return generate_response('Deny', 'Unauthorized')
    
    try:
        if auth_token.startswith('Bearer '):
            return generate_response('Allow', 'authorized')
        return generate_response('Deny', 'Invalid token')
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_response('Deny', 'Error processing request')

def generate_response(effect, message):
    return {
        "isAuthorized": effect == 'Allow',
        "context": {
            "message": message
        }
    }