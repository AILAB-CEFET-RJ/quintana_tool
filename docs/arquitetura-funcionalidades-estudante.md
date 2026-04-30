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
  "rewrite_checklist_state": {}
}
```

Observações:

- `created_at` e `updated_at` são preenchidos no backend no momento da submissão.
- `version_group_id` agrupa versões da mesma redação.
- `parent_redacao_id` aponta para a versão usada como base da reescrita.
- `version_number` indica a posição da redação na sequência de versões.
- `feedback_structured` guarda a devolutiva navegável usada pelo frontend.
- `rewrite_checklist_state` foi reservado para persistência futura do estado do checklist.

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

Arquivo:

```text
backend/pedagogy.py
```

Função principal:

```py
build_structured_feedback(grades)
```

Essa função gera uma estrutura determinística com:

- diagnóstico por competência;
- sugestão de melhoria;
- ação prática;
- prioridades de estudo;
- checklist de reescrita.

Ela funciona mesmo quando o feedback textual gerado por LLM não está disponível.

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
  "rewrite_of": "<id_redacao>"
}
```

O backend usa `rewrite_of` para vincular a nova submissão à versão anterior.

## Compatibilidade com dados antigos

As funcionalidades foram implementadas com fallback para redações antigas:

- se não houver `created_at`, a linha do tempo usa o timestamp do `ObjectId`;
- se não houver `version_number`, a redação é tratada como versão `1`;
- se não houver `feedback_structured`, o frontend monta uma devolutiva básica a partir das notas;
- se não houver versões associadas, a aba `Versões` mostra um estado vazio.

## Limitações atuais

- O checklist é interativo apenas no cliente; o estado marcado ainda não é persistido.
- O feedback estruturado atual é determinístico e baseado nas notas; ele não usa resposta JSON do LLM.
- Redações submetidas por OCR recebem feedback estruturado, mas o fluxo principal de reescrita foi implementado para submissão textual.
