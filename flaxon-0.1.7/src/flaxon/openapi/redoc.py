from __future__ import annotations

from flaxon.http import HTMLResponse


class ReDoc:
    def __init__(self, openapi_url: str = "/openapi.json", title: str = "Flaxon API") -> None:
        self.openapi_url = openapi_url
        self.title = title

    def render(self) -> HTMLResponse:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{self.title} - ReDoc</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        redoc {{
            display: block;
        }}
    </style>
</head>
<body>
    <redoc spec-url="{self.openapi_url}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
        return HTMLResponse(html)


def create_redoc(openapi_url: str = "/openapi.json", title: str = "Flaxon API") -> HTMLResponse:
    doc = ReDoc(openapi_url, title)
    return doc.render()
