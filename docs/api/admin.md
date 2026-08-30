# Admin API Reference

## Admin Dashboard

::: flaxon.admin.AdminDashboard
    options:
        members:
            - __init__
            - register
            - unregister
            - index
            - list_view
            - add_view
            - detail_view
            - edit_view
            - delete_view
            - get_urls

---

## Admin Configuration

::: flaxon.admin.AdminConfig
    options:
        members:
            - __init__
            - to_dict

---

## Registry

::: flaxon.admin.Registry
    options:
        members:
            - register
            - unregister
            - get
            - get_by_model
            - get_all
            - clear

---

## Admin Model

::: flaxon.admin.AdminModel
    options:
        members:
            - __init__
            - get_name
            - get_verbose_name
            - get_verbose_name_plural
            - add_action
            - get_actions

---

# Admin Views

## Base View

::: flaxon.admin.views.AdminView
    options:
        members:
            - __init__
            - render

---

## Change List View

::: flaxon.admin.views.ChangeListView
    options:
        members:
            - render

---

## Detail View

::: flaxon.admin.views.DetailView
    options:
        members:
            - render

---

## Create View

::: flaxon.admin.views.CreateView
    options:
        members:
            - render

---

## Update View

::: flaxon.admin.views.UpdateView
    options:
        members:
            - render

---

## Delete View

::: flaxon.admin.views.DeleteView
    options:
        members:
            - render

---

# Decorators

## admin_model

::: flaxon.admin.decorators.admin_model
    options:
        show_source: false

---

## admin_action

::: flaxon.admin.decorators.admin_action
    options:
        show_source: false

---

## admin_display

::: flaxon.admin.decorators.admin_display
    options:
        show_source: false

---

# Exceptions

## AdminError

::: flaxon.admin.exceptions.AdminError

---

## ModelNotFoundError

::: flaxon.admin.exceptions.ModelNotFoundError

---

## PermissionDeniedError

::: flaxon.admin.exceptions.PermissionDeniedError

---

## ValidationError

::: flaxon.admin.exceptions.ValidationError

## Production Services

These services are available for durable Admin integrations:

```python
from flaxon.admin import (
    DurableJobStore, DurableJobWorker, ImmutableAuditLog,
    NotificationService, ResumableUploadStore, WebAuthnService,
)
```

| Service | Purpose |
|---|---|
| `DurableJobStore` | Persist queued, running, completed, and failed jobs with retry metadata. |
| `DurableJobWorker` | Register named handlers and process due jobs. |
| `ImmutableAuditLog` | Append hash-chained records and verify tamper evidence. |
| `NotificationService` | Store preferences and per-user channel delivery records. |
| `ResumableUploadStore` | Persist upload sessions, chunks, and final SHA-256 validation. |
| `WebAuthnService` | Delegate registration and assertion ceremonies to an injected provider. |

## HTTP Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/media/resumable` | Create a resumable upload session. |
| `PATCH` | `/admin/media/resumable/{upload_id}` | Upload a raw byte chunk using `Upload-Offset`. |
| `POST` | `/admin/media/resumable/{upload_id}/complete` | Validate and persist the completed upload. |
| `GET` | `/admin/notifications/preferences` | Read the current user’s notification preferences. |
| `POST` | `/admin/notifications/preferences` | Update preferences with a CSRF header. |
| `GET` | `/admin/audit/verify` | Verify the persisted audit hash chain. |
| `POST` | `/admin/profile/webauthn/register/begin` | Start provider-backed credential registration. |
| `POST` | `/admin/profile/webauthn/register/finish` | Complete credential registration. |
| `POST` | `/admin/profile/webauthn/authenticate/begin` | Start provider-backed authentication. |
| `POST` | `/admin/profile/webauthn/authenticate/finish` | Verify an authentication assertion. |

All authenticated Admin mutations require the session cookie and
`X-CSRF-Token`. Use `redis_url` for shared sessions, rate limits, and
multi-worker coordination.
# Admin API Reference

For the current production contract, including authentication, CSRF,
persistence, migrations, CMS APIs, extension hooks, and custom clients, see
[Admin and CMS Production Guide](../guides/admin-cms.md) and
[Admin and CMS API Reference](admin-cms.md). The symbols below document the
lower-level model-admin classes.

For the current production contract, including authentication, CSRF,
persistence, migrations, CMS APIs, extension hooks, and custom clients, see
[Admin and CMS Production Guide](../guides/admin-cms.md) and
[Admin and CMS API Reference](admin-cms.md). The symbols below document the
lower-level model-admin classes.
