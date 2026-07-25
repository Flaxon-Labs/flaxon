from flaxon import Flaxon
from flaxon.testing import TestClient
from flaxon.validation import Schema, fields


class UserInput(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)


def test_schema_injection_success():
    app = Flaxon("test")

    @app.post("/users")
    async def create(data: UserInput):
        return data.to_dict()

    response = TestClient(app).post("/users", json_data={"name": "Aldane", "email": "a@example.com"})
    assert response.status_code == 200
    assert response.json()["name"] == "Aldane"


def test_schema_injection_error():
    app = Flaxon("test")

    @app.post("/users")
    async def create(data: UserInput):
        return data.to_dict()

    response = TestClient(app).post("/users", json_data={"name": "A", "email": "wrong"})
    payload = response.json()
    assert response.status_code == 422
    assert payload["error"]["code"] == "FX-VAL-001"
    assert "email" in payload["error"]["fields"]
