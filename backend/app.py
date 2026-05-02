import database
from flask import Flask, request, jsonify
from bson import ObjectId
from functions import evaluate_redacao, persist_essay, get_text
from llm import get_llm_feedback, get_structured_llm_feedback
from pedagogy import build_structured_feedback
from analytics import build_teacher_analytics
from schemas import validate_required_fields
from flask_cors import CORS
import bcrypt
import os
from threading import Thread
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app) 


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


@app.route("/")
def health():
    db_ok, db_error = database.check_db_connection()
    status = {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else f"unavailable: {db_error}",
    }
    return jsonify(status), 200 if db_ok else 503


@app.post("/model")
def post_model_response():
    essay = request.json['essay']
    id_theme = request.json['id']
    student = request.json['aluno']
    rewrite_of = request.json.get('rewrite_of')
    class_id = request.json.get('class_id')
    activity_id = request.json.get('activity_id')

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
        "feedback_llm": "",
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

    def gerar_feedback():
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
            database.db.redacoes.update_one(
                {"_id": essay_id},
                {"$set": {
                    "feedback_llm": f"Feedback textual indisponível no momento: {exc}",
                    "feedback_structured_source": "fallback",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )

    Thread(target=gerar_feedback).start()

    response = jsonify({"grades": grades, "redacao_id": str(essay_id), "version_number": version_number})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.post("/model_ocr")
def post_model_response_witht_ocr():
    print("model_ocr")
    image = request.files['image']
    print('imagem', image)
    id_theme = request.form.get('id')
    student = request.form.get('aluno')
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
    try:
        feedback_llm = get_llm_feedback(essay, grades, theme)
    except Exception as exc:
        feedback_llm = f"Feedback textual indisponível no momento: {exc}"

    now = datetime.now(timezone.utc).isoformat()
    feedback_structured = build_structured_feedback(grades)
    feedback_structured_source = "fallback"
    try:
        feedback_structured = validate_structured_feedback_payload(get_structured_llm_feedback(essay, grades, theme))
        feedback_structured_source = "llm"
    except Exception:
        pass

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

    response = jsonify({"grades": obj})
    response.headers.add('Access-Control-Allow-Origin', '*')

    persist_essay(essay, obj)
    return response


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
                "nomeUsuario": user.get('username')
            }), 200
        else:
            return jsonify({"error": "Email ou senha incorretos"}), 401

    return jsonify({"error": "Usuário não encontrado"}), 404


@app.get("/users/alunos")
def get_alunos():
    alunos = database.get_alunos()
    response = jsonify(alunos)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.get("/professores/<nome_professor>/analytics")
def get_professor_analytics(nome_professor):
    class_id = request.args.get("class_id")
    activity_id = request.args.get("activity_id")
    group_by = request.args.get("group_by", "activity")
    analytics = build_teacher_analytics(nome_professor, class_id, activity_id, group_by)
    return jsonify(analytics)


@app.get("/classes")
def get_classes():
    teacher = request.args.get("teacher")
    if not teacher:
        return jsonify({"error": "teacher é obrigatório"}), 400

    return jsonify(database.get_classes(teacher))


@app.post("/classes")
def create_class():
    data = request.json
    if 'teacher' not in data or 'name' not in data:
        return jsonify({"error": "Dados insuficientes"}), 400

    now = datetime.now(timezone.utc).isoformat()
    class_data = {
        "name": data.get("name"),
        "teacher": data.get("teacher"),
        "students": data.get("students", []),
        "created_at": now,
        "updated_at": now,
        "schema_version": 1,
    }
    validate_required_fields("classes", class_data)
    inserted_id = database.create_class(class_data).inserted_id
    class_data["_id"] = str(inserted_id)
    return jsonify(class_data), 201


@app.put("/classes/<id>")
def update_class(id):
    try:
        data = request.json
        teacher = data.get("teacher")
        if teacher and not class_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = database.update_class(id, data)

        if result.matched_count == 1:
            return jsonify({"message": "Turma atualizada com sucesso!"}), 200
        return jsonify({"error": "Turma não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/classes/<id>")
def delete_class(id):
    try:
        teacher = request.args.get("teacher")
        if teacher and not class_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Turma não pertence ao professor informado"}), 403
        result = database.delete_class(id)
        if result.deleted_count == 1:
            return jsonify({"message": "Turma deletada com sucesso!"}), 200
        return jsonify({"error": "Turma não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/activities")
def get_activities():
    teacher = request.args.get("teacher")
    class_id = request.args.get("class_id")
    if not teacher:
        return jsonify({"error": "teacher é obrigatório"}), 400

    return jsonify(database.get_activities(teacher, class_id))


@app.post("/activities")
def create_activity():
    data = request.json
    if 'teacher' not in data or 'title' not in data or 'class_id' not in data or 'theme_id' not in data:
        return jsonify({"error": "Dados insuficientes"}), 400

    now = datetime.now(timezone.utc).isoformat()
    activity_data = {
        "title": data.get("title"),
        "teacher": data.get("teacher"),
        "class_id": data.get("class_id"),
        "theme_id": data.get("theme_id"),
        "due_date": data.get("due_date", ""),
        "created_at": now,
        "updated_at": now,
        "schema_version": 1,
    }
    validate_required_fields("activities", activity_data)
    inserted_id = database.create_activity(activity_data).inserted_id
    activity_data["_id"] = str(inserted_id)
    return jsonify(activity_data), 201


@app.put("/activities/<id>")
def update_activity(id):
    try:
        data = request.json
        teacher = data.get("teacher")
        if teacher and not activity_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = database.update_activity(id, data)

        if result.matched_count == 1:
            return jsonify({"message": "Atividade atualizada com sucesso!"}), 200
        return jsonify({"error": "Atividade não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/activities/<id>")
def delete_activity(id):
    try:
        teacher = request.args.get("teacher")
        if teacher and not activity_belongs_to_teacher(id, teacher):
            return jsonify({"error": "Atividade não pertence ao professor informado"}), 403
        result = database.delete_activity(id)
        if result.deleted_count == 1:
            return jsonify({"message": "Atividade deletada com sucesso!"}), 200
        return jsonify({"error": "Atividade não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/activities/<id>/submissions")
def get_activity_submissions(id):
    teacher = request.args.get("teacher")
    if teacher and not activity_belongs_to_teacher(id, teacher):
        return jsonify({"error": "Atividade não pertence ao professor informado"}), 403

    if not ObjectId.is_valid(id):
        return jsonify({"error": "ID inválido"}), 400

    status = build_activity_submission_status(id)
    if not status:
        return jsonify({"error": "Atividade não encontrada"}), 404

    return jsonify(status)


@app.get("/temas")
def get_temas():
    temas = database.get_temas()
    return jsonify(temas)


@app.post("/temas")
def create_tema():
    tema_data = request.json
    if 'nome_professor' not in tema_data or 'tema' not in tema_data or 'descricao' not in tema_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    validate_required_fields("temas", tema_data)
    database.create_tema(tema_data)
    return jsonify({"message": "Tema criado com sucesso"}), 201


@app.get("/students/<username>/activities")
def get_student_activities(username):
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
def update_rewrite_checklist(id):
    try:
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
        return jsonify({"error": str(e)}), 500


@app.put("/temas/<id>")
def update_tema(id):
    try:
        object_id = ObjectId(id)
        data = request.json

        result = database.update_tema(object_id, data)

        if result.matched_count == 1:
            if result.modified_count == 1:
                return jsonify({"message": "Tema atualizado com sucesso!"}), 200
            else:
                return jsonify({"message": "Nada foi atualizado."}), 304
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/temas/<id>")
def delete_tema(id):
    try:
        object_id = ObjectId(id)
        result = database.delete_tema(object_id)

        if result.deleted_count == 1:
            return jsonify({"message": "Tema deletado com sucesso!"}), 200
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/redacoes")
def get_redacoes():
    user_name = request.args.get("user")
    redacoes = database.get_redacoes(user_name)
    return jsonify(redacoes)


@app.post("/redacoes")
def create_redacao():
    redacao_data = request.json
    if 'titulo_redacao' not in redacao_data or 'id_tema' not in redacao_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    database.create_redacoes(redacao_data)
    return jsonify({"message": "Redação criada com sucesso"}), 201


@app.get("/redacoes/<id>")
def get_redacao_by_id(id):
    redacao = database.get_redacao_by_id(id)
    return jsonify(redacao)

@app.get("/redacoes/<id>/versions")
def get_redacao_versions(id):
    redacoes = database.get_redacao_versions(id)
    return jsonify(redacoes)


@app.put("/redacoes/<id>")
def update_redacao(id):
    try:
        data = request.json
        result = database.update_redacao(id, data)

        if result.matched_count == 1:
            if result.modified_count == 1:
                return jsonify({"message": "Redacao atualizado com sucesso!"}), 200
            else:
                return jsonify({"message": "Nada foi atualizado."}), 304
        else:
            return jsonify({"error": "Tema não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  from support import use_vectorizer
  debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
  app.run(host='0.0.0.0', port=5000, debug=debug)
