"""
Document schemas used by the MongoDB collections.

The application currently uses MongoDB without database-enforced schemas. This
module centralizes the expected document shapes so backend code and docs have a
single technical reference.
"""

from typing import Any, Dict, List, Optional, TypedDict


class UserDocument(TypedDict, total=False):
    _id: str
    email: str
    password: bytes
    display_name: str
    tipoUsuario: str


class TemaDocument(TypedDict, total=False):
    _id: str
    teacher_id: str
    teacher_name: str
    tema: str
    descricao: str


class FeedbackCompetency(TypedDict, total=False):
    code: str
    title: str
    description: str
    score: float
    diagnosis: str
    suggestion: str
    practice_action: str


class FeedbackPriority(TypedDict, total=False):
    rank: int
    competency: str
    title: str
    score: float
    reason: str
    next_action: str


class RewriteChecklistItem(TypedDict, total=False):
    id: str
    competency: str
    label: str


class StructuredFeedback(TypedDict, total=False):
    competencies: List[FeedbackCompetency]
    priorities: List[FeedbackPriority]
    rewrite_checklist: List[RewriteChecklistItem]


class RedacaoDocument(TypedDict, total=False):
    _id: str
    titulo: str
    texto: str
    nota_total: float
    nota_professor: Any
    nota_competencia_1_model: float
    nota_competencia_2_model: float
    nota_competencia_3_model: float
    nota_competencia_4_model: float
    nota_competencia_5_model: float
    nota_competencia_1_professor: float
    nota_competencia_2_professor: float
    nota_competencia_3_professor: float
    nota_competencia_4_professor: float
    nota_competencia_5_professor: float
    id_tema: str
    student_id: str
    student_name: str
    feedback_llm: str
    feedback_professor: str
    competencias: Dict[str, str]
    created_at: str
    updated_at: str
    submitted_at: str
    version_group_id: Optional[str]
    parent_redacao_id: Optional[str]
    version_number: int
    feedback_structured: StructuredFeedback
    feedback_structured_source: str
    rewrite_checklist_state: Dict[str, bool]
    class_id: Optional[str]
    activity_id: Optional[str]
    correction_source: str
    is_latest_version: bool
    schema_version: int


class ClassDocument(TypedDict, total=False):
    _id: str
    name: str
    teacher_id: str
    student_ids: List[str]
    created_at: str
    updated_at: str


class ActivityDocument(TypedDict, total=False):
    _id: str
    title: str
    teacher_id: str
    class_id: str
    theme_id: str
    due_date: str
    created_at: str
    updated_at: str


class PasswordResetTokenDocument(TypedDict, total=False):
    _id: str
    user_id: str
    email: str
    token_hash: str
    created_at: Any
    expires_at: Any
    used_at: Any
    requester_ip_hash: str
    schema_version: int


class PasswordResetAttemptDocument(TypedDict, total=False):
    _id: str
    kind: str
    key_hash: str
    requester_ip_hash: str
    created_at: Any
    schema_version: int


SCHEMAS: Dict[str, Dict[str, Any]] = {
    "users": {
        "required": ["email", "password", "display_name", "tipoUsuario"],
        "optional": ["_id"],
    },
    "temas": {
        "required": ["teacher_id", "tema", "descricao"],
        "optional": ["_id", "teacher_name"],
    },
    "redacoes": {
        "required": [
            "titulo",
            "texto",
            "nota_total",
            "id_tema",
            "student_id",
            "nota_competencia_1_model",
            "nota_competencia_2_model",
            "nota_competencia_3_model",
            "nota_competencia_4_model",
            "nota_competencia_5_model",
        ],
        "optional": [
            "_id",
            "nota_professor",
            "nota_competencia_1_professor",
            "nota_competencia_2_professor",
            "nota_competencia_3_professor",
            "nota_competencia_4_professor",
            "nota_competencia_5_professor",
            "feedback_llm",
            "feedback_professor",
            "competencias",
            "created_at",
            "updated_at",
            "submitted_at",
            "version_group_id",
            "parent_redacao_id",
            "version_number",
            "feedback_structured",
            "feedback_structured_source",
            "rewrite_checklist_state",
            "class_id",
            "activity_id",
            "correction_source",
            "is_latest_version",
            "schema_version",
            "student_name",
        ],
    },
    "classes": {
        "required": ["name", "teacher_id", "student_ids", "created_at", "updated_at"],
        "optional": ["_id"],
    },
    "activities": {
        "required": ["title", "teacher_id", "class_id", "theme_id", "created_at", "updated_at"],
        "optional": ["_id", "due_date"],
    },
    "password_reset_tokens": {
        "required": ["user_id", "email", "token_hash", "created_at", "expires_at", "used_at"],
        "optional": ["_id", "requester_ip_hash", "schema_version"],
    },
    "password_reset_attempts": {
        "required": ["kind", "key_hash", "created_at"],
        "optional": ["_id", "requester_ip_hash", "schema_version"],
    },
}


def missing_required_fields(collection: str, document: Dict[str, Any]) -> List[str]:
    schema = SCHEMAS.get(collection)
    if not schema:
        raise ValueError(f"Schema desconhecido: {collection}")

    return [field for field in schema["required"] if field not in document]


def validate_required_fields(collection: str, document: Dict[str, Any]) -> None:
    missing = missing_required_fields(collection, document)
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes em {collection}: {', '.join(missing)}")
