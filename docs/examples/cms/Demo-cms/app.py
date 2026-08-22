from flaxon import Flaxon
from flaxon.admin import AdminDashboard, AdminConfig, admin_model
from flaxon.admin.cms import CMS, ContentType, CMSField

app = Flaxon("combined-example", debug=True)

# --------------------------------------------------------------------
# 1. AdminDashboard — model-based admin (Product)
# --------------------------------------------------------------------

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


# --------------------------------------------------------------------
# 2. CMS — content panel (Posts/Pages), mounted under /admin/cms
#    Entirely optional and independent of AdminDashboard above: it
#    only needs `app`, doesn't touch admin.registry, and would work
#    fine even if AdminDashboard were never created.
# --------------------------------------------------------------------

cms = CMS(app, url_prefix="/admin/cms", title="My Site CMS")

cms.register(ContentType(
    name="post",
    label="Post",
    label_plural="Posts",
    fields=[
        CMSField("title", "Title", required=True),
        CMSField("content", "Content", type="richtext"),
        CMSField("featured_image", "Featured Image URL", type="url", required=False),
    ],
    list_display=["title", "status", "updated_at"],
    list_filter=["status"],
    search_fields=["title", "content"],
))

cms.register(ContentType(
    name="page",
    label="Page",
    label_plural="Pages",
    fields=[
        CMSField("title", "Title", required=True),
        CMSField("content", "Content", type="richtext"),
    ],
))


@app.get("/")
async def home():
    return {
        "message": "Welcome",
        "product_admin": "/admin/product",
        "cms": "/admin/cms",
    }