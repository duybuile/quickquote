# 🛠️ Antigravity Project: The Plumber's Bidding Agent

**GOAL:** Build a real-time, voice-activated AI Agent that allows a non-technical SMB (plumber) to capture job details via voice and instantly generate a structured, accurate, and competitively priced bid for the APE AI Quote Marketplace.

**CORE AGENT:** Bidding Orchestrator (using Gemini 3 Pro/supported LLM)
**CRITICAL OUTPUT:** Strict JSON object containing the finalized bid data.
**DEVELOPMENT FOLDER: provider/**

---

## PHASE 1: Environment Setup & Tool Integration

**Objective:** Configure the Agent's access to external APIs and define the foundational environment.

### 1. Agent Identity & Project Setup

* **Antigravity View:** Agent Manager
* **Prompt/Instruction:**
    1.  Initialize a new project named `QuoteAggregator-BiddingAgent`.
    2.  Define the primary agent, **'Bidding Orchestrator,'** with the system prompt: "You are an expert agent that manages plumbing quotes. You must use the `Weaviate_RAG` tool to retrieve pricing data and the `LiveKit_API` tool to manage real-time voice transcription."

### 2. External API Tool Definitions

* **Antigravity View:** Tool/API Management
* **Action:** Securely configure and define the API access for the following tools (the Agent must use these names):
    * `Weaviate_RAG`: For vector database queries (custom pricing).
    * `LiveKit_API`: For real-time audio and streaming.
    * `ElevenLabs_TTS`: For high-quality voice feedback to the plumber.
    * `dlthub_API`: For exporting final job data to an external ledger.

---

## PHASE 2: Knowledge Base & Retrieval-Augmented Generation (RAG)

**Objective:** Ground the Agent's quotes in the plumber's private pricing data.

### 1. Database Setup & Ingestion

* **Antigravity View:** Terminal
* **Instruction:** "Execute the necessary commands to set up the Weaviate instance. Use the `dlthub_API` to ingest and vectorize the plumber's custom Excel rate sheets and PDF service guides into a Weaviate class named `PlumberRates`."

### 2. RAG Tool Function Definition

* **Antigravity View:** Editor View
* **Action:** The Agent must generate a function definition (`query_weaviate`) that the Orchestrator can call:

```python
# RAG Tool Definition for the Agent
def query_weaviate(service_description: str) -> str:
    """
    Searches the PlumberRates class in Weaviate for prices, materials, and time
    estimates related to the given service description. Returns raw JSON result.
    """
    # Implementation details will be filled by the Agent
    pass
```
