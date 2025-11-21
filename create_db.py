from app.db import engine, Base
import app.models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
