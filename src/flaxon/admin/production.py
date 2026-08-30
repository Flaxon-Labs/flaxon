"""Durable services used by the Admin production integration.

The services deliberately depend on the small AdminStore contract so projects
can replace it with their own database-backed repository.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from inspect import isawaitable
from typing import Any, Callable


@dataclass
class DurableJob:
    id: str
    name: str
    payload: dict[str, Any]
    status: str = "queued"
    attempts: int = 0
    max_attempts: int = 3
    error: str | None = None
    run_after: float = 0.0
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class DurableJobStore:
    """Persistent job queue with retry history and idempotent completion."""

    def __init__(self, store: Any, namespace: str = "admin_jobs") -> None:
        self.store = store
        self.namespace = namespace

    def _save(self, jobs: dict[str, Any]) -> None:
        self.store.set(self.namespace, "jobs", jobs)

    def list(self) -> list[DurableJob]:
        return [DurableJob(**item) for item in (self.store.get(self.namespace, "jobs", {}) or {}).values()]

    def enqueue(self, name: str, payload: dict[str, Any], *, max_attempts: int = 3, run_after: float = 0.0, job_id: str | None = None) -> DurableJob:
        jobs = self.store.get(self.namespace, "jobs", {}) or {}
        now = time.time()
        job = DurableJob(job_id or secrets.token_urlsafe(16), name, payload, max_attempts=max(1, max_attempts), run_after=run_after, created_at=now, updated_at=now)
        jobs[job.id] = job.to_dict()
        self._save(jobs)
        return job

    def claim_due(self, limit: int = 10) -> list[DurableJob]:
        jobs = self.store.get(self.namespace, "jobs", {}) or {}
        now = time.time()
        claimed: list[DurableJob] = []
        for raw in jobs.values():
            if len(claimed) >= limit:
                break
            if raw.get("status") == "queued" and raw.get("run_after", 0) <= now:
                raw["status"] = "running"
                raw["attempts"] = int(raw.get("attempts", 0)) + 1
                raw["updated_at"] = now
                claimed.append(DurableJob(**raw))
        self._save(jobs)
        return claimed

    def complete(self, job_id: str) -> None:
        jobs = self.store.get(self.namespace, "jobs", {}) or {}
        if job_id in jobs:
            jobs[job_id].update(status="completed", updated_at=time.time())
            self._save(jobs)

    def fail(self, job_id: str, error: str, retry_delay: float = 5.0) -> None:
        jobs = self.store.get(self.namespace, "jobs", {}) or {}
        raw = jobs.get(job_id)
        if raw is None:
            return
        if int(raw.get("attempts", 0)) < int(raw.get("max_attempts", 3)):
            raw.update(status="queued", error=error, run_after=time.time() + retry_delay * raw["attempts"], updated_at=time.time())
        else:
            raw.update(status="failed", error=error, updated_at=time.time())
        self._save(jobs)


class DurableJobWorker:
    def __init__(self, jobs: DurableJobStore) -> None:
        self.jobs = jobs
        self.handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(self, name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self.handlers[name] = handler

    async def run_once(self, limit: int = 10) -> list[DurableJob]:
        completed: list[DurableJob] = []
        for job in self.jobs.claim_due(limit):
            try:
                handler = self.handlers[job.name]
                result = handler(job.payload)
                if isawaitable(result):
                    await result
                self.jobs.complete(job.id)
                completed.append(job)
            except Exception as exc:  # noqa: BLE001
                self.jobs.fail(job.id, str(exc))
        return completed


class ImmutableAuditLog:
    """Append-only hash chained audit log with verification and retention."""

    def __init__(self, store: Any, namespace: str = "audit") -> None:
        self.store = store
        self.namespace = namespace

    def append(self, action: str, actor: str, details: dict[str, Any], *, ip: str | None = None, user_agent: str | None = None) -> dict[str, Any]:
        entries = self.store.get(self.namespace, "entries", []) or []
        entry = {"id": secrets.token_hex(12), "action": action, "actor": actor, "details": details, "ip": ip, "user_agent": user_agent, "created_at": time.time(), "previous_hash": entries[-1]["hash"] if entries else "0" * 64}
        entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
        entries.append(entry)
        self.store.set(self.namespace, "entries", entries)
        return entry

    def verify(self) -> bool:
        previous = "0" * 64
        for entry in self.store.get(self.namespace, "entries", []) or []:
            candidate = dict(entry)
            digest = candidate.pop("hash")
            if candidate.get("previous_hash") != previous or not hmac.compare_digest(hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(), digest):
                return False
            previous = digest
        return True

    def prune(self, before: float) -> int:
        entries = self.store.get(self.namespace, "entries", []) or []
        kept = [entry for entry in entries if entry.get("created_at", 0) >= before]
        if len(kept) != len(entries):
            # Rebuild the retained segment because changing the first link
            # changes every downstream digest in the chain.
            previous = "0" * 64
            for index, entry in enumerate(kept):
                entry["previous_hash"] = previous
                entry.pop("hash", None)
                entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
                previous = entry["hash"]
            self.store.set(self.namespace, "entries", kept)
        return len(entries) - len(kept)


class NotificationService:
    def __init__(self, store: Any, namespace: str = "notifications") -> None:
        self.store = store
        self.namespace = namespace

    def set_preferences(self, username: str, preferences: dict[str, bool]) -> None:
        values = self.store.get(self.namespace, "preferences", {}) or {}
        values[username] = {str(key): bool(value) for key, value in preferences.items()}
        self.store.set(self.namespace, "preferences", values)

    def preferences(self, username: str) -> dict[str, bool]:
        return (self.store.get(self.namespace, "preferences", {}) or {}).get(username, {})

    def publish(self, username: str, channel: str, payload: dict[str, Any], sender: Callable[[str, dict[str, Any]], Any] | None = None) -> dict[str, Any]:
        preferences = self.preferences(username)
        if preferences.get(channel) is False:
            return {"delivered": False, "reason": "disabled"}
        message = {"id": secrets.token_urlsafe(12), "username": username, "channel": channel, "payload": payload, "created_at": time.time(), "read": False}
        messages = self.store.get(self.namespace, "messages", []) or []
        messages.append(message)
        self.store.set(self.namespace, "messages", messages[-5000:])
        if sender is not None:
            result = sender(channel, message)
            return {"delivered": True, "async": hasattr(result, "__await__"), "message": message}
        return {"delivered": True, "message": message}


class ResumableUploadStore:
    """Chunk store that survives restarts and validates the final digest."""

    def __init__(self, store: Any, namespace: str = "uploads") -> None:
        self.store = store
        self.namespace = namespace

    def create(self, filename: str, total_size: int, sha256: str | None = None) -> str:
        upload_id = secrets.token_urlsafe(16)
        uploads = self.store.get(self.namespace, "sessions", {}) or {}
        uploads[upload_id] = {"filename": filename, "total_size": total_size, "sha256": sha256, "chunks": {}, "created_at": time.time()}
        self.store.set(self.namespace, "sessions", uploads)
        return upload_id

    def put_chunk(self, upload_id: str, offset: int, data: bytes) -> None:
        uploads = self.store.get(self.namespace, "sessions", {}) or {}
        session = uploads.get(upload_id)
        if session is None or offset < 0 or offset + len(data) > int(session["total_size"]):
            raise ValueError("Invalid upload chunk")
        session["chunks"][str(offset)] = base64.b64encode(data).decode("ascii")
        self.store.set(self.namespace, "sessions", uploads)

    def finalize(self, upload_id: str) -> tuple[str, bytes]:
        uploads = self.store.get(self.namespace, "sessions", {}) or {}
        session = uploads.get(upload_id)
        if session is None:
            raise ValueError("Upload session not found")
        parts = [base64.b64decode(value) for _, value in sorted(session["chunks"].items(), key=lambda item: int(item[0]))]
        data = b"".join(parts)
        if len(data) != int(session["total_size"]):
            raise ValueError("Upload is incomplete")
        digest = hashlib.sha256(data).hexdigest()
        if session.get("sha256") and not hmac.compare_digest(digest, session["sha256"]):
            raise ValueError("Upload digest mismatch")
        del uploads[upload_id]
        self.store.set(self.namespace, "sessions", uploads)
        return session["filename"], data


class WebAuthnService:
    """Adapter boundary for a real WebAuthn implementation.

    Pass a provider backed by ``webauthn``/``py-webauthn``. The service stores
    credential metadata but never accepts a client assertion by itself.
    """

    def __init__(self, store: Any, provider: Any | None = None, namespace: str = "webauthn") -> None:
        self.store = store
        self.provider = provider
        self.namespace = namespace

    def begin_registration(self, username: str, **kwargs: Any) -> Any:
        if self.provider is None:
            raise RuntimeError("A WebAuthn provider is required")
        return self.provider.begin_registration(username, **kwargs)

    def finish_registration(self, username: str, response: Any) -> Any:
        if self.provider is None:
            raise RuntimeError("A WebAuthn provider is required")
        credential = self.provider.finish_registration(username, response)
        values = self.store.get(self.namespace, username, []) or []
        values.append(credential)
        self.store.set(self.namespace, username, values)
        return credential

    def begin_authentication(self, username: str) -> Any:
        if self.provider is None:
            raise RuntimeError("A WebAuthn provider is required")
        return self.provider.begin_authentication(username, self.store.get(self.namespace, username, []) or [])

    def finish_authentication(self, username: str, response: Any) -> bool:
        if self.provider is None:
            raise RuntimeError("A WebAuthn provider is required")
        return bool(self.provider.finish_authentication(username, response, self.store.get(self.namespace, username, []) or []))
