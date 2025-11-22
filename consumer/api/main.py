"""
FastAPI backend for QuickQuote consumer app.

Provides endpoints for:
- Serving the chat UI
- Direct chat API with Gemini
- Provider API stub
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
import google.generativeai as genai
from typing import Optional, List, Dict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import dotenv_values
env_config = dotenv_values(".env")
google_api_key = env_config.get("GOOGLE_API_KEY")

# Fallback to os.getenv if not in .env file
if not google_api_key:
    google_api_key = os.getenv("GOOGLE_API_KEY")

if google_api_key:
    genai.configure(api_key=google_api_key)
    logger.info(f"✅ Google API Key loaded: {google_api_key[:10]}...")
else:
    logger.error("❌ GOOGLE_API_KEY not found in environment!")

# Create FastAPI app
app = FastAPI(title="QuickQuote Consumer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory conversation storage (use Redis/DB in production)
conversations: Dict[str, List[Dict]] = {}

# System prompt for the agent
INTAKE_PROMPT = """
You are the QuickQuote intake agent. Your job is to extract detailed job information from the customer to generate a precise quote request.

**Your Process:**
1. **Analyze Input**: Extract the following fields:
   - **Customer Name**: (If not provided, ask or use "Valued Customer")
   - **Issue**: A RICH description. Include symptoms, duration, and any attempted fixes.
   - **Address**: Location of the job.
   - **Urgency**: Low, Medium, or High.
   - **Preferred Date**: When they want the service.

2. **Decide Action**:
   - If you have the **Issue** and **Address**, you can proceed.
   - If the issue description is too vague (e.g., "it's broken"), ask for more details like "What exactly is happening?" or "How long has it been going on?"
   - If urgency or date are missing, infer them or ask.

**Response Format:**
- For follow-up questions: Just respond with plain text.
- When ready to generate quote: Respond with JSON in this exact format:
```json
{
  "action": "generate_quote",
  "customer_name": "Mr. Henry Johnson",
  "issue": "Water is continuously running...",
  "address": "45 Willow Creek Lane",
  "urgency": "Medium",
  "preferred_date": "Tuesday morning"
}
```

**Examples:**
- User: "I need a plumber"
  You: "Sure! What is the address and the specific problem?"

- User: "My toilet is running at 123 Main St. Need it fixed ASAP."
  You: ```json
{
  "action": "generate_quote",
  "customer_name": "Valued Customer",
  "issue": "Toilet running continuously",
  "address": "123 Main St",
  "urgency": "High",
  "preferred_date": "ASAP"
}
```
"""


# Pydantic models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    image_url: Optional[str] = None

class TokenRequest(BaseModel):
    session_id: str
    user_id: str
    name: str

# LiveKit Configuration
LIVEKIT_URL = env_config.get("LIVEKIT_URL") or os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = env_config.get("LIVEKIT_API_KEY") or os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = env_config.get("LIVEKIT_API_SECRET") or os.getenv("LIVEKIT_API_SECRET")

if LIVEKIT_API_KEY:
    logger.info(f"✅ LiveKit API Key loaded: {LIVEKIT_API_KEY[:5]}...")
else:
    logger.error("❌ LIVEKIT_API_KEY not found!")

if LIVEKIT_API_SECRET:
    logger.info("✅ LiveKit API Secret loaded")
else:
    logger.error("❌ LIVEKIT_API_SECRET not found!")

@app.post("/api/token")
async def get_token(req: TokenRequest):
    """Generate LiveKit token for the frontend."""
    from livekit import api
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured")

    grant = api.VideoGrant(room_join=True, room=f"quote-session-{req.session_id}")
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(req.user_id) \
        .with_name(req.name) \
        .with_grants(grant) \
        .to_jwt()

    return {"token": token, "url": LIVEKIT_URL}


class ChatResponse(BaseModel):
    response: str
    quotes: Optional[List[Dict]] = None


class JobSummary(BaseModel):
    service_type: str
    location: str
    description: str
    inferred_details: dict
    customer_messages: list
    media: dict


class QuoteResponse(BaseModel):
    status: str
    quote_id: str
    message: str


# Helper function to generate mock quotes
def generate_mock_quotes(customer_name: str, issue: str, address: str, urgency: str, preferred_date: str) -> List[Dict]:
    """Generate mock quotes based on detailed job info."""
    
    # LOG THE FINAL JOB SUMMARY
    logger.info("="*60)
    logger.info("📝 FINAL JOB SUMMARY GENERATED (Ready for Provider API)")
    logger.info(f"   Customer Name:  {customer_name}")
    logger.info(f"   Issue:          {issue}")
    logger.info(f"   Address:        {address}")
    logger.info(f"   Urgency:        {urgency}")
    logger.info(f"   Preferred Date: {preferred_date}")
    logger.info("="*60)

    base_price = 100
    if "plumb" in issue.lower() or "toilet" in issue.lower():
        base_price = 150
    elif "electric" in issue.lower():
        base_price = 200
    
    if urgency.lower() in ["high", "asap", "emergency"]:
        base_price += 50

    return [
        {
            "provider": "ProFix Services",
            "price": base_price,
            "rating": 4.8,
            "eta": "Tomorrow" if urgency != "High" else "Today"
        },
        {
            "provider": "Budget Handyman",
            "price": int(base_price * 0.8),
            "rating": 4.2,
            "eta": "3 days"
        },
        {
            "provider": "Premium Home Care",
            "price": int(base_price * 1.5),
            "rating": 4.9,
            "eta": "Today"
        }
    ]


# Routes
@app.get("/")
async def root():
    """Serve the chat UI"""
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Direct chat endpoint with Gemini.
    Handles conversation state and triggers quote generation when ready.
    """
    try:
        if not google_api_key:
            raise HTTPException(status_code=500, detail="Google API key not configured")
        
        # Get or create conversation history
        session_id = request.session_id
        if session_id not in conversations:
            conversations[session_id] = []
        
        history = conversations[session_id]
        
        # Create Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=INTAKE_PROMPT
        )
        
        # Build chat history for Gemini
        chat_history = []
        for msg in history:
            chat_history.append({
                "role": msg["role"],
                "parts": [msg["content"]]
            })
        
        # Start chat session
        chat_session = model.start_chat(history=chat_history)
        
        # Send user message
        if request.image_url:
            # Handle image input (future enhancement)
            response = chat_session.send_message(request.message)
        else:
            response = chat_session.send_message(request.message)
        
        agent_response = response.text
        
        # Store in history
        history.append({"role": "user", "content": request.message})
        history.append({"role": "model", "content": agent_response})
        
        logger.info(f"Chat [{session_id}] User: {request.message}")
        logger.info(f"Chat [{session_id}] Agent: {agent_response}")
        
        # Check if response contains quote trigger (JSON)
        quotes = None
        if "```json" in agent_response or '"action": "generate_quote"' in agent_response:
            try:
                # Extract JSON from response
                json_start = agent_response.find("{")
                json_end = agent_response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    quote_data = json.loads(agent_response[json_start:json_end])
                    
                    if quote_data.get("action") == "generate_quote":
                        # Generate quotes
                        quotes = generate_mock_quotes(
                            customer_name=quote_data.get("customer_name", "Valued Customer"),
                            issue=quote_data.get("issue", "General Repair"),
                            address=quote_data.get("address", "Unknown"),
                            urgency=quote_data.get("urgency", "Standard"),
                            preferred_date=quote_data.get("preferred_date", "Flexible")
                        )
                        agent_response = "I've generated a detailed quote request for you!"
                        logger.info(f"Generated {len(quotes)} quotes")
            except json.JSONDecodeError:
                logger.warning("Failed to parse quote JSON from agent response")
        
        return ChatResponse(
            response=agent_response,
            quotes=quotes
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/provider/request-quote", response_model=QuoteResponse)
async def request_quote(summary: JobSummary):
    """
    Provider API stub - accepts quote requests and returns mock response.
    
    In production, this would forward the request to actual service providers.
    """
    logger.info(f"📋 Quote request received:")
    logger.info(f"   Service: {summary.service_type}")
    logger.info(f"   Location: {summary.location}")
    logger.info(f"   Description: {summary.description}")
    
    # Generate mock quote ID
    quote_id = f"QQ-{hash(summary.service_type + summary.location) % 10000:04d}"
    
    return QuoteResponse(
        status="received",
        quote_id=quote_id,
        message="Quote request submitted to providers",
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
