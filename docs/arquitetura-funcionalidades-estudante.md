# Arquitetura das funcionalidades para estudantes

Este documento descreve a implementação técnica dos recursos de acompanhamento pedagógico para estudantes.

## Campos persistidos

As redações são persistidas na coleção `redacoes` do MongoDB.

Além dos campos já existentes de nota e texto, novas submissões passam a incluir:

```json
{
  "created_at": "2026-04-29T...",
  "updated_at": "2026-04-29T...",
  "version_group_id": "<id da primeira versão ou null>",
  "parent_redacao_id": "<id da versão anterior ou null>",
  "version_number": 1,
  "feedback_structured": {
    "competencies": [],
    "priorities": [],
    "rewrite_checklist": []
  },
  "feedback_structured_source": "fallback",
  "rewrite_checklist_state": {},
  "class_id": "...",
  "activity_id": "...",
  "submitted_at": "2026-04-30T...",
  "schema_version": 1
}
```

Observações:

- `created_at` e `updated_at` são preenchidos no backend no momento da submissão.
- `version_group_id` agrupa versões da mesma redação.
- `parent_redacao_id` aponta para a versão usada como base da reescrita.
- `version_number` indica a posição da redação na sequência de versões.
- `feedback_structured` guarda a devolutiva navegável usada pelo frontend.
- `feedback_structured_source` indica se a estrutura veio do LLM ou do fallback determinístico.
- `rewrite_checklist_state` persiste o estado marcado do checklist.
- `class_id` e `activity_id` vinculam a redação a uma turma e atividade, quando houver.
- `schema_version` indica a versão do esquema lógico usado pela aplicação.

## Backend

### Submissão de redação

Arquivo principal:

```text
backend/app.py
```

Endpoint:

```http
POST /model
```

Responsabilidades:

- receber texto, tema, aluno e, opcionalmente, `rewrite_of`;
- avaliar a redação;
- persistir notas por competência;
- criar metadados de data;
- criar metadados de versão;
- gerar `feedback_structured`;
- iniciar geração assíncrona do feedback textual.

Quando `rewrite_of` é enviado, o backend:

- busca a redação anterior;
- reaproveita ou cria o `version_group_id`;
- calcula o próximo `version_number`;
- salva a nova redação como nova versão.

### Feedback estruturado

Arquivos:

```text
backend/pedagogy.py
backend/llm.py
```

Funções principais:

```py
build_structured_feedback(grades)
get_structured_llm_feedback(essay, grades, theme)
```

O sistema tenta gerar feedback estruturado via LLM em JSON. Se a chamada falhar ou retornar estrutura inválida, usa o fallback determinístico de `backend/pedagogy.py`.

A estrutura contém:

- diagnóstico por competência;
- sugestão de melhoria;
- ação prática;
- prioridades de estudo;
- checklist de reescrita.

O campo `feedback_structured_source` registra a origem: `llm` ou `fallback`.

### Checklist de reescrita

Endpoint:

```http
PUT /redacoes/<id>/rewrite-checklist
```

Payload:

```json
{
  "rewrite_checklist_state": {
    "c1": true,
    "c2": false
  }
}
```

Responsabilidade:

- persistir os itens marcados no checklist da redação.

### Atividades do estudante

Endpoint:

```http
GET /students/<username>/activities
```

Responsabilidade:

- buscar turmas em que o estudante está matriculado;
- buscar atividades dessas turmas;
- verificar se já existe redação enviada para cada atividade;
- retornar status `pending`, `submitted` ou `late`.

### Consulta de versões

Arquivo:

```text
backend/database.py
```

Endpoint:

```http
GET /redacoes/<id>/versions
```

Responsabilidade:

- localizar a redação;
- identificar seu `version_group_id`;
- retornar todas as versões associadas;
- ordenar por `version_number`.

Registros antigos sem versionamento são tratados como versão `1`.

## Frontend

### Utilitário de competências

Arquivo:

```text
frontend/src/lib/competencias.ts
```

Responsabilidades:

- centralizar código, título, campos de nota e ação padrão de cada competência;
- oferecer helpers para extrair notas por competência.

Principais exports:

```ts
COMPETENCIES
getScore()
getCompetencyScores()
```

### Componentes de acompanhamento

Diretório:

```text
frontend/src/components/studentInsights/
```

Componentes:

- `CompetencyRadar.tsx`: radar das cinco competências.
- `ProgressTimeline.tsx`: linha do tempo de progresso na aba de redações.
- `StudyPriorityCard.tsx`: cartão com as três prioridades de estudo.
- `CompetencyFeedbackMap.tsx`: mapa de feedback por competência.
- `RewriteChecklist.tsx`: checklist da próxima reescrita.
- `VersionComparison.tsx`: comparação entre versões da mesma redação.
- `StudentActivitiesPanel.tsx`: lista de atividades atribuídas ao estudante.

### Modal de detalhes da redação

Arquivo:

```text
frontend/src/components/modalDetalhesRedacao.tsx
```

Responsabilidades:

- apresentar resumo da redação;
- exibir radar e prioridades;
- exibir texto e notas;
- exibir mapa de feedback e checklist;
- consultar versões pelo endpoint `/redacoes/<id>/versions`;
- exibir comparação entre versões;
- iniciar o fluxo de reescrita.

### Fluxo de reescrita

Origem:

```text
frontend/src/components/modalDetalhesRedacao.tsx
```

Ao clicar em `Reescrever`, o frontend navega para:

```text
/quintana/redacao?id=<id_tema>&rewriteOf=<id_redacao>
```

Destino:

```text
frontend/src/pages/quintana/redacao.tsx
```

Ao submeter, a página envia:

```json
{
  "essay": "...",
  "id": "<id_tema>",
  "aluno": "<nome_usuario>",
  "rewrite_of": "<id_redacao>",
  "class_id": "<id_turma>",
  "activity_id": "<id_atividade>"
}
```

O backend usa `rewrite_of` para vincular a nova submissão à versão anterior.

## Compatibilidade com dados antigos

As funcionalidades foram implementadas com fallback para redações antigas:

- se não houver `created_at`, a linha do tempo usa o timestamp do `ObjectId`;
- se não houver `version_number`, a redação é tratada como versão `1`;
- se não houver `feedback_structured`, o frontend monta uma devolutiva básica a partir das notas;
- se não houver versões associadas, a aba `Versões` mostra um estado vazio.
- redações antigas sem `class_id` e `activity_id` continuam aparecendo normalmente no histórico do estudante.

## Limitações atuais

- O feedback estruturado via LLM depende de uma chave válida da API; sem ela, o fallback determinístico é usado.
- O painel de atividades do aluno lista atividades de turmas em que o nome de usuário aparece em `classes.students`.
