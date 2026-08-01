
# Admin Dashboard

Flaxon includes a built-in admin dashboard that provides a CRUD interface for managing your application data. It's inspired by Django's admin but built for async-first Python applications.

## Overview

The admin dashboard provides:
- Automatic CRUD views for registered models
- List views with filtering and search
- Detail, create, update, and delete views
- Responsive UI with Tailwind CSS
- Dark mode support
- Three.js 3D background effects

## Installation

The admin dashboard is part of `flaxon` core. No additional installation required.

```bash
pip install flaxon>=0.1.7

Quick Start
1. Create an Admin Dashboard
python
from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig

app = Flaxon("my-app")

# Create dashboard with custom config
config = AdminConfig(
    site_title="My Admin",
    site_header="My Administration",
    index_title="Welcome to My Admin",
)

admin = AdminDashboard(app, config=config, url_prefix="/admin")
2. Define a Model
python
from flaxon.admin import admin_model

@admin_model
class Product:
    __name__ = "product"
    __verbose_name__ = "Product"
    __verbose_name_plural__ = "Products"

    # In-memory storage (replace with your database)
    _data = {}

    @classmethod
    async def get_instances(cls) -> list[dict]:
        """Return all instances for the list view."""
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id: str) -> dict | None:
        """Return a single instance for detail/edit views."""
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data: dict) -> dict:
        """Create a new instance from form data."""
        id = str(len(cls._data) + 1)
        data["id"] = id
        cls._data[id] = data
        return data

    @classmethod
    async def update_instance(cls, id: str, data: dict) -> dict | None:
        """Update an existing instance."""
        if id not in cls._data:
            return None
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id: str) -> bool:
        """Delete an instance."""
        if id in cls._data:
            del cls._data[id]
            return True
        return False
3. Register the Model
python
# Register model with custom options
admin.register(
    Product,
    list_display=["id", "name", "price"],
    search_fields=["name"],
    fields=["name", "description", "price", "status"],
    readonly_fields=["id"],
)
4. Access the Admin
Start your Flaxon app and visit /admin in your browser.

bash
flaxon run app:app --reload
The CRUD Hook Protocol
The admin dashboard relies on optional hook methods on your model classes. All hooks are optional — the admin will gracefully handle missing methods.

Available Hooks
Method	Signature	Purpose	When Called
get_instances()	() -> list[dict]	Fetch all records	List view
get_instance(id)	(id) -> dict | None	Fetch single record	Detail/Edit views
create_instance(data)	(data: dict) -> dict	Create new record	Add form submission
update_instance(id, data)	(id, data: dict) -> dict | None	Update record	Edit form submission
delete_instance(id)	(id) -> bool	Delete record	Delete confirmation
Hook Features
All optional — implemented via hasattr() checks

Sync or async — the admin handles both (await if async)

Auto-detected — no registration needed beyond @admin_model

Example with SQLAlchemy
python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@admin_model
class User:
    __name__ = "user"
    __verbose_name__ = "User"
    __verbose_name_plural__ = "Users"

    @classmethod
    async def get_instances(cls) -> list[dict]:
        async with AsyncSession(engine) as session:
            result = await session.execute(select(UserModel))
            users = result.scalars().all()
            return [u.to_dict() for u in users]

    @classmethod
    async def get_instance(cls, id: str) -> dict | None:
        async with AsyncSession(engine) as session:
            user = await session.get(UserModel, int(id))
            return user.to_dict() if user else None
Admin Configuration
AdminConfig Options
python
from flaxon.admin import AdminConfig

config = AdminConfig(
    site_title="Flaxon Admin",        # Title shown in browser
    site_header="Flaxon Administration", # Header text
    index_title="Welcome to Flaxon Admin", # Index page title
    enable_dark_mode=True,            # Toggle dark mode support
    enable_search=True,               # Enable global search
    enable_actions=True,              # Enable bulk actions
    enable_filters=True,              # Enable list filters
    enable_pagination=True,           # Enable pagination
    logo_url="/static/logo.png",      # Custom logo URL
    custom_styles="/static/admin.css", # Additional CSS
    custom_scripts="/static/admin.js", # Additional JS
)
Model Registration Options
python
admin.register(
    Product,
    list_display=["id", "name", "price", "created_at"],  # Columns in list view
    list_filter=["status", "category"],                   # Filter sidebar
    search_fields=["name", "description"],                # Searchable fields
    fields=["name", "description", "price", "status"],    # Form fields
    readonly_fields=["id", "created_at"],                 # Read-only fields
    ordering=["-created_at"],                             # Default ordering
    name="products",                                      # URL name override
    icon="fa-box",                                        # FontAwesome icon
)
Custom Actions
Add custom actions to the admin list view:

python
from flaxon.admin import admin_action

class Product:
    # ... model methods ...

    @admin_action("mark_active")
    async def mark_active(self, ids: list[str]) -> dict:
        for id in ids:
            if id in self._data:
                self._data[id]["status"] = "active"
        return {"success": True, "updated": len(ids)}
Custom Display Methods
Add custom columns to the list view:

python
from flaxon.admin import admin_display

class Product:
    # ... model methods ...

    @admin_display(header="Full Name")
    def display_name(self, obj: dict) -> str:
        return f"{obj['name']} (${obj['price']})"
URL Structure
URL	Purpose
/admin/	Dashboard index
/admin/<model_name>/	Model list view
/admin/<model_name>/add	Create new record
/admin/<model_name>/<id>	Detail view
/admin/<model_name>/<id>/edit	Edit record
/admin/<model_name>/<id>/delete	Delete confirmation
Advanced Usage
Custom Template Directory
python
admin = AdminDashboard(
    app,
    template_dir="templates/my_admin",  # Custom template location
)
Multiple Admin Instances
python
# Main admin
main_admin = AdminDashboard(app, url_prefix="/admin")

# Separate admin for API management
api_admin = AdminDashboard(app, url_prefix="/api-admin")
Custom Views
python
from flaxon.admin.views import AdminView

class CustomDashboardView(AdminView):
    async def render(self) -> HTMLResponse:
        context = {
            "custom_data": await get_dashboard_stats(),
            "title": "Custom Dashboard",
        }
        return await self.dashboard.jinax.render_response("custom/dashboard.html", context)

# Register custom view
admin._register_custom_view("/dashboard", CustomDashboardView)
Security
The admin dashboard does not include built-in authentication. You should:

Add authentication middleware

Protect admin routes with @login_required

Use session-based or JWT authentication

python
from flaxon.middleware import AuthenticationMiddleware

app.add_middleware(AuthenticationMiddleware)

@admin.require_login
async def admin_route(request):
    # Only accessible to authenticated users
    pass


API Reference
See the Admin API Reference for detailed class and method documentation.