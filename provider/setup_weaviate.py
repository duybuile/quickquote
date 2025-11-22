import weaviate
import weaviate.classes.config as wvc
import os
from dotenv import load_dotenv

load_dotenv()

def setup_schema():
    """
    Defines the PlumberRates collection in Weaviate using v4 API.
    """
    # Connect to Weaviate (v4)
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-Goog-Api-Key": os.getenv("GOOGLE_API_KEY")
            }
        )
        print(f"Connected to Weaviate at {os.getenv('WEAVIATE_URL')}")
    except Exception as e:
        print(f"Failed to connect to Weaviate: {e}")
        return

    try:
        # Check if collection exists and delete if so
        if client.collections.exists("PlumberRates"):
            print("Collection 'PlumberRates' already exists. Deleting it to update schema...")
            client.collections.delete("PlumberRates")
        
        # Create collection
        client.collections.create(
            name="PlumberRates",
            description="Pricing and service details for plumbing jobs",
            # No vectorizer_config means we will provide vectors manually (Client-side vectorization)
            properties=[
                wvc.Property(name="service_id", data_type=wvc.DataType.TEXT, description="Unique identifier for the service"),
                wvc.Property(name="service_name", data_type=wvc.DataType.TEXT, description="Name of the service"),
                wvc.Property(name="description", data_type=wvc.DataType.TEXT, description="Detailed description of the service"),
                wvc.Property(name="price", data_type=wvc.DataType.NUMBER, description="Base price for the service"),
                wvc.Property(name="estimated_hours", data_type=wvc.DataType.NUMBER, description="Estimated time to complete the job"),
                wvc.Property(name="standard_material_cost", data_type=wvc.DataType.NUMBER, description="Cost of standard materials"),
                wvc.Property(name="required_materials", data_type=wvc.DataType.TEXT_ARRAY, description="List of required materials"),
                wvc.Property(name="repair_steps", data_type=wvc.DataType.TEXT_ARRAY, description="Step-by-step repair instructions")
            ]
        )
        print("Successfully created 'PlumberRates' collection in Weaviate.")
        
    except Exception as e:
        print(f"Error creating schema: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_schema()
