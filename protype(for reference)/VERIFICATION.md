# Prototype Verification

Verified on Python 3.13.5 in July 2026.

- `pytest`: 8 tests passed.
- CLI route inspection: 5 HTTP routes and 1 WebSocket route listed for the hello example.
- CLI doctor: application imported successfully; expected development warning for missing production secret.
- Live Uvicorn smoke test:
  - `GET /health` returned HTTP 200.
  - `POST /api/users` with a valid JSON body returned HTTP 200 and validated output.
  - Startup and shutdown lifecycle completed successfully.

The prototype is alpha software. Protocol hardening, security audit, broad load testing, and stable API guarantees remain future work.
