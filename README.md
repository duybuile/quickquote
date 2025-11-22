# Plumber's Bidding Agent

A real-time, voice-activated AI Agent designed to help plumbers capture job details via voice and instantly generate structured, accurate, and competitively priced bids.

## 🏗️ Architecture

The system consists of two main components:

1.  **Consumer**: The client-side application (Voice Agent) that interacts with the user via LiveKit. It captures audio, transcribes it, and sends structured data to the Provider.
2.  **Provider**: The backend logic that powers the intelligence. It hosts the Knowledge Base (Weaviate), performs RAG (Retrieval-Augmented Generation), and uses Google Gemini to generate the final quote.

These two components communicate via a **FastAPI** service.

## 🚀 Prerequisites

*   Python 3.10+
*   **Weaviate**: A Weaviate instance (Cloud or Local).
*   **Google Gemini API Key**: For the LLM.
*   **LiveKit Credentials**: For real-time audio/video (if running the Consumer).

## 🛠️ Setup & Installation

### 1. Environment Variables

Create a `.env` file in the root directory with the following keys:

```env
# Weaviate Configuration
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key

# LiveKit Configuration (for Consumer)
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

### 2. Provider Setup (Backend)

The Provider handles data ingestion and quote generation.

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Knowledge Base:**
    *   **Setup Schema:** Creates the `PlumberRates` collection in Weaviate.
        ```bash
        python provider/setup_weaviate.py
        ```
    *   **Ingest Data:** Loads plumber rates and services from `data/` into Weaviate.
        ```bash
        python provider/ingest_rates.py
        ```

3.  **Run the API Service:**
    Start the FastAPI server to listen for quote requests.
    ```bash
    uvicorn provider.api:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.
    *   **Endpoint:** `POST /generate-quote`
    *   **Docs:** `http://127.0.0.1:8000/docs`

### 3. Consumer Setup (Frontend/Agent)

Navigate to the `consumer` directory for specific instructions on running the Voice Agent.

```bash
cd consumer
# Follow instructions in consumer/README.md
```

## 🧪 Testing the Provider

You can test the Provider independently using the CLI script or the API.

**CLI Test:**
Generates a quote based on `data/customer/henry_john.json`.
```bash
python provider/generate_quote.py
```

**API Test:**
Send a POST request to `http://127.0.0.1:8000/generate-quote` with a JSON body:
```json
{
  "customer_name": "John Doe",
  "issue": "Leaky faucet in the kitchen",
  "address": "123 Main St",
  "phone": "555-0123",
  "email": "john@example.com",
  "urgency": "Low",
  "preferred_time": "Morning"
}
```