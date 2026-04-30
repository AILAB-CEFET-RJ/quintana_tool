import database
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from functions import evaluate_redacao, persist_essay, get_text
from llm import get_llm_feedback
from pedagogy import build_structured_feedback
from analytics import build_teacher_analytics
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


@app.route("/")
def health():
    return ("OK!", 200)


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
        "rewrite_checklist_state": {},
        "class_id": class_id,
        "activity_id": activity_id,
        "submitted_at": now,
        "correction_source": "model",
        "is_latest_version": True
    }

    if parent_redacao:
        database.db.redacoes.update_many(
            {"version_group_id": version_group_id},
            {"$set": {"is_latest_version": False}}
        )

    essay_id = database.db.redacoes.insert_one(essay_data).inserted_id

    def gerar_feedback():
        try:
            feedback = get_llm_feedback(essay, grades, theme)
            database.db.redacoes.update_one(
                {"_id": essay_id},
                {"$set": {
                    "feedback_llm": feedback,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        except Exception as exc:
            database.db.redacoes.update_one(
                {"_id": essay_id},
                {"$set": {
                    "feedback_llm": f"Feedback textual indisponível no momento: {exc}",
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

    feedback_llm = get_llm_feedback(essay, grades)

    now = datetime.now(timezone.utc).isoformat()
    feedback_structured = build_structured_feedback(grades)

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
        "rewrite_checklist_state": {},
        "class_id": class_id,
        "activity_id": activity_id,
        "submitted_at": now,
        "correction_source": "model",
        "is_latest_version": True
    }

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
    analytics = build_teacher_analytics(nome_professor, class_id, activity_id)
    return jsonify(analytics)


@app.get("/temas")
def get_temas():
    temas = database.get_temas()
    return jsonify(temas)


@app.post("/temas")
def create_tema():
    tema_data = request.json
    if 'nome_professor' not in tema_data or 'tema' not in tema_data or 'descricao' not in tema_data:
        return jsonify({"error": "Dados insuficientes"}), 400

    database.create_tema(tema_data)
    return jsonify({"message": "Tema criado com sucesso"}), 201


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
  debug = True # com essa opção como True, ao salvar, o "site" recarrega automaticamente.
  app.run(host='0.0.0.0', port=5000, debug=debug)
