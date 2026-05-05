import database
from flask import Flask, g, request, jsonify
from bson import ObjectId
from functions import evaluate_redacao, persist_essay, get_text
from llm import get_llm_feedback, get_structured_llm_feedback
from pedagogy import build_structured_feedback, build_textual_feedback_from_structured
from analytics import build_teacher_analytics
from schemas import validate_required_fields
from flask_cors import CORS
from config import get_cors_origins, should_expose_errors
from auth import create_token, require_auth, require_role
from analytics_cache import get_cached_analytics, invalidate_teacher_analytics, set_cached_analytics
import bcrypt
import os
from threading import Thread
from datetime import datetime, timezone

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


def activity_belongs_to_teacher(activity_id, teacher):
    if not activity_id or not ObjectId.is_valid(activity_id):
        return False
    return database.db.activities.find_one({"_id": ObjectId(activity_id), "teacher": teacher}) is not None


def class_belongs_to_teacher(class_id, teacher):
    if not class_id or not ObjectId.is_valid(class_id):
        return False
    return database.db.classes.find_one({"_id": ObjectId(class_id), "teacher": teacher}) is not None


def theme_belongs_to_teacher(theme_id, teacher):
    if not theme_id or not ObjectId.is_valid(theme_id):
        return False
    return database.db.temas.find_one({"_id": ObjectId(theme_id), "nome_professor": teacher}) is not None


def redacao_belongs_to_user(redacao, user):
    if not redacao or not user:
        return False

    username = user.get("username")
    role = user.get("tipoUsuario")
    if role == "aluno":
        return redacao.get("aluno") == username

    if role == "professor":
        if theme_belongs_to_teacher(redacao.get("id_tema"), username):
            return True
        if class_belongs_to_teacher(redacao.get("class_id"), username):
            return True
        if activity_belongs_to_teacher(redacao.get("activity_id"), username):
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
        theme = database.db.temas.find_one({"_id": ObjectId(theme_id)}, {"nome_professor": 1})
        if theme and theme.get("nome_professor"):
            teachers.add(theme["nome_professor"])

    class_id = redacao.get("class_id")
    if class_id and ObjectId.is_valid(class_id):
        class_doc = database.db.classes.find_one({"_id": ObjectId(class_id)}, {"teacher": 1})
        if class_doc and class_doc.get("teacher"):
            teachers.add(class_doc["teacher"])

    activity_id = redacao.get("activity_id")
    if activity_id and ObjectId.is_valid(activity_id):
        activity = database.db.activities.find_one({"_id": ObjectId(activity_id)}, {"teacher": 1})
        if activity and activity.get("teacher"):
            teachers.add(activity["teacher"])

    for teacher in teachers:
        invalidate_teacher_analytics(teacher)


def build_activity_submission_status(activity_id):
    activity = database.db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        return None

    class_doc = database.db.classes.find_one({"_id": ObjectId(activity.get("class_id"))}) if ObjectId.is_valid(activity.get("class_id", "")) else None
    theme = database.db.temas.find_one({"_id": ObjectId(activity.get("theme_id"))}) if ObjectId.is_valid(activity.get("theme_id", "")) else None
    expected_students = sorted(class_doc.get("students", [])) if class_doc else []
    redacoes = list(database.db.redacoes.find({"activity_id": activity_id}))
    submitted_students = sorted(set(redacao.get("aluno") for redacao in redacoes if redacao.get("aluno")))
    missing_students = sorted(set(expected_students) - set(submitted_students))
    due_date = activity.get("due_date", "")
    today = datetime.now(timezone.utc).date().isoformat()
    late_students = missing_students if due_date and due_date < today else []

    return {
        "activity": {
            "_id": str(activity["_id"]),
            "title": activity.get("title"),
            "teacher": activity.get("teacher"),
            "class_id": activity.get("class_id"),
            "class_name": class_doc.get("name") if class_doc else "Turma não encontrada",
            "theme_id": activity.get("theme_id"),
            "theme": theme.get("tema") if theme else "Tema não encontrado",
            "due_date": due_date,
        },
        "expected_students": expected_students,
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
    student = g.current_user["username"]
    rewrite_of = request.json.get('rewrite_of')
    class_id = request.json.get('class_id')
    activity_id = request.json.get('activity_id')
    if rewrite_of:
        parent_candidate = database.get_redacao_document(rewrite_of) if ObjectId.is_valid(rewrite_of) else None
        if not parent_candidate or parent_candidate.get("aluno") != student:
            return jsonify({"error": "Redação de origem inválida"}), 403

    lines = essay.split('\n')
    title = lines[0] if lines else "Título não fornecido"
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
        "aluno": student,
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
    student = g.current_user["username"]
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
        "aluno": student,
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
        "username": user_data['nomeUsuario'],
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
                "tipoUsuario": user.get('tipoUsuario', 'usuario'),
                "nomeUsuario": user.get('username'),
                "token": create_token(user.get('username'), user.get('tipoUsuario', 'usuario'))
            }), 200
        return jsonify({"error": "E-mail ou senha inválidos"}), 401

    return jsonify({"error": "E-mail ou senha inválidos"}), 401


@app.get("/users/alunos")
@require_role("professor")
def get_alunos():
    alunos = database.get_alunos()
    return jsonify(alunos)


@app.get("/professores/<nome_professor>/analytics")
@require_role("professor")
def get_professor_analytics(nome_professor):
    if nome_professor != g.current_user["username"]:
        return jsonify({"error": "Acesso negado"}), 403
    class_id = request.args.get("class_id")
    activity_id = request.args.get("activity_id")
    group_by = request.args.get("group_by", "activity")
    if class_id and not class_belongs_to_teacher(class_id, nome_professor):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403
    if activity_id and not activity_belongs_to_teacher(activity_id, nome_professor):
        return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
    cached = get_cached_analytics(nome_professor, class_id, activity_id, group_by)
    if cached:
        return jsonify(cached)
    analytics = build_teacher_analytics(nome_professor, class_id, activity_id, group_by)
    return jsonify(set_cached_analytics(nome_professor, class_id, activity_id, group_by, analytics))


@app.get("/classes")
@require_role("professor")
def get_classes():
    teacher = g.current_user["username"]

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
        "teacher": g.current_user["username"],
        "students": data.get("students", []),
        "created_at": now,
        "updated_at": now,
        "schema_version": 1,
    }
    validate_required_fields("classes", class_data)
    inserted_id = database.create_class(class_data).inserted_id
    invalidate_teacher_analytics(g.current_user["username"])
    class_data["_id"] = str(inserted_id)
    return jsonify(class_data), 201


@app.put("/classes/<id>")
@require_role("professor")
def update_class(id):
    try:
        data = request.json
        teacher = g.current_user["username"]
        if not class_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        data["teacher"] = teacher
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
        teacher = g.current_user["username"]
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
    teacher = g.current_user["username"]
    class_id = request.args.get("class_id")
    if class_id and not class_belongs_to_teacher(class_id, teacher):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403

    return jsonify(database.get_activities(teacher, class_id))


@app.post("/activities")
@require_role("professor")
def create_activity():
    data = request.json
    teacher = g.current_user["username"]
    if 'title' not in data or 'class_id' not in data or 'theme_id' not in data:
        return jsonify({"error": "Dados insuficientes"}), 400
    if not class_belongs_to_teacher(data.get("class_id"), teacher):
        return jsonify({"error": "Turma não pertence ao professor informado"}), 403
    if not theme_belongs_to_teacher(data.get("theme_id"), teacher):
        return jsonify({"error": "Tema não pertence ao professor informado"}), 403

    now = datetime.now(timezone.utc).isoformat()
    activity_data = {
        "title": data.get("title"),
        "teacher": teacher,
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
        teacher = g.current_user["username"]
        if not activity_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
        if data.get("class_id") and not class_belongs_to_teacher(data.get("class_id"), teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        if data.get("theme_id") and not theme_belongs_to_teacher(data.get("theme_id"), teacher):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        data["teacher"] = teacher
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
        teacher = g.current_user["username"]
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
    teacher = g.current_user["username"]
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
        temas = [tema for tema in temas if tema.get("nome_professor") == g.current_user["username"]]
    return jsonify(temas)


@app.post("/temas")
@require_role("professor")
def create_tema():
    tema_data = request.json
    if 'tema' not in tema_data or 'descricao' not in tema_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    tema_data["nome_professor"] = g.current_user["username"]
    validate_required_fields("temas", tema_data)
    database.create_tema(tema_data)
    invalidate_teacher_analytics(g.current_user["username"])
    return jsonify({"message": "Tema criado com sucesso"}), 201


@app.get("/students/<username>/activities")
@require_role("aluno")
def get_student_activities(username):
    if username != g.current_user["username"]:
        return jsonify({"error": "Acesso negado"}), 403
    classes = list(database.db.classes.find({"students": username}))
    class_ids = [str(item["_id"]) for item in classes]
    activities = list(database.db.activities.find({"class_id": {"$in": class_ids}}))
    theme_ids = [item.get("theme_id") for item in activities]
    themes = {
        str(item["_id"]): item
        for item in database.db.temas.find({"_id": {"$in": [ObjectId(value) for value in theme_ids if ObjectId.is_valid(value)]}})
    }
    submitted = {
        item.get("activity_id")
        for item in database.db.redacoes.find({"aluno": username, "activity_id": {"$in": [str(item["_id"]) for item in activities]}})
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
        if redacao.get("aluno") != g.current_user["username"]:
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
        if not theme_belongs_to_teacher(id, g.current_user["username"]):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        object_id = ObjectId(id)
        data = request.json
        data["nome_professor"] = g.current_user["username"]

        result = database.update_tema(object_id, data)
        invalidate_teacher_analytics(g.current_user["username"])

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
        if not theme_belongs_to_teacher(id, g.current_user["username"]):
            return jsonify({"error": "Tema não pertence ao professor informado"}), 403
        object_id = ObjectId(id)
        result = database.delete_tema(object_id)
        invalidate_teacher_analytics(g.current_user["username"])

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
        redacoes = database.get_redacoes_page_for_student(g.current_user["username"], page, page_size)
    elif g.current_user.get("tipoUsuario") == "professor":
        student = request.args.get("student")
        redacoes = database.get_redacoes_page_for_teacher(g.current_user["username"], page, page_size, student)
    else:
        redacoes = {"items": [], "page": int(page), "page_size": int(page_size), "total": 0}
    return jsonify(redacoes)


@app.post("/redacoes")
@require_role("aluno")
def create_redacao():
    redacao_data = request.json
    if 'titulo_redacao' not in redacao_data or 'id_tema' not in redacao_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    redacao_data["aluno"] = g.current_user["username"]
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
