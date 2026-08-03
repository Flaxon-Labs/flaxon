
# Validation

## Overview

Flaxon provides declarative validation schemas that automatically validate request data and inject validated objects into route handlers.

Validation supports:

- Type checking
- Required fields
- Length validation
- Range validation
- Custom validators
- Nested schemas
- Serialization
- Automatic error responses

---

# Basic Schema

```python
from flaxon.validation import Schema, fields


class CreateUser(Schema):

    name = fields.String(
        required=True,
        min_length=2,
        max_length=80
    )

    email = fields.Email(
        required=True
    )

    age = fields.Integer(
        required=False,
        minimum=13,
        maximum=120
    )
````

---

# Using Schemas in Routes

```python
@app.post("/users")
async def create_user(data: CreateUser):

    # Data is automatically validated

    return {
        "success": True,
        "user": data.to_dict()
    }
```

Invalid data automatically returns:

```json
{
    "error": {
        "code": "FX-VAL-001",
        "message": "Validation failed"
    }
}
```

---

# Field Types

## String

```python
class UserSchema(Schema):

    name = fields.String(
        required=True,
        min_length=2,
        max_length=80,
        strip=True,
        pattern=r"^[a-zA-Z\s]+$"
    )
```

---

## Integer

```python
class ProductSchema(Schema):

    price = fields.Integer(
        required=True,
        minimum=0,
        maximum=999999
    )
```

---

## Float

```python
class PriceSchema(Schema):

    amount = fields.Float(
        required=True,
        minimum=0.0,
        maximum=9999.99
    )
```

---

## Boolean

```python
class SettingsSchema(Schema):

    active = fields.Boolean(
        required=True
    )

    notifications = fields.Boolean(
        default=True
    )
```

---

## Choice

```python
class StatusSchema(Schema):

    status = fields.Choice(
        [
            "pending",
            "active",
            "suspended",
            "deleted"
        ],
        required=True
    )
```

---

## Email

```python
class ContactSchema(Schema):

    email = fields.Email(
        required=True
    )
```

---

## Date

```python
class EventSchema(Schema):

    date = fields.Date(
        required=True,
        format="%Y-%m-%d"
    )
```

---

## DateTime

```python
class ScheduleSchema(Schema):

    datetime = fields.DateTime(
        required=True,
        format="%Y-%m-%dT%H:%M:%S"
    )
```

---

## UUID

```python
class TokenSchema(Schema):

    token = fields.UUID(
        required=True
    )
```

---

## List

```python
class BulkCreateSchema(Schema):

    users = fields.List(
        item_field=fields.String(
            min_length=2
        ),
        min_items=1,
        max_items=100
    )
```

---

## Nested Schemas

```python
class AddressSchema(Schema):

    street = fields.String(
        required=True
    )

    city = fields.String(
        required=True
    )

    zipcode = fields.String(
        required=True,
        pattern=r"^\d{5}$"
    )



class UserSchema(Schema):

    name = fields.String(
        required=True
    )

    address = fields.Nested(
        AddressSchema
    )
```

---

# Validation Errors

```python
@app.post("/users")
async def create_user(data: CreateUser):

    return {
        "user": data.to_dict()
    }
```

If validation fails:

```json
{
    "success": false,
    "error": {
        "code": "FX-VAL-001",
        "message": "Request validation failed.",
        "fields": {
            "email": [
                "Enter a valid email address."
            ],
            "age": [
                "Must be at least 13."
            ]
        }
    }
}
```

---

# Custom Validators

```python
from flaxon.validation.validators import custom_validator


def validate_unique_email(value, field):

    if email_exists(value):

        raise ValueError(
            "Email already registered"
        )


class CreateUser(Schema):

    email = fields.Email(
        required=True,
        validators=[
            custom_validator(
                validate_unique_email
            )
        ]
    )
```

---

# Combining Validators

```python
from flaxon.validation.validators import (
    and_validators,
    or_validators,
)



class UserSchema(Schema):

    username = fields.String(
        validators=[
            and_validators(
                length_validator(3, 20),
                pattern_validator(
                    r"^[a-zA-Z0-9_]+$"
                )
            )
        ]
    )


    contact = fields.String(
        validators=[
            or_validators(
                email_validator(),
                pattern_validator(
                    r"^\+\d{10,15}$"
                )
            )
        ]
    )
```

---

# Serialization

Objects returned from routes are automatically serialized.

```python
@app.get("/users/<int:user_id>")
async def get_user(user_id: int):

    user = await db.fetch_one(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )

    return user
```

---

## Custom Serialization

```python
class UserSchema(Schema):

    name = fields.String()

    email = fields.Email()


    def to_dict(self):

        return {
            "name": self.name,
            "email": self.email,
            "display_name": self.name.upper()
        }
```

---

# Full Example

```python
from flaxon import Flaxon

from flaxon.validation import (
    Schema,
    fields
)

from flaxon.validation.validators import (
    custom_validator
)



app = Flaxon(
    "validation-demo"
)



def validate_unique_username(value, field):

    if value == "admin":

        raise ValueError(
            "Username already exists"
        )



class CreateUser(Schema):

    username = fields.String(
        required=True,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        validators=[
            custom_validator(
                validate_unique_username
            )
        ]
    )


    email = fields.Email(
        required=True
    )


    password = fields.String(
        required=True,
        min_length=8,
        max_length=128
    )


    age = fields.Integer(
        required=False,
        minimum=13,
        maximum=120
    )


    role = fields.Choice(
        [
            "user",
            "moderator",
            "admin"
        ],
        default="user"
    )



class UpdateUser(Schema):

    username = fields.String(
        min_length=3,
        max_length=30
    )


    email = fields.Email()


    age = fields.Integer(
        minimum=13,
        maximum=120
    )



@app.post("/users")
async def create_user(data: CreateUser):

    # Hash password before saving

    return {
        "success": True,
        "user": data.to_dict()
    }



@app.patch("/users/<int:user_id>")
async def update_user(
    user_id: int,
    data: UpdateUser
):

    return {
        "updated": True,
        "id": user_id,
        "data": data.to_dict()
    }
```

---

# Validation Best Practices

* Validate all incoming data.
* Never trust client input.
* Use schemas for API requests.
* Keep validation separate from business logic.
* Create reusable validators.
* Return meaningful validation errors.
* Validate file uploads.
* Validate authentication payloads.
* Use nested schemas for complex objects.

---

# Next Steps

Continue with:

* Authentication
* Authorization
* Serialization
* Error Handling
* Database Integration
* API Development


