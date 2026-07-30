
---

## docs/guides/validation.md

```markdown
# Validation

## Overview

Flaxon provides declarative validation schemas that automatically validate request data and inject validated objects into route handlers.

## Basic Schema

```python
from flaxon.validation import Schema, fields

class CreateUser(Schema):
    name = fields.String(required=True, min_length=2, max_length=80)
    email = fields.Email(required=True)
    age = fields.Integer(required=False, minimum=13, maximum=120)

    Using Schemas in Routes
python
@app.post("/users")
async def create_user(data: CreateUser):
    # data is automatically validated
    # Invalid data returns 422
    return {"success": True, "user": data.to_dict()}
Field Types
String
python
class UserSchema(Schema):
    name = fields.String(
        required=True,
        min_length=2,
        max_length=80,
        strip=True,
        pattern=r"^[a-zA-Z\s]+$",
    )
Integer
python
class ProductSchema(Schema):
    price = fields.Integer(
        required=True,
        minimum=0,
        maximum=999999,
    )
Float
python
class PriceSchema(Schema):
    amount = fields.Float(
        required=True,
        minimum=0.0,
        maximum=9999.99,
    )
Boolean
python
class SettingsSchema(Schema):
    active = fields.Boolean(required=True)
    notifications = fields.Boolean(default=True)
Choice
python
class StatusSchema(Schema):
    status = fields.Choice(
        ["pending", "active", "suspended", "deleted"],
        required=True,
    )
Email
python
class ContactSchema(Schema):
    email = fields.Email(required=True)
Date
python
class EventSchema(Schema):
    date = fields.Date(required=True, format="%Y-%m-%d")
DateTime
python
class ScheduleSchema(Schema):
    datetime = fields.DateTime(required=True, format="%Y-%m-%dT%H:%M:%S")
UUID
python
class TokenSchema(Schema):
    token = fields.UUID(required=True)
List
python
class BulkCreateSchema(Schema):
    users = fields.List(
        item_field=fields.String(min_length=2),
        min_items=1,
        max_items=100,
    )
Nested
python
class AddressSchema(Schema):
    street = fields.String(required=True)
    city = fields.String(required=True)
    zipcode = fields.String(required=True, pattern=r"^\d{5}$")

class UserSchema(Schema):
    name = fields.String(required=True)
    address = fields.Nested(AddressSchema)
Validation Errors
python
@app.post("/users")
async def create_user(data: CreateUser):
    # If validation fails, Flaxon automatically returns:
    # {
    #   "success": false,
    #   "error": {
    #     "code": "FX-VAL-001",
    #     "message": "Request validation failed.",
    #     "fields": {
    #       "email": ["Enter a valid email address."],
    #       "age": ["Must be at least 13."]
    #     }
    #   }
    # }
    return {"user": data.to_dict()}
Custom Validators
python
from flaxon.validation.validators import Validator, custom_validator

def validate_unique_email(value, field):
    # Check if email already exists in database
    if email_exists(value):
        raise ValueError("Email already registered")

class CreateUser(Schema):
    email = fields.Email(
        required=True,
        validators=[custom_validator(validate_unique_email)],
    )
Combining Validators
python
from flaxon.validation.validators import and_validators, or_validators

class UserSchema(Schema):
    # Must meet all conditions
    username = fields.String(
        validators=[and_validators(
            length_validator(3, 20),
            pattern_validator(r"^[a-zA-Z0-9_]+$"),
        )],
    )

    # Must meet at least one condition
    contact = fields.String(
        validators=[or_validators(
            email_validator(),
            pattern_validator(r"^\+\d{10,15}$"),
        )],
    )
Serialization
python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    return user  # Automatically serialized

# Custom serialization
class UserSchema(Schema):
    name = fields.String()
    email = fields.Email()

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "display_name": self.name.upper(),
        }
Full Example
python
from flaxon import Flaxon
from flaxon.validation import Schema, fields
from flaxon.validation.validators import custom_validator

app = Flaxon("validation-demo")

def validate_unique_username(value, field):
    # Simulate database check
    if value == "admin":
        raise ValueError("Username 'admin' is already taken")

class CreateUser(Schema):
    username = fields.String(
        required=True,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        validators=[custom_validator(validate_unique_username)],
    )
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        min_length=8,
        max_length=128,
    )
    age = fields.Integer(required=False, minimum=13, maximum=120)
    role = fields.Choice(
        ["user", "moderator", "admin"],
        default="user",
    )

class UpdateUser(Schema):
    username = fields.String(min_length=3, max_length=30)
    email = fields.Email()
    age = fields.Integer(minimum=13, maximum=120)

@app.post("/users")
async def create_user(data: CreateUser):
    # Password should be hashed before storing
    return {"success": True, "user": data.to_dict()}

@app.patch("/users/<int:user_id>")
async def update_user(user_id: int, data: UpdateUser):
    # Only provided fields are validated
    return {"updated": True, "id": user_id, "data": data.to_dict()}