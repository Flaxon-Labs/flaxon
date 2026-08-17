
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

# Run the application
flaxon run app:app --reload
````

---

# Full Example Code

## app.py

```python
from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig, admin_model


app = Flaxon(
    "admin-example",
    debug=True,
)


# Admin configuration
config = AdminConfig(
    site_title="Product Admin",
    site_header="Product Administration",
    index_title="Welcome to Product Admin",
)


# Create admin dashboard
admin = AdminDashboard(
    app,
    config=config,
    url_prefix="/admin",
)


# Define Product model
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
        """
        Return all products.
        """
        return list(cls._data.values())


    @classmethod
    async def get_instance(
        cls,
        id: str
    ) -> dict | None:
        """
        Return a single product.
        """
        return cls._data.get(id)


    @classmethod
    async def create_instance(
        cls,
        data: dict
    ) -> dict:
        """
        Create a new product.
        """

        product_id = str(cls._id_counter)

        cls._id_counter += 1

        data["id"] = product_id

        cls._data[product_id] = data

        return data


    @classmethod
    async def update_instance(
        cls,
        id: str,
        data: dict
    ) -> dict | None:
        """
        Update a product.
        """

        if id not in cls._data:
            return None

        cls._data[id].update(data)

        return cls._data[id]


    @classmethod
    async def delete_instance(
        cls,
        id: str
    ) -> bool:
        """
        Delete a product.
        """

        if id in cls._data:
            del cls._data[id]
            return True

        return False



# Register model in admin panel

admin.register(
    Product,

    list_display=[
        "id",
        "name",
        "price",
        "status",
        "created_at",
    ],

    list_filter=[
        "status",
    ],

    search_fields=[
        "name",
        "description",
    ],

    fields=[
        "name",
        "description",
        "price",
        "status",
        "created_at",
    ],

    readonly_fields=[
        "id",
        "created_at",
    ],

    ordering=[
        "-created_at",
    ],
)



# Seed initial data

async def seed_data():

    products = [

        {
            "name": "Laptop",
            "description": "High-performance laptop",
            "price": 999.99,
            "status": "active",
            "created_at": "2026-01-15",
        },

        {
            "name": "Mouse",
            "description": "Wireless mouse",
            "price": 29.99,
            "status": "active",
            "created_at": "2026-01-20",
        },

        {
            "name": "Keyboard",
            "description": "Mechanical keyboard",
            "price": 79.99,
            "status": "draft",
            "created_at": "2026-01-25",
        },

    ]


    for product in products:
        await Product.create_instance(product)



# Welcome route

@app.get("/")
async def home(request):

    return {

        "message": "Welcome to the Admin Panel Example!",

        "admin_url": "/admin",

        "products_count": len(Product._data),

    }



```

Seed data from a separate setup script or an application startup hook, then run
the application with `flaxon run app:app --reload`.

---

# What You'll See

## Admin Dashboard

Visit:

```
/admin
```

Displays:

* Registered models
* Statistics
* Admin navigation

---

## Product List

Visit:

```
/admin/product
```

Features:

* Search products
* Filter by status
* Sorting
* Pagination

---

## Product Detail

Click a product to view:

* Product information
* Metadata
* Available actions

---

## Create Product

Use:

```
Add Product
```

to create new products.

---

## Edit Product

Click the edit button to update existing products.

---

## Delete Product

Delete products with confirmation protection.

---

# Customizing the Admin

## Adding a Custom Action

```python
from flaxon.admin import admin_action


@admin_action("mark_inactive")
async def mark_inactive(
    self,
    ids: list[str]
) -> dict:

    updated = 0

    for id in ids:

        if id in self._data:

            self._data[id]["status"] = "inactive"

            updated += 1


    return {

        "success": True,

        "updated": updated,

    }
```

---

# Adding a Custom Display Field

```python
from flaxon.admin import admin_display


@admin_display(
    header="Price with Tax"
)
def display_price_with_tax(
    self,
    obj: dict
) -> str:

    price = obj.get(
        "price",
        0
    )

    tax = price * 0.15

    return f"${price + tax:.2f}"
```

---

# Database Integration

The admin panel can be connected to:

* SQLite
* PostgreSQL
* MySQL
* Custom database adapters

Example:

```python
admin.register(
    Product,
    database="default",
)
```

---

# Authentication

Protect the admin dashboard:

```python
from flaxon.security import login_required


@app.middleware
async def admin_auth(request, call_next):

    if request.path.startswith("/admin"):

        if not request.user:

            return {
                "error": "Authentication required"
            }

    return await call_next(request)
```

---

# Next Steps

* Add authentication
* Connect a real database
* Create custom admin pages
* Add custom themes
* Add dashboard widgets
* Deploy to production

