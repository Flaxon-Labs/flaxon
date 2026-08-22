

# Flaxon Admin Dashboard Guide

> Learn how to build a powerful administration dashboard with Flaxon. This guide covers registration, CRUD operations, customization, permissions, actions, dashboards, and best practices.

---

# Table of Contents

1. Introduction
2. Creating an Admin Dashboard
3. Registering Models
4. CRUD Operations
5. Model Hooks
6. List Display
7. Search
8. Filters
9. Read-only Fields
10. Custom Actions
11. Custom Display Fields
12. Custom Views
13. Permissions
14. Admin Configuration
15. Templates
16. Styling
17. JavaScript
18. Dashboard Widgets
19. Authentication
20. Best Practices
21. Complete Example

---

# Introduction

The Flaxon Admin module provides a complete administration panel similar to Django Admin.

Instead of writing CRUD pages manually, Flaxon automatically generates pages for your models.

Features include:

- Automatic CRUD
- Search
- Filtering
- Pagination
- Custom actions
- Custom fields
- Dashboard
- Authentication
- Permissions
- Custom templates
- Dark mode
- Fully customizable

---

# Creating an Admin Dashboard

```python
from flaxon import Flaxon
from flaxon.admin import AdminDashboard

app = Flaxon("shop")

admin = AdminDashboard(
    app,
    url_prefix="/admin",
)
```

Visit:

```
/admin
```

---

# Admin Configuration

```python
from flaxon.admin import AdminConfig

config = AdminConfig(
    site_title="Shop Admin",
    site_header="Shop Administration",
    index_title="Dashboard",
)

admin = AdminDashboard(
    app,
    config=config,
)
```

---

## Available Options

| Option | Description |
|---------|-------------|
| site_title | Browser title |
| site_header | Header text |
| index_title | Dashboard heading |
| logo_url | Custom logo |
| enable_dark_mode | Enable dark theme |
| enable_search | Search bar |
| enable_filters | Sidebar filters |
| enable_actions | Bulk actions |
| enable_pagination | Pagination |
| custom_styles | CSS file |
| custom_scripts | JavaScript file |

---

# Registering Models

```python
from flaxon.admin import admin_model

@admin_model
class Product:
    pass
```

Register:

```python
admin.register(Product)
```

---

# Registering with Options

```python
admin.register(
    Product,
    list_display=[
        "id",
        "name",
        "price",
        "status",
    ],
    search_fields=[
        "name",
        "description",
    ],
    list_filter=[
        "status",
        "category",
    ],
    readonly_fields=[
        "id",
    ],
)
```

---

# CRUD Pages

Flaxon automatically creates:

```
/admin/products/
/admin/products/add/
/admin/products/1/
/admin/products/1/edit/
/admin/products/1/delete/
```

No extra code required.

---

# Required Model Hooks

The admin automatically calls these methods if available.

---

## List Records

```python
@classmethod
async def get_instances(cls):
    return list(cls._data.values())
```

---

## Get One Record

```python
@classmethod
async def get_instance(cls, id):
    return cls._data.get(id)
```

---

## Create

```python
@classmethod
async def create_instance(cls, data):
    cls._data[data["id"]] = data
    return data
```

---

## Update

```python
@classmethod
async def update_instance(cls, id, data):
    cls._data[id].update(data)
    return cls._data[id]
```

---

## Delete

```python
@classmethod
async def delete_instance(cls, id):
    del cls._data[id]
    return True
```

---

# List Display

Choose visible columns.

```python
admin.register(
    Product,
    list_display=[
        "id",
        "name",
        "price",
        "stock",
    ],
)
```

Produces

| ID | Name | Price | Stock |

---

# Search

```python
admin.register(
    Product,
    search_fields=[
        "name",
        "description",
    ],
)
```

Users can search:

```
Laptop
Phone
Mouse
```

---

# Filters

```python
admin.register(
    Product,
    list_filter=[
        "category",
        "status",
    ],
)
```

Sidebar:

```
Category

Electronics
Books
Games

Status

Published
Draft
Archived
```

---

# Read-only Fields

```python
admin.register(
    Product,
    readonly_fields=[
        "id",
        "created_at",
    ],
)
```

These fields cannot be edited.

---

# Custom Admin Actions

Actions allow bulk updates.

```python
from flaxon.admin import admin_action

@admin_action("Publish")
async def publish(self, ids):
    ...
```

Register:

```python
admin.register(
    Post,
    actions=[
        publish,
    ],
)
```

Example:

```
Select posts

▼ Actions

Publish

Delete

Archive
```

---

# Custom Display Fields

```python
from flaxon.admin import admin_display

@admin_display(header="Price + Tax")
def total_price(self, obj):
    return obj["price"] * 1.15
```

Display:

| Price | Price + Tax |

---

# Admin Views

Built-in views include:

- ListView
- DetailView
- CreateView
- UpdateView
- DeleteView

You may subclass them.

```python
from flaxon.admin.views import ListView

class ProductList(ListView):

    async def render(self):
        ...
```

---

# Dashboard

Default dashboard shows:

- Registered models
- Recent activity
- Quick links

You can extend it.

```python
class Dashboard:

    async def get_context(self):

        return {
            "users": 150,
            "orders": 92,
            "sales": 10234,
        }
```

---

# Permissions

Protect admin pages.

```python
@app.middleware
async def auth(request, call_next):

    if not request.user:
        return RedirectResponse("/login")

    return await call_next(request)
```

---

# Role-Based Access

```python
if not request.user.has_role("admin"):
    raise PermissionDeniedError()
```

---

# Authentication

Recommended flow:

```
Login

↓

Session

↓

Admin

↓

Logout
```

---

# Custom Templates

Default structure

```
templates/

    admin/

        base.html

        index.html

        list.html

        detail.html

        add.html

        edit.html

        delete.html
```

Override any template.

---

# Static Files

```
static/

    admin/

        css/

            admin.css

        js/

            admin.js

        images/
```

---

# Custom CSS

```python
config = AdminConfig(
    custom_styles="/static/admin/admin.css",
)
```

---

# Custom JavaScript

```python
config = AdminConfig(
    custom_scripts="/static/admin/admin.js",
)
```

---

# Dashboard Widgets

Example widget:

```python
class SalesWidget:

    async def render(self):

        return {
            "title": "Sales",
            "value": "$15,230",
        }
```

Possible widgets:

- Users
- Orders
- Revenue
- CPU
- Memory
- Recent Activity
- Latest Orders

---

# Pagination

Automatically enabled.

```
Showing

1–25

of

12,000
```

---

# Bulk Delete

```python
Delete Selected
```

Deletes every checked row.

---

# Bulk Update

Example:

```
Select

↓

Mark Active

↓

Update
```

---

# Export Data

Future example:

```
CSV

Excel

JSON

PDF
```

---

# Audit Logging

Recommended model hook:

```python
log_action(
    user=request.user,
    action="delete",
    model="Product",
)
```

---

# Best Practices

Always:

- Require login
- Use HTTPS
- Enable CSRF
- Limit permissions
- Log changes
- Validate input
- Paginate large datasets
- Hide dangerous actions

---

# Complete Example

```python
from flaxon import Flaxon
from flaxon.admin import (
    AdminDashboard,
    AdminConfig,
    admin_model,
)

app = Flaxon("shop")

config = AdminConfig(
    site_title="Shop Admin",
    enable_dark_mode=True,
)

admin = AdminDashboard(
    app,
    config=config,
)

@admin_model
class Product:

    _data = {}

    @classmethod
    async def get_instances(cls):
        return list(cls._data.values())

    @classmethod
    async def get_instance(cls, id):
        return cls._data.get(id)

    @classmethod
    async def create_instance(cls, data):
        cls._data[data["id"]] = data
        return data

    @classmethod
    async def update_instance(cls, id, data):
        cls._data[id].update(data)
        return cls._data[id]

    @classmethod
    async def delete_instance(cls, id):
        del cls._data[id]
        return True

admin.register(
    Product,
    list_display=[
        "id",
        "name",
        "price",
    ],
    search_fields=[
        "name",
    ],
    list_filter=[
        "category",
    ],
)
```


# Flaxon GraphQL + Admin Integration Guide

> Learn how to combine **Flaxon GraphQL** and the **Flaxon Admin Dashboard** into a single application. This guide demonstrates how both systems can work together using the same models and business logic.

---

# Table of Contents

1. Introduction
2. Why Use GraphQL and Admin Together?
3. Architecture
4. Shared Models
5. Shared Services
6. GraphQL + Admin Example
7. Authentication
8. Permissions
9. Realtime Updates
10. File Structure
11. Best Practices
12. Production Tips
13. Complete Project Example
14. Summary

---

# Introduction

Flaxon's GraphQL module and Admin Dashboard are designed to work together.

Instead of creating separate logic for your API and your admin panel, both systems can share:

- Models
- Services
- Validation
- Authentication
- Permissions
- Database access
- Business logic

This means less duplicated code and easier maintenance.

---

# Why Use GraphQL and Admin Together?

A modern application usually has two different users.

| User | Uses |
|-------|------|
| Customers | GraphQL API |
| Employees | Admin Dashboard |

Example

```
Customers

↓

GraphQL API

↓

Business Logic

↓

Database

↑

Admin Dashboard

↓

Administrators
```

Both interfaces use the same backend.

---

# Architecture

```
                Browser
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼

   GraphQL API         Admin Dashboard

        │                     │
        └──────────┬──────────┘
                   │

            Service Layer

                   │

             Validation Layer

                   │

                Database
```

---

# Shared Models

Both GraphQL and Admin should use the same model.

```python
@admin_model
class Product:

    _products = []

    @classmethod
    async def get_instances(cls):
        return cls._products

    @classmethod
    async def create_instance(cls, data):
        cls._products.append(data)
        return data
```

The admin panel automatically uses these methods.

GraphQL can use the same methods.

```python
Product.get_instances()

Product.create_instance()
```

---

# Shared Services

Instead of putting business logic inside GraphQL or Admin, create a service.

```
services/

    product_service.py
```

Example

```python
class ProductService:

    @staticmethod
    async def all():

        return Product.get_instances()

    @staticmethod
    async def create(data):

        return Product.create_instance(data)
```

Now both systems call the service.

---

# GraphQL Query

```python
class Query(ObjectType):

    products = Field(List(ProductType))

    @staticmethod
    async def resolve_products(parent, args, context, info):

        return await ProductService.all()
```

---

# Admin Registration

```python
admin.register(

    Product,

    list_display=[
        "id",
        "name",
        "price",
    ],
)
```

No duplicated logic.

---

# Creating Data

GraphQL mutation

```graphql
mutation {

    createProduct(
        name: "Laptop"
        price: 1200
    ) {

        id
        name
    }

}
```

Mutation

↓

Service

↓

Database

↓

Admin instantly shows new product.

---

# Editing Data

Administrator edits

```
/admin/products/5/edit
```

Admin

↓

Service

↓

Database

↓

GraphQL returns updated data.

---

# Deleting Data

Administrator deletes

```
Product #12
```

Immediately

```
GraphQL

↓

No longer returns Product #12
```

Everything stays synchronized.

---

# Authentication

Use one authentication system.

```
Login

↓

Session

↓

JWT

↓

GraphQL

+

Admin
```

Example

```python
app.use_auth(JWTBackend(...))
```

Both systems now know

```python
request.user
```

---

# Permissions

GraphQL

```python
if not context.user.has_role("admin"):

    raise PermissionDeniedError()
```

Admin

```python
if not request.user.has_role("admin"):

    raise PermissionDeniedError()
```

Shared permission system.

---

# Validation

Validation should be reused.

```
Request

↓

Schema

↓

Validation

↓

Service

↓

Database
```

Example

```python
CreateProduct.load(data)
```

Admin and GraphQL use the same schema.

---

# Error Handling

GraphQL

```json
{
  "errors": [
    {
      "message": "Permission denied."
    }
  ]
}
```

Admin

```
Permission denied.
```

---

# Realtime Updates

GraphQL subscriptions work well with the admin.

Admin creates a product.

↓

Subscription publishes an event.

↓

Connected clients receive the update immediately.

```
Admin

↓

Product Created

↓

Subscription

↓

Mobile App

↓

Website

↓

Desktop App
```

---

# Subscription Example

```python
await subscription_manager.publish(

    "products",

    product,
)
```

Client

```graphql
subscription {

    productCreated {

        id
        name
    }

}
```

---

# Recommended File Structure

```
app/

├── admin/
│
├── graphql/
│
├── models/
│
├── services/
│
├── validation/
│
├── auth/
│
├── database/
│
├── routes/
│
├── templates/
│
└── static/
```

---

# Project Structure

```
app.py

↓

GraphQL

↓

Services

↓

Database

↓

Admin

↓

Templates
```

---

# Best Practices

Use:

- Shared services
- Shared validation
- Shared permissions
- Shared authentication
- Shared database models
- Shared caching

Avoid:

- Duplicate business logic
- Duplicate validation
- Duplicate permissions
- Direct database access inside GraphQL

---

# Production Tips

Enable

- JWT Authentication
- HTTPS
- Rate limiting
- CSRF protection
- Logging
- Monitoring
- Pagination
- Complexity limits
- Query depth limits
- Persisted queries

Protect

- `/admin`
- `/graphql`

Use role-based access for both.

---

# Complete Project Example

```
myapp/

├── app.py
│
├── models/
│   ├── user.py
│   ├── product.py
│   └── order.py
│
├── services/
│   ├── user_service.py
│   ├── product_service.py
│   └── order_service.py
│
├── graphql/
│   ├── schema.py
│   ├── queries.py
│   ├── mutations.py
│   └── subscriptions.py
│
├── admin/
│   ├── users.py
│   ├── products.py
│   └── orders.py
│
├── validation/
│
├── auth/
│
├── templates/
│
└── static/
```

---

# Typical Request Flow

```
Client

↓

GraphQL Query

↓

Resolver

↓

Service

↓

Validation

↓

Database

↓

Response
```

---

# Typical Admin Flow

```
Administrator

↓

Admin Form

↓

Validation

↓

Service

↓

Database

↓

Redirect
```

---

# Comparing Both Systems

| Feature | GraphQL | Admin |
|----------|----------|-------|
| External API | ✅ | ❌ |
| Internal Management | ❌ | ✅ |
| CRUD | Manual | Automatic |
| Mobile Apps | ✅ | ❌ |
| Web Apps | ✅ | ✅ |
| Dashboard | ❌ | ✅ |
| Real-time | ✅ | ❌ |
| Subscriptions | ✅ | ❌ |
| Search | Client-defined | Built-in |
| Filters | Client-defined | Built-in |

---

# When to Use GraphQL

Use GraphQL when building:

- Mobile apps
- Single-page applications
- Public APIs
- Third-party integrations
- Real-time systems
- Flexible APIs

---

# When to Use Admin

Use Admin when managing:

- Products
- Orders
- Customers
- Blog posts
- Users
- Inventory
- Reports
- Internal tools

---

# Combining Everything

A typical Flaxon application includes:

```
REST API

+

GraphQL API

+

Admin Dashboard

+

Authentication

+

Validation

+

Database

+

Templates

+

WebSockets
```

All powered by the same framework.



# Flaxon GraphQL & Admin — Real-World Projects

> In this lesson you'll learn how GraphQL and the Admin Dashboard work together by building practical applications. Each project demonstrates common patterns used in production.

---

# Table of Contents

1. Introduction
2. Project 1 — Blog CMS
3. Project 2 — E-Commerce Store
4. Project 3 — School Management System
5. Project 4 — Hospital Management
6. Project 5 — Inventory Management
7. Project 6 — Social Media API
8. Project 7 — SaaS Dashboard
9. Project Architecture
10. Best Practices
11. Summary

---

# Introduction

GraphQL and the Admin Dashboard complement each other.

GraphQL provides a flexible API for applications, while the Admin Dashboard gives administrators an easy way to manage data.

```
Customers

↓

GraphQL API

↓

Database

↑

Admin Dashboard

↓

Administrators
```

---

# Project 1 — Blog CMS

## Features

- Articles
- Categories
- Tags
- Comments
- Authors
- Drafts
- Publishing

---

## GraphQL

Public website

```graphql
query {

    posts {

        title

        slug

        author {

            name
        }

    }

}
```

---

## Admin

Editors manage

- Posts
- Categories
- Tags
- Users
- Comments

without writing CRUD pages.

---

## Folder Structure

```
blog/

├── graphql/
├── admin/
├── models/
├── services/
├── templates/
└── static/
```

---

# Project 2 — E-Commerce Store

## GraphQL

Customers

- Browse products
- Search
- Categories
- Shopping cart
- Orders

Example

```graphql
query {

    products {

        id

        name

        price

        stock

    }

}
```

---

## Admin

Employees manage

- Products
- Inventory
- Categories
- Coupons
- Orders
- Customers

---

## Dashboard

```
Orders Today

125

Revenue

$25,200

Products

812

Customers

2,945
```

---

# Project 3 — School Management

Students use GraphQL.

Teachers use Admin.

---

## GraphQL

```graphql
query {

    courses {

        title

        teacher

        students

    }

}
```

---

## Admin

Manage

- Students
- Teachers
- Courses
- Attendance
- Exams
- Grades

---

# Project 4 — Hospital Management

Patients use GraphQL.

Staff use Admin.

---

## GraphQL

Patients can

- Book appointments
- View prescriptions
- View reports
- Update profile

---

## Admin

Doctors manage

- Patients
- Staff
- Rooms
- Billing
- Medicines
- Reports

---

# Project 5 — Inventory Management

Warehouse application.

---

## GraphQL

Warehouse scanners

↓

GraphQL

↓

Inventory

---

## Admin

Manage

- Products
- Warehouses
- Suppliers
- Shipments
- Purchases

---

# Project 6 — Social Media

GraphQL powers

- Feed
- Messages
- Notifications
- Friends
- Posts

---

Example

```graphql
query {

    timeline {

        user

        post

        likes

        comments

    }

}
```

---

## Admin

Moderators manage

- Users
- Reports
- Posts
- Comments
- Bans

---

# Project 7 — SaaS Dashboard

Customers

↓

GraphQL

↓

Subscription

↓

Database

Admins

↓

Admin Dashboard

---

Manage

- Companies
- Users
- Plans
- Billing
- API Keys
- Support Tickets

---

# Authentication Flow

```
Login

↓

JWT

↓

GraphQL

↓

API
```

Admin

```
Login

↓

Session

↓

Dashboard
```

---

# Shared Validation

Both systems use

```
Schema

↓

Validation

↓

Database
```

No duplicated validation rules.

---

# Shared Services

```
GraphQL

↓

ProductService

↓

Database

↑

Admin
```

Business logic exists only once.

---

# Notifications

Administrator

↓

Creates Product

↓

Database

↓

Subscription

↓

Clients Receive Update

---

# Audit Logging

Every change is recorded.

```
Admin

↓

Edit Product

↓

Audit Log

↓

Database
```

---

# Background Tasks

Administrator

↓

Generate Report

↓

Task Queue

↓

Worker

↓

Download PDF

---

# GraphQL Playground

Developers

```
/graphql/graphiql
```

or

```
/graphql/altair
```

for testing queries.

---

# Admin Interface

```
Dashboard

↓

Users

↓

Products

↓

Orders

↓

Reports

↓

Settings
```

---

# Recommended Architecture

```
app/

├── graphql/
│
├── admin/
│
├── auth/
│
├── validation/
│
├── services/
│
├── database/
│
├── tasks/
│
├── websocket/
│
├── templates/
│
└── static/
```

---

# Production Checklist

Use

- HTTPS
- JWT
- Sessions
- CSRF
- Rate limiting
- Logging
- Monitoring
- Validation
- Pagination
- Search
- Filters
- Caching

---

# Security Checklist

Protect

- `/admin`
- `/graphql`

Enable

- Authentication
- Authorization
- Query depth limits
- Complexity limits
- Persisted queries
- Input validation
- Audit logging

---

# Deployment

Example

```
Internet

↓

NGINX

↓

Flaxon

↓

GraphQL

↓

Admin

↓

Database

↓

Redis

↓

Workers
```

---

# REST vs GraphQL vs Admin

| Feature | REST | GraphQL | Admin |
|----------|------|----------|-------|
| Public API | ✅ | ✅ | ❌ |
| Internal Dashboard | ❌ | ❌ | ✅ |
| Mobile Apps | ✅ | ✅ | ❌ |
| CRUD | Manual | Manual | Automatic |
| Search | Manual | Client-defined | Built-in |
| Filters | Manual | Client-defined | Built-in |
| Dashboard | ❌ | ❌ | ✅ |
| Real-time | WebSockets | Subscriptions | ❌ |

---

# Complete Enterprise Stack

A production Flaxon application might include:

```
Flaxon

├── REST API
├── GraphQL API
├── Admin Dashboard
├── Authentication
├── Authorization
├── Validation
├── ORM
├── Templates
├── Static Files
├── WebSockets
├── Background Tasks
├── Scheduler
├── Cache
├── Database
└── Monitoring
```

---

# Learning Path

1. Learn Flaxon basics.
2. Build REST APIs.
3. Learn routing and middleware.
4. Learn validation.
5. Learn authentication.
6. Build GraphQL APIs.
7. Create subscriptions.
8. Build an Admin Dashboard.
9. Connect GraphQL and Admin.
10. Deploy to production.

---
