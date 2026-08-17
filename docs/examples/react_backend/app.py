"""Flaxon API used by the accompanying React example."""

from flaxon import Flaxon, JSONResponse, NotFound
from flaxon.middleware import CORSMiddleware
from flaxon.validation import Schema, fields

app = Flaxon("react-backend", debug=True)
app.add_middleware(CORSMiddleware, allowed_origins=["http://localhost:5173"])


class CreateProduct(Schema):
    name = fields.StrField(required=True, min_length=1, max_length=120)
    price = fields.FloatField(required=True, minimum=0)


class UpdateProduct(Schema):
    name = fields.StrField(required=True, min_length=1, max_length=120)
    price = fields.FloatField(required=True, minimum=0)


products = [
    {"id": 1, "name": "Laptop", "price": 1200.0},
    {"id": 2, "name": "Keyboard", "price": 80.0},
]
next_product_id = 3


def find_product(product_id: int) -> dict:
    for product in products:
        if product["id"] == product_id:
            return product
    raise NotFound("Product not found")


@app.get("/api/products")
async def list_products() -> dict:
    return {"products": products}


@app.get("/api/products/<int:product_id>")
async def get_product(product_id: int) -> dict:
    return {"product": find_product(product_id)}


@app.post("/api/products")
async def create_product(data: CreateProduct) -> JSONResponse:
    global next_product_id
    product = {"id": next_product_id, **data.to_dict()}
    next_product_id += 1
    products.append(product)
    return JSONResponse({"product": product}, status_code=201)


@app.put("/api/products/<int:product_id>")
async def update_product(product_id: int, data: UpdateProduct) -> dict:
    product = find_product(product_id)
    product.update(data.to_dict())
    return {"product": product}


@app.delete("/api/products/<int:product_id>")
async def delete_product(product_id: int) -> dict:
    product = find_product(product_id)
    products.remove(product)
    return {"deleted": True}
