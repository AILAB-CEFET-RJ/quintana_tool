# Esquema lógico do banco de dados

O Quintana usa MongoDB sem validação de schema no próprio banco. A referência técnica dos documentos esperados está em:

```text
backend/schemas.py
```

Este documento resume as coleções e seus principais campos.

## Coleções

- `users`
- `temas`
- `redacoes`
- `classes`
- `activities`
- `password_reset_tokens`
- `password_reset_attempts`

## `users`

```json
{
  "_id": "...",
  "email": "aluno@example.com",
  "password": "<bcrypt>",
  "display_name": "Maria Silva",
  "tipoUsuario": "aluno",
  "schema_version": 1
}
```

`tipoUsuario` pode ser `aluno` ou `professor`.

## `temas`

```json
{
  "_id": "...",
  "teacher_id": "...",
  "teacher_name": "Profa. Mariana Oliveira",
  "tema": "Desinformação",
  "descricao": "Texto da proposta..."
}
```

## `redacoes`

```json
{
  "_id": "...",
  "titulo": "Título da redação",
  "texto": "Texto...",
  "student_id": "...",
  "student_name": "Maria Silva",
  "id_tema": "...",
  "nota_total": 640,
  "nota_competencia_1_model": 160,
  "nota_competencia_2_model": 120,
  "nota_competencia_3_model": 120,
  "nota_competencia_4_model": 160,
  "nota_competencia_5_model": 80,
  "nota_professor": "",
  "feedback_llm": "...",
  "feedback_structured": {
    "competencies": [],
    "priorities": [],
    "rewrite_checklist": []
  },
  "feedback_structured_source": "llm",
  "rewrite_checklist_state": {
    "c1": true
  },
  "created_at": "2026-04-30T...",
  "updated_at": "2026-04-30T...",
  "submitted_at": "2026-04-30T...",
  "version_group_id": "...",
  "parent_redacao_id": "...",
  "version_number": 2,
  "class_id": "...",
  "activity_id": "...",
  "correction_source": "model",
  "is_latest_version": true,
  "schema_version": 1
}
```

Observações:

- `version_group_id` agrupa versões da mesma redação.
- `parent_redacao_id` aponta para a versão anterior.
- `feedback_structured_source` pode ser `llm` ou `fallback`.
- `class_id` e `activity_id` são opcionais para redações antigas ou envios fora de atividade.

## `classes`

```json
{
  "_id": "...",
  "name": "3001 - Manhã",
  "teacher_id": "...",
  "student_ids": ["...", "..."],
  "created_at": "2026-04-30T...",
  "updated_at": "2026-04-30T...",
  "schema_version": 1
}
```

## `activities`

```json
{
  "_id": "...",
  "title": "Redação 3",
  "teacher_id": "...",
  "class_id": "...",
  "theme_id": "...",
  "due_date": "2026-05-10",
  "created_at": "2026-04-30T...",
  "updated_at": "2026-04-30T...",
  "schema_version": 1
}
```

## `password_reset_tokens`

```json
{
  "_id": "...",
  "user_id": "...",
  "email": "aluno@example.com",
  "token_hash": "<sha256>",
  "created_at": "2026-05-07T...",
  "expires_at": "2026-05-07T...",
  "used_at": null,
  "requester_ip_hash": "<sha256>",
  "schema_version": 1
}
```

Observações:

- o token em texto puro nunca é salvo;
- `expires_at` tem índice TTL;
- tokens antigos do mesmo usuário são marcados como usados quando um novo link é gerado.

## `password_reset_attempts`

```json
{
  "_id": "...",
  "kind": "email",
  "key_hash": "<sha256>",
  "requester_ip_hash": "<sha256>",
  "created_at": "2026-05-07T...",
  "schema_version": 1
}
```

Essa coleção registra tentativas por e-mail e por IP para aplicar rate limiting no fluxo de redefinição de senha. Os registros têm expiração automática.

## Validação no backend

O arquivo `backend/schemas.py` define:

- `TypedDicts` para cada documento;
- `SCHEMAS` com campos obrigatórios e opcionais;
- `missing_required_fields`;
- `validate_required_fields`.

A validação atual é leve e aplicada nos principais pontos de escrita do backend. Ela não substitui uma validação de schema no MongoDB.
