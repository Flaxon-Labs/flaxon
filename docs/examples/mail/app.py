"""Flaxon contact-form API that sends an email via flaxon.mail."""

from flaxon import Flaxon, JSONResponse
from flaxon.middleware import CORSMiddleware
from flaxon.validation import Schema, fields
from flaxon.mail import Mailer, Message
from flaxon.mail.adapters.console import ConsoleAdapter
# Swap ConsoleAdapter for real SMTP delivery:
# from flaxon.mail.adapters.smtp import SMTPAdapter
# mailer = Mailer(SMTPAdapter(host="smtp.example.com", port=587,
#                              username="user@example.com", password="secret"))

app = Flaxon("mail-example", debug=True)
app.add_middleware(CORSMiddleware, allowed_origins=["http://localhost:5500", "http://127.0.0.1:5500"])

# ConsoleAdapter just prints the email to the terminal — good for local dev.
mailer = Mailer(ConsoleAdapter(print_body=True))


class ContactForm(Schema):
    name = fields.StrField(required=True, min_length=1, max_length=120)
    email = fields.StrField(required=True, min_length=3, max_length=200)
    message = fields.StrField(required=True, min_length=1, max_length=2000)


@app.post("/api/contact")
async def send_contact_email(data: ContactForm) -> JSONResponse:
    email = (
        Message()
        .from_address("noreply@example.com", "My App")
        .to("support@example.com")
        .reply_to(data.email, data.name)
        .subject(f"New contact form message from {data.name}")
        .body(f"From: {data.name} <{data.email}>\n\n{data.message}")
        .build()
    )

    await mailer.send(email)

    return JSONResponse({"sent": True}, status_code=201)

