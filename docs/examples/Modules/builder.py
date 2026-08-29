"""A small drag-and-drop page builder for Flaxon.

Pages are stored as an ordered list of "blocks" -- each block has a
type (heading, paragraph, image, button, divider, spacer) and a dict
of properties. The builder SPA lets you drag blocks from a palette
onto a canvas, reorder them, edit their properties, and save. Saved
pages render as real HTML at a public URL.

Usage:

    from flaxon import Flaxon
    from builder import builder_module

    app = Flaxon("my-app")
    app.mount_module(builder_module, prefix="/builder")

Then visit /builder to edit, and /builder/p/<slug> to view the
rendered page.
"""

from __future__ import annotations

import html
import uuid
from pathlib import Path
from typing import Any

from flaxon.exceptions import BadRequest, NotFound
from flaxon.http import HTMLResponse, JSONResponse, Request
from flaxon.modules import FlaxonModule

BLOCK_TYPES: dict[str, dict[str, Any]] = {
    "heading": {
        "label": "Heading",
        "icon": "H",
        "props": {"text": "New Heading", "level": "2"},
    },
    "paragraph": {
        "label": "Paragraph",
        "icon": "P",
        "props": {"text": "New paragraph text. Click to edit."},
    },
    "image": {
        "label": "Image",
        "icon": "IMG",
        "props": {"src": "https://placehold.co/600x300", "alt": "Image"},
    },
    "button": {
        "label": "Button",
        "icon": "BTN",
        "props": {"text": "Click me", "href": "#", "style": "primary"},
    },
    "divider": {
        "label": "Divider",
        "icon": "--",
        "props": {},
    },
    "spacer": {
        "label": "Spacer",
        "icon": "  ",
        "props": {"height": "40"},
    },
}

# In-memory store: slug -> {"title": str, "blocks": [ {id, type, props}, ... ]}
_pages: dict[str, dict[str, Any]] = {
    "home": {
        "title": "Home",
        "blocks": [
            {"id": "b1", "type": "heading", "props": {"text": "Welcome", "level": "1"}},
            {"id": "b2", "type": "paragraph", "props": {"text": "Built with the Flaxon drag-and-drop builder."}},
        ],
    }
}

_PACKAGE_DIR = Path(__file__).parent

builder_module = FlaxonModule("builder")


def _validate_block(raw: dict[str, Any]) -> dict[str, Any]:
    block_type = raw.get("type")
    if block_type not in BLOCK_TYPES:
        raise BadRequest(f"Unknown block type '{block_type}'.")
    props = raw.get("props") or {}
    if not isinstance(props, dict):
        raise BadRequest("Block 'props' must be an object.")
    return {
        "id": raw.get("id") or uuid.uuid4().hex[:8],
        "type": block_type,
        "props": {str(k): str(v) for k, v in props.items()},
    }


def render_blocks(blocks: list[dict[str, Any]]) -> str:
    """Turn saved block JSON into real HTML."""
    parts = []
    for block in blocks:
        block_type = block.get("type")
        props = block.get("props", {})

        if block_type == "heading":
            level = props.get("level", "2")
            level = level if level in {"1", "2", "3", "4"} else "2"
            text = html.escape(props.get("text", ""))
            parts.append(f"<h{level}>{text}</h{level}>")
        elif block_type == "paragraph":
            text = html.escape(props.get("text", ""))
            parts.append(f"<p>{text}</p>")
        elif block_type == "image":
            src = html.escape(props.get("src", ""), quote=True)
            alt = html.escape(props.get("alt", ""), quote=True)
            parts.append(f'<img src="{src}" alt="{alt}" style="max-width:100%;">')
        elif block_type == "button":
            href = html.escape(props.get("href", "#"), quote=True)
            text = html.escape(props.get("text", "Button"))
            style = props.get("style", "primary")
            css = (
                "display:inline-block;padding:10px 20px;border-radius:6px;text-decoration:none;"
                + ("background:#4f46e5;color:#fff;" if style == "primary" else "background:#e5e7eb;color:#111;")
            )
            parts.append(f'<a href="{href}" style="{css}">{text}</a>')
        elif block_type == "divider":
            parts.append('<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">')
        elif block_type == "spacer":
            height = props.get("height", "40")
            height = height if height.isdigit() else "40"
            parts.append(f'<div style="height:{height}px"></div>')
    return "\n".join(parts)


# --------------------------------------------------------------------
# Builder editor UI
# --------------------------------------------------------------------

@builder_module.get("/")
async def editor_shell() -> HTMLResponse:
    html_content = (_PACKAGE_DIR / "builder.html").read_text(encoding="utf-8")
    return HTMLResponse(html_content)


# --------------------------------------------------------------------
# Editor JSON API
# --------------------------------------------------------------------

@builder_module.get("/api/block-types")
async def list_block_types() -> JSONResponse:
    return JSONResponse({
        "types": [
            {"type": key, "label": v["label"], "icon": v["icon"], "default_props": v["props"]}
            for key, v in BLOCK_TYPES.items()
        ]
    })


@builder_module.get("/api/pages")
async def list_pages() -> JSONResponse:
    return JSONResponse({
        "pages": [{"slug": slug, "title": p["title"]} for slug, p in _pages.items()]
    })


@builder_module.get("/api/pages/<slug>")
async def get_page(slug: str) -> JSONResponse:
    page = _pages.get(slug)
    if page is None:
        raise NotFound(f"No page '{slug}'.")
    return JSONResponse({"slug": slug, **page})


@builder_module.put("/api/pages/<slug>")
async def save_page(request: Request, slug: str) -> JSONResponse:
    data = await request.json() or {}
    raw_blocks = data.get("blocks")
    if not isinstance(raw_blocks, list):
        raise BadRequest("'blocks' must be a list.")

    validated = [_validate_block(b) for b in raw_blocks]
    title = str(data.get("title") or slug)

    _pages[slug] = {"title": title, "blocks": validated}
    return JSONResponse({"slug": slug, "title": title, "blocks": validated})


@builder_module.delete("/api/pages/<slug>")
async def delete_page(slug: str) -> JSONResponse:
    if slug not in _pages:
        raise NotFound(f"No page '{slug}'.")
    del _pages[slug]
    return JSONResponse({"deleted": True})


# --------------------------------------------------------------------
# Public rendered page
# --------------------------------------------------------------------

@builder_module.get("/p/<slug>")
async def render_page(slug: str) -> HTMLResponse:
    page = _pages.get(slug)
    if page is None:
        raise NotFound(f"No page '{slug}'.")

    body = render_blocks(page["blocks"])
    title = html.escape(page["title"])
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1f2937; }}
    img {{ border-radius: 8px; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
    return HTMLResponse(doc)