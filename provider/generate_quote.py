import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from provider.tools.weaviate_tool import query_weaviate

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = 'models/gemma-3-4b-it'

def load_customer_data(file_path):
    """Loads customer data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_quote():
    """
    Orchestrates the quote generation process.
    1. Reads customer data.
    2. Queries Weaviate for relevant services.
    3. Uses Gemini to generate a structured quote.
    """
    print("Starting Quote Generation Process...")
    
    # 1. Load Customer Data
    # Note: User mentioned "Customer now only has one json file". 
    # We'll look for the first JSON file in the directory to be robust.
    customer_dir = os.path.join("data", "customer")
    customer_file = None
    if os.path.exists(customer_dir):
        for f in os.listdir(customer_dir):
            if f.endswith(".json"):
                customer_file = os.path.join(customer_dir, f)
                break
    
    if not customer_file:
        print(f"No customer JSON file found in {customer_dir}")
        return

    customer_data = load_customer_data(customer_file)
    print(f"Loaded customer data for: {customer_data.get('customer_name')}")
    
    issue_description = customer_data.get("issue")
    print(f"Issue: {issue_description}")
    
    # 2. Query Weaviate
    print("Querying Knowledge Base...")
    rag_results_json = query_weaviate(issue_description)
    rag_results = json.loads(rag_results_json)
    print(f"Found {len(rag_results)} relevant services.")
    
    # 3. Generate Quote with Gemini
    print("Generating Quote with Gemini...")
    
    # Using the model defined at the top of the file.
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    You are an expert plumbing quoting agent. 
    
    **Customer Details:**
    {json.dumps(customer_data, indent=2)}
    
    **Relevant Services & Rates (from Knowledge Base):**
    {rag_results_json}
    
    **Instructions:**
    1. Analyze the customer's issue and the retrieved services.
    2. Select the most appropriate service(s) from the list.
    3. Calculate the total estimated cost (Labor + Materials).
    4. Generate a professional, itemized quote for the customer.
    5. Include a step-by-step repair plan based on the selected service.
    6. The output must be a JSON object with the following structure:
    {{
        "quote_id": "generated_id",
        "customer_name": "...",
        "selected_service": "...",
        "line_items": [
            {{"description": "...", "cost": 0.0}}
        ],
        "total_cost": 0.0,
        "estimated_duration": "...",
        "repair_plan": [
            "Step 1...",
            "Step 2..."
        ],
        "message_to_customer": "Professional message..."
    }}
    
    Return ONLY the JSON object.
    """
    
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"Error generating content with model '{model.model_name}': {e}")
        print("\nChecking available models...")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"- {m.name}")
        except Exception as list_error:
            print(f"Could not list models: {list_error}")
        return

    try:
        # Clean up response if it contains markdown code blocks
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        quote_json = json.loads(text)
        print("\n--- GENERATED QUOTE ---\n")
        print(json.dumps(quote_json, indent=2))
        
        # Save to file
        output_file = "generated_quote.json"
        with open(output_file, 'w') as f:
            json.dump(quote_json, f, indent=2)
        print(f"\nQuote saved to {output_file}")
        
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    generate_quote()
