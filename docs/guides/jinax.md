
---

## docs/guides/jinax.md

```markdown
# Jinax Templates

## Overview

Jinax is Flaxon's optional Jinja2 template integration. It provides server-side HTML rendering with autoescaping, inheritance, filters, and async support.

## Installation

```bash
pip install flaxon[templates]


Setup
python
from flaxon import Flaxon
from flaxon.jinax import Jinax

app = Flaxon("website")
app.use_templates(Jinax("templates", auto_reload=True))
Basic Template
Template File (templates/home.html)
html
<!doctype html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>Welcome, {{ name }}!</h1>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</body>
</html>
Route
python
@app.get("/")
async def home(request):
    return await request.render("home.html", {
        "title": "Home",
        "name": "World",
        "items": ["Routing", "Validation", "Templates"],
    })
Template Inheritance
Base Template (templates/base.html)
html
<!doctype html>
<html>
<head>
    <title>{% block title %}Flaxon{% endblock %}</title>
</head>
<body>
    <header>{% block header %}Default Header{% endblock %}</header>
    <main>{% block content %}{% endblock %}</main>
    <footer>{% block footer %}Default Footer{% endblock %}</footer>
</body>
</html>
Child Template (templates/page.html)
html
{% extends "base.html" %}

{% block title %}My Page{% endblock %}

{% block header %}Welcome to My Page{% endblock %}

{% block content %}
    <h1>{{ heading }}</h1>
    <p>{{ description }}</p>
{% endblock %}
Filters
Built-in Filters
python
{{ value|capitalize }}
{{ value|lower }}
{{ value|upper }}
{{ value|title }}
{{ value|trim }}
{{ value|escape }}
{{ value|safe }}
{{ value|json }}
{{ value|length }}
{{ value|reverse }}
{{ value|join(", ") }}
{{ value|replace(old, new) }}
{{ value|date("%Y-%m-%d") }}
{{ value|datetime("%Y-%m-%d %H:%M:%S") }}
{{ value|currency("USD") }}
{{ value|truncate(100, "...") }}
{{ value|default("N/A") }}
{{ value|first }}
{{ value|last }}
Custom Filters
python
jinax = Jinax("templates")

def currency_filter(value, symbol="$"):
    return f"{symbol}{value:.2f}"

jinax.add_filter("currency", currency_filter)

@app.get("/")
async def home(request):
    return await request.render("product.html", {
        "price": 99.99,
    })
html
<p>Price: {{ price|currency("USD") }}</p>
Functions
python
jinax = Jinax("templates")

def get_user(name):
    return {"name": name, "email": f"{name}@example.com"}

jinax.add_global("get_user", get_user)

@app.get("/")
async def home(request):
    return await request.render("user.html", {
        "username": "alice",
    })
html
{% set user = get_user(username) %}
<p>{{ user.name }} - {{ user.email }}</p>
Macros
templates/macros.html
html
{% macro render_card(title, content, color="blue") %}
<div class="card card-{{ color }}">
    <h3>{{ title }}</h3>
    <p>{{ content }}</p>
</div>
{% endmacro %}
Using Macros
html
{% import "macros.html" as macros %}

{{ macros.render_card("Welcome", "This is a card", "green") }}
Async Rendering
python
@app.get("/async")
async def async_template(request):
    # Jinax supports async rendering
    return await request.render("async.html", {
        "data": await fetch_data(),
    })
Hot Reloading
python
app.use_templates(Jinax("templates", auto_reload=True))
Template Caching
python
jinax = Jinax("templates", cache_size=100)
Complete Example
python
from flaxon import Flaxon
from flaxon.jinax import Jinax

app = Flaxon("website-demo")
app.use_templates(Jinax("templates", auto_reload=True))

# Custom filter
def currency_filter(value, symbol="$"):
    return f"{symbol}{value:,.2f}"

jinax = app.jinax
jinax.add_filter("currency", currency_filter)

# Custom function
def get_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

jinax.add_global("now", get_time)

@app.get("/")
async def home(request):
    products = [
        {"name": "Laptop", "price": 999.99},
        {"name": "Mouse", "price": 19.99},
        {"name": "Keyboard", "price": 49.99},
    ]

    return await request.render("home.html", {
        "title": "Store",
        "products": products,
    })

@app.get("/about")
async def about(request):
    return await request.render("about.html", {
        "page": "About Us",
    })
templates/home.html
html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
    <h1>Welcome to our store</h1>
    <div class="products">
    {% for product in products %}
        <div class="product">
            <h3>{{ product.name }}</h3>
            <p>{{ product.price|currency("USD") }}</p>
        </div>
    {% endfor %}
    </div>
    <p>Generated at: {{ now() }}</p>
{% endblock %}