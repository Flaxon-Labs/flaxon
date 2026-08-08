# Admin Panel Cheat Sheet

Everything the admin dashboard offers — what's fully functional, and what's registered but not yet wired to real behavior (marked clearly below, so you don't lose time debugging something that was never connected).

## Setup

```python
admin = app.enable_admin(
    url_prefix="/admin",        # default
    config=AdminConfig(site_title="My Admin"),
    template_dir=None,          # None = built-in theme; pass a path to override
)
```

## Registering a model — every option

```python
admin.register(
    Product,
    name="products",                    # URL slug override (default: class name, lowercased)
    list_display=["name", "price"],     # columns shown on the list page
    list_filter=["category"],           # stored, not yet functional -- see below
    search_fields=["name"],             # stored, not yet functional -- see below
    fields=["name", "price"],           # fields shown on add/edit forms
    readonly_fields=["created_at"],     # shown but not editable on the edit form
    ordering=["-created_at"],           # stored on the model, not yet applied automatically
    icon="box",                         # for your own custom sidebar/template use
)
```

Or via decorator, registering to the default global registry instead of a specific app instance:
```python
from flaxon.admin.decorators import admin_model

@admin_model(list_display=["name"])
class Product:
    ...
```

## The CRUD data hooks — this is what actually makes it work

Implement any of these five as `@staticmethod`s (sync or async, both work) on the class you register. Every one is optional; the admin just does nothing for the operations you don't implement.

```python
class Product:
    @staticmethod
    def get_instances(): ...                    # list page
    @staticmethod
    def get_instance(object_id): ...             # detail/edit page
    @staticmethod
    def create_instance(form_data): ...           # add form submit
    @staticmethod
    def update_instance(object_id, form_data): ... # edit form submit
    @staticmethod
    def delete_instance(object_id): ...            # delete confirm
```

Full runnable example with an in-memory store — [see the admin guide](admin.md#a-complete-working-example).

## URLs generated per model

```
GET  /admin/<model>              list
GET  /admin/<model>/add          add form
POST /admin/<model>/add          create
GET  /admin/<model>/<id>         detail
GET  /admin/<model>/<id>/edit    edit form
POST /admin/<model>/<id>/edit    update
GET  /admin/<model>/<id>/delete  delete confirm
POST /admin/<model>/<id>/delete  delete
```

## Bulk actions — registered, but no way to trigger them yet

```python
admin_model_instance = admin.registry.get("product")
admin_model_instance.add_action("mark_featured", some_function)
admin_model_instance.get_actions()  # -> {"mark_featured": some_function}
```
or the decorator form:
```python
from flaxon.admin.decorators import admin_action

@admin_action("mark_featured")
def mark_featured(request, selected_ids): ...
```
**Both register the action correctly, but there's currently no route or UI control that actually calls it.** If you build on this, you'd need to add your own POST route reading `request.form()["action"]` and looking it up via `get_actions()` yourself.

## Custom column display — registered, but not read by anything

```python
from flaxon.admin.decorators import admin_display

@admin_display("Full Name")
def full_name(self): return f"{self.first} {self.last}"
```
Sets `._admin_display`/`._admin_header` on the function, but the list template doesn't currently look for or call these — `list_display` column values come from raw attribute access, not this decorator.

## Search & filtering — metadata only, not applied

`list_filter` and `search_fields` are stored on the model and passed to the list template as context, but `get_instances()` is called with no filter/search arguments — nothing in the admin currently reads a search box or filter dropdown and narrows the results. If you need working search/filter, implement it yourself inside your own `get_instances()`, reading from `request.query`.

## Exceptions

```python
from flaxon.admin.exceptions import AdminError, ModelNotFoundError, PermissionDeniedError, ValidationError
```
Available for you to raise from your own hooks; nothing in the admin core raises these automatically yet.

## Templates you can override

`base.html` `index.html` `list.html` `detail.html` `add.html` `edit.html` `delete.html` — every one gets a `dashboard` variable (the `AdminDashboard` instance) and `models` variable (everything registered) automatically.

## Quick reference: what's real vs. scaffolding

| Feature | Status |
|---|---|
| List / detail / add / edit / delete pages | ✅ Fully functional |
| CRUD data hooks (`get_instances` etc.) | ✅ Fully functional |
| `list_display` columns | ✅ Functional |
| `readonly_fields` on edit form | ✅ Functional |
| Custom `template_dir` | ✅ Functional |
| `list_filter` / `search_fields` | ⚠️ Stored, not applied |
| Bulk `admin_action`s | ⚠️ Registered, no trigger route |
| `admin_display` custom columns | ⚠️ Decorator sets attrs nothing reads |
| `ordering` | ⚠️ Stored, not auto-applied |