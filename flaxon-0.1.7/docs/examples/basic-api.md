# Basic API Example

This example demonstrates a simple REST API with Flaxon.

## Application Code

```python
# app.py
from flaxon import Flaxon
from flaxon.validation import Schema, fields

app = Flaxon("basic-api", debug=True)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "basic-api"}

# Home endpoint
@app.get("/")
async def home():
    return {
        "message": "Welcome to the Basic API",
        "endpoints": [
            "GET /health",
            "GET /users",
            "GET /users/<id>",
            "POST /users",
            "PUT /users/<id>",
            "DELETE /users/<id>",
        ],
    }

# Schema for user creation
class CreateUser(Schema):
    name = fields.String(required=True, min_length=2, max_length=80)
    email = fields.Email(required=True)
    age = fields.IntField(required=False, minimum=13, maximum=120)

# Schema for user update
class UpdateUser(Schema):
    name = fields.String(required=False, min_length=2, max_length=80)
    email = fields.Email(required=False)
    age = fields.IntField(required=False, minimum=13, maximum=120)

# In-memory storage
users = []
user_id_counter = 1

@app.get("/users")
async def list_users():
    return users

@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}, 404

@app.post("/users")
async def create_user(data: CreateUser):
    global user_id_counter
    user = data.to_dict()
    user["id"] = user_id_counter
    user_id_counter += 1
    users.append(user)
    return {"created": True, "user": user}, 201

@app.put("/users/<int:user_id>")
async def update_user(user_id: int, data: UpdateUser):
    for user in users:
        if user["id"] == user_id:
            user.update(data.to_dict())
            return {"updated": True, "user": user}
    return {"error": "User not found"}, 404

@app.delete("/users/<int:user_id>")
async def delete_user(user_id: int):
    for i, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(i)
            return {"deleted": True, "id": user_id}
    return {"error": "User not found"}, 404


    Running the Application
bash
# Install dependencies
pip install flaxon[standard]

# Run the application
flaxon run app:app --reload
Testing the API
Create a User
bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "age": 30}'
List All Users
bash
curl http://localhost:8000/users
Get a User
bash
curl http://localhost:8000/users/1
Update a User
bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated"}'
Delete a User
bash
curl -X DELETE http://localhost:8000/users/1
Health Check
bash
curl http://localhost:8000/health