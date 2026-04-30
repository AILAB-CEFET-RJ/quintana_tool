# Arquitetura das funcionalidades para professores

Este documento descreve a implementação técnica dos recursos de professor.

## Coleções principais

As funcionalidades de professor usam as coleções:

- `users`
- `temas`
- `redacoes`
- `classes`
- `activities`

## Coleção `classes`

Representa uma turma gerenciada por um professor.

Estrutura:

```json
{
  "_id": "...",
  "name": "3001 - Manhã",
  "teacher": "professor1",
  "students": ["Ana", "Bruno", "Carlos"],
  "created_at": "2026-04-30T...",
  "updated_at": "2026-04-30T...",
  "schema_version": 1
}
```

Campos:

- `name`: nome da turma;
- `teacher`: nome de usuário do professor;
- `students`: lista de nomes de usuário dos estudantes;
- `created_at`: data de criação;
- `updated_at`: data da última atualização.

## Coleção `activities`

Representa uma atividade de redação vinculada a uma turma e a um tema.

Estrutura:

```json
{
  "_id": "...",
  "title": "Redação 3 - proposta de intervenção",
  "teacher": "professor1",
  "class_id": "...",
  "theme_id": "...",
  "due_date": "2026-05-10",
  "created_at": "2026-04-30T...",
  "updated_at": "2026-04-30T...",
  "schema_version": 1
}
```

Campos:

- `title`: título da atividade;
- `teacher`: nome de usuário do professor;
- `class_id`: turma associada;
- `theme_id`: tema associado;
- `due_date`: prazo opcional;
- `created_at`: data de criação;
- `updated_at`: data da última atualização.

## Campos em `redacoes`

Para integrar redações a turmas e atividades, novas submissões podem receber:

```json
{
  "class_id": "...",
  "activity_id": "...",
  "submitted_at": "2026-04-30T...",
  "correction_source": "model",
  "is_latest_version": true,
  "schema_version": 1
}
```

Campos:

- `class_id`: identifica a turma;
- `activity_id`: identifica a atividade;
- `submitted_at`: data da submissão;
- `correction_source`: origem da correção;
- `is_latest_version`: indica se a redação é a versão mais recente dentro de um grupo de versões.

## Endpoints de turmas

### Listar turmas

```http
GET /classes?teacher=<nome_professor>
```

Retorna as turmas do professor.

### Criar turma

```http
POST /classes
```

Payload:

```json
{
  "teacher": "professor1",
  "name": "3001 - Manhã",
  "students": ["Ana", "Bruno"]
}
```

### Atualizar turma

```http
PUT /classes/<id>
```

### Remover turma

```http
DELETE /classes/<id>
```

## Endpoints de atividades

### Listar atividades

```http
GET /activities?teacher=<nome_professor>
```

Também aceita filtro por turma:

```http
GET /activities?teacher=<nome_professor>&class_id=<id_turma>
```

### Criar atividade

```http
POST /activities
```

Payload:

```json
{
  "teacher": "professor1",
  "title": "Redação 3",
  "class_id": "...",
  "theme_id": "...",
  "due_date": "2026-05-10"
}
```

### Atualizar atividade

```http
PUT /activities/<id>
```

### Remover atividade

```http
DELETE /activities/<id>
```

### Status de submissões da atividade

```http
GET /activities/<id>/submissions?teacher=<nome_professor>
```

Retorno:

```json
{
  "activity": {},
  "expected_students": [],
  "submitted_students": [],
  "missing_students": [],
  "late_students": [],
  "submission_count": 10,
  "expected_count": 20
}
```

## Endpoint de análise

```http
GET /professores/<nome_professor>/analytics
```

Filtros opcionais:

```http
GET /professores/<nome_professor>/analytics?class_id=<id_turma>&activity_id=<id_atividade>
```

Também aceita agrupamento longitudinal:

```http
GET /professores/<nome_professor>/analytics?group_by=activity
GET /professores/<nome_professor>/analytics?group_by=theme
GET /professores/<nome_professor>/analytics?group_by=week
```

Retorno:

```json
{
  "scope": {},
  "distribution": [],
  "ranking": [],
  "heatmap": [],
  "groups": [],
  "evolution": [],
  "theme_performance": [],
  "alerts": []
}
```

## Camada de análise

Arquivo:

```text
backend/analytics.py
```

Responsabilidades:

- buscar redações associadas aos temas do professor;
- aplicar filtros de `class_id` e `activity_id`;
- considerar apenas versões mais recentes;
- calcular distribuição por competência com estatísticas de boxplot;
- montar ranking de competências problemáticas;
- montar heatmap aluno x competência;
- agrupar estudantes por perfil pedagógico;
- calcular evolução por atividade, tema ou dia;
- comparar desempenho por tema;
- gerar alertas pedagógicos expandidos.

Função principal:

```py
build_teacher_analytics(professor_name, class_id=None, activity_id=None, group_by="activity")
```

## Frontend

### Painel principal

Arquivo:

```text
frontend/src/pages/quintana/home.tsx
```

Responsabilidades:

- carregar temas;
- carregar redações;
- carregar alunos;
- carregar turmas e atividades;
- consultar análise do professor;
- renderizar filtros de turma e atividade;
- renderizar abas do professor.

### Aba `Análise da turma`

Componente:

```text
frontend/src/components/teacherAnalytics/TeacherAnalyticsPanel.tsx
```

Inclui:

- alertas pedagógicos;
- ranking de competências problemáticas;
- distribuição por competência;
- heatmap aluno x competência;
- agrupamento pedagógico;
- evolução da turma;
- comparação por tema.

### Aba `Turmas e atividades`

Componente:

```text
frontend/src/components/teacherAnalytics/TeacherClassActivityManager.tsx
```

Inclui:

- cadastro de turma;
- listagem de turmas;
- edição de turma;
- remoção de turma;
- cadastro de atividade;
- listagem de atividades;
- edição de atividade;
- remoção de atividade;
- link de envio da atividade;
- status de submissão da atividade.

## Fluxo de envio por atividade

Ao criar uma atividade, o frontend gera um link:

```text
/quintana/redacao?id=<theme_id>&classId=<class_id>&activityId=<activity_id>
```

A página de redação lê esses parâmetros e envia para o backend:

```json
{
  "id": "<theme_id>",
  "class_id": "<class_id>",
  "activity_id": "<activity_id>"
}
```

Assim, a redação fica vinculada à atividade e pode aparecer nos filtros e alertas.

## Compatibilidade com dados antigos

Redações antigas sem `class_id` e `activity_id` continuam aparecendo nas análises gerais do professor, desde que estejam vinculadas a temas criados por ele.

Quando o professor filtra por turma ou atividade, apenas redações com os campos correspondentes são consideradas.

## Limitações atuais

- A associação de aluno à turma usa o nome de usuário como identificador.
- O link de atividade precisa ser distribuído pelo professor; ainda não há painel do aluno com atividades pendentes.
- A validação de escopo por professor usa o parâmetro `teacher`, pois ainda não há autenticação backend com token/JWT.
