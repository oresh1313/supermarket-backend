from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Chain(Base):
    __tablename__ = "chains"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    gov_chain_id = Column(String, unique=True, nullable=False)

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, ForeignKey("chains.id"))
    name = Column(String, nullable=False)
    city = Column(String)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Numeric(10,2))
    updated_at = Column(DateTime, default=datetime.utcnow)
