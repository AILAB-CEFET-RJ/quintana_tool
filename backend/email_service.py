from email.message import EmailMessage
import smtplib

from config import (
    PASSWORD_RESET_DEV_MODE,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)


def send_password_reset_email(email, reset_url):
    if PASSWORD_RESET_DEV_MODE:
        print(f"[password-reset] Link de redefinicao para {email}: {reset_url}", flush=True)
        return

    if not SMTP_HOST or not SMTP_FROM:
        raise RuntimeError("SMTP_HOST e SMTP_FROM devem estar configurados")

    message = EmailMessage()
    message["Subject"] = "Redefinicao de senha - Quintana"
    message["From"] = SMTP_FROM
    message["To"] = email
    message.set_content(
        "\n".join([
            "Ola,",
            "",
            "Recebemos uma solicitacao para redefinir a senha da sua conta no Quintana.",
            "Use o link abaixo para escolher uma nova senha:",
            "",
            reset_url,
            "",
            "Se voce nao solicitou essa alteracao, ignore esta mensagem.",
            "",
            "Quintana",
        ])
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER or SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)
