from typing import Optional, Dict, Any
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import logging

from app.core.config import settings
from app.core.logger import logger

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER or "",
    MAIL_PASSWORD=settings.SMTP_PASSWORD.get_secret_value() if settings.SMTP_PASSWORD else "",
    MAIL_FROM=settings.SMTP_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=settings.SMTP_SSL,
    USE_CREDENTIALS=bool(settings.SMTP_USER),
    VALIDATE_CERTS=True,
)

class EmailService:
    @staticmethod
    async def _send(
        to: str,
        subject: str,
        html: str,
    ) -> bool:
        try:
            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=html,
                subtype="html",
            )

            fm = FastMail(conf)
            await fm.send_message(message)

            logger.info(f"📧 Email sent to {to}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False

    @staticmethod
    async def send_subscription_welcome(
        to: str,
        name: str,
        tier: str,
        price: float,
    ) -> bool:
        html = f"""
        <div style="font-family: monospace; background:#0a0a0f; color:#fff; padding:40px; border-radius:12px;">
            <h1 style="color:#06b6d4;">Welcome to {tier.title()}! 🚀</h1>
            <p>Hi {name},</p>
            <p>Your Chronos Search subscription is now active.</p>
            <div style="background:rgba(6,182,212,0.1); padding:20px; border-radius:8px; margin:20px 0;">
                <p><strong>Plan:</strong> {tier.title()}</p>
                <p><strong>Amount:</strong> ${price:.2f}/month</p>
            </div>
            <p>You now have access to:</p>
            <ul>
                <li>100 searches per day</li>
                <li>All 12 platforms</li>
                <li>6-month history</li>
                <li>Advanced analytics</li>
            </ul>
            <a href="{settings.FRONTEND_URL}/dashboard" style="display:inline-block; padding:12px 24px; background:linear-gradient(135deg,#06b6d4,#a855f7); color:white; text-decoration:none; border-radius:8px; margin-top:20px;">Go to Dashboard →</a>
        </div>
        """
        return await EmailService._send(to, f"Welcome to Chronos {tier.title()}", html)

    @staticmethod
    async def send_payment_succeeded(
        to: str,
        name: str,
        amount: float,
        description: str,
    ) -> bool:
        html = f"""
        <div style="font-family: monospace; background:#0a0a0f; color:#fff; padding:40px; border-radius:12px;">
            <h2 style="color:#22c55e;">✅ Payment Successful</h2>
            <p>Hi {name},</p>
            <p>Your payment has been processed successfully.</p>
            <div style="background:rgba(34,197,94,0.1); padding:20px; border-radius:8px; margin:20px 0;">
                <p><strong>Amount:</strong> ${amount:.2f}</p>
                <p><strong>For:</strong> {description}</p>
            </div>
            <a href="{settings.FRONTEND_URL}/billing" style="color:#06b6d4;">View Billing →</a>
        </div>
        """
        return await EmailService._send(to, f"Payment Confirmed - ${amount:.2f}", html)

    @staticmethod
    async def send_payout_completed(
        to: str,
        name: str,
        amount: float,
    ) -> bool:
        html = f"""
        <div style="font-family: monospace; background:#0a0a0f; color:#fff; padding:40px; border-radius:12px;">
            <h2 style="color:#22c55e;">💰 Payout Sent</h2>
            <p>Hi {name},</p>
            <p>Your reward payout has been sent successfully!</p>
            <div style="background:rgba(34,197,94,0.1); padding:20px; border-radius:8px; margin:20px 0;">
                <p><strong>Amount:</strong> ${amount:.2f}</p>
                <p><strong>Arrives:</strong> 1-3 business days</p>
            </div>
            <a href="{settings.FRONTEND_URL}/rewards" style="color:#22c55e;">View Rewards →</a>
        </div>
        """
        return await EmailService._send(to, f"Payout Sent - ${amount:.2f}", html)

    @staticmethod
    async def send_trial_ending_soon(
        to: str,
        name: str,
        days_left: int,
    ) -> bool:
        html = f"""
        <div style="font-family: monospace; background:#0a0a0f; color:#fff; padding:40px; border-radius:12px;">
            <h2 style="color:#facc15;">⏰ Trial Ending Soon</h2>
            <p>Hi {name},</p>
            <p>Your free trial ends in <strong>{days_left} days</strong>.</p>
            <p>Subscribe now to keep all your Pro features.</p>
            <a href="{settings.FRONTEND_URL}/billing" style="display:inline-block; padding:12px 24px; background:linear-gradient(135deg,#06b6d4,#a855f7); color:white; text-decoration:none; border-radius:8px; margin-top:20px;">Upgrade Now →</a>
        </div>
        """
        return await EmailService._send(to, f"Trial ends in {days_left} days", html)


email_service = EmailService()