
---

## docs/examples/jinax-website.md

```markdown
# Jinax Website Example

This example demonstrates a server-rendered website using Jinax templates.

## Application Code

```python
# app.py
from datetime import datetime
from pathlib import Path
from flaxon import Flaxon
from flaxon.jinax import Jinax

app = Flaxon("website", debug=True)

# Configure Jinax templates
app.use_templates(Jinax("templates", auto_reload=True))

# Custom filter
jinax = app.jinax

def currency_filter(value, symbol="$"):
    try:
        amount = float(value)
        return f"{symbol}{amount:,.2f}"
    except (TypeError, ValueError):
        return value

jinax.add_filter("currency", currency_filter)

# Custom function
def get_year():
    return datetime.now().year

jinax.add_global("current_year", get_year)

# Routes
@app.get("/")
async def home(request):
    products = [
        {"id": 1, "name": "Flaxon T-Shirt", "price": 29.99, "in_stock": True},
        {"id": 2, "name": "Flaxon Mug", "price": 14.99, "in_stock": True},
        {"id": 3, "name": "Flaxon Sticker Pack", "price": 9.99, "in_stock": False},
        {"id": 4, "name": "Flaxon Developer Guide", "price": 49.99, "in_stock": True},
    ]

    return await request.render("home.html", {
        "title": "Flaxon Store",
        "products": products,
    })

@app.get("/about")
async def about(request):
    return await request.render("about.html", {
        "title": "About Us",
        "description": "Flaxon is a technology-neutral, async-first Python backend framework.",
        "features": [
            "Async-first ASGI architecture",
            "Flask-style route decorators",
            "Optional modular structure",
            "Request validation",
            "WebSocket support",
            "Middleware stack",
            "Readable debugger",
        ],
    })

@app.get("/product/<int:product_id>")
async def product_detail(request, product_id: int):
    products = [
        {"id": 1, "name": "Flaxon T-Shirt", "price": 29.99, "in_stock": True, "description": "Premium cotton t-shirt with Flaxon logo."},
        {"id": 2, "name": "Flaxon Mug", "price": 14.99, "in_stock": True, "description": "Ceramic mug with Flaxon branding."},
        {"id": 3, "name": "Flaxon Sticker Pack", "price": 9.99, "in_stock": False, "description": "Pack of 5 Flaxon stickers."},
        {"id": 4, "name": "Flaxon Developer Guide", "price": 49.99, "in_stock": True, "description": "Complete guide to building with Flaxon."},
    ]

    product = None
    for p in products:
        if p["id"] == product_id:
            product = p
            break

    if not product:
        return await request.render("404.html", {"title": "Product Not Found"}), 404

    return await request.render("product.html", {
        "title": product["name"],
        "product": product,
    })



    Template Files
templates/base.html
html
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Flaxon{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f8fafc; color: #0f172a; }
        nav { background: #0f172a; color: #e2e8f0; padding: 1rem 2rem; display: flex; gap: 2rem; align-items: center; }
        nav a { color: #e2e8f0; text-decoration: none; }
        nav a:hover { color: #7dd3fc; }
        nav .brand { font-weight: bold; font-size: 1.2rem; }
        main { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
        footer { text-align: center; padding: 2rem; color: #94a3b8; border-top: 1px solid #e2e8f0; margin-top: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin: 1.5rem 0; }
        .card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card h3 { margin-bottom: 0.5rem; }
        .price { font-size: 1.25rem; font-weight: bold; color: #0284c7; }
        .in-stock { color: #22c55e; font-size: 0.875rem; }
        .out-of-stock { color: #ef4444; font-size: 0.875rem; }
        .btn { display: inline-block; background: #0284c7; color: white; padding: 0.5rem 1rem; border-radius: 6px; text-decoration: none; margin-top: 0.5rem; }
        .btn:hover { background: #0369a1; }
        .tag { display: inline-block; background: #e2e8f0; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; margin: 0.25rem; }
        .feature-list { list-style: none; padding: 0; }
        .feature-list li { padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0; }
        .feature-list li:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <nav>
        <span class="brand">Flaxon</span>
        <a href="/">Home</a>
        <a href="/about">About</a>
        <span style="margin-left: auto; color: #94a3b8;">Simple Python. Serious Applications.</span>
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>&copy; {{ current_year() }} Flaxon. All rights reserved.</p>
    </footer>
</body>
</html>
templates/home.html
html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
    <h1>Welcome to the Flaxon Store</h1>
    <p>Explore our collection of Flaxon merchandise and resources.</p>

    <div class="grid">
        {% for product in products %}
            <div class="card">
                <h3>{{ product.name }}</h3>
                <p class="price">{{ product.price|currency("USD") }}</p>
                {% if product.in_stock %}
                    <span class="in-stock">✓ In Stock</span>
                {% else %}
                    <span class="out-of-stock">✗ Out of Stock</span>
                {% endif %}
                <br>
                <a href="/product/{{ product.id }}" class="btn">View Details</a>
            </div>
        {% endfor %}
    </div>
{% endblock %}
templates/about.html
html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>

    <h2>Features</h2>
    <ul class="feature-list">
        {% for feature in features %}
            <li>{{ feature }}</li>
        {% endfor %}
    </ul>

    <h2>Get Started</h2>
    <pre><code>pip install flaxon[standard]
flaxon run app:app --reload</code></pre>
{% endblock %}
templates/product.html
html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
    <a href="/">← Back to store</a>

    <div class="card" style="margin-top: 1rem;">
        <h1>{{ product.name }}</h1>
        <p class="price">{{ product.price|currency("USD") }}</p>
        <p>{{ product.description }}</p>
        {% if product.in_stock %}
            <span class="in-stock">✓ In Stock</span>
        {% else %}
            <span class="out-of-stock">✗ Out of Stock</span>
        {% endif %}
        <br>
        <button class="btn">Add to Cart</button>
    </div>
{% endblock %}
Running the Application
bash
# Install dependencies
pip install flaxon[standard,templates]

# Run the application
flaxon run app:app --reload
Visit http://localhost:8000 to see the website.