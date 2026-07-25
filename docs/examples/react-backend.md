
---

## docs/examples/react-backend.md

```markdown
# React Backend Example

This example demonstrates a backend for a React application with CORS support and API endpoints.

## Application Code

```python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware
from flaxon.validation import Schema, fields

app = Flaxon("react-backend")

# Configure CORS for React development server
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
)

# Product schema
class CreateProduct(Schema):
    name = fields.String(required=True, min_length=2, max_length=100)
    price = fields.FloatField(required=True, minimum=0)
    description = fields.String(required=False, max_length=500)
    category = fields.String(required=False, max_length=50)
    in_stock = fields.BoolField(default=True)

# In-memory storage
products = []
product_id_counter = 1

@app.get("/api/products")
async def list_products(request):
    category = request.query.get("category")
    in_stock = request.query.get_bool("in_stock")

    result = products
    if category:
        result = [p for p in result if p.get("category") == category]
    if in_stock is not None:
        result = [p for p in result if p.get("in_stock") == in_stock]

    return {"data": result, "total": len(result)}

@app.get("/api/products/<int:product_id>")
async def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}, 404

@app.post("/api/products")
async def create_product(data: CreateProduct):
    global product_id_counter
    product = data.to_dict()
    product["id"] = product_id_counter
    product_id_counter += 1
    products.append(product)
    return {"created": True, "product": product}, 201

@app.put("/api/products/<int:product_id>")
async def update_product(product_id: int, data: CreateProduct):
    for product in products:
        if product["id"] == product_id:
            product.update(data.to_dict())
            return {"updated": True, "product": product}
    return {"error": "Product not found"}, 404

@app.delete("/api/products/<int:product_id>")
async def delete_product(product_id: int):
    for i, product in enumerate(products):
        if product["id"] == product_id:
            products.pop(i)
            return {"deleted": True}
    return {"error": "Product not found"}, 404

@app.get("/api/categories")
async def list_categories():
    categories = list(set(p.get("category") for p in products if p.get("category")))
    return {"categories": categories}

@app.get("/api/stats")
async def get_stats():
    total = len(products)
    in_stock = sum(1 for p in products if p.get("in_stock", False))
    total_value = sum(p.get("price", 0) for p in products)

    return {
        "total_products": total,
        "in_stock": in_stock,
        "out_of_stock": total - in_stock,
        "total_value": round(total_value, 2),
    }

    Running the Application
bash
# Install dependencies
pip install flaxon[standard]

# Run the application
flaxon run app:app --reload --host 0.0.0.0 --port 8000
React Client Example
javascript
// api.js
const API_URL = "http://localhost:8000/api";

export async function getProducts() {
  const response = await fetch(`${API_URL}/products`);
  return response.json();
}

export async function getProduct(id) {
  const response = await fetch(`${API_URL}/products/${id}`);
  return response.json();
}

export async function createProduct(product) {
  const response = await fetch(`${API_URL}/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(product),
  });
  return response.json();
}

export async function updateProduct(id, product) {
  const response = await fetch(`${API_URL}/products/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(product),
  });
  return response.json();
}

export async function deleteProduct(id) {
  const response = await fetch(`${API_URL}/products/${id}`, {
    method: "DELETE",
  });
  return response.json();
}