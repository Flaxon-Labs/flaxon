"""Small Flaxon admin panel demo — Product model, in-memory storage.

Requires the flaxon-admin-fixes.md patch applied (Request.form(), the
admin index.html url_prefix fix, and the views.py FormData->dict fix).
With those in place, the Add/Edit forms at /admin/product work normally —
no manual seeding workaround needed.
"""

from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig, admin_model

app = Flaxon("admin-example", debug=True)

admin = AdminDashboard(
    app,
    config=AdminConfig(site_title="Product Admin"),
    url_prefix="/admin",
)


@admin_model(
    list_display=["id", "name", "price"],
    search_fields=["name"],
    fields=["name", "price"],
)
class Product:
    _data: dict = {}
    _id_counter = 1

    @classmethod
    async def get_instances(cls) -> list[dict]:
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id: str) -> dict | None:
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data: dict) -> dict:
        product_id = str(cls._id_counter)
        cls._id_counter += 1
        data["id"] = product_id
        cls._data[product_id] = data
        return data

    @classmethod
    async def update_instance(cls, id: str, data: dict) -> dict | None:
        if id not in cls._data:
            return None
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id: str) -> bool:
        return cls._data.pop(id, None) is not None


@app.get("/")
async def home():
    return {"message": "Welcome", "admin": "/admin"}