from fastapi import FastAPI
from .db import engine, Base

app = FastAPI()

@app.get("/")
def home():
    return {"status": "API running successfully"}
