from email.message import EmailMessage
import os

import aiosmtplib

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()


async def send_reset_code_email(email: str, name: str, code: str):
    message = EmailMessage()
    message["From"] = os.getenv("EMAIL_USER"),
    message["To"] = email
    message["Subject"] = "Código para restablecer tu contraseña"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
          <h2 style="color: #4CAF50;">Hola {name},</h2>
          <p style="font-size: 16px;">Hemos recibido una solicitud para restablecer tu contraseña.</p>
          <p style="font-size: 16px;">Tu código de verificación es:</p>
          <div style="text-align: center; margin: 20px 0;">
            <span style="font-size: 28px; font-weight: bold; background: #e8f5e9; color: #2e7d32; padding: 10px 20px; border-radius: 8px;">{code}</span>
          </div>
          <p style="font-size: 14px; color: #555;">Este código es válido por <strong>10 minutos</strong>. Si no solicitaste este cambio, puedes ignorar este mensaje.</p>
          <hr style="margin: 30px 0;">
          <p style="font-size: 12px; color: #999;">© 2025 CashCycle. Todos los derechos reservados.</p>
        </div>
      </body>
    </html>
    """
    message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        username=os.getenv("EMAIL_USER"),
        password=os.getenv("EMAIL_PASS"),
        start_tls=True,
    )
