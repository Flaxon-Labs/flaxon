from __future__ import annotations

from .mailer import Mailer
from .message import Attachment, Email, EmailAddress, Message
from .templates import EmailTemplate, TemplateEngine

__all__ = [
    "Attachment",
    "Email",
    "EmailAddress",
    "EmailTemplate",
    "Mailer",
    "Message",
    "TemplateEngine",
]
