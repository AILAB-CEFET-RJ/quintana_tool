from config import PASSWORD_RESET_DEV_MODE


def send_password_reset_email(email, reset_url):
    if PASSWORD_RESET_DEV_MODE:
        print(f"[password-reset] Link de redefinicao para {email}: {reset_url}", flush=True)
        return

    raise RuntimeError("Envio de e-mail SMTP ainda nao configurado")
