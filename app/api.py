# app/api.py
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models, schemas


app = FastAPI(title="Supermarket Compare API")


# ===== תלות לחיבור למסד הנתונים =====

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== Health / דף בית =====

@app.get("/", tags=["health"])
def home():
    return {"status": "ok", "message": "Supermarket backend is alive"}


# ===== Catalog: רשתות וסניפים =====

@app.get("/chains", response_model=List[schemas.ChainOut], tags=["catalog"])
def list_chains(db: Session = Depends(get_db)):
    return db.query(models.Chain).order_by(models.Chain.name).all()


@app.get("/stores", response_model=List[schemas.StoreOut], tags=["catalog"])
def list_stores(
    chain_id: Optional[int] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Store)
    if chain_id is not None:
        q = q.filter(models.Store.chain_id == chain_id)
    if city:
        q = q.filter(models.Store.city.ilike(f"%{city}%"))
    return q.order_by(models.Store.city, models.Store.name).all()


# ===== Products: חיפוש מוצרים =====

@app.get("/products/search", response_model=List[schemas.ProductOut], tags=["products"])
def search_products(
    q: str = Query(..., min_length=2, description="טקסט לחיפוש במוצר"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # חיפוש לפי שם מוצר (אפשר להרחיב לקטגוריה, מותג וכו')
    return (
        db.query(models.Product)
        .filter(models.Product.name.ilike(f"%{q}%"))
        .order_by(models.Product.name)
        .limit(limit)
        .all()
    )


# ===== Basket: השוואת סל קניות =====

@app.post("/basket/compare",
          response_model=schemas.BasketCompareResponse,
          tags=["basket"])
def compare_basket(
    payload: schemas.BasketCompareRequest,
    db: Session = Depends(get_db),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="סל קניות ריק")

    # שלב 1: אילו סניפים נכללים?
    stores_q = db.query(models.Store)
    if payload.chain_ids:
        stores_q = stores_q.filter(models.Store.chain_id.in_(payload.chain_ids))
    if payload.city:
        stores_q = stores_q.filter(models.Store.city.ilike(f"%{payload.city}%"))

    stores = stores_q.all()
    if not stores:
        raise HTTPException(status_code=404,
                            detail="לא נמצאו סניפים שמתאימים לסינון")

    results: List[schemas.BasketPriceForStore] = []

    for store in stores:
        total = Decimal("0")
        missing = False

        for item in payload.items:
            # קישור בין מוצר לסניף
            sp = (
                db.query(models.StoreProduct)
                .filter(
                    models.StoreProduct.store_id == store.id,
                    models.StoreProduct.product_id == item.product_id,
                )
                .first()
            )
            if not sp:
                missing = True
                break

            # המחיר האחרון
            price = (
                db.query(models.Price)
                .filter(models.Price.store_product_id == sp.id)
                .order_by(models.Price.effective_at.desc())
                .first()
            )

            if not price:
                missing = True
                break

            total += price.price_nis * item.quantity

        # כרגע: מציגים רק סניפים שיש בהם את כל המוצרים
        if not missing:
            results.append(
                schemas.BasketPriceForStore(
                    chain_id=store.chain.id,
                    chain_name=store.chain.name,
                    store_id=store.id,
                    store_name=store.name,
                    city=store.city,
                    total_price=total,
                )
            )

    # מיון מהכי זול
    results.sort(key=lambda r: r.total_price)

    return schemas.BasketCompareResponse(items=payload.items, results=results)
