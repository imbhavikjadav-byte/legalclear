import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def _html_body(document_name: str, overall_risk: str, date_str: str, time_str: str) -> str:
    risk_colours = {"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EF4444"}
    risk_colour = risk_colours.get(overall_risk, "#64748B")

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <!-- Header -->
        <tr>
          <td style="background:#0F1A2E;padding:28px 32px;text-align:center;">
            <h1 style="margin:0;color:#F59E0B;font-size:28px;letter-spacing:1px;">LegalClear</h1>
            <p style="margin:6px 0 0;color:#94A3B8;font-size:13px;">Legal Document Plain-English Translation</p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 16px;color:#1e293b;font-size:15px;">Hi there,</p>
            <p style="margin:0 0 16px;color:#1e293b;font-size:15px;">
              Your plain-English translation of <strong>{document_name}</strong> is attached as a PDF.
            </p>
            <p style="margin:0 0 16px;color:#64748b;font-size:14px;">
              This report was generated on {date_str} at {time_str}.
            </p>
            <table cellpadding="0" cellspacing="0" style="margin:20px 0;">
              <tr>
                <td style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 20px;">
                  <span style="color:#64748b;font-size:13px;">Overall Risk Level:</span>
                  <span style="background:{risk_colour};color:white;font-weight:bold;padding:3px 10px;border-radius:4px;font-size:13px;margin-left:10px;">{overall_risk}</span>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 16px;color:#1e293b;font-size:15px;">
              Please note: This report is for informational purposes only and does not constitute legal advice.
            </p>
            <p style="margin:24px 0 0;color:#1e293b;font-size:15px;">— The LegalClear Team</p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px 32px;text-align:center;">
            <p style="margin:0;color:#94a3b8;font-size:11px;">
              LegalClear provides plain-English summaries for informational purposes only.
              This is not legal advice. If you have significant concerns about a document,
              please consult a qualified lawyer before signing.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_email_with_pdf(
    recipient_email: str,
    translation_data: dict,
    pdf_bytes: bytes,
    document_name: str,
) -> None:
    sendgrid_key = os.getenv("SENDGRID_API_KEY", "").strip()
    email_from = (os.getenv("EMAIL_FROM", "legalclear@example.com").strip(), "Legal Clear")

    now = datetime.now(timezone.utc)
    date_str = f"{now.day} {now.strftime('%B %Y')}"  # cross-platform, e.g. "3 May 2026"
    time_str = now.strftime("%H:%M UTC")

    overall_risk = translation_data.get("overall_risk_level", "UNKNOWN")
    subject = f"Your LegalClear Translation Report — {document_name}"
    html_content = _html_body(document_name, overall_risk, date_str, time_str)

    safe_name = document_name.replace(" ", "-")[:40]
    pdf_filename = f"LegalClear-{safe_name}-{now.strftime('%Y%m%d')}.pdf"

    if sendgrid_key:
        _send_via_sendgrid(
            sendgrid_key,
            email_from,
            recipient_email,
            subject,
            html_content,
            pdf_bytes,
            pdf_filename,
        )
    else:
        _send_via_smtp(
            email_from,
            recipient_email,
            subject,
            html_content,
            pdf_bytes,
            pdf_filename,
        )


def _send_via_sendgrid(
    api_key: str,
    sender: str,
    recipient: str,
    subject: str,
    html_content: str,
    pdf_bytes: bytes,
    pdf_filename: str,
) -> None:
    import base64
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail,
        Attachment,
        FileContent,
        FileName,
        FileType,
        Disposition,
    )

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=html_content,
    )

    encoded_pdf = base64.b64encode(pdf_bytes).decode()
    attachment = Attachment(
        FileContent(encoded_pdf),
        FileName(pdf_filename),
        FileType("application/pdf"),
        Disposition("attachment"),
    )
    message.attachment = attachment

    sg = SendGridAPIClient(api_key)
    try:
        response = sg.send(message)
    except Exception as exc:
        # Surface the full SendGrid exception (includes auth/sender errors)
        raise RuntimeError(f"SendGrid API error: {exc}") from exc

    if response.status_code not in (200, 202):
        body = getattr(response, 'body', b'')
        if isinstance(body, bytes):
            body = body.decode('utf-8', errors='replace')
        raise RuntimeError(
            f"SendGrid returned status {response.status_code}: {body}"
        )


def _send_via_smtp(
    sender: str,
    recipient: str,
    subject: str,
    html_content: str,
    pdf_bytes: bytes,
    pdf_filename: str,
) -> None:
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    if not email_password:
        raise RuntimeError("No email credentials configured.")

    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{pdf_filename}"')
    msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(sender, email_password)
        server.sendmail(sender, recipient, msg.as_string())
