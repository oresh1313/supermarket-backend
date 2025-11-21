# app/schemas.py
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ===== Catalog =====

class ChainOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class StoreOut(BaseModel):
    id: int
    name: str
    city: Optional[str]
    chain_id: int

    class Config:
        orm_mode = True


class ProductOut(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    quantity: Optional[str]
    category: Optional[str]

    class Config:
        orm_mode = True


# ===== Basket compare =====

class BasketItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class BasketCompareRequest(BaseModel):
    items: List[BasketItem]
    # אפשר לסנן את ההשוואה
    chain_ids: Optional[List[int]] = None
    city: Optional[str] = None


class BasketPriceForStore(BaseModel):
    chain_id: int
    chain_name: str
    store_id: int
    store_name: str
    city: Optional[str]
    total_price: Decimal
    currency: str = "ILS"


class BasketCompareResponse(BaseModel):
    items: List[BasketItem]
    results: List[BasketPriceForStore]
