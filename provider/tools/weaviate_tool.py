import os
import json
import weaviate

from sentence_transformers import SentenceTransformer

# Load model (global to avoid reloading on every call, though in a real agent this might be handled differently)
model = SentenceTransformer('all-MiniLM-L6-v2')

def query_weaviate(service_description: str) -> str:
    """
    Searches the PlumberRates class in Weaviate for prices, materials, and time
    estimates related to the given service description. Returns raw JSON result.
    """
    try:
        # Connect to Weaviate (v4)
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
        )
        
        try:
            # Get collection
            plumber_rates = client.collections.get("PlumberRates")
            
            # Compute vector for query
            query_vector = model.encode(service_description).tolist()
            
            # Perform vector search using near_vector
            response = plumber_rates.query.near_vector(
                near_vector=query_vector,
                limit=3,
                return_properties=[
                    "service_name", "description", "price", "estimated_hours", 
                    "service_id", "standard_material_cost", "required_materials", "repair_steps"
                ]
            )
            
            # Parse results
            results = []
            for obj in response.objects:
                results.append(obj.properties)
                
            return json.dumps(results, indent=2)
            
        finally:
            client.close()
        
    except Exception as e:
        print(f"Error querying Weaviate: {e}")
        return "[]"
