from __future__ import annotations

from flaxon.http import HTMLResponse


class SwaggerUI:
    def __init__(self, openapi_url: str = "/openapi.json", title: str = "Flaxon API") -> None:
        self.openapi_url = openapi_url
        self.title = title

    def render(self) -> HTMLResponse:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{self.title} - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "{self.openapi_url}",
                dom_id: "#swagger-ui",
                deepLinking: true,
                docExpansion: "list",
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                displayRequestDuration: true,
                filter: true,
                persistAuthorization: true,
                showExtensions: true,
                showCommonExtensions: true,
            }});
            window.ui = ui;
        }};
    </script>
</body>
</html>"""
        return HTMLResponse(html)


def create_swagger_ui(openapi_url: str = "/openapi.json", title: str = "Flaxon API") -> HTMLResponse:
    ui = SwaggerUI(openapi_url, title)
    return ui.render()
