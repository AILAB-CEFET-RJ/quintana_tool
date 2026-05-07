from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
import certifi
from config import MONGO_DB_NAME, MONGO_URI

mongo_uri = MONGO_URI

mongo_options = {"serverSelectionTimeoutMS": 20000}
if mongo_uri and (mongo_uri.startswith("mongodb+srv://") or "mongodb.net" in mongo_uri):
    mongo_options.update({"tls": True, "tlsCAFile": certifi.where()})

client = MongoClient(mongo_uri, **mongo_options)
db = client[MONGO_DB_NAME]

REDACAO_LIST_PROJECTION = {
    "titulo": 1,
    "nota_total": 1,
    "id_tema": 1,
    "student_id": 1,
    "student_name": 1,
    "nota_competencia_1_model": 1,
    "nota_competencia_2_model": 1,
    "nota_competencia_3_model": 1,
    "nota_competencia_4_model": 1,
    "nota_competencia_5_model": 1,
    "nota_professor": 1,
    "nota_competencia_1_professor": 1,
    "nota_competencia_2_professor": 1,
    "nota_competencia_3_professor": 1,
    "nota_competencia_4_professor": 1,
    "nota_competencia_5_professor": 1,
    "created_at": 1,
    "updated_at": 1,
    "submitted_at": 1,
    "version_group_id": 1,
    "parent_redacao_id": 1,
    "version_number": 1,
    "class_id": 1,
    "activity_id": 1,
    "correction_source": 1,
    "is_latest_version": 1,
}


def check_db_connection():
    try:
        client.admin.command('ping')
        return True, None
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return False, str(e)

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
        "display_name": user_data['nomeUsuario'],
        "tipoUsuario": user_data.get('tipoUsuario', 'usuario'),
        "schema_version": 1
    })

def login(user_data):
    users_collection = db.users
    return users_collection.find_one({"email": user_data['email']})

def find_user_by_email(email):
    users_collection = db.users
    return users_collection.find_one({"email": email})

def find_user_by_id(user_id):
    users_collection = db.users
    return users_collection.find_one({"_id": ObjectId(user_id)}) if user_id and ObjectId.is_valid(str(user_id)) else None

def update_user_password(user_id, hashed_password):
    users_collection = db.users
    return users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password}}
    )

def ensure_password_reset_indexes():
    db.password_reset_tokens.create_index("token_hash", unique=True)
    db.password_reset_tokens.create_index("user_id")
    db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)

def ensure_password_reset_attempt_indexes():
    db.password_reset_attempts.create_index([("kind", 1), ("key_hash", 1), ("created_at", -1)])
    db.password_reset_attempts.create_index("created_at", expireAfterSeconds=86400)

def count_password_reset_attempts(kind, key_hash, since):
    ensure_password_reset_attempt_indexes()
    return db.password_reset_attempts.count_documents({
        "kind": kind,
        "key_hash": key_hash,
        "created_at": {"$gte": since},
    })

def create_password_reset_attempt(document):
    ensure_password_reset_attempt_indexes()
    return db.password_reset_attempts.insert_one(document)

def invalidate_password_reset_tokens(user_id, used_at):
    return db.password_reset_tokens.update_many(
        {"user_id": str(user_id), "used_at": None},
        {"$set": {"used_at": used_at}}
    )

def create_password_reset_token(document):
    ensure_password_reset_indexes()
    return db.password_reset_tokens.insert_one(document)

def get_password_reset_token(token_hash):
    ensure_password_reset_indexes()
    return db.password_reset_tokens.find_one({"token_hash": token_hash})

def mark_password_reset_token_used(token_id, used_at):
    return db.password_reset_tokens.update_one(
        {"_id": token_id if isinstance(token_id, ObjectId) else ObjectId(token_id), "used_at": None},
        {"$set": {"used_at": used_at}}
    )

def get_alunos():
    users_collection = db.users
    alunos = list(users_collection.find({"tipoUsuario": "aluno"}))

    for aluno in alunos:
        aluno['_id'] = str(aluno['_id'])  # Convertendo ObjectId para string
        aluno.pop('password', None)  # Remove o campo 'password' para evitar problemas com bytes

    return alunos

def serialize_document(document):
    document['_id'] = str(document['_id'])
    document.pop('password', None)
    return document

def update_tema(id, data):
    temas_collection = db.temas

    object_id = ObjectId(id)
    result = temas_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "tema": data.get("tema"),
            "descricao": data.get("descricao"),
            "teacher_id": data.get("teacher_id"),
            "teacher_name": data.get("teacher_name")
        }}
    )

    return result

def delete_tema(id):
    temas_collection = db.temas
    return temas_collection.delete_one({"_id": id})

def get_classes(teacher):
    classes = list(db.classes.find({"teacher_id": str(teacher)}))
    return [serialize_document(item) for item in classes]

def create_class(data):
    return db.classes.insert_one(data)

def update_class(id, data):
    return db.classes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "name": data.get("name"),
            "teacher_id": data.get("teacher_id"),
            "student_ids": data.get("student_ids", []),
            "updated_at": data.get("updated_at"),
        }}
    )

def delete_class(id):
    return db.classes.delete_one({"_id": ObjectId(id)})

def get_activities(teacher, class_id=None):
    query = {"teacher_id": str(teacher)}
    if class_id:
        query["class_id"] = class_id
    activities = list(db.activities.find(query))
    return [serialize_document(item) for item in activities]

def create_activity(data):
    return db.activities.insert_one(data)

def update_activity(id, data):
    return db.activities.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "title": data.get("title"),
            "teacher_id": data.get("teacher_id"),
            "class_id": data.get("class_id"),
            "theme_id": data.get("theme_id"),
            "due_date": data.get("due_date"),
            "updated_at": data.get("updated_at"),
        }}
    )

def delete_activity(id):
    return db.activities.delete_one({"_id": ObjectId(id)})

def get_redacoes(user_id):
    redacoes_collection = db.redacoes
    if user_id is not None:
        redacoes = list(redacoes_collection.find({"student_id": str(user_id)}))
    else:
        redacoes = list(redacoes_collection.find())
    for redacao in redacoes:
        redacao['_id'] = str(redacao['_id'])
    return redacoes

def paginate_redacoes(query, page=1, page_size=20, projection=None):
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)
    skip = (page - 1) * page_size
    projection = projection or REDACAO_LIST_PROJECTION
    cursor = (
        db.redacoes
        .find(query, projection)
        .sort([("created_at", -1), ("_id", -1)])
        .skip(skip)
        .limit(page_size)
    )
    items = [serialize_redacao(item) for item in cursor]
    total = db.redacoes.count_documents(query)
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }

def teacher_redacoes_query(teacher_id):
    teacher_id = str(teacher_id)
    theme_ids = [str(item["_id"]) for item in db.temas.find({"teacher_id": teacher_id}, {"_id": 1})]
    class_ids = [str(item["_id"]) for item in db.classes.find({"teacher_id": teacher_id}, {"_id": 1})]
    activity_ids = [str(item["_id"]) for item in db.activities.find({"teacher_id": teacher_id}, {"_id": 1})]
    return {"$or": [
        {"id_tema": {"$in": theme_ids}},
        {"class_id": {"$in": class_ids}},
        {"activity_id": {"$in": activity_ids}},
    ]}

def get_redacoes_page_for_student(student_id, page=1, page_size=20):
    return paginate_redacoes({"student_id": str(student_id)}, page, page_size)

def get_redacoes_for_teacher(teacher):
    query = teacher_redacoes_query(teacher)
    redacoes = list(db.redacoes.find(query))
    return [serialize_redacao(item) for item in redacoes]

def get_redacoes_page_for_teacher(teacher_id, page=1, page_size=20, student=None):
    query = teacher_redacoes_query(teacher_id)
    if student:
        query = {"$and": [query, {"student_id": student}]}
    return paginate_redacoes(query, page, page_size)

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
    redacao.pop('password', None)
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
