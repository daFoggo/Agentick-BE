import smtplib
from email.message import EmailMessage
import logging
from typing import Optional

from app.core.config import configs

logger = logging.getLogger(__name__)

def send_invitation_email(
    email_to: str,
    inviter_name: str,
    target_name: str,
    invite_link: str,
    target_type: str = "team",
) -> None:
    if not configs.SMTP_USER or not configs.SMTP_PASSWORD:
        logger.warning(
            f"SMTP configurations are missing. Mock sending email to {email_to} with link: {invite_link}"
        )
        return

    subject = f"Invitation to join {target_name} on {configs.EMAILS_FROM_NAME}"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-w-md; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2563eb;">You have been invited!</h2>
                <p>Hello,</p>
                <p><b>{inviter_name}</b> has invited you to join the {target_type} <b>{target_name}</b> on {configs.EMAILS_FROM_NAME}.</p>
                <p>Click the button below to view and accept the invitation:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                <p>If you don't have an account yet, you will be asked to sign up first.</p>
                <p>Thanks,<br>The {configs.EMAILS_FROM_NAME} Team</p>
            </div>
        </body>
    </html>
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{configs.EMAILS_FROM_NAME} <{configs.SMTP_USER}>"
    msg["To"] = email_to
    msg.set_content(
        f"Hello,\n\n{inviter_name} has invited you to join {target_name}.\nPlease visit: {invite_link}"
    )
    msg.add_alternative(html_content, subtype="html")

    try:
        server = smtplib.SMTP(configs.SMTP_HOST, configs.SMTP_PORT)
        server.starttls()
        server.login(configs.SMTP_USER, configs.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent invitation email to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {e}")
        raise e
