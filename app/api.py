# app/api.py
from typing import List, Optional
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Supermarket API")

# ===========================
#   מודלים (Pydantic)
# ===========================


class Chain(BaseModel):
    id: int
    name: str


class Store(BaseModel):
    id: int
    chain_id: int
    name: str
    city: str


class Product(BaseModel):
    id: int
    name: str
    category: str


class StorePrice(BaseModel):
    store_id: int
    product_id: int
    price: Decimal


class BasketItem(BaseModel):
    product_id: int
    quantity: int


class BasketCompareRequest(BaseModel):
    items: List[BasketItem]
    # אפשר לסנן רק לרשתות מסוימות / עיר מסוימת
    chain_ids: Optional[List[int]] = None
    city: Optional[str] = None


class BasketStoreResult(BaseModel):
    chain_id: int
    chain_name: str
    store_id: int
    store_name: str
    city: str
    total_price: Decimal


class BasketCompareResponse(BaseModel):
    items: List[BasketItem]
    results: List[BasketStoreResult]


# ===========================
#   דאטה לדוגמה בזיכרון
#   (אפשר להחליף למסד אמיתי בהמשך)
# ===========================

CHAINS: List[Chain] = [
    Chain(id=1, name="שופרסל"),
    Chain(id=2, name="רמי לוי"),
    Chain(id=3, name="יקטאן"),
]

STORES: List[Store] = [
    Store(id=1, chain_id=1, name="שופרסל דיל אבן גבירול", city="תל אביב"),
    Store(id=2, chain_id=1, name="שופרסל אקספרס קרליבך", city="תל אביב"),
    Store(id=3, chain_id=2, name="רמי לוי חולון", city="חולון"),
    Store(id=4, chain_id=3, name="יקטאן באר שבע", city="באר שבע"),
]

PRODUCTS: List[Product] = [
    Product(id=1, name="חלב 3% טרה 1L", category="מוצרי חלב"),
    Product(id=2, name="לחם פרוס אחיד", category="מאפה"),
    Product(id=3, name="ביצה L 12 יח'", category="ביצים"),
]

# מחירים בכל סניף עבור כל מוצר
PRICES: List[StorePrice] = [
    # חלב
    StorePrice(store_id=1, product_id=1, price=Decimal("6.20")),
    StorePrice(store_id=2, product_id=1, price=Decimal("6.50")),
    StorePrice(store_id=3, product_id=1, price=Decimal("5.90")),
    StorePrice(store_id=4, product_id=1, price=Decimal("6.10")),
    # לחם
    StorePrice(store_id=1, product_id=2, price=Decimal("7.00")),
    StorePrice(store_id=3, product_id=2, price=Decimal("6.80")),
    StorePrice(store_id=4, product_id=2, price=Decimal("7.20")),
    # ביצים
    StorePrice(store_id=1, product_id=3, price=Decimal("13.90")),
    StorePrice(store_id=2, product_id=3, price=Decimal("14.50")),
    StorePrice(store_id=3, product_id=3, price=Decimal("13.50")),
]

# ===========================
#   נקודות קצה
# ===========================


@app.get("/", tags=["health"])
def home():
    """
    בדיקת בריאות השרת
    """
    return {"status": "ok", "message": "Supermarket backend is alive"}


# ------- קטלוג: רשתות וסניפים -------


@app.get("/chains", response_model=List[Chain], tags=["catalog"])
def list_chains():
    """
    מחזיר את רשימת רשתות הסופר
    """
    return CHAINS


@app.get("/stores", response_model=List[Store], tags=["catalog"])
def list_stores(
    chain_id: Optional[int] = None,
    city: Optional[str] = None,
):
    """
    מחזיר סניפים, עם אפשרות לסינון לפי chain_id ועיר
    """
    stores = STORES
    if chain_id is not None:
        stores = [s for s in stores if s.chain_id == chain_id]
    if city:
        city_lower = city.lower()
        stores = [s for s in stores if city_lower in s.city.lower()]
    return stores


# ------- מוצרים -------


@app.get(
    "/products/search",
    response_model=List[Product],
    tags=["products"],
)
def search_products(
    q: str = Query(..., min_length=2, description="טקסט לחיפוש בשם המוצר"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    חיפוש מוצרים לפי טקסט בשם המוצר
    """
    q_lower = q.lower()
    results = [p for p in PRODUCTS if q_lower in p.name.lower()]
    return results[:limit]


# ------- השוואת סל קניות -------


@app.post(
    "/basket/compare",
    response_model=BasketCompareResponse,
    tags=["basket"],
)
def compare_basket(payload: BasketCompareRequest):
    """
    מקבל סל קניות ומשווה את המחיר בין סניפים.
    כרגע נכללים רק סניפים שיש בהם מחיר לכל המוצרים בסל.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="סל קניות ריק")

    # סינון סניפים לפי רשת / עיר אם צריך
    candidate_stores = STORES
    if payload.chain_ids:
        candidate_stores = [
            s for s in candidate_stores if s.chain_id in payload.chain_ids
        ]
    if payload.city:
        city_lower = payload.city.lower()
        candidate_stores = [
            s for s in candidate_stores if city_lower in s.city.lower()
        ]

    if not candidate_stores:
        raise HTTPException(
            status_code=404,
            detail="לא נמצאו סניפים שמתאימים לסינון",
        )

    results: List[BasketStoreResult] = []

    for store in candidate_stores:
        total = Decimal("0")
        missing = False

        for item in payload.items:
            # חיפוש מחיר למוצר בסניף
            price_record = next(
                (
                    sp
                    for sp in PRICES
                    if sp.store_id == store.id and sp.product_id == item.product_id
                ),
                None,
            )

            if price_record is None:
                missing = True
                break

            total += price_record.price * item.quantity

        # כרגע מציגים רק סניפים עם כיסוי מלא של הסל
        if not missing:
            chain = next(c for c in CHAINS if c.id == store.chain_id)
            results.append(
                BasketStoreResult(
                    chain_id=chain.id,
                    chain_name=chain.name,
                    store_id=store.id,
                    store_name=store.name,
                    city=store.city,
                    total_price=total,
                )
            )

    # מיון מהזול ליקר
    results.sort(key=lambda r: r.total_price)

    return BasketCompareResponse(items=payload.items, results=results)
