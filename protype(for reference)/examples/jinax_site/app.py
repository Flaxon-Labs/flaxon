from pathlib import Path

from flaxon import Flaxon
from flaxon.jinax import Jinax

BASE_DIR = Path(__file__).parent

app = Flaxon("jinax-demo", debug=True)
app.use_templates(
    Jinax(
        BASE_DIR / "templates",
        auto_reload=True,
        strict_undefined=True,
    )
)


@app.get("/")
async def home(request):
    products = [
        {"id": 1, "name": "Flaxon Starter", "price": 0},
        {"id": 2, "name": "Flaxon Production Guide", "price": 19.99},
    ]
    return await request.render(
        "home.html",
        {
            "title": "Flaxon + Jinax",
            "heading": "Jinax is optional",
            "products": products,
        },
    )
