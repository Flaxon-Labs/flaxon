# Validation API

## Schema

Base schema class for data validation.

### Constructor

```python
class Schema(metaclass=SchemaMeta):
    __fields__: dict[str, Field]

    Class Methods
load
python
@classmethod
def load(cls, data: Any) -> Schema
Load and validate data from a dictionary.

Parameter	Type	Description
data	Any	Data to validate (must be a dict)
Raises: ValidationError if validation fails

Returns: Schema instance with validated data

python
user = CreateUser.load({"name": "Alice", "email": "alice@example.com"})
Methods
to_dict
python
def to_dict(self) -> dict[str, Any]
Convert schema to a dictionary.

python
data = user.to_dict()
# {"name": "Alice", "email": "alice@example.com"}
to_json
python
def to_json(self) -> dict[str, Any]
Convert schema to a JSON-serializable dictionary.

python
json_data = user.to_json()
validate
python
def validate(self) -> None
Validate the schema data manually.

Raises: ValidationError if validation fails

Fields
StrField
String field with validation options.

python
StrField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    min_length: int | None = None,
    max_length: int | None = None,
    strip: bool = True,
    pattern: str | None = None,
)
Parameter	Type	Description
required	bool	Field must be present
default	Any	Default value if not provided
nullable	bool	Allow null values
min_length	int | None	Minimum string length
max_length	int | None	Maximum string length
strip	bool	Strip whitespace
pattern	str | None	Regex pattern to match
python
name = fields.String(required=True, min_length=2, max_length=80)
IntField
Integer field with range validation.

python
IntField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    minimum: int | None = None,
    maximum: int | None = None,
)
Parameter	Type	Description
minimum	int | None	Minimum allowed value
maximum	int | None	Maximum allowed value
python
age = fields.IntField(minimum=13, maximum=120)
FloatField
Float field with range validation.

python
FloatField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    minimum: float | None = None,
    maximum: float | None = None,
)
python
price = fields.FloatField(minimum=0.0, maximum=9999.99)
BoolField
Boolean field.

python
BoolField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
)
python
active = fields.BoolField(default=True)
ChoiceField
Choice field with allowed values.

python
ChoiceField(
    choices: list[Any] | tuple[Any, ...] | set[Any],
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
)
Parameter	Type	Description
choices	list | tuple | set	Allowed choices
python
status = fields.ChoiceField(["pending", "active", "deleted"], default="pending")
EmailField
Email field with email validation.

python
EmailField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    min_length: int | None = None,
    max_length: int | None = None,
)
python
email = fields.EmailField(required=True)
DateField
Date field with format validation.

python
DateField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    format: str = "%Y-%m-%d",
)
Parameter	Type	Description
format	str	Date format string
python
birthday = fields.DateField(format="%Y-%m-%d")
DateTimeField
DateTime field with format validation.

python
DateTimeField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    format: str = "%Y-%m-%dT%H:%M:%S",
)
python
created_at = fields.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
DecimalField
Decimal field with precision validation.

python
DecimalField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
    places: int | None = None,
)
Parameter	Type	Description
places	int | None	Maximum decimal places
python
amount = fields.DecimalField(minimum=0, places=2)
UUIDField
UUID field with UUID validation.

python
UUIDField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
)
python
token = fields.UUIDField(required=True)
ListField
List field with item validation.

python
ListField(
    item_field: Field | None = None,
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
    min_items: int | None = None,
    max_items: int | None = None,
)
Parameter	Type	Description
item_field	Field | None	Field for each item
min_items	int | None	Minimum number of items
max_items	int | None	Maximum number of items
python
tags = fields.ListField(fields.String(min_length=1), min_items=1, max_items=10)
NestedField
Nested schema field.

python
NestedField(
    schema_class: type[Schema],
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
)
Parameter	Type	Description
schema_class	type[Schema]	Nested schema class
python
class AddressSchema(Schema):
    street = fields.String(required=True)
    city = fields.String(required=True)

class UserSchema(Schema):
    name = fields.String(required=True)
    address = fields.NestedField(AddressSchema)
AnyField
Field that accepts any value.

python
AnyField(
    *,
    required: bool = False,
    default: Any = None,
    nullable: bool = False,
)
python
metadata = fields.AnyField()
Validators
required_validator
python
required_validator(value: Any, field: Any, message: str | None = None) -> None
Validates that a value is not None.

length_validator
python
length_validator(min_length: int | None = None, max_length: int | None = None) -> Validator
Creates a validator for string/list length.

python
validator = length_validator(min_length=3, max_length=20)
min_validator
python
min_validator(min_value: Any) -> Validator
Creates a validator for minimum value.

python
validator = min_validator(0)
max_validator
python
max_validator(max_value: Any) -> Validator
Creates a validator for maximum value.

python
validator = max_validator(100)
range_validator
python
range_validator(min_value: Any, max_value: Any) -> Validator
Creates a validator for range.

python
validator = range_validator(13, 120)
email_validator
python
email_validator() -> Validator
Creates a validator for email format.

python
validator = email_validator()
url_validator
python
url_validator() -> Validator
Creates a validator for URL format.

python
validator = url_validator()
pattern_validator
python
pattern_validator(pattern: str) -> Validator
Creates a validator for regex pattern.

python
validator = pattern_validator(r"^[a-zA-Z0-9_]+$")
and_validators
python
and_validators(*validators: Validator) -> Validator
Combines multiple validators with AND logic.

python
validator = and_validators(
    length_validator(3, 20),
    pattern_validator(r"^[a-zA-Z0-9_]+$"),
)
or_validators
python
or_validators(*validators: Validator) -> Validator
Combines multiple validators with OR logic.

python
validator = or_validators(
    email_validator(),
    pattern_validator(r"^\+\d{10,15}$"),
)
custom_validator
python
custom_validator(func: Callable[[Any, Any], None]) -> Validator
Creates a custom validator from a function.

python
def validate_unique(value, field):
    if value_exists(value):
        raise FieldError("Value already exists")

validator = custom_validator(validate_unique)
Exceptions
ValidationError
Raised when validation fails.

python
ValidationError(fields: dict[str, list[str]])
Attribute	Type	Description
fields	dict[str, list[str]]	Field error messages
python
try:
    user = CreateUser.load(data)
except ValidationError as exc:
    print(exc.fields)
    # {"email": ["Enter a valid email address."]}
FieldError
Raised when a field validation fails.

python
FieldError(message: str)
Attribute	Type	Description
message	str	Error message
Complete Example
python
from flaxon.validation import Schema, fields
from flaxon.validation.validators import custom_validator, and_validators, pattern_validator

# Custom validator
def validate_unique_email(value, field):
    if value == "admin@example.com":
        raise FieldError("Email already registered")

# Define schema
class CreateUser(Schema):
    username = fields.String(
        required=True,
        min_length=3,
        max_length=30,
        validators=[
            and_validators(
                pattern_validator(r"^[a-zA-Z0-9_]+$"),
            )
        ],
    )
    email = fields.Email(
        required=True,
        validators=[custom_validator(validate_unique_email)],
    )
    password = fields.String(
        required=True,
        min_length=8,
        max_length=128,
    )
    age = fields.IntField(
        required=False,
        minimum=13,
        maximum=120,
    )
    role = fields.ChoiceField(
        ["user", "moderator", "admin"],
        default="user",
    )
    tags = fields.ListField(
        fields.String(min_length=1),
        max_items=10,
    )

# Use schema
@app.post("/users")
async def create_user(data: CreateUser):
    # Data is automatically validated
    # Invalid data returns 422 with field errors
    return {"user": data.to_dict()}