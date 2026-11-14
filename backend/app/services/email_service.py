"""
Cyber Raksha AI - Email Notification Service
Supports genuine SMTP dispatch with automated fallback and test audit log.
Provides templates for account verification, security threat alerts, and cybercrime complaint status updates.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("cyber_raksha.email")


class EmailService:
    def __init__(self):
        self.outbox_history: List[Dict[str, Any]] = []

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Dispatches email via standard SMTP if configured; records into outbox_history
        and logs cleanly if SMTP credentials are absent or in development.
        """
        record = {
            "to": to_email,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "QUEUED"
        }

        # If SMTP is configured, attempt real delivery
        if settings.SMTP_HOST and settings.SMTP_HOST.strip():
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
                msg["To"] = to_email

                part1 = MIMEText(body_text, "plain", "utf-8")
                msg.attach(part1)
                if body_html:
                    part2 = MIMEText(body_html, "html", "utf-8")
                    msg.attach(part2)

                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
                server.quit()

                record["status"] = "SENT_SMTP"
                logger.info(f"Email successfully dispatched via SMTP to {to_email} (Subject: '{subject}')")
            except Exception as e:
                record["status"] = "SMTP_FAILED_FALLBACK_RECORDED"
                record["error"] = str(e)
                logger.warning(f"SMTP dispatch to {to_email} failed: {e}. Falling back to audit record.")
        else:
            record["status"] = "RECORDED_NO_SMTP_CONFIG"
            logger.info(f"[EMAIL NOTIFICATION AUDIT] To: {to_email} | Subject: '{subject}' | Status: Recorded")

        self.outbox_history.append(record)
        return True

    def send_verification_email(self, to_email: str, token: str, full_name: Optional[str] = None) -> bool:
        """Dispatches an email address verification link."""
        name = full_name or "Citizen"
        verification_link = f"https://cyberraksha-backend.onrender.com/api/v1/auth/verify-email?token={token}"
        subject = "Verify Your Cyber Raksha AI Account"
        text = (
            f"Hello {name},\n\n"
            f"Welcome to Cyber Raksha AI. Please click the link below to verify your email address:\n\n"
            f"{verification_link}\n\n"
            f"If you did not create this account, please disregard this email.\n\n"
            f"Stay Safe,\nCyber Raksha AI Defense Team"
        )
        html = (
            f"<h2>Cyber Raksha AI Account Verification</h2>"
            f"<p>Hello <strong>{name}</strong>,</p>"
            f"<p>Thank you for enrolling in Cyber Raksha AI autonomous fraud defense.</p>"
            f"<p><a href='{verification_link}' style='padding: 10px 20px; background-color: #00E5FF; color: #000; text-decoration: none; border-radius: 4px; font-weight: bold;'>Verify Email Address</a></p>"
            f"<p>Or copy this link into your browser: {verification_link}</p>"
        )
        return self.send_email(to_email, subject, text, html)

    def send_security_alert_email(
        self,
        to_email: str,
        threat_type: str,
        severity: str,
        details: str
    ) -> bool:
        """Dispatches a real-time security alert email when a High/Critical incident is detected."""
        subject = f"⚠️ [CRITICAL ALERT] Cyber Raksha Detected {threat_type} ({severity})"
        text = (
            f"SECURITY ALERT NOTIFICATION\n"
            f"Severity: {severity}\n"
            f"Threat Category: {threat_type}\n"
            f"Details: {details}\n\n"
            f"Protective Action Recommended:\n"
            f"- DO NOT click suspicious links or share OTP / UPI PIN.\n"
            f"- Dial National Cybercrime Helpline 1930 immediately if money was deducted.\n"
            f"- Use Cyber Raksha AI Complaint Assistant to report this to cybercrime.gov.in.\n"
        )
        html = (
            f"<h2 style='color: #FF3B30;'>⚠️ Cyber Raksha Threat Alert</h2>"
            f"<p><strong>Severity:</strong> <span style='color: #FF3B30;'>{severity}</span></p>"
            f"<p><strong>Category:</strong> {threat_type}</p>"
            f"<div style='background: #f8f9fa; padding: 12px; border-left: 4px solid #FF3B30;'>{details}</div>"
            f"<h3>Recommended Next Steps:</h3>"
            f"<ul>"
            f"<li>Do not share OTP, PIN, or passwords with anyone.</li>"
            f"<li>For urgent financial fraud, immediately dial <strong>1930</strong>.</li>"
            f"<li>Open your Cyber Raksha app to file an official draft with <strong>cybercrime.gov.in</strong>.</li>"
            f"</ul>"
        )
        return self.send_email(to_email, subject, text, html)

    def send_complaint_confirmation_email(
        self,
        to_email: str,
        complaint_id: str,
        category: str,
        official_ack_number: Optional[str] = None
    ) -> bool:
        """Dispatches complaint drafting and tracking confirmation."""
        subject = f"🛡️ Cybercrime Complaint Structured: {complaint_id}"
        ack_str = f"Official Ack Number: {official_ack_number}\n" if official_ack_number else "Awaiting submission to cybercrime.gov.in\n"
        text = (
            f"Your cybercrime complaint draft has been successfully generated.\n\n"
            f"Complaint Reference: {complaint_id}\n"
            f"Category: {category}\n"
            f"{ack_str}\n"
            f"Portal URL: https://cybercrime.gov.in\n"
            f"Helpline: 1930\n\n"
            f"Track your status inside the Cyber Raksha app."
        )
        html = (
            f"<h2>Cybercrime Complaint Assistant Summary</h2>"
            f"<p><strong>Complaint Reference:</strong> <code>{complaint_id}</code></p>"
            f"<p><strong>Category:</strong> {category}</p>"
            f"<p><strong>Official Status:</strong> {official_ack_number or 'Draft Prepared / Pending Submission'}</p>"
            f"<p>You can track updates and update official FIR / Acknowledgement numbers inside the Cyber Raksha app.</p>"
        )
        return self.send_email(to_email, subject, text, html)

    def send_complaint_status_email(
        self,
        to_email: str,
        complaint_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Dispatches an update when official action or status changes on a tracked complaint."""
        subject = f"📋 Update on Complaint {complaint_id}: {new_status}"
        text = (
            f"Status Update on Complaint {complaint_id}\n\n"
            f"New Status: {new_status}\n"
            f"Notes: {notes or 'No additional notes.'}\n\n"
            f"Cyber Raksha AI Defense Team"
        )
        return self.send_email(to_email, subject, text)


email_service = EmailService()

