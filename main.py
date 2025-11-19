import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ecommerce API ready"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Connected"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response

# Helper to serialize Mongo ObjectId
class ProductOut(Product):
    id: Optional[str] = None

class OrderOut(Order):
    id: Optional[str] = None

# Seed some demo products if collection empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}
    demo = [
        {
            "title": "Wireless Headphones",
            "description": "Noise-cancelling over-ear headphones with 30h battery.",
            "price": 129.99,
            "category": "Electronics",
            "image": "https://images.unsplash.com/photo-1518449007433-7db30f2f8bb3?q=80&w=1400&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "title": "Smart Watch",
            "description": "Fitness tracking, notifications, and heart-rate monitor.",
            "price": 199.0,
            "category": "Gadgets",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1400&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "title": "Espresso Maker",
            "description": "Compact espresso machine for rich, cafe-style shots.",
            "price": 89.5,
            "category": "Home",
            "image": "https://images.unsplash.com/photo-1503481766315-7a586b20f66d?q=80&w=1400&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "title": "Running Shoes",
            "description": "Lightweight, breathable shoes for daily training.",
            "price": 74.99,
            "category": "Apparel",
            "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1400&auto=format&fit=crop",
            "in_stock": True,
        },
    ]
    for p in demo:
        create_document("product", p)
    return {"seeded": True, "count": len(demo)}

@app.get("/products", response_model=List[ProductOut])
def list_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    docs = get_documents("product")
    out = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
        out.append(d)
    return out

@app.post("/orders", response_model=OrderOut)
def create_order(order: Order):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    order_id = create_document("order", order)
    doc = db["order"].find_one({"_id": ObjectId(order_id)})
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create order")
    doc["id"] = str(doc["_id"]) 
    doc.pop("_id", None)
    return doc

@app.get("/schema")
def get_schema_overview():
    # Minimal endpoint for external tools to read schemas
    return {
        "collections": ["user", "product", "order"],
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
