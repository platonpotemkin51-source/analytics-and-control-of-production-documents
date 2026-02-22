from fastapi import FastAPI

from app.api.routes import router
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WoodFlow")
app.include_router(router)


@app.get("/")
def landing():
    return {
        "name": "WoodFlow",
        "description": "Warehouse and shipment management for timber business",
        "next": ["/docs", "/api/auth/bootstrap", "/api/auth/login"],
    }
