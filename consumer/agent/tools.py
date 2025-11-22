"""
Custom tools for the QuickQuote consumer agent.
"""

from livekit.agents import function_tool
import httpx
import logging

logger = logging.getLogger(__name__)


@function_tool
async def generate_job_summary(
    context,
    service_type: str,
    location: str,
    description: str,
    size: str = None,
    urgency: str = "normal",
):
    """
    Generate and submit a job summary to the provider API.
    
    Call this tool when you have collected enough information from the customer
    to create a quote request.
    
    Args:
        service_type: Type of service needed (e.g., "lawn care", "plumbing", "painting")
        location: Customer's location (city or full address)
        description: Detailed description of the job from the customer
        size: Optional size/scope information (e.g., "1000 sq ft", "3 bedrooms")
        urgency: How urgent the job is ("normal", "urgent", "emergency")
    
    Returns:
        A confirmation message for the customer
    """
    logger.info(f"Generating job summary for {service_type} in {location}")
    
    # Build the job summary payload
    summary = {
        "service_type": service_type,
        "location": location,
        "description": description,
        "inferred_details": {
            "area_size": size,
            "urgency": urgency,
        },
        "customer_messages": [],  # Would include conversation history
        "media": {
            "image_urls": [],  # Would include any uploaded images
            "image_descriptions": [],
        },
    }
    
    try:
        # Call the Provider API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/provider/request-quote",
                json=summary,
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
        
        quote_id = result.get("quote_id", "unknown")
        logger.info(f"Quote request submitted successfully: {quote_id}")
        
        # Publish quote results to UI
        import json
        await context.room.local_participant.publish_data(
            json.dumps({
                "type": "quote_result",
                "quotes": [
                    {
                        "provider": "QuickQuote Pro",
                        "price": "150-200",
                        "details": f"Standard {service_type} service"
                    },
                    {
                        "provider": "Local Expert",
                        "price": "180",
                        "details": "Premium service with warranty"
                    }
                ]
            }).encode()
        )
        
        return (
            f"Perfect! I've submitted your quote request for {service_type} in {location}. "
            f"I've sent the quote details to your screen!"
        )
        
    except Exception as e:
        logger.error(f"Failed to submit quote request: {e}")
        return (
            "I've collected all your information, but there was a technical issue submitting "
            "the request. Please try again in a moment, or contact support."
        )
