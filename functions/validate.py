import json
from cloudflare.workers.types import Response

# This function is automatically triggered for requests to /validate
def onRequest(context):
    """Validates the server for Puch AI by returning a phone number."""
    # IMPORTANT: Remember to replace the placeholder with your own number.
    phone_number = {
        "number": "+919876543210" 
    }
    # Cloudflare Functions must return a Response object
    return Response(json.dumps(phone_number), headers={'Content-Type': 'application/json'})
