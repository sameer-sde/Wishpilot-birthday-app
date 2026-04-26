import smtplib
import ssl
from email.message import EmailMessage


def send_email(config, recipient, subject, body):
    smtp_host = str(config.get("smtp_host", "")).strip()
    smtp_port = int(config.get("smtp_port", 587))
    sender_email = str(config.get("sender_email", "")).strip()
    sender_name = str(config.get("sender_name", "WishPilot")).strip() or "WishPilot"
    password = str(config.get("password", ""))
    use_tls = bool(config.get("use_tls", True))

    recipient = str(recipient).strip()
    subject = str(subject).strip()
    body = str(body).strip()

    if not smtp_host:
        raise ValueError("SMTP host is required.")
    if not sender_email:
        raise ValueError("Sender email is required.")
    if not password:
        raise ValueError("SMTP password is required.")
    if not recipient:
        raise ValueError("Recipient email is required.")
    if not subject:
        raise ValueError("Email subject is required.")
    if not body:
        raise ValueError("Email body is required.")

    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    ssl_context = ssl.create_default_context()

    try:
        if use_tls:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl_context)
                server.ehlo()
                server.login(sender_email, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=ssl_context) as server:
                server.login(sender_email, password)
                server.send_message(msg)

    except smtplib.SMTPAuthenticationError as exc:
        raise ValueError("SMTP authentication failed. Check sender email and app password.") from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise ValueError("Recipient email was refused by the SMTP server.") from exc
    except smtplib.SMTPConnectError as exc:
        raise ValueError("Could not connect to the SMTP server.") from exc
    except smtplib.SMTPServerDisconnected as exc:
        raise ValueError("SMTP server disconnected unexpectedly.") from exc
    except smtplib.SMTPException as exc:
        raise ValueError(f"SMTP error: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Network or SSL error: {exc}") from exc