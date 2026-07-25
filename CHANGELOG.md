# Changelog

All notable changes to Flaxon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- ASGI application with HTTP, WebSocket, and lifespan support
- Flask-style route decorators with typed parameters
- Request validation with declarative schemas
- WebSocket support with room broadcasting
- Jinax template integration (optional Jinja2)
- Middleware: CORS, request ID, security headers, rate limiting
- CLI commands: run, routes, doctor, new
- Testing utilities: sync and async test clients
- Debugger with development/production modes
- Sensitive data redaction

## [0.1.0] - 2026-07-22

### Added
- Initial alpha release
- Core framework prototype
- Example applications: hello_api, jinax_site, react_backend, android_backend
- Comprehensive documentation

### Known Limitations
- WebSocket manager is in-memory only (single-process)
- Rate limiter is in-memory only (single-process)
- No OpenAPI generation yet
- No official plugin system yet
- No authentication/authorization modules yet