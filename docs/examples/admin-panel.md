# Admin Panel Example

This example demonstrates a complete Flaxon admin panel with a Product model using in-memory storage.

## Running the Example

```bash
# Create a new Flaxon project
flaxon new admin-example
cd admin-example

# Install dependencies
pip install flaxon

# Create app.py with the code below
# Run the app
flaxon run app:app --reload


Full Example Code
app.py
python
from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig, admin_model

app = Flaxon("admin-example", debug=True)

# Admin configuration
config = AdminConfig(
    site_title="Product Admin",
    site_header="Product Administration",
    index_title="Welcome to Product Admin",
)

# Create admin dashboard
admin = AdminDashboard(app, config=config, url_prefix="/admin")

# Define Product model with CRUD hooks
@admin_model
class Product:
    __name__ = "product"
    __verbose_name__ = "Product"
    __verbose_name_plural__ = "Products"

    # In-memory storage
    _data = {}
    _id_counter = 1

    @classmethod
    async def get_instances(cls) -> list[dict]:
        """Return all products for the list view."""
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id: str) -> dict | None:
        """Return a single product for detail/edit views."""
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data: dict) -> dict:
        """Create a new product from form data."""
        product_id = str(cls._id_counter)
        cls._id_counter += 1
        data["id"] = product_id
        cls._data[product_id] = data
        return data

    @classmethod
    async def update_instance(cls, id: str, data: dict) -> dict | None:
        """Update an existing product."""
        if id not in cls._data:
            return None
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id: str) -> bool:
        """Delete a product."""
        if id in cls._data:
            del cls._data[id]
            return True
        return False

# Register Product with custom admin options
admin.register(
    Product,
    list_display=["id", "name", "price", "status", "created_at"],
    list_filter=["status"],
    search_fields=["name", "description"],
    fields=["name", "description", "price", "status", "created_at"],
    readonly_fields=["id", "created_at"],
    ordering=["-created_at"],
)

# Seed some initial data
import asyncio

async def seed_data():
    products = [
        {"name": "Laptop", "description": "High-performance laptop", "price": 999.99, "status": "active", "created_at": "2026-01-15"},
        {"name": "Mouse", "description": "Wireless mouse", "price": 29.99, "status": "active", "created_at": "2026-01-20"},
        {"name": "Keyboard", "description": "Mechanical keyboard", "price": 79.99, "status": "draft", "created_at": "2026-01-25"},
    ]
    for p in products:
        await Product.create_instance(p)

asyncio.run(seed_data())

# Welcome route
@app.get("/")
async def home(request):
    return {
        "message": "Welcome to the Admin Panel Example!",
        "admin_url": "/admin",
        "products_count": len(Product._data),
    }

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, reload=True)


What You'll See
Admin Dashboard
Visit /admin to see the dashboard with registered models and statistics.

Product List
Visit /admin/product to see all products with search and filter capabilities.

Product Detail
Click any product to view its details.

Create Product
Use the "Add Product" button to create new products.

Edit Product
Click the edit icon on any product to modify it.

Delete Product
Use the delete button to remove products (with confirmation).

Customizing the Admin
Adding a Custom Action
python
from flaxon.admin import admin_action

@admin_action("mark_inactive")
async def mark_inactive(self, ids: list[str]) -> dict:
    for id in ids:
        if id in self._data:
            self._data[id]["status"] = "inactive"
    return {"success": True, "updated": len(ids)}
Adding a Custom Display Field
python
from flaxon.admin import admin_display

@admin_display(header="Price with Tax")
def display_price_with_tax(self, obj: dict) -> str:
    price = obj.get("price", 0)
    tax = price * 0.15
    return f"${price + tax:.2f}"


Next Steps
Add authentication to protect the admin

Connect to a real database (SQLite, PostgreSQL)

Create custom admin views

Add custom CSS and JavaScript

Deploy to production