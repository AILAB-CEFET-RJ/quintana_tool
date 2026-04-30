from pymongo import MongoClient
from bson import ObjectId
import os

mongo_uri = os.getenv('MONGO_URI')

client = MongoClient(mongo_uri)
db = client.textgrader

def create_tema(data):
    temas_collection = db.temas
    temas_collection.insert_one(data)

def get_temas():
    temas_collection = db.temas
    temas = list(temas_collection.find())
    for tema in temas:
        tema['_id'] = str(tema['_id'])

    return temas

def get_tema(id):
    temas_collection = db.temas
    tema = temas_collection.find_one({"_id": ObjectId(id)})
    tema['_id'] = str(tema['_id'])
    return tema['descricao']

def insert_user(user_data, password):
    users_collection = db.users

    users_collection.insert_one({
        "email": user_data['email'],
        "password": password,
        "username": user_data['nomeUsuario'],
        "tipoUsuario": user_data.get('tipoUsuario', 'usuario')
    })

def login(user_data):
    users_collection = db.users
    return users_collection.find_one({"email": user_data['email']})

def get_alunos():
    users_collection = db.users
    alunos = list(users_collection.find({"tipoUsuario": "aluno"}))

    for aluno in alunos:
        aluno['_id'] = str(aluno['_id'])  # Convertendo ObjectId para string
        aluno.pop('password', None)  # Remove o campo 'password' para evitar problemas com bytes

    return alunos

def update_tema(id, data):
    temas_collection = db.temas

    object_id = ObjectId(id)
    result = temas_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "tema": data.get("tema"),
            "descricao": data.get("descricao"),
            "nome_professor": data.get("nome_professor")
        }}
    )

    return result

def delete_tema(id):
    temas_collection = db.temas
    return temas_collection.delete_one({"_id": id})

def get_redacoes(user_name):
    redacoes_collection = db.redacoes
    if user_name is not None:
        redacoes = list(redacoes_collection.find({"aluno": user_name}))
    else:
        redacoes = list(redacoes_collection.find())
    for redacao in redacoes:
        redacao['_id'] = str(redacao['_id'])
    return redacoes

def create_redacoes(data):
    redacoes_collection = db.redacoes
    redacoes_collection.insert_one(data)

def get_redacao_by_id(id):
    redacoes_collection = db.redacoes
    redacao = redacoes_collection.find_one({"_id": ObjectId(id)})
    redacao['_id'] = str(redacao['_id'])
    return redacao

def get_redacao_document(id):
    redacoes_collection = db.redacoes
    return redacoes_collection.find_one({"_id": ObjectId(id)})

def serialize_redacao(redacao):
    redacao['_id'] = str(redacao['_id'])
    return redacao

def get_redacao_versions(id):
    redacoes_collection = db.redacoes
    redacao = redacoes_collection.find_one({"_id": ObjectId(id)})

    if not redacao:
        return []

    redacao_id = str(redacao['_id'])
    version_group_id = redacao.get("version_group_id") or redacao_id

    redacoes = list(redacoes_collection.find({
        "$or": [
            {"version_group_id": version_group_id},
            {"_id": ObjectId(version_group_id) if ObjectId.is_valid(version_group_id) else ObjectId(id)}
        ]
    }))

    for item in redacoes:
        if "version_number" not in item:
            item["version_number"] = 1
        serialize_redacao(item)

    return sorted(redacoes, key=lambda item: (item.get("version_number", 1), item.get("created_at", "")))

def update_redacao(id, data):
    redacoes_collection = db.redacoes
    object_id = ObjectId(id)
        

    result = redacoes_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "nome_professor": data.get("nome_professor"),
            "nota_competencia_1_professor": data.get("nota_competencia_1_professor"),
            "nota_competencia_2_professor": data.get("nota_competencia_2_professor"),
            "nota_competencia_3_professor": data.get("nota_competencia_3_professor"),
            "nota_competencia_4_professor": data.get("nota_competencia_4_professor"),
            "nota_competencia_5_professor": data.get("nota_competencia_5_professor"),
            "feedback_professor": data.get("feedback_professor"),
            "nota_professor": float(data.get("nota_competencia_1_professor")) + float(data.get(
                "nota_competencia_2_professor")) + float(data.get("nota_competencia_3_professor")) + float(data.get(
                "nota_competencia_4_professor")) + float(data.get("nota_competencia_5_professor")),
        }}
    )

    return result
