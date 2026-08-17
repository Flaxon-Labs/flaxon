
# Admin Dashboard

Flaxon includes an optional built-in admin dashboard for managing application data through a web interface.

It provides a CRUD-based management system inspired by Django Admin while being designed for **async-first Python applications**.

---

# Overview

The Flaxon Admin Dashboard provides:

- Automatic CRUD interfaces for registered models
- List views with filtering and searching
- Detail, create, update, and delete pages
- Responsive UI built with Tailwind CSS
- Dark mode support
- Customizable dashboard layout
- Extension support through hooks and custom views

---

# Installation

The admin dashboard is included with Flaxon.

No additional package installation is required.

```bash
pip install "flaxon>=0.1.7"
````

---

# Quick Start

## 1. Create an Admin Dashboard

```python
from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig


app = Flaxon(
    "my-app"
)


config = AdminConfig(
    site_title="My Admin",
    site_header="My Administration",
    index_title="Welcome to My Admin",
)


admin = AdminDashboard(
    app,
    config=config,
    url_prefix="/admin"
)
```

---

# 2. Define a Model

Models registered with the admin dashboard provide CRUD operations through optional hook methods.

Example:

```python
from flaxon.admin import admin_model


@admin_model
class Product:

    __name__ = "product"

    __verbose_name__ = "Product"

    __verbose_name_plural__ = "Products"


    _data = {}


    @classmethod
    async def get_instances(cls) -> list[dict]:
        return list(
            cls._data.values()
        )


    @classmethod
    async def get_instance(
        cls,
        id: str
    ) -> dict | None:

        return cls._data.get(id)


    @classmethod
    async def create_instance(
        cls,
        data: dict
    ) -> dict:

        id = str(
            len(cls._data) + 1
        )

        data["id"] = id

        cls._data[id] = data

        return data


    @classmethod
    async def update_instance(
        cls,
        id: str,
        data: dict
    ) -> dict | None:

        if id not in cls._data:
            return None

        cls._data[id].update(data)

        return cls._data[id]


    @classmethod
    async def delete_instance(
        cls,
        id: str
    ) -> bool:

        if id in cls._data:
            del cls._data[id]
            return True

        return False
```

---

# 3. Register the Model

Configure how the model appears in the dashboard.

```python
admin.register(
    Product,

    list_display=[
        "id",
        "name",
        "price"
    ],

    search_fields=[
        "name"
    ],

    fields=[
        "name",
        "description",
        "price",
        "status"
    ],

    readonly_fields=[
        "id"
    ]
)
```

---

# 4. Access the Admin Dashboard

Start your Flaxon application:

```bash
flaxon run app:app --reload
```

Open:

```
http://localhost:8000/admin
```

---

# CRUD Hook Protocol

The admin dashboard uses optional model hook methods.

All hooks are optional. Missing methods are handled automatically.

| Method                      | Signature                    | Purpose          | Used For            |
| --------------------------- | ---------------------------- | ---------------- | ------------------- |
| `get_instances()`           | `() -> list[dict]`           | Fetch records    | List page           |
| `get_instance(id)`          | `(id) -> dict \| None`       | Fetch one record | Detail/Edit         |
| `create_instance(data)`     | `(data: dict) -> dict`       | Create record    | Add form            |
| `update_instance(id, data)` | `(id, data) -> dict \| None` | Update record    | Edit form           |
| `delete_instance(id)`       | `(id) -> bool`               | Delete record    | Delete confirmation |

---

# Hook Features

The admin system supports:

* Optional hooks
* Automatic detection
* Sync and async methods
* Custom storage backends

The dashboard does not require a specific ORM.

---

# Example with SQLAlchemy

Flaxon Admin can work with external database solutions.

Example:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from flaxon.admin import admin_model


@admin_model
class User:


    __name__ = "user"

    __verbose_name__ = "User"

    __verbose_name_plural__ = "Users"


    @classmethod
    async def get_instances(cls):

        async with AsyncSession(engine) as session:

            result = await session.execute(
                select(UserModel)
            )

            users = result.scalars().all()

            return [
                user.to_dict()
                for user in users
            ]
```

---

# Admin Configuration

## AdminConfig Options

```python
from flaxon.admin import AdminConfig


config = AdminConfig(

    site_title="Flaxon Admin",

    site_header="Flaxon Administration",

    index_title="Welcome to Flaxon Admin",

    enable_dark_mode=True,

    enable_search=True,

    enable_actions=True,

    enable_filters=True,

    enable_pagination=True,

    logo_url="/static/logo.png",

    custom_styles="/static/admin.css",

    custom_scripts="/static/admin.js"
)
```

---

# Model Registration Options

```python
admin.register(

    Product,

    list_display=[
        "id",
        "name",
        "price",
        "created_at"
    ],

    list_filter=[
        "status",
        "category"
    ],

    search_fields=[
        "name",
        "description"
    ],

    fields=[
        "name",
        "description",
        "price",
        "status"
    ],

    readonly_fields=[
        "id",
        "created_at"
    ],

    ordering=[
        "-created_at"
    ],

    name="products",

    icon="fa-box"
)
```

---

# Custom Actions

Custom actions allow bulk operations from the admin interface.

Example:

```python
from flaxon.admin import admin_action


class Product:

    @admin_action("mark_active")
    async def mark_active(
        self,
        ids: list[str]
    ):

        for id in ids:

            if id in self._data:

                self._data[id]["status"] = "active"


        return {
            "success": True,
            "updated": len(ids)
        }
```

---

# Custom Display Methods

Create custom columns for list views.

```python
from flaxon.admin import admin_display


class Product:

    @admin_display(
        header="Full Name"
    )
    def display_name(
        self,
        obj: dict
    ) -> str:

        return (
            f"{obj['name']} "
            f"(${obj['price']})"
        )
```

---

# URL Structure

| URL                               | Purpose             |
| --------------------------------- | ------------------- |
| `/admin/`                         | Dashboard home      |
| `/admin/<model_name>/`            | Model list          |
| `/admin/<model_name>/add`         | Create record       |
| `/admin/<model_name>/<id>`        | Detail view         |
| `/admin/<model_name>/<id>/edit`   | Edit record         |
| `/admin/<model_name>/<id>/delete` | Delete confirmation |

---

# Advanced Usage

## Custom Template Directory

```python
admin = AdminDashboard(
    app,
    template_dir="templates/my_admin"
)
```

---

## Multiple Admin Instances

Create multiple dashboards for different purposes.

```python
main_admin = AdminDashboard(
    app,
    url_prefix="/admin"
)


api_admin = AdminDashboard(
    app,
    url_prefix="/api-admin"
)
```

---

# Custom Views

Create custom dashboard pages.

```python
from flaxon.admin.views import AdminView


class CustomDashboardView(AdminView):

    async def render(self):

        context = {

            "custom_data":
                await get_dashboard_stats(),

            "title":
                "Custom Dashboard"
        }


        return await self.dashboard.jinax.render_response(
            "custom/dashboard.html",
            context
        )


admin._register_custom_view(
    "/dashboard",
    CustomDashboardView
)
```

---

# Security

The admin dashboard does **not automatically provide authentication**.

You should:

* Add authentication middleware
* Protect admin routes
* Use secure sessions or JWT authentication
* Restrict admin access by user role

Example:

```python
from flaxon.security import AuthenticationMiddleware


app.add_middleware(
    AuthenticationMiddleware
)


@admin.require_login
async def admin_route(request):

    # Only authenticated users can access

    pass
```

---

# API Reference

For detailed classes, methods, and configuration options, see:

**Admin API Reference**

