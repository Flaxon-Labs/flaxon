
---

## docs/security.md

```markdown
# Security

## Overview

Security is integrated into Flaxon's defaults and documentation. The framework establishes autoescaped templates, structured validation, security headers, request identifiers, redaction, safe production errors, and basic rate limiting.

## Built-in Security Features

### Autoescaping

Jinax templates autoescape HTML and XML content, preventing XSS attacks.

### Request Validation

Declarative schemas validate request data before processing:

```python
class CreateUser(Schema):
    name = fields.String(required=True, min_length=2)
    email = fields.Email(required=True)

    Security Headers
Flaxon adds these security headers by default:

X-Content-Type-Options: nosniff

X-Frame-Options: DENY

Referrer-Policy: strict-origin-when-cross-origin

Permissions-Policy: geolocation=(), microphone=(), camera=()

Request IDs
Every request gets a unique ID for tracing and debugging.

Redaction
Sensitive data is redacted in debug output:

passwords, secrets, tokens

authorization headers

API keys, private keys

credit card information

Production-Safe Errors
In production, errors return safe responses without traceback information.

Rate Limiting
Prevents abuse through configurable rate limits.

Security Recommendations
Production Checklist
□ Set FLAXON_DEBUG=false
□ Set FLAXON_SECRET_KEY (32+ random bytes)
□ Set FLAXON_ALLOWED_HOSTS to your domains
□ Use HTTPS
□ Use secure cookies (Secure, HttpOnly, SameSite)
□ Implement authentication and authorization
□ Use rate limiting
□ Validate all user input
□ Use parameterized database queries
□ Keep dependencies updated
Authentication
python
from flaxon.security import JWTBackend, login_required

app = Flaxon("secure-app")
backend = JWTBackend(secret_key="your-secret")

@app.post("/login")
async def login(request):
    # Validate credentials
    user = await authenticate_user(data)
    token = await backend.create_token(user)
    return {"token": token}

@app.get("/protected")
@login_required
async def protected(request):
    user = getattr(request, "user", None)
    return {"user": user.to_dict()}
CSRF Protection
python
from flaxon.security import CSRFMiddleware

app.add_middleware(CSRFMiddleware, secret_key="your-secret")
CORS Configuration
python
from flaxon.middleware import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["https://example.com"],
    allow_credentials=True,
)
Rate Limiting
python
from flaxon.security import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, requests=60, window_seconds=60)
Threat Mitigation
Threat	Control
XSS	Jinja2 autoescape, CSP
SQL Injection	Parameterized queries, validation
Credential Theft	Secure password hashing, MFA
Token Abuse	Short tokens, refresh rotation
CSRF	CSRF tokens
DDoS	Rate limiting, timeouts
Data Leakage	Redaction, safe errors
Supply Chain	Pinned dependencies, scanning
Reporting Vulnerabilities
If you discover a security vulnerability, please email aldanehutchinson5@gmail.com or open a private security advisory on GitHub.