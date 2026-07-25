
from __future__ import annotations

from typing import Any


class TemplateEngine:
    """
    Template engine for generating project files and code components.
    """

    def __init__(self) -> None:
        """Initialize the template engine with default Flaxon templates."""
        self._templates = self._default_templates()

    def _default_templates(self) -> dict[str, str]:
        return {
            "app.py": """from flaxon import Flaxon

app = Flaxon("{name}", debug=True)

@app.get("/")
async def home():
    return {{"message": "Hello from {name}"}}

@app.get("/health")
async def health():
    return {{"status": "healthy", "service": "{name}"}}
""",
            "pyproject.toml": """[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["flaxon-framework[standard]>=0.1.0"]
""",
            "gitignore": """.venv/
__pycache__/
*.pyc
.env
dist/
build/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
""",
            "README.md": """# {name}

A Flaxon application.

## Installation

```bash
python -m pip install -e .

```

## Running

```bash
flaxon run app:app --reload

```

## Testing

```bash
pytest

```

""",
            "controller.py": """from flaxon import Router

router = Router(prefix="/api/{name}")

@router.get("/")
async def index():
    return {{"message": "{name} controller"}}

@router.get("/{id:int}")
async def get(id: int):
    return {{"id": id, "name": "{name}"}}

@router.post("/")
async def create(request):
    data = await request.json()
    return {{"created": True, "data": data}}
""",

            "schema.py": """from flaxon.validation import Schema, fields

class Create{name_capitalize}(Schema):
    name = fields.String(required=True, min_length=2, max_length=80)
    email = fields.Email(required=True)
    age = fields.Integer(required=False, minimum=13, maximum=120)


class Update{name_capitalize}(Schema):
    name = fields.String(required=False, min_length=2, max_length=80)
    email = fields.Email(required=False)
    age = fields.Integer(required=False, minimum=13, maximum=120)
""",

            "service.py": """class {name_capitalize}Service:
    def __init__(self, db):
        self.db = db

    async def get_all(self):
        return await self.db.fetch_all("SELECT * FROM {name}s")

    async def get_by_id(self, id):
        return await self.db.fetch_one(
            "SELECT * FROM {name}s WHERE id = $1",
            id,
        )

    async def create(self, data):
        return await self.db.fetch_one(
            "INSERT INTO {name}s (name, email) VALUES ($1, $2) RETURNING *",
            data["name"],
            data["email"],
        )

    async def update(self, id, data):
        return await self.db.fetch_one(
            "UPDATE {name}s SET name = $1, email = $2 WHERE id = $3 RETURNING *",
            data["name"],
            data["email"],
            id,
        )

    async def delete(self, id):
        await self.db.execute(
            "DELETE FROM {name}s WHERE id = $1",
            id,
        )
""",

            "middleware.py": """from flaxon.middleware import Middleware

class {name_capitalize}Middleware(Middleware):
    def __init__(self, app, options=None):
        super().__init__(app)
        self.options = options or {}

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        scope["{name}"] = "value"

        async def send_wrapper(message):
            await send(message)

        await self.app(scope, receive, send_wrapper)
""",
}


    def render(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a registered template by name.
        """
        context = context or {}
        template = self._templates.get(template_name, "")
        return self.render_string(template, context)

    def render_string(
        self,
        template: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a template string using the supplied context.
        """
        context = context or {}
        result = template

        flat_context: dict[str, str] = {}

        for key, value in context.items():
            if isinstance(value, str):
                flat_context[key] = value
            elif hasattr(value, "dict") and callable(value.dict):
                for sub_key, sub_value in value.dict().items():
                    flat_context[f"{key}.{sub_key}"] = str(sub_value)
            else:
                flat_context[key] = str(value)

        for key, value in flat_context.items():
            result = result.replace(f"{{{key}}}", value)

        return result.replace("{{", "{").replace("}}", "}")

    def add_template(self, name: str, template: str) -> None:
        """Register or replace a template."""
        self._templates[name] = template

    def get_template(self, name: str) -> str | None:
        """Return a template by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """Return all registered template names."""
        return list(self._templates.keys())
