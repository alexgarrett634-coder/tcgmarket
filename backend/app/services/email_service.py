"""Async email via aiosmtplib."""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_email(to: str, subject: str, html: str) -> None:
    if not settings.smtp_host or not settings.smtp_user:
        return  # Email not configured; skip silently

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
    )


async def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    html = f"""
    <h2>Verify your email</h2>
    <p>Click the link below to verify your account:</p>
    <a href="{link}">{link}</a>
    <p>This link expires in 24 hours.</p>
    """
    await send_email(to, "Verify your PokéMarket account", html)


async def send_price_alert_email(to: str, card_name: str, direction: str, price: float, threshold: float) -> None:
    label = "risen above" if direction == "above" else "fallen below"
    html = f"""
    <h2>Price Alert — {card_name}</h2>
    <p>The price has {label} your alert threshold of <strong>${threshold:.2f}</strong>.</p>
    <p>Current price: <strong>${price:.2f}</strong></p>
    """
    await send_email(to, f"Price Alert: {card_name} {label} ${threshold:.2f}", html)


async def send_market_won_email(to: str, market_title: str, payout: float, currency: str) -> None:
    unit = "Prediction Coins" if currency == "coins" else "Market Credits"
    html = f"""
    <h2>You won a prediction market!</h2>
    <p>Market: <strong>{market_title}</strong></p>
    <p>Payout: <strong>{payout:.2f} {unit}</strong></p>
    """
    await send_email(to, f"You won: {market_title}", html)
