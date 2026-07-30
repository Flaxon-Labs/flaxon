
---

## docs/api/security.md

```markdown
# Security API

## JWTBackend

JWT authentication backend.

### Constructor

```python
JWTBackend(secret_key: str, algorithm: str = "HS256")

Methods
authenticate
python
async def authenticate(request: Request) -> User | None
Authenticate a request.

create_token
python
async def create_token(user: User, expires_in: int | None = None) -> str
Create a JWT token.

validate_token
python
async def validate_token(token: str) -> User | None
Validate a JWT token.

revoke_token
python
async def revoke_token(token: str) -> None
Revoke a token.

SessionBackend
Session authentication backend.

Constructor
python
SessionBackend(session_store: dict[str, dict[str, Any]] | None = None)
Methods
authenticate
python
async def authenticate(request: Request) -> User | None
Authenticate a request.

create_token
python
async def create_token(user: User, expires_in: int | None = None) -> str
Create a session token.

validate_token
python
async def validate_token(token: str) -> User | None
Validate a session token.

revoke_token
python
async def revoke_token(token: str) -> None
Revoke a session.

User
User object.

Constructor
python
User(id: str | int, username: str | None = None, email: str | None = None, roles: list[str] | None = None, permissions: list[str] | None = None, metadata: dict[str, Any] | None = None)
Methods
has_role
python
def has_role(role: str) -> bool
Check if user has a role.

has_permission
python
def has_permission(permission: str) -> bool
Check if user has a permission.

to_dict
python
def to_dict() -> dict[str, Any]
Convert to dictionary.

login_required
python
login_required(func: Callable) -> Callable
Decorator to require authentication.

permission_required
python
permission_required(permission: str) -> Callable
Decorator to require a permission.

role_required
python
role_required(role: str) -> Callable
Decorator to require a role.

authorize
python
authorize(permission: str | None = None, role: str | None = None) -> Callable
Decorator to require both permission and role.

CSRF
CSRF protection.

Constructor
python
CSRF(secret_key: str, cookie_name: str = "_csrf", header_name: str = "x-csrf-token")
Methods
generate_token
python
def generate_token() -> str
Generate a CSRF token.

verify_token
python
def verify_token(token: str) -> bool
Verify a CSRF token.

get_token_from_request
python
def get_token_from_request(request: Request) -> str | None
Get token from request.

validate_request
python
def validate_request(request: Request) -> None
Validate a request's CSRF token.

RateLimiter
Rate limiter.

Constructor
python
RateLimiter(requests: int = 60, window_seconds: int = 60, key_func: Callable[[dict[str, Any]], str] | None = None)
Methods
check
python
async def check(scope: dict[str, Any]) -> bool
Check if rate limit is exceeded.

get_remaining
python
def get_remaining(scope: dict[str, Any]) -> int
Get remaining requests.

get_retry_after
python
def get_retry_after(scope: dict[str, Any]) -> int
Get retry-after seconds.

APIKeyManager
API key management.

Methods
generate_key
python
def generate_key(prefix: str = "flx") -> tuple[str, str]
Generate a new API key.

register
python
def register(key: str, metadata: dict[str, Any] | None = None) -> None
Register an API key.

validate
python
def validate(key: str) -> dict[str, Any] | None
Validate an API key.

revoke
python
def revoke(key: str) -> None
Revoke an API key.

list_keys
python
def list_keys() -> list[dict[str, Any]]
List all API keys.

hash_password
python
hash_password(password: str) -> str
Hash a password.

verify_password
python
verify_password(password: str, hashed: str) -> bool
Verify a password against a hash.

needs_rehash
python
needs_rehash(hashed: str) -> bool
Check if a hash needs to be rehashed.


