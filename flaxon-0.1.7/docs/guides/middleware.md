
---

## docs/guides/middleware.md

```markdown
# Middleware

## Overview

Middleware wraps your ASGI application and can process requests before they reach your route handlers and responses before they are sent to the client.

## Adding Middleware

```python
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware

app = Flaxon("my-app")

# Add middleware
app.add_middleware(RequestIDMiddleware, header_name="x-request-id")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["https://example.com"],
    allow_credentials=True,
)

Built-in Middleware
RequestIDMiddleware
Adds a unique request ID to each request and response.

python
from flaxon.middleware import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware, header_name="x-request-id")
SecurityHeadersMiddleware
Adds security headers to all responses.

python
from flaxon.middleware import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    hsts=True,
    csp="default-src 'self'",
)
CORSMiddleware
Handles Cross-Origin Resource Sharing.

python
from flaxon.middleware import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["https://example.com"],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
    allow_credentials=True,
)
CompressionMiddleware
Compresses responses using gzip, deflate, or brotli.

python
from flaxon.middleware import CompressionMiddleware

app.add_middleware(
    CompressionMiddleware,
    minimum_size=1024,
    level=6,
)
RateLimitMiddleware
Limits the number of requests per client.

python
from flaxon.security import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests=60,
    window_seconds=60,
)
BodyLimitMiddleware
Limits the size of request bodies.

python
from flaxon.middleware import BodyLimitMiddleware

app.add_middleware(
    BodyLimitMiddleware,
    max_size=5 * 1024 * 1024,
)
TimeoutMiddleware
Sets a timeout for request processing.

python
from flaxon.middleware import TimeoutMiddleware

app.add_middleware(
    TimeoutMiddleware,
    timeout=30,
)
TrustedHostsMiddleware
Validates the Host header against allowed hosts.

python
from flaxon.middleware import TrustedHostsMiddleware

app.add_middleware(
    TrustedHostsMiddleware,
    allowed_hosts=["example.com", "api.example.com"],
)
LoggingMiddleware
Logs requests and responses.

python
from flaxon.middleware import LoggingMiddleware

app.add_middleware(
    LoggingMiddleware,
    log_headers=True,
    log_body=False,
)
RecoveryMiddleware
Catches exceptions and returns safe error responses.

python
from flaxon.middleware import RecoveryMiddleware

app.add_middleware(
    RecoveryMiddleware,
    debug=False,
)
Custom Middleware
python
from flaxon.middleware import Middleware

class CustomMiddleware(Middleware):
    def __init__(self, app, header_name="x-custom"):
        super().__init__(app)
        self.header_name = header_name

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Pre-processing
        scope["custom_value"] = "processed"

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode(), b"custom-value"))
                message["headers"] = headers
            await send(message)

        # Post-processing
        await self.app(scope, receive, send_wrapper)
Middleware Order
Middleware is executed in the order it is added (first added = outermost).

python
app.add_middleware(RequestIDMiddleware)      # Executed first (outermost)
app.add_middleware(SecurityHeadersMiddleware) # Executed second
app.add_middleware(CORSMiddleware)            # Executed third
app.add_middleware(CustomMiddleware)          # Executed last (innermost)
Request Flow
text
Request → RequestIDMiddleware → SecurityHeadersMiddleware → CORSMiddleware → CustomMiddleware → App
Response ← RequestIDMiddleware ← SecurityHeadersMiddleware ← CORSMiddleware ← CustomMiddleware ← App
Conditional Middleware
python
class ConditionalMiddleware(Middleware):
    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")

        if path.startswith("/api"):
            await self.app(scope, receive, send)
        else:
            # Skip middleware for non-API paths
            await self.app(scope, receive, send)
Full Example
python
from flaxon import Flaxon
from flaxon.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    CORSMiddleware,
    BodyLimitMiddleware,
    TimeoutMiddleware,
    LoggingMiddleware,
    RecoveryMiddleware,
)
from flaxon.security import RateLimitMiddleware

app = Flaxon("middleware-demo")

# Add middleware in order
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware, hsts=True)
app.add_middleware(RecoveryMiddleware, debug=False)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["https://example.com"],
)
app.add_middleware(
    RateLimitMiddleware,
    requests=60,
    window_seconds=60,
)
app.add_middleware(BodyLimitMiddleware, max_size=10 * 1024 * 1024)
app.add_middleware(TimeoutMiddleware, timeout=30)

@app.get("/")
async def home():
    return {"message": "Hello"}