from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("react-backend")
app.add_middleware(CORSMiddleware, allowed_origins=["http://localhost:5173"])


@app.get("/api/products")
async def products():
    return [
        {"id": 1, "name": "Laptop", "price": 1200},
        {"id": 2, "name": "Keyboard", "price": 80},
    ]
