
---

## docs/guides/authorization.md

```markdown
# Authorization

## Overview

Flaxon provides role-based and permission-based authorization through decorators and utility functions.

## Roles

### Defining Roles

```python
from flaxon.security import Role, register_role

admin_role = register_role(
    name="admin",
    permissions=["read", "write", "delete", "manage_users"],
    description="Administrator with full access",
)

moderator_role = register_role(
    name="moderator",
    permissions=["read", "write", "delete"],
    description="Moderator with limited access",
)

user_role = register_role(
    name="user",
    permissions=["read"],
    description="Regular user with read-only access",
)Role Hierarchy
python
moderator = register_role(
    name="moderator",
    permissions=["write", "delete"],
    parent=user_role,  # Inherits all user permissions
)

admin = register_role(
    name="admin",
    permissions=["manage_users"],
    parent=moderator,  # Inherits all moderator permissions
)
Permission-Based Authorization
python
from flaxon.security import permission_required, Permission

# Define permissions
register_permission("read", "Read data")
register_permission("write", "Write data")
register_permission("delete", "Delete data")

@app.get("/api/users")
@permission_required("read")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@app.post("/api/users")
@permission_required("write")
async def create_user():
    return {"created": True}

@app.delete("/api/users/<int:user_id>")
@permission_required("delete")
async def delete_user(user_id: int):
    return {"deleted": True}
Role-Based Authorization
python
from flaxon.security import role_required

@app.get("/admin/dashboard")
@role_required("admin")
async def admin_dashboard():
    return {"admin": True}

@app.get("/moderator/reports")
@role_required("moderator")
async def moderator_reports():
    return {"reports": []}
Combining Roles and Permissions
python
from flaxon.security import authorize

@app.delete("/api/users/<int:user_id>")
@authorize(permission="delete", role="admin")
async def delete_user(user_id: int):
    return {"deleted": True}
Permission Checking in Functions
python
from flaxon.security import AuthorizationChecker

async def get_user_data(request):
    checker = AuthorizationChecker(getattr(request, "user", None))

    if checker.has_permission("read"):
        return await db.fetch_all("SELECT * FROM users")

    raise HTTPException(403, "Insufficient permissions")
Multiple Permissions
python
@app.post("/api/bulk")
@login_required
async def bulk_operation(request):
    user = getattr(request, "user")
    checker = AuthorizationChecker(user)

    # Require any of the specified permissions
    checker.require_any_permission("write", "admin")

    # Or require all permissions
    checker.require_all_permissions("write", "read")

    return {"success": True}
Resource-Level Authorization
python
@app.get("/users/<int:user_id>")
async def get_user(request, user_id: int):
    user = getattr(request, "user")

    # Check if user owns the resource or is admin
    if user.id != user_id and "admin" not in user.roles:
        raise HTTPException(403, "Cannot access this user")

    return await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
Complete Authorization Example
python
from flaxon import Flaxon, HTTPException
from flaxon.security import (
    login_required,
    permission_required,
    role_required,
    authorize,
    AuthorizationChecker,
    register_role,
    register_permission,
)

app = Flaxon("authz-demo")

# Define roles and permissions
register_permission("read_user", "Read user data")
register_permission("write_user", "Write user data")
register_permission("delete_user", "Delete user data")
register_permission("manage_roles", "Manage roles")

register_role("admin", permissions=["read_user", "write_user", "delete_user", "manage_roles"])
register_role("editor", permissions=["read_user", "write_user"])
register_role("viewer", permissions=["read_user"])

@app.get("/users")
@permission_required("read_user")
async def list_users():
    return await db.fetch_all("SELECT * FROM users")

@app.get("/users/<int:user_id>")
@permission_required("read_user")
async def get_user(user_id: int):
    return await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

@app.post("/users")
@permission_required("write_user")
async def create_user(request):
    data = await request.json()
    return {"created": True, "user": data}

@app.put("/users/<int:user_id>")
@authorize(permission="write_user", role="admin")
async def update_user(user_id: int, request):
    data = await request.json()
    return {"updated": True, "id": user_id}

@app.delete("/users/<int:user_id>")
@role_required("admin")
async def delete_user(user_id: int):
    return {"deleted": True, "id": user_id}

@app.post("/users/<int:user_id>/roles")
@permission_required("manage_roles")
async def assign_role(user_id: int, request):
    data = await request.json()
    return {"assigned": True, "user_id": user_id, "role": data["role"]}