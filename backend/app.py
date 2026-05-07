import database
from flask import Flask, g, request, jsonify
from bson import ObjectId
from functions import evaluate_redacao, persist_essay, get_text
from llm import get_llm_feedback, get_structured_llm_feedback
from pedagogy import build_structured_feedback, build_textual_feedback_from_structured
from analytics import build_teacher_analytics
from schemas import validate_required_fields
from flask_cors import CORS
from config import (
    FRONTEND_URL,
    JWT_SECRET,
    PASSWORD_RESET_DEV_MODE,
    PASSWORD_RESET_EXPIRATION_MINUTES,
    PASSWORD_RESET_RATE_LIMIT_EMAIL_MAX,
    PASSWORD_RESET_RATE_LIMIT_IP_MAX,
    PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES,
    get_cors_origins,
    should_expose_errors,
)
from auth import create_token, decode_token, get_bearer_token, require_auth, require_role
from analytics_cache import get_cached_analytics, invalidate_teacher_analytics, set_cached_analytics
from email_service import send_password_reset_email
import bcrypt
import hashlib
import os
import secrets
from threading import Thread
from datetime import datetime, timedelta, timezone
from itsdangerous import BadSignature, SignatureExpired

app = Flask(__name__)
cors_origins = get_cors_origins()
CORS(app, origins=cors_origins if cors_origins else [])


competencias = {
    "comp1":"Domínio da modalidade escrita formal",
    "comp2":"Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa",
    "comp3":"Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista",
    "comp4":"Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação",
    "comp5":"Proposta de intervenção com respeito aos direitos humanos",
}


def current_user_id():
    return str(g.current_user.get("user_id", ""))


def current_display_name():
    return g.current_user.get("display_name", "")


def activity_belongs_to_teacher(activity_id, teacher_id):
    if not activity_id or not ObjectId.is_valid(activity_id):
        return False
    return database.db.activities.find_one({"_id": ObjectId(activity_id), "teacher_id": str(teacher_id)}) is not None


def class_belongs_to_teacher(class_id, teacher_id):
    if not class_id or not ObjectId.is_valid(class_id):
        return False
    return database.db.classes.find_one({"_id": ObjectId(class_id), "teacher_id": str(teacher_id)}) is not None


def theme_belongs_to_teacher(theme_id, teacher_id):
    if not theme_id or not ObjectId.is_valid(theme_id):
        return False
    return database.db.temas.find_one({"_id": ObjectId(theme_id), "teacher_id": str(teacher_id)}) is not None


def redacao_belongs_to_user(redacao, user):
    if not redacao or not user:
        return False

    user_id = str(user.get("user_id", ""))
    role = user.get("tipoUsuario")
    if role == "aluno":
        return redacao.get("student_id") == user_id

    if role == "professor":
        if theme_belongs_to_teacher(redacao.get("id_tema"), user_id):
            return True
        if class_belongs_to_teacher(redacao.get("class_id"), user_id):
            return True
        if activity_belongs_to_teacher(redacao.get("activity_id"), user_id):
            return True

    return False


def get_authorized_redacao_or_404(id):
    if not ObjectId.is_valid(id):
        return None, (jsonify({"error": "ID inválido"}), 400)

    redacao = database.get_redacao_document(id)
    if not redacao:
        return None, (jsonify({"error": "Redação não encontrada"}), 404)

    if not redacao_belongs_to_user(redacao, g.current_user):
        return None, (jsonify({"error": "Acesso negado"}), 403)

    return redacao, None


def invalidate_analytics_for_redacao(redacao):
    if not redacao:
        return

    teachers = set()
    theme_id = redacao.get("id_tema")
    if theme_id and ObjectId.is_valid(theme_id):
        theme = database.db.temas.find_one({"_id": ObjectId(theme_id)}, {"teacher_id": 1})
        if theme and theme.get("teacher_id"):
            teachers.add(theme["teacher_id"])

    class_id = redacao.get("class_id")
    if class_id and ObjectId.is_valid(class_id):
        class_doc = database.db.classes.find_one({"_id": ObjectId(class_id)}, {"teacher_id": 1})
        if class_doc and class_doc.get("teacher_id"):
            teachers.add(class_doc["teacher_id"])

    activity_id = redacao.get("activity_id")
    if activity_id and ObjectId.is_valid(activity_id):
        activity = database.db.activities.find_one({"_id": ObjectId(activity_id)}, {"teacher_id": 1})
        if activity and activity.get("teacher_id"):
            teachers.add(activity["teacher_id"])

    for teacher in teachers:
        invalidate_teacher_analytics(teacher)


def build_activity_submission_status(activity_id):
    activity = database.db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        return None

    class_doc = database.db.classes.find_one({"_id": ObjectId(activity.get("class_id"))}) if ObjectId.is_valid(activity.get("class_id", "")) else None
    theme = database.db.temas.find_one({"_id": ObjectId(activity.get("theme_id"))}) if ObjectId.is_valid(activity.get("theme_id", "")) else None
    expected_student_ids = sorted(class_doc.get("student_ids", [])) if class_doc else []
    users = {
        str(item["_id"]): item.get("display_name", item.get("email", "Aluno"))
        for item in database.db.users.find({"_id": {"$in": [ObjectId(value) for value in expected_student_ids if ObjectId.is_valid(value)]}})
    }
    redacoes = list(database.db.redacoes.find({"activity_id": activity_id}))
    submitted_student_ids = sorted(set(redacao.get("student_id") for redacao in redacoes if redacao.get("student_id")))
    missing_student_ids = sorted(set(expected_student_ids) - set(submitted_student_ids))
    submitted_students = [users.get(student_id, student_id) for student_id in submitted_student_ids]
    missing_students = [users.get(student_id, student_id) for student_id in missing_student_ids]
    due_date = activity.get("due_date", "")
    today = datetime.now(timezone.utc).date().isoformat()
    late_students = missing_students if due_date and due_date < today else []

    return {
        "activity": {
            "_id": str(activity["_id"]),
            "title": activity.get("title"),
            "teacher_id": activity.get("teacher_id"),
            "class_id": activity.get("class_id"),
            "class_name": class_doc.get("name") if class_doc else "Turma não encontrada",
            "theme_id": activity.get("theme_id"),
            "theme": theme.get("tema") if theme else "Tema não encontrado",
            "due_date": due_date,
        },
        "expected_students": [users.get(student_id, student_id) for student_id in expected_student_ids],
        "submitted_students": submitted_students,
        "missing_students": missing_students,
        "late_students": late_students,
        "submission_count": len(submitted_students),
        "expected_count": len(expected_students),
    }


def validate_structured_feedback_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("feedback estruturado não é objeto")
    if not isinstance(payload.get("competencies"), list) or len(payload["competencies"]) != 5:
        raise ValueError("feedback estruturado deve conter 5 competências")
    if not isinstance(payload.get("priorities"), list):
        raise ValueError("feedback estruturado deve conter prioridades")
    if not isinstance(payload.get("rewrite_checklist"), list):
        raise ValueError("feedback estruturado deve conter checklist")
    return payload


def error_response(message, status=500, exc=None):
    payload = {"error": message}
    if exc is not None and should_expose_errors():
        payload["detail"] = str(exc)
    return jsonify(payload), status


def should_use_llm_feedback():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(key) and key.lower() not in {"dummy", "none", "null", "changeme"}


def hash_password_reset_token(token):
    return hashlib.sha256(f"{JWT_SECRET}:{token}".encode("utf-8")).hexdigest()


def hash_password_reset_lookup(value):
    normalized = (value or "").strip().lower()
    return hashlib.sha256(f"{JWT_SECRET}:password-reset-lookup:{normalized}".encode("utf-8")).hexdigest()


def build_password_reset_url(token):
    return f"{FRONTEND_URL}/quintana/redefinir-senha?token={token}"


def password_reset_generic_response():
    return jsonify({
        "message": "Se o e-mail estiver cadastrado, enviaremos instruções para redefinir a senha."
    }), 200


def password_reset_rate_limit_response():
    return jsonify({
        "error": "Muitas solicitações de redefinição. Aguarde alguns minutos antes de tentar novamente."
    }), 429


def get_optional_current_user():
    token = get_bearer_token()
    if not token:
        return None, None

    try:
        return decode_token(token), None
    except SignatureExpired:
        return None, (jsonify({"error": "Sessão expirada"}), 401)
    except BadSignature:
        return None, (jsonify({"error": "Token inválido"}), 401)


def get_request_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def enforce_password_reset_rate_limit(email):
    now = datetime.utcnow()
    since = now - timedelta(minutes=PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES)
    ip = get_request_ip()
    email_hash = hash_password_reset_lookup(email)
    ip_hash = hash_password_reset_lookup(ip)

    email_attempts = database.count_password_reset_attempts("email", email_hash, since)
    ip_attempts = database.count_password_reset_attempts("ip", ip_hash, since)

    if email_attempts >= PASSWORD_RESET_RATE_LIMIT_EMAIL_MAX or ip_attempts >= PASSWORD_RESET_RATE_LIMIT_IP_MAX:
        if PASSWORD_RESET_DEV_MODE:
            print(
                f"[password-reset] Rate limit atingido para email_hash={email_hash[:10]} ip={ip}",
                flush=True
            )
        return False

    base_document = {
        "created_at": now,
        "requester_ip_hash": ip_hash,
        "schema_version": 1,
    }
    database.create_password_reset_attempt({
        **base_document,
        "kind": "email",
        "key_hash": email_hash,
    })
    database.create_password_reset_attempt({
        **base_document,
        "kind": "ip",
        "key_hash": ip_hash,
    })
    return True


@app.route("/")
def health():
    db_ok, db_error = database.check_db_connection()
    status = {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
    }
    if db_error and should_expose_errors():
        status["database_error"] = db_error
    return jsonify(status), 200 if db_ok else 503


@app.post("/model")
@require_role("aluno")
def post_model_response():
    essay = request.json['essay']
    id_theme = request.json['id']
    student_id = current_user_id()
    student_name = current_display_name()
    rewrite_of = request.json.get('rewrite_of')
    class_id = request.json.get('class_id')
    activity_id = request.json.get('activity_id')
    submitted_title = (request.json.get('title') or "").strip()
    if rewrite_of:
        parent_candidate = database.get_redacao_document(rewrite_of) if ObjectId.is_valid(rewrite_of) else None
        if not parent_candidate or parent_candidate.get("student_id") != student_id:
            return jsonify({"error": "Redação de origem inválida"}), 403

    if submitted_title:
        title = submitted_title
        rest_of_essay = essay
    else:
        lines = essay.split('\n')
        title = lines[0].strip() if lines and lines[0].strip() else "Sem título"
        rest_of_essay = '\n'.join(line for line in lines[1:] if line.strip())

    obj = evaluate_redacao(essay)

    grades = {
        competencias["comp1"]: float(obj.get('nota_1', 0)),
        competencias["comp2"]: float(obj.get('nota_2', 0)),
        competencias["comp3"]: float(obj.get('nota_3', 0)),
        competencias["comp4"]: float(obj.get('nota_4', 0)),
        competencias["comp5"]: float(obj.get('nota_5', 0))
    }

    theme = database.get_tema(id_theme)

    now = datetime.now(timezone.utc).isoformat()
    parent_redacao = database.get_redacao_document(rewrite_of) if rewrite_of and ObjectId.is_valid(rewrite_of) else None
    version_group_id = str(parent_redacao.get("version_group_id") or parent_redacao["_id"]) if parent_redacao else None
    version_number = 1

    if parent_redacao:
        database.db.redacoes.update_one(
            {"_id": parent_redacao["_id"]},
            {"$set": {
                "version_group_id": version_group_id,
                "version_number": int(parent_redacao.get("version_number", 1))
            }}
        )
        existing_versions = database.get_redacao_versions(str(parent_redacao["_id"]))
        version_number = max([int(item.get("version_number", 1)) for item in existing_versions] or [1]) + 1

    feedback_structured = build_structured_feedback(grades)
    feedback_text_fallback = build_textual_feedback_from_structured(feedback_structured)

    essay_data = {
        "titulo": title,
        "texto": rest_of_essay.strip(),
        "nota_competencia_1_model": grades[competencias["comp1"]],
        "nota_competencia_2_model": grades[competencias["comp2"]],
        "nota_competencia_3_model": grades[competencias["comp3"]],
        "nota_competencia_4_model": grades[competencias["comp4"]],
        "nota_competencia_5_model": grades[competencias["comp5"]],
        "nota_total": sum(grades.values()),
        "nota_professor": "",
        "id_tema": id_theme,
        "student_id": student_id,
        "student_name": student_name,
        "feedback_llm": feedback_text_fallback,
        "competencias": competencias,
        "created_at": now,
        "updated_at": now,
        "version_group_id": version_group_id,
        "parent_redacao_id": rewrite_of if parent_redacao else None,
        "version_number": version_number,
        "feedback_structured": feedback_structured,
        "feedback_structured_source": "fallback",
        "rewrite_checklist_state": {},
        "class_id": class_id,
        "activity_id": activity_id,
        "submitted_at": now,
        "correction_source": "model",
        "is_latest_version": True
    }
    essay_data["schema_version"] = 1
    validate_required_fields("redacoes", essay_data)

    if parent_redacao:
        database.db.redacoes.update_many(
            {"version_group_id": version_group_id},
            {"$set": {"is_latest_version": False}}
        )

    essay_id = database.db.redacoes.insert_one(essay_data).inserted_id
    invalidate_analytics_for_redacao(essay_data)

    def gerar_feedback():
        if not should_use_llm_feedback():
            return

        try:
            feedback = get_llm_feedback(essay, grades, theme)
            structured = validate_structured_feedback_payload(get_structured_llm_feedback(essay, grades, theme))
            database.db.redacoes.update_one(
                {"_id": essay_id},
                {"$set": {
                    "feedback_llm": feedback,
                    "feedback_structured": structured,
                    "feedback_structured_source": "llm",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        except Exception as exc:
            if should_expose_errors():
                app.logger.warning("LLM feedback unavailable for redacao_id=%s: %s", essay_id, exc)
            database.db.redacoes.update_one(
                {"_id": essay_id},
                {"$set": {
                    "feedback_llm": feedback_text_fallback,
                    "feedback_structured_source": "fallback",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )

    Thread(target=gerar_feedback).start()

    return jsonify({"grades": grades, "redacao_id": str(essay_id), "version_number": version_number})


@app.post("/model_ocr")
@require_role("aluno")
def post_model_response_witht_ocr():
    image = request.files['image']
    id_theme = request.form.get('id')
    student_id = current_user_id()
    student_name = current_display_name()
    class_id = request.form.get('class_id')
    activity_id = request.form.get('activity_id')

    essay = get_text(image)

    obj = evaluate_redacao(essay)

    grades = {
        "nota1": float(obj.get('nota_1', 0)),
        "nota2": float(obj.get('nota_2', 0)),
        "nota3": float(obj.get('nota_3', 0)),
        "nota4": float(obj.get('nota_4', 0)),
        "nota5": float(obj.get('nota_5', 0))
    }

    theme = database.get_tema(id_theme)
    now = datetime.now(timezone.utc).isoformat()
    feedback_structured = build_structured_feedback(grades)
    feedback_llm = build_textual_feedback_from_structured(feedback_structured)
    feedback_structured_source = "fallback"
    if should_use_llm_feedback():
        try:
            feedback_llm = get_llm_feedback(essay, grades, theme)
            feedback_structured = validate_structured_feedback_payload(get_structured_llm_feedback(essay, grades, theme))
            feedback_structured_source = "llm"
        except Exception as exc:
            if should_expose_errors():
                app.logger.warning("LLM feedback unavailable for OCR submission: %s", exc)

    essay_data = {
        "titulo": "Redação de imagem",
        "texto": essay,
        "nota_competencia_1_model": grades['nota1'],
        "nota_competencia_2_model": grades['nota2'],
        "nota_competencia_3_model": grades['nota3'],
        "nota_competencia_4_model": grades['nota4'],
        "nota_competencia_5_model": grades['nota5'],
        "nota_total": sum(grades.values()),
        "id_tema": id_theme,
        "student_id": student_id,
        "student_name": student_name,
        "feedback_llm": feedback_llm,
        "created_at": now,
        "updated_at": now,
        "version_group_id": None,
        "parent_redacao_id": None,
        "version_number": 1,
        "feedback_structured": feedback_structured,
        "feedback_structured_source": feedback_structured_source,
        "rewrite_checklist_state": {},
        "class_id": class_id,
        "activity_id": activity_id,
        "submitted_at": now,
        "correction_source": "model",
        "is_latest_version": True
    }
    essay_data["schema_version"] = 1
    validate_required_fields("redacoes", essay_data)

    essays_collection = database.db.redacoes
    essays_collection.insert_one(essay_data).inserted_id
    invalidate_analytics_for_redacao(essay_data)

    persist_essay(essay, obj)
    return jsonify({"grades": obj})


@app.post("/userRegister")
def create_user():
    user_data = request.json

    if 'email' not in user_data or 'password' not in user_data or 'nomeUsuario' not in user_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())

    user_document = {
        **user_data,
        "display_name": user_data['nomeUsuario'],
        "password": hashed_password,
        "tipoUsuario": user_data.get('tipoUsuario', 'usuario'),
    }
    validate_required_fields("users", user_document)

    database.insert_user(user_data, hashed_password)

    return jsonify({"message": "Usuário criado com sucesso"}), 201


@app.post("/userLogin")
def login():
    user_data = request.json

    if 'email' not in user_data or 'password' not in user_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    user = database.login(user_data)

    if user:
        if bcrypt.checkpw(user_data['password'].encode('utf-8'), user['password']):
            return jsonify({
                "userId": str(user.get("_id")),
                "tipoUsuario": user.get('tipoUsuario', 'usuario'),
                "nomeUsuario": user.get('display_name', user.get('email')),
                "token": create_token(user.get("_id"), user.get('display_name', user.get('email')), user.get('tipoUsuario', 'usuario'))
            }), 200
        return jsonify({"error": "E-mail ou senha inválidos"}), 401

    return jsonify({"error": "E-mail ou senha inválidos"}), 401


@app.post("/password-reset/request")
def request_password_reset():
    data = request.json or {}
    email = (data.get("email") or "").strip()

    if not email:
        return password_reset_generic_response()

    if not enforce_password_reset_rate_limit(email):
        return password_reset_rate_limit_response()

    current_user, auth_error = get_optional_current_user()
    if auth_error:
        return auth_error

    if current_user:
        authenticated_user = database.find_user_by_id(current_user.get("user_id"))
        if not authenticated_user or authenticated_user.get("email") != email:
            if PASSWORD_RESET_DEV_MODE:
                print(
                    f"[password-reset] Solicitacao bloqueada: usuario autenticado "
                    f"{current_user.get('user_id')} tentou gerar link para {email}",
                    flush=True
                )
            return jsonify({"error": "Saia da conta atual antes de solicitar redefinição para outro e-mail."}), 403

    user = database.find_user_by_email(email)
    if not user:
        if PASSWORD_RESET_DEV_MODE:
            print(f"[password-reset] Solicitacao ignorada: e-mail nao encontrado ({email})", flush=True)
        return password_reset_generic_response()

    now = datetime.utcnow()
    token = secrets.token_urlsafe(32)
    token_hash = hash_password_reset_token(token)
    expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRATION_MINUTES)

    database.invalidate_password_reset_tokens(user["_id"], now)
    database.create_password_reset_token({
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": expires_at,
        "used_at": None,
        "requester_ip_hash": hash_password_reset_lookup(get_request_ip()),
        "schema_version": 1,
    })

    try:
        send_password_reset_email(user.get("email"), build_password_reset_url(token))
    except Exception as exc:
        print(f"[password-reset] Falha ao preparar envio para {email}: {exc}")

    return password_reset_generic_response()


@app.post("/password-reset/confirm")
def confirm_password_reset():
    data = request.json or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Token e nova senha são obrigatórios."}), 400

    if len(new_password) < 8:
        return jsonify({"error": "A nova senha deve ter pelo menos 8 caracteres."}), 400

    token_document = database.get_password_reset_token(hash_password_reset_token(token))
    now = datetime.utcnow()

    if not token_document or token_document.get("used_at") is not None:
        return jsonify({"error": "Token inválido ou expirado."}), 400

    expires_at = token_document.get("expires_at")
    if not expires_at or expires_at < now:
        return jsonify({"error": "Token inválido ou expirado."}), 400

    user_id = token_document.get("user_id")
    if not user_id or not ObjectId.is_valid(user_id):
        return jsonify({"error": "Token inválido ou expirado."}), 400

    user = database.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "Token inválido ou expirado."}), 400

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    database.update_user_password(user_id, hashed_password)
    database.mark_password_reset_token_used(token_document["_id"], now)

    return jsonify({"message": "Senha redefinida com sucesso."}), 200


@app.get("/users/alunos")
@require_role("professor")
def get_alunos():
    alunos = database.get_alunos()
    return jsonify(alunos)


@app.get("/professores/<teacher_id>/analytics")
@require_role("professor")
def get_professor_analytics(teacher_id):
    current_teacher_id = current_user_id()
    if teacher_id != current_teacher_id:
        return jsonify({"error": "Acesso negado"}), 403
    class_id = request.args.get("class_id")
    activity_id = request.args.get("activity_id")
    group_by = request.args.get("group_by", "activity")
    if class_id and not class_belongs_to_teacher(class_id, current_teacher_id):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403
    if activity_id and not activity_belongs_to_teacher(activity_id, current_teacher_id):
        return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
    cached = get_cached_analytics(current_teacher_id, class_id, activity_id, group_by)
    if cached:
        return jsonify(cached)
    analytics = build_teacher_analytics(current_teacher_id, class_id, activity_id, group_by)
    return jsonify(set_cached_analytics(current_teacher_id, class_id, activity_id, group_by, analytics))


@app.get("/classes")
@require_role("professor")
def get_classes():
    teacher = current_user_id()

    return jsonify(database.get_classes(teacher))


@app.post("/classes")
@require_role("professor")
def create_class():
    data = request.json
    if 'name' not in data:
        return jsonify({"error": "Dados insuficientes"}), 400

    now = datetime.now(timezone.utc).isoformat()
    class_data = {
        "name": data.get("name"),
        "teacher_id": current_user_id(),
        "student_ids": data.get("student_ids", []),
        "created_at": now,
        "updated_at": now,
        "schema_version": 1,
    }
    validate_required_fields("classes", class_data)
    inserted_id = database.create_class(class_data).inserted_id
    invalidate_teacher_analytics(current_user_id())
    class_data["_id"] = str(inserted_id)
    return jsonify(class_data), 201


@app.put("/classes/<id>")
@require_role("professor")
def update_class(id):
    try:
        data = request.json
        teacher = current_user_id()
        if not class_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        data["teacher_id"] = teacher
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = database.update_class(id, data)
        invalidate_teacher_analytics(teacher)

        if result.matched_count == 1:
            return jsonify({"message": "Turma atualizada com sucesso!"}), 200
        return jsonify({"error": "Turma não encontrada"}), 404
    except Exception as e:
        return error_response("Erro ao atualizar turma", 500, e)


@app.delete("/classes/<id>")
@require_role("professor")
def delete_class(id):
    try:
        teacher = current_user_id()
        if not class_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        result = database.delete_class(id)
        invalidate_teacher_analytics(teacher)
        if result.deleted_count == 1:
            return jsonify({"message": "Turma deletada com sucesso!"}), 200
        return jsonify({"error": "Turma não encontrada"}), 404
    except Exception as e:
        return error_response("Erro ao deletar turma", 500, e)


@app.get("/activities")
@require_role("professor")
def get_activities():
    teacher = current_user_id()
    class_id = request.args.get("class_id")
    if class_id and not class_belongs_to_teacher(class_id, teacher):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403

    return jsonify(database.get_activities(teacher, class_id))


@app.post("/activities")
@require_role("professor")
def create_activity():
    data = request.json
    teacher = current_user_id()
    if 'title' not in data or 'class_id' not in data or 'theme_id' not in data:
        return jsonify({"error": "Dados insuficientes"}), 400
    if not class_belongs_to_teacher(data.get("class_id"), teacher):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403
    if not theme_belongs_to_teacher(data.get("theme_id"), teacher):
        return jsonify({"error": "Tema não pertence ao professor informado"}), 403

    now = datetime.now(timezone.utc).isoformat()
    activity_data = {
        "title": data.get("title"),
        "teacher_id": teacher,
        "class_id": data.get("class_id"),
        "theme_id": data.get("theme_id"),
        "due_date": data.get("due_date", ""),
        "created_at": now,
        "updated_at": now,
        "schema_version": 1,
    }
    validate_required_fields("activities", activity_data)
    inserted_id = database.create_activity(activity_data).inserted_id
    invalidate_teacher_analytics(teacher)
    activity_data["_id"] = str(inserted_id)
    return jsonify(activity_data), 201


@app.put("/activities/<id>")
@require_role("professor")
def update_activity(id):
    try:
        data = request.json
        teacher = current_user_id()
        if not activity_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
        if data.get("class_id") and not class_belongs_to_teacher(data.get("class_id"), teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        if data.get("theme_id") and not theme_belongs_to_teacher(data.get("theme_id"), teacher):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        data["teacher_id"] = teacher
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = database.update_activity(id, data)
        invalidate_teacher_analytics(teacher)

        if result.matched_count == 1:
            return jsonify({"message": "Atividade atualizada com sucesso!"}), 200
        return jsonify({"error": "Atividade não encontrada"}), 404
    except Exception as e:
        return error_response("Erro ao atualizar atividade", 500, e)


@app.delete("/activities/<id>")
@require_role("professor")
def delete_activity(id):
    try:
        teacher = current_user_id()
        if not activity_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
        result = database.delete_activity(id)
        invalidate_teacher_analytics(teacher)
        if result.deleted_count == 1:
            return jsonify({"message": "Atividade deletada com sucesso!"}), 200
        return jsonify({"error": "Atividade não encontrada"}), 404
    except Exception as e:
        return error_response("Erro ao deletar atividade", 500, e)


@app.get("/activities/<id>/submissions")
@require_role("professor")
def get_activity_submissions(id):
    teacher = current_user_id()
    if not activity_belongs_to_teacher(id, teacher):
        return jsonify({"error": "Atividade não pertence ao professor informado"}), 403

    if not ObjectId.is_valid(id):
        return jsonify({"error": "ID inválido"}), 400

    status = build_activity_submission_status(id)
    if not status:
        return jsonify({"error": "Atividade não encontrada"}), 404

    return jsonify(status)


@app.get("/temas")
@require_auth
def get_temas():
    temas = database.get_temas()
    if g.current_user.get("tipoUsuario") == "professor":
        temas = [tema for tema in temas if tema.get("teacher_id") == current_user_id()]
    return jsonify(temas)


@app.post("/temas")
@require_role("professor")
def create_tema():
    tema_data = request.json
    if 'tema' not in tema_data or 'descricao' not in tema_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    tema_data["teacher_id"] = current_user_id()
    tema_data["teacher_name"] = current_display_name()
    validate_required_fields("temas", tema_data)
    database.create_tema(tema_data)
    invalidate_teacher_analytics(current_user_id())
    return jsonify({"message": "Tema criado com sucesso"}), 201


@app.get("/students/<student_id>/activities")
@require_role("aluno")
def get_student_activities(student_id):
    if student_id != current_user_id():
        return jsonify({"error": "Acesso negado"}), 403
    classes = list(database.db.classes.find({"student_ids": student_id}))
    class_ids = [str(item["_id"]) for item in classes]
    activities = list(database.db.activities.find({"class_id": {"$in": class_ids}}))
    theme_ids = [item.get("theme_id") for item in activities]
    themes = {
        str(item["_id"]): item
        for item in database.db.temas.find({"_id": {"$in": [ObjectId(value) for value in theme_ids if ObjectId.is_valid(value)]}})
    }
    submitted = {
        item.get("activity_id")
        for item in database.db.redacoes.find({"student_id": student_id, "activity_id": {"$in": [str(item["_id"]) for item in activities]}})
    }
    class_map = {str(item["_id"]): item for item in classes}

    result = []
    today = datetime.now(timezone.utc).date().isoformat()
    for activity in activities:
        activity_id = str(activity["_id"])
        class_doc = class_map.get(activity.get("class_id"), {})
        theme = themes.get(activity.get("theme_id"), {})
        status = "submitted" if activity_id in submitted else "pending"
        if status == "pending" and activity.get("due_date") and activity.get("due_date") < today:
            status = "late"

        result.append({
            "_id": activity_id,
            "title": activity.get("title"),
            "theme_id": activity.get("theme_id"),
            "theme": theme.get("tema", "Tema não encontrado"),
            "description": theme.get("descricao", ""),
            "class_id": activity.get("class_id"),
            "class_name": class_doc.get("name", "Turma não encontrada"),
            "due_date": activity.get("due_date", ""),
            "status": status,
        })

    return jsonify(result)


@app.put("/redacoes/<id>/rewrite-checklist")
@require_role("aluno")
def update_rewrite_checklist(id):
    try:
        redacao, response = get_authorized_redacao_or_404(id)
        if response:
            return response
        if redacao.get("student_id") != current_user_id():
            return jsonify({"error": "Acesso negado"}), 403
        data = request.json
        state = data.get("rewrite_checklist_state", {})
        result = database.db.redacoes.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "rewrite_checklist_state": state,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

        if result.matched_count == 1:
            return jsonify({"message": "Checklist atualizado com sucesso!"}), 200
        return jsonify({"error": "Redação não encontrada"}), 404
    except Exception as e:
        return error_response("Erro ao atualizar checklist", 500, e)


@app.put("/temas/<id>")
@require_role("professor")
def update_tema(id):
    try:
        if not theme_belongs_to_teacher(id, current_user_id()):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        object_id = ObjectId(id)
        data = request.json
        data["teacher_id"] = current_user_id()
        data["teacher_name"] = current_display_name()

        result = database.update_tema(object_id, data)
        invalidate_teacher_analytics(current_user_id())

        if result.matched_count == 1:
            if result.modified_count == 1:
                return jsonify({"message": "Tema atualizado com sucesso!"}), 200
            else:
                return jsonify({"message": "Nada foi atualizado."}), 304
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return error_response("Erro ao atualizar tema", 500, e)


@app.delete("/temas/<id>")
@require_role("professor")
def delete_tema(id):
    try:
        if not theme_belongs_to_teacher(id, current_user_id()):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        object_id = ObjectId(id)
        result = database.delete_tema(object_id)
        invalidate_teacher_analytics(current_user_id())

        if result.deleted_count == 1:
            return jsonify({"message": "Tema deletado com sucesso!"}), 200
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return error_response("Erro ao deletar tema", 500, e)


@app.get("/redacoes")
@require_auth
def get_redacoes():
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 20)
    if g.current_user.get("tipoUsuario") == "aluno":
        redacoes = database.get_redacoes_page_for_student(current_user_id(), page, page_size)
    elif g.current_user.get("tipoUsuario") == "professor":
        student = request.args.get("student")
        redacoes = database.get_redacoes_page_for_teacher(current_user_id(), page, page_size, student)
    else:
        redacoes = {"items": [], "page": int(page), "page_size": int(page_size), "total": 0}
    return jsonify(redacoes)


@app.post("/redacoes")
@require_role("aluno")
def create_redacao():
    redacao_data = request.json
    if 'titulo_redacao' not in redacao_data or 'id_tema' not in redacao_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    redacao_data["student_id"] = current_user_id()
    redacao_data["student_name"] = current_display_name()
    database.create_redacoes(redacao_data)
    return jsonify({"message": "Redação criada com sucesso"}), 201


@app.get("/redacoes/<id>")
@require_auth
def get_redacao_by_id(id):
    redacao, response = get_authorized_redacao_or_404(id)
    if response:
        return response
    return jsonify(database.serialize_redacao(redacao))

@app.get("/redacoes/<id>/versions")
@require_auth
def get_redacao_versions(id):
    redacao, response = get_authorized_redacao_or_404(id)
    if response:
        return response
    redacoes = database.get_redacao_versions(id)
    allowed = [item for item in redacoes if redacao_belongs_to_user(item, g.current_user)]
    return jsonify(allowed)


@app.put("/redacoes/<id>")
@require_role("professor")
def update_redacao(id):
    try:
        redacao, response = get_authorized_redacao_or_404(id)
        if response:
            return response
        data = request.json
        redacao_before = database.get_redacao_document(id)
        result = database.update_redacao(id, data)
        invalidate_analytics_for_redacao(redacao_before)

        if result.matched_count == 1:
            if result.modified_count == 1:
                return jsonify({"message": "Redacao atualizado com sucesso!"}), 200
            else:
                return jsonify({"message": "Nada foi atualizado."}), 304
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return error_response("Erro ao atualizar redação", 500, e)


if __name__ == "__main__":
  from support import use_vectorizer
  debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
  app.run(host='0.0.0.0', port=5000, debug=debug)
