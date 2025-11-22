import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from provider.generate_quote import generate_quote_from_data

app = FastAPI(title="Plumber's Bidding Agent API")

class CustomerData(BaseModel):
    customer_name: str
    issue: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    urgency: Optional[str] = None
    preferred_time: Optional[str] = None
    preferred_date: Optional[str] = None
    notes: Optional[str] = None

@app.post("/generate-quote")
async def create_quote_endpoint(customer: CustomerData):
    """
    Generates a quote based on the provided customer data.
    """
    try:
        # Convert Pydantic model to dict
        customer_dict = customer.model_dump()
        
        # Generate quote
        quote = generate_quote_from_data(customer_dict)
        
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Plumber's Bidding Agent API is running"}
