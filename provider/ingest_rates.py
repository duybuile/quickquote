import os
import json
import csv
import ast
import dlt
from dlt.destinations import weaviate
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "plumber", "darshan")

# Load model for client-side vectorization
model = SentenceTransformer('all-MiniLM-L6-v2')

def parse_json_rates(file_path):
    """Parses rates from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    normalized_data = []
    for item in data:
        # Create a text representation for embedding
        text_to_vectorize = f"{item.get('service_name')} {item.get('description')}"
        vector = model.encode(text_to_vectorize).tolist()
        
        normalized_data.append({
            "service_name": item.get("service_name"),
            "description": item.get("description"),
            "price": float(item.get("price", 0)),
            "estimated_hours": float(item.get("estimated_hours", 0)),
            "service_id": f"JSON_{item.get('service_name').replace(' ', '_')}", 
            "standard_material_cost": 0.0,
            "required_materials": [],
            "repair_steps": [],
            # dlt/Weaviate adapter expects 'vector' or special configuration for manual vectors
            # Usually, dlt handles this if we map it correctly, but for Weaviate destination, 
            # we might need to pass it as a specific field or configure the adapter.
            # However, dlt's weaviate adapter might not support explicit 'vector' field out of the box 
            # without config. 
            # A simpler way with dlt is to let it ingest the data, but since we disabled the vectorizer,
            # we need to ensure Weaviate receives the vector.
            # 
            # Actually, dlt's weaviate destination supports 'vector' column if configured.
            # But to be safe and simple, we might want to use the Weaviate Client directly here 
            # since we are doing custom vectorization, OR trust dlt.
            # Let's try to pass 'vector' and see if dlt maps it. 
            # If not, we might need to use weaviate client directly for ingestion to ensure vectors are set.
            # Given the complexity, let's switch to direct Weaviate Client ingestion for maximum control over vectors.
            "vector": vector
        })
    return normalized_data

def parse_csv_service(file_path):
    """Parses a service definition from a CSV file."""
    service_data = {
        "required_materials": [],
        "repair_steps": []
    }
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        current_list_field = None
        
        for row in reader:
            field = row.get("Field Name", "").strip()
            value = row.get("Value", "").strip()
            
            if field:
                current_list_field = None 
                
                if field == "service_id":
                    service_data["service_id"] = value
                elif field == "service_description":
                    service_data["description"] = value
                    service_data["service_name"] = value 
                elif field == "estimated_labor_avg":
                    service_data["estimated_hours"] = float(value)
                elif field == "base_rate_value":
                    service_data["price"] = float(value)
                elif field == "standard_material_cost":
                    service_data["standard_material_cost"] = float(value)
                elif field == "required_materials":
                    try:
                        service_data["required_materials"] = json.loads(value)
                    except:
                        service_data["required_materials"] = [value]
                elif field == "repair_steps":
                    current_list_field = "repair_steps"
                    if not value.startswith("["):
                         service_data["repair_steps"].append(value)
            
            elif current_list_field == "repair_steps" and value:
                service_data["repair_steps"].append(value)

    if "service_name" not in service_data and "description" in service_data:
         service_data["service_name"] = service_data.get("service_id", "Unknown Service")

    # Vectorize
    text_to_vectorize = f"{service_data.get('service_name', '')} {service_data.get('description', '')}"
    service_data["vector"] = model.encode(text_to_vectorize).tolist()

    return service_data

def ingest_rates():
    """
    Ingests plumber rates into Weaviate using Weaviate Client directly for manual vectors.
    """
    import weaviate
    
    # Connect to Weaviate
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
    )
    
    all_services = []
    
    # 1. Parse JSON
    json_path = os.path.join(DATA_DIR, "darshan.json")
    if os.path.exists(json_path):
        print(f"Parsing JSON: {json_path}")
        all_services.extend(parse_json_rates(json_path))
        
    # 2. Parse CSVs
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".csv"):
                csv_path = os.path.join(DATA_DIR, filename)
                print(f"Parsing CSV: {csv_path}")
                try:
                    service = parse_csv_service(csv_path)
                    all_services.append(service)
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

    print(f"Found {len(all_services)} services. Ingesting...")
    
    # 3. Ingest to Weaviate
    try:
        collection = client.collections.get("PlumberRates")
        
        with collection.batch.dynamic() as batch:
            for service in all_services:
                # Extract vector
                vector = service.pop("vector")
                
                # Add object with vector
                batch.add_object(
                    properties=service,
                    vector=vector
                )
                
        print("Ingestion complete.")
        if len(client.collections.get("PlumberRates").batch.failed_objects) > 0:
            print(f"Failed objects: {client.collections.get('PlumberRates').batch.failed_objects}")
            
    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    ingest_rates()
