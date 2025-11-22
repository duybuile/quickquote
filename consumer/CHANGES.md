# QuickQuote - Simplified Text-Based Flow

## ✅ Changes Made

**Removed:**
- ❌ ElevenLabs TTS (no voice output)
- ❌ Voice responses from agent

**Kept:**
- ✅ Voice input (OpenAI Whisper STT)
- ✅ Text input
- ✅ Image input
- ✅ GPT-4o for understanding

**New Flow:**
```
Customer Input (voice/text/image)
    ↓
OpenAI Whisper (if voice) → Text
    ↓
GPT-4o extracts job details
    ↓
Agent calls Provider API
    ↓
Display quote results in UI (text/visual)
```

## Benefits

1. **Simpler** - No voice output complexity
2. **Cheaper** - No TTS costs
3. **Faster** - Text responses are instant
4. **Better UX** - Users can see and review quotes visually

## What Changed

### Backend (`consumer_agent.py`)
- Removed TTS configuration
- Agent now sends text messages via data channel
- Simplified system prompt for concise text responses

### Frontend (`app.js`)
- Handles text messages from agent
- Displays messages in chat UI
- Added quote results display function

### Dependencies
- Removed `elevenlabs` from requirements
- Removed `ELEVEN_API_KEY` from .env

## Next Steps

1. **Restart the agent** to load new code:
   ```bash
   # Stop current agent (Ctrl+C)
   python agent/consumer_agent.py start
   ```

2. **Refresh browser** to load new JavaScript

3. **Test the flow:**
   - Click voice button or type message
   - Agent responds with text (no voice)
   - Quotes display visually in UI

## To Do

- [ ] Build out real Provider API integration
- [ ] Design quote results UI styling
- [ ] Add loading states for quote fetching
- [ ] Handle error cases
