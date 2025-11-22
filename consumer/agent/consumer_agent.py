"""
QuickQuote Consumer Intake Agent

LiveKit agent that handles voice conversations with customers to collect
job requirements and generate quote requests.
"""

import logging
import json
import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AutoSubscribe,
    JobContext,
    JobProcess,
    JobRequest,
    WorkerOptions,
    cli,
)
from livekit import rtc
import google.generativeai as genai

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt for the agent
INTAKE_PROMPT = """
You are the QuickQuote intake agent. Your job is to extract job details from customer input (text or images) and generate a quote request.

**Your Process:**
1. **Analyze Input**:
   - If an **IMAGE** is provided: Look for the issue (e.g., leaky pipe, long grass, damaged wall). Infer the service type and description from it.
   - If **TEXT** is provided: Extract service, location, and description.

2. **Decide Action**:
   - **CRITICAL**: If you have enough info (Service Type + Location + Rough Description), call `generate_job_summary` **IMMEDIATELY**.
   - Do NOT ask polite filler questions.
   - Do NOT ask for "more details" if the image shows the problem clearly.
   - Only ask a follow-up question if a *critical* piece is missing (like Location).

**Response Style:**
- If calling the tool: "I see the issue. Generating your quote now..."
- If asking a question: "I see the damage. What city is this in?" (Keep it under 10 words).

**Examples:**
- User sends photo of a broken window + "Fix this in SF":
  -> Call `generate_job_summary(service="Window Repair", location="San Francisco", description="Broken window glass")`

- User says "Plumber needed":
  -> You: "Sure. Where are you located and what's the problem?"
"""


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the LiveKit agent.
    
    This function is called when a customer joins a room.
    """
    logger.info(f"Agent starting for room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect()
    
    # Create the agent with instructions and tools
    agent = Agent(
        instructions=INTAKE_PROMPT,
        tools=[generate_job_summary],  # Add custom tools
    )
    
    # Create agent session with STT/LLM only (no TTS - text responses only)
    session = AgentSession(
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=None,  # STT disabled (requires Deepgram or Google Cloud credentials)
        llm=google.LLM(model="gemini-2.0-flash-exp"),  # Gemini LLM
        # No TTS - we'll send text responses to UI instead
    )
    
    # Start the session
    await session.start(agent=agent, room=ctx.room)
    
    # Listen for user speech (transcription)
    @session.on("user_speech_committed")
    def on_user_speech(msg):
        if isinstance(msg, str): return
        # Send transcription to UI
        import asyncio
        asyncio.create_task(ctx.room.local_participant.publish_data(
            json.dumps({
                "type": "transcription",
                "text": msg.content,
                "role": "user"
            }).encode()
        ))

    # Listen for agent speech (text response)
    @session.on("agent_speech_committed")
    def on_agent_speech(msg):
        if isinstance(msg, str): return
        # Send agent response to UI
        import asyncio
        asyncio.create_task(ctx.room.local_participant.publish_data(
            json.dumps({
                "type": "agent_message",
                "text": msg.content
            }).encode()
        ))
    
    # Listen for text/image messages from UI
    @ctx.room.on("data_received")
    def on_data_received(dp):
        try:
            logger.info(f"Raw data received from {dp.participant.identity}: {len(dp.data)} bytes")
            # Decode data
            if isinstance(dp.data, bytes):
                data_str = dp.data.decode("utf-8")
            else:
                data_str = dp.data
                
            msg = json.loads(data_str)
            
            # Import ChatMessage types
            from livekit.agents.llm import ChatMessage, ChatRole, ChatImage
            
            if msg.get("type") == "text":
                text = msg.get("content")
                logger.info(f"Received text message: {text}")
                agent.chat_ctx.append(ChatMessage(role=ChatRole.USER, content=text))
                logger.info("Added message to chat context, triggering response...")
                trigger_response()
                
            elif msg.get("type") == "image":
                image_url = msg.get("url")
                logger.info(f"Received image message: {image_url[:50]}...")
                
                # Create ChatImage content
                image_content = ChatImage(image=image_url) 
                
                agent.chat_ctx.append(ChatMessage(role=ChatRole.USER, content=[image_content]))
                logger.info("Added image to chat context, triggering response...")
                trigger_response()

        except Exception as e:
            logger.error(f"Failed to process data received: {e}", exc_info=True)

    def trigger_response():
        import asyncio
        async def generate_response():
            try:
                logger.info("Calling LLM with context...")
                stream = await session.llm.chat(chat_ctx=agent.chat_ctx)
                full_response = ""
                
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        
                logger.info(f"Generated response: {full_response}")
                
                # Add agent response to context
                from livekit.agents.llm import ChatMessage, ChatRole
                agent.chat_ctx.append(ChatMessage(role=ChatRole.ASSISTANT, content=full_response))
                
                # Send to UI
                await ctx.room.local_participant.publish_data(
                    json.dumps({
                        "type": "agent_message",
                        "text": full_response
                    }).encode()
                )
                logger.info("Sent response to UI")
            except Exception as e:
                logger.error(f"LLM generation failed: {e}", exc_info=True)
        
        asyncio.create_task(generate_response())
    
    logger.info("Agent session started successfully")


async def request_fnc(req: JobRequest) -> None:
    print(f"DEBUG: Received job request for room: {req.room.name}")
    logger.info(f"Received job request for room: {req.room.name}")
    await req.accept(entrypoint)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
        )
    )
