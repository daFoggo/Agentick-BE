import logging
import smtplib
from email.message import EmailMessage

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


def send_agent_outreach_email(
    email_to: str,
    subject: str,
    body_content: str,
    task_link: str,
) -> None:
    if not configs.SMTP_USER or not configs.SMTP_PASSWORD:
        logger.warning(
            f"SMTP configurations are missing. Mock sending outreach email to {email_to} with content:\n{body_content}"
        )
        return

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-w-md; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2563eb;">Action Required</h2>
                <div style="white-space: pre-wrap; margin-bottom: 20px;">{body_content}</div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{task_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                        Update Now
                    </a>
                </div>
                <p>Thanks,<br>Your {configs.EMAILS_FROM_NAME} Assistant</p>
            </div>
        </body>
    </html>
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{configs.EMAILS_FROM_NAME} <{configs.SMTP_USER}>"
    msg["To"] = email_to
    msg.set_content(f"{body_content}\n\nUpdate here: {task_link}")
    msg.add_alternative(html_content, subtype="html")

    try:
        server = smtplib.SMTP(configs.SMTP_HOST, configs.SMTP_PORT)
        server.starttls()
        server.login(configs.SMTP_USER, configs.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent agent outreach email to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send outreach email to {email_to}: {e}")
        raise e


def send_risk_alert_email(
    email_to: str,
    task_title: str,
    risk_score: float,
    risk_level: str,
    due_date: str,
    recommendation: str,
    task_link: str,
) -> None:
    if not configs.SMTP_USER or not configs.SMTP_PASSWORD:
        logger.warning(
            f"SMTP configurations are missing. Mock sending risk alert email to {email_to}."
        )
        return

    subject = f"⚠️ [Agentick Risk Alert] High Risk Detected on '{task_title}'"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e11d48; border-radius: 8px;">
                <h2 style="color: #e11d48; margin-top: 0;">⚠️ High Deadline Risk Detected</h2>
                <p>Hello,</p>
                <p>The Agentick AI analyzer has detected a high deadline risk for the task: <b>{task_title}</b>.</p>
                <div style="background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0 0 8px 0;"><b>Risk Score:</b> <code style="font-size: 1.1em; color: #e11d48;">{risk_score:.2f}</code> ({risk_level.upper()})</p>
                    <p style="margin: 0 0 8px 0;"><b>Deadline:</b> {due_date}</p>
                    <p style="margin: 0;"><b>AI Recommendation:</b> {recommendation}</p>
                </div>
                <p>Click the button below to update progress or adjust resources immediately:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{task_link}" style="background-color: #e11d48; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                        Manage Task
                    </a>
                </div>
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
        f"High Risk Detected!\n\nTask: {task_title}\nRisk Score: {risk_score:.2f} ({risk_level.upper()})\nAI Recommendation: {recommendation}\n\nManage here: {task_link}"
    )
    msg.add_alternative(html_content, subtype="html")

    try:
        server = smtplib.SMTP(configs.SMTP_HOST, configs.SMTP_PORT)
        server.starttls()
        server.login(configs.SMTP_USER, configs.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent risk alert email to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send risk alert email to {email_to}: {e}")
        raise e
