
---

## docs/configuration.md

```markdown
# Configuration

## Overview

Flaxon uses a configuration system that loads from defaults, dictionaries, and environment variables.

## Configuration Sources

1. **Defaults** — Built-in default values
2. **Dictionary** — Values passed to `Flaxon()` or `Config()`
3. **Environment Variables** — Prefixed with `FLAXON_`

## Default Configuration

```python
DEFAULTS = {
    "ENV": "development",
    "DEBUG": False,
    "SECRET_KEY": None,
    "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
    "MAX_BODY_SIZE": 10 * 1024 * 1024,
    "TRUSTED_PROXIES": [],
    "PROXY_HEADERS": ["x-forwarded-for", "x-forwarded-proto", "x-forwarded-host"],
}

Setting Configuration
Through Code
python
from flaxon import Flaxon

app = Flaxon(
    "my-app",
    debug=True,
    config={
        "ENV": "production",
        "MAX_BODY_SIZE": 5 * 1024 * 1024,
    }
)
Through Environment Variables
bash
export FLAXON_ENV=production
export FLAXON_DEBUG=false
export FLAXON_SECRET_KEY=your-secret-key
Using .env File
bash
# .env
FLAXON_ENV=production
FLAXON_DEBUG=false
FLAXON_SECRET_KEY=your-secret-key
Configuration Methods
python
# Access configuration
app.config.DEBUG
app.config["DEBUG"]
app.config.get("DEBUG")

# Get environment
app.config.get_env()  # "development" | "testing" | "staging" | "production"

# Check environment
app.config.is_development()
app.config.is_production()

# Get values
app.config.get_secret_key()
app.config.get_allowed_hosts()
app.config.get_max_body_size()
Production Configuration
bash
FLAXON_ENV=production
FLAXON_DEBUG=false
FLAXON_SECRET_KEY=<32+ random hex bytes>
FLAXON_ALLOWED_HOSTS=api.example.com,example.com
FLAXON_MAX_BODY_SIZE=10485760
Security Recommendations
Setting	Recommendation
DEBUG	Always false in production
SECRET_KEY	32+ random bytes, stored outside source control
ALLOWED_HOSTS	Explicit domains, not wildcards
MAX_BODY_SIZE	Set according to upload requirements