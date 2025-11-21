from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Supermarket API")

# -------------------------
# MODELS
# -------------------------

class Product(BaseModel):
    id: int
    name: str
    price: float
    category: Optional[str] = None

class Purchase(BaseModel):
    user_id: int
    product_id: int
    quantity: int

# -------------------------
# ENDPOINTS
# -------------------------

@app.get("/")
def home():
    return {"message": "Supermarket API is running!"}

# Get all products
@app.get("/products", response_model=List[Product])
def get_products():
    return [
        {"id": 1, "name": "Milk", "price": 5.90, "category": "Dairy"},
        {"id": 2, "name": "Bread", "price": 4.20, "category": "Bakery"},
        {"id": 3, "name": "Chicken", "price": 24.90, "category": "Meat"},
    ]

# Register purchase
@app.post("/purchase")
def add_purchase(p: Purchase):
    return {"status": "success", "details": p}

# Price calculation example
@app.get("/calctotal/{product_id}/{qty}")
def calc_total(product_id: int, qty: int):
    prices = {1: 5.90, 2: 4.20, 3: 24.90}
    if product_id not in prices:
        return {"error": "Product not found"}
    return {"total": round(prices[product_id] * qty, 2)}
