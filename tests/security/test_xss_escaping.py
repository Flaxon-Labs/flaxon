import pytest

from flaxon import Flaxon
from flaxon.jinax import Jinax
from flaxon.testing import TestClient


def test_jinax_autoescape(tmp_path):
    app = Flaxon("test-xss")
    (tmp_path / "test.html").write_text("{{ script }}", encoding="utf-8")

    jinax = Jinax(template_directory=tmp_path, auto_reload=True)
    app.use_templates(jinax)

    @app.get("/")
    async def home(request):
        return await request.render("test.html", {
            "script": "<script>alert('XSS')</script>",
        })

    client = TestClient(app)
    response = client.get("/")

    assert "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;" in response.text
    assert "<script>alert('XSS')</script>" not in response.text


def test_jinax_safe_filter(tmp_path):
    app = Flaxon("test-safe")
    (tmp_path / "test_safe.html").write_text("{{ safe_html }}{{ safe_html | safe }}{{ unsafe_html }}", encoding="utf-8")

    jinax = Jinax(template_directory=tmp_path, auto_reload=True)
    app.use_templates(jinax)

    @app.get("/")
    async def home(request):
        return await request.render("test_safe.html", {
            "safe_html": "<strong>Safe HTML</strong>",
            "unsafe_html": "<script>alert('XSS')</script>",
        })

    client = TestClient(app)
    response = client.get("/")

    assert "&lt;strong&gt;Safe HTML&lt;/strong&gt;" in response.text
    assert "<strong>Safe HTML</strong>" in response.text


def test_html_escape_function():
    from flaxon.jinax.escaping import Escaper

    assert Escaper.escape_html("<script>") == "&lt;script&gt;"
    assert Escaper.escape_html('"test"') == "&quot;test&quot;"
    assert Escaper.escape_html("&") == "&amp;"


def test_js_escape_function():
    from flaxon.jinax.escaping import Escaper

    assert Escaper.escape_js("test's") == "test\\'s"
    assert Escaper.escape_js('test"') == 'test\\"'
    assert Escaper.escape_js("test\n") == "test\\n"


def test_url_escape_function():
    from flaxon.jinax.escaping import Escaper

    escaped = Escaper.escape_url("hello world")
    assert "%20" in escaped
    assert Escaper.unescape_url(escaped) == "hello world"


def test_safe_string_escaping():
    from flaxon.jinax.escaping import SafeString, escape

    safe = SafeString("<strong>Safe</strong>")
    assert escape(safe, autoescape=True) == "<strong>Safe</strong>"

    unsafe = "<script>alert('XSS')</script>"
    assert escape(unsafe, autoescape=True) != unsafe


def test_xss_validation_schema():
    from flaxon.validation import Schema, fields

    class UserInput(Schema):
        name = fields.StrField(required=True, max_length=80)
        bio = fields.StrField(required=False, max_length=500)

    data = {
        "name": "User<script>alert('XSS')</script>",
        "bio": "Normal bio",
    }

    import re
    sanitized_name = re.sub(r"<[^>]*>", "", data["name"])

    assert "<script>" not in sanitized_name


def test_html_sanitization():
    from flaxon.security.sanitization import Sanitizer

    html = "<div><script>alert('XSS')</script><p>Hello</p></div>"
    sanitized = Sanitizer.strip_tags(html)
    assert "script" not in sanitized
    assert "alert" not in sanitized
    assert "Hello" in sanitized
