# Roadmap

Flaxon's development roadmap and milestone planning.

## Version 0.1.0 — Core Prototype ✅

**Released:** July 2026

- ASGI application with HTTP, WebSocket, lifespan
- Flask-style decorators with typed parameters
- Request validation with declarative schemas
- WebSocket support with room broadcasting
- Jinax template integration (optional Jinja2)
- Middleware: CORS, request ID, security headers, rate limiting
- CLI: run, routes, doctor, new
- Testing: sync and async test clients
- Debugger with development/production modes
- Sensitive data redaction

## Version 0.2.0 — Protocol Hardening

**Target:** Q3 2026

- [ ] ASGI protocol conformance tests
- [ ] HTTP/1.1 and HTTP/2 improvements
- [ ] Multipart/form-data uploads
- [ ] Streaming request body handling
- [ ] WebSocket disconnect and backpressure handling
- [ ] Graceful shutdown improvements
- [ ] Request and response timeouts
- [ ] Trusted host middleware
- [ ] Body size limit middleware
- [ ] Improved middleware error recovery

## Version 0.3.0 — Production Services

**Target:** Q4 2026

- [ ] Session management (signed cookies + backends)
- [ ] OpenAPI/Swagger documentation generation
- [ ] Structured logging (JSON logs with request context)
- [ ] Health check endpoints (liveness, readiness)
- [ ] Prometheus metrics integration
- [ ] Better configuration management (settings classes)
- [ ] Environment-specific configuration
- [ ] .env file support
- [ ] Email sending (SMTP, console)
- [ ] Static file serving

## Version 0.4.0 — Plugins and Ecosystem

**Target:** Q1 2027

- [ ] Formal plugin system with discovery
- [ ] flaxon-sqlalchemy: SQLAlchemy integration
- [ ] flaxon-redis: Redis caching and rate limiting
- [ ] flaxon-auth: Authentication (JWT, OAuth, sessions)
- [ ] flaxon-storage: File storage (local, S3)
- [ ] flaxon-observability: OpenTelemetry integration
- [ ] flaxon-tasks: Background task queue
- [ ] Plugin hooks for: startup, shutdown, routes, CLI commands, health checks

## Version 0.5.0 — Distributed Systems

**Target:** Q2 2027

- [ ] Distributed task queues (Redis, RabbitMQ)
- [ ] Scheduled tasks and cron jobs
- [ ] Redis-backed WebSocket broadcaster
- [ ] Distributed rate limiting
- [ ] Distributed caching
- [ ] Database connection pooling
- [ ] Transaction management
- [ ] Migration tooling
- [ ] Deployment guides (Docker, Kubernetes)

## Version 0.9.0 — Release Candidate

**Target:** Q3 2027

- [ ] API freeze
- [ ] Security audit
- [ ] Performance benchmarks
- [ ] Migration guide from 0.x
- [ ] Broad CI and compatibility testing
- [ ] Documentation complete
- [ ] Example applications comprehensive

## Version 1.0.0 — Stable Release

**Target:** Q4 2027

- [ ] Documented compatibility policy
- [ ] Signed releases
- [ ] Governance model
- [ ] Long-term support (LTS) policy
- [ ] Production-ready certification

## Future Ideas

### Version 1.1+

- GraphQL support
- gRPC support
- Server-Sent Events (SSE)
- WebSockets over HTTP/3 (QUIC)
- Real-time collaboration features
- Admin dashboard
- Code generation from OpenAPI
- Database migration tools
- More database adapters
- More cloud service integrations

## Contribution Wanted!

We welcome contributions at any stage. Check our [Contributing Guide](CONTRIBUTING.md) to get started.

---

**Help us shape the future of Python backend development.** 🚀