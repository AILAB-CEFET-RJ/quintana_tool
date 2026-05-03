from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import JWT_EXPIRATION_HOURS, JWT_SECRET

serializer = URLSafeTimedSerializer(JWT_SECRET, salt="quintana-auth")


def create_token(username, tipo_usuario):
    return serializer.dumps({
        "username": username,
        "tipoUsuario": tipo_usuario,
    })


def decode_token(token):
    return serializer.loads(token, max_age=JWT_EXPIRATION_HOURS * 3600)


def get_bearer_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header.replace("Bearer ", "", 1).strip()


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Autenticação obrigatória"}), 401

        try:
            g.current_user = decode_token(token)
        except SignatureExpired:
            return jsonify({"error": "Sessão expirada"}), 401
        except BadSignature:
            return jsonify({"error": "Token inválido"}), 401

        return fn(*args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.current_user.get("tipoUsuario") not in roles:
                return jsonify({"error": "Acesso negado"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
