# QuickQuote Consumer App

Voice-first customer intake system using LiveKit Agents and OpenAI GPT-4o.

## Features

- 🎤 **Real-time voice conversations** with AI agent
- 💬 **Multimodal input** - voice, text, and images
- 🎨 **Premium mobile-native UI** - Uber/Airbnb quality design
- ⚡ **Instant quote requests** - Get quotes in seconds
- 🤖 **Intelligent follow-ups** - GPT-4o asks clarifying questions

## Prerequisites

- Python 3.10+
- OpenAI API key (for GPT-4o LLM + Whisper STT)
- LiveKit account (free tier available at https://cloud.livekit.io)
- ElevenLabs API key (free tier available at https://elevenlabs.io)

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and add your keys:
```bash
cp .env.example .env
```

Required keys:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (from LiveKit Cloud)
- `GOOGLE_API_KEY` (for Gemini LLM and Google STT)

### 3. Run the Application

```bash
# Terminal 1: Start LiveKit agent worker
python agent/consumer_agent.py start

# Terminal 2: Start FastAPI backend
uvicorn api.main:app --reload --port 8000
```

### 4. Open in Browser

Navigate to `http://localhost:8000` and click "Start Call" to begin!

## Project Structure

```
consumer/
├── agent/
│   ├── consumer_agent.py    # Main LiveKit agent
│   └── tools.py              # Custom tools (job summary)
├── api/
│   ├── main.py               # FastAPI application
│   └── models.py             # Pydantic models
├── static/
│   ├── index.html            # Premium mobile UI
│   ├── style.css             # Styling
│   └── app.js                # LiveKit client integration
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. **Customer starts call** - Clicks voice button, connects to LiveKit room
2. **Agent greets customer** - AI agent asks what service they need
3. **Conversation flows** - GPT-4o intelligently asks follow-up questions
4. **Quote submitted** - Agent generates job summary and calls Provider API

## API Endpoints

### `GET /`
Serves the chat UI

### `POST /api/token`
Generates LiveKit room token for customer

Request:
```json
{
  "session_id": "string",
  "user_id": "string"
}
```

Response:
```json
{
  "token": "string",
  "url": "string",
  "room": "string"
}
```

### `POST /provider/request-quote`
Provider API stub (returns mock quote)

Request:
```json
{
  "service_type": "string",
  "location": "string",
  "description": "string",
  ...
}
```

Response:
```json
{
  "status": "received",
  "quote_id": "string"
}
```

## Development

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Deployment

See deployment guide in `docs/deployment.md` (coming soon)

## License

MIT
