from __future__ import annotations

from examples.graphql_github_clone.app import app
from flaxon.testing import TestClient


def test_github_clone_example_api_and_playgrounds():
    client = TestClient(app)

    home = client.get("/")
    assert home.status_code == 200
    assert "flaxon forge" in home.text
    assert "/static/css/app.css" in home.text
    assert "/static/js/app.js" in home.text

    css = client.get("/static/css/app.css")
    javascript = client.get("/static/js/app.js")
    assert css.status_code == 200 and "repo-grid" in css.text
    assert javascript.status_code == 200 and "graphql" in javascript.text.lower()

    query = client.post(
        "/graphql",
        json_data={
            "query": "{ viewer { login } repositories(search: \"flaxon\") { name stars owner { login } } }"
        },
    )
    assert query.status_code == 200
    assert query.json()["data"]["viewer"] == {"login": "ada"}
    assert query.json()["data"]["repositories"][0]["owner"] == {"login": "ada"}

    mutation = client.post(
        "/graphql",
        json_data={
            "query": "mutation { createRepository(name: \"demo\", description: \"Example\") { name stars } }"
        },
    )
    assert mutation.json()["data"]["createRepository"] == {"name": "demo", "stars": 0}

    assert client.get("/graphql/graphiql").status_code == 200
    assert client.get("/graphql/altair").status_code == 200
    assert client.get("/graphql").status_code == 200
