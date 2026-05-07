# Scripts de Suporte — Quintana

Scripts utilitários para preparar e validar o ambiente do Quintana (textgrader).

---

## `load_corpus_seed.py`

Popula o MongoDB com dados sintéticos realistas a partir de redações reais (corpus JSON). Cria professores, alunos, turmas, atividades e redações corrigidas, respeitando os schemas definidos em `backend/schemas.py`.

### Quando usar

- Antes de uma oficina ou demonstração, para ter dados prontos no banco.
- Para resetar um ambiente de testes para um estado conhecido.
- Ao adicionar novos temas ao corpus e querer refleti-los no banco.

### Dependências

```
pymongo
bcrypt
```

O módulo `pedagogy.py` (do backend) é opcional. Se disponível, gera feedback estruturado sintético; caso contrário, usa um fallback básico.

### Uso

```bash
python backend/scripts/load_corpus_seed.py \
  --input backend/data/tema-10.json backend/data/tema-34.json backend/data/tema-100.json \
  --mongo-uri <url_banco> \
  --seed-batch corpus_2026_01
```

### Argumentos

| Argumento | Obrigatório | Padrão | Descrição |
|-----------|-------------|--------|-----------|
| `--input` | Sim* | — | Um ou mais arquivos JSON de corpus de redações |
| `--mongo-uri` | Não | `mongodb://localhost:27017` | URI de conexão com o MongoDB |
| `--seed-batch` | Não | `corpus_2026_01` | Identificador do lote; usado para isolar e limpar dados |
| `--db-name` | Não | `textgrader` | Nome do banco de dados MongoDB |
| `--clear-only` | Não | `false` | Se presente, apenas remove os dados do `seed_batch` informado, sem inserir nada |

*Obrigatório quando `--clear-only` não é usado.

### Formato dos arquivos de entrada

Cada arquivo JSON deve conter uma lista de objetos (ou um único objeto) com os campos:

```json
{
  "tema": "Nome do tema da redação",
  "titulo": "Título da redação",
  "texto": "Corpo da redação...",
  "competencias": [
    {"nota": 160},
    {"nota": 140},
    {"nota": 120},
    {"nota": 160},
    {"nota": 140}
  ]
}
```

### O que é criado

| Coleção | Quantidade |
|---------|------------|
| `users` (professores) | 3 fixos |
| `users` (alunos) | 120 (20 por turma × 6 turmas) |
| `temas` | 1 por tema encontrado nos JSONs |
| `classes` | 6 (2 por professor) |
| `activities` | 30 (5 por turma) |
| `redacoes` | ~1.620 (estimado; ~10% dos alunos não entregam por atividade) |

Todos os documentos recebem o campo `seed_batch` com o valor informado, permitindo re-execução idempotente (dados do batch anterior são removidos antes de cada carga).

### Credenciais geradas

- **Senha padrão:** `123456` (para professores e alunos)
- **Professores:** `mariana.oliveira@quintana.local`, `rafael.mendes@quintana.local`, `carla.santos@quintana.local`
- **Alunos:** `aluno001@quintana.local` a `aluno120@quintana.local`

O login usa `email`. Relações internas entre usuários, redações, turmas, temas e atividades usam `_id` em campos como `student_id`, `teacher_id` e `student_ids`.

### Limpar dados de um batch

```bash
python backend/scripts/load_corpus_seed.py \
  --mongo-uri <url_banco> \
  --seed-batch corpus_2026_01 \
  --clear-only
```

---

## `workshop_healthcheck.py`

Valida se o ambiente está pronto para uma oficina ou smoke test. Verifica MongoDB, o health endpoint do backend, autenticação de professor e aluno, e os principais endpoints da API.

### Quando usar

- Imediatamente antes de uma oficina ou demonstração.
- Após subir o ambiente (Docker Compose, etc.) para confirmar que tudo está funcionando.

### Dependências

```
pymongo
```

Usa apenas a biblioteca padrão do Python para requisições HTTP (`urllib`).

### Uso

```bash
python backend/scripts/workshop_healthcheck.py \
  --backend-url http://localhost:5000 \
  --mongo-uri <url_banco> \
  --seed-batch corpus_2026_01
```

### Argumentos

| Argumento | Padrão | Descrição |
|-----------|--------|-----------|
| `--backend-url` | `http://localhost:5000` | URL base do backend Flask |
| `--mongo-uri` | `mongodb://localhost:27017` | URI de conexão com o MongoDB |
| `--db-name` | `textgrader` | Nome do banco de dados |
| `--seed-batch` | `""` | Filtra contagens por batch; vazio = conta todos os documentos |
| `--professor-email` | `rafael.mendes@quintana.local` | E-mail do professor usado no teste de login |
| `--student-email` | `aluno001@quintana.local` | E-mail do aluno usado no teste de login |
| `--password` | `123456` | Senha usada nos testes de autenticação |

### O que é verificado

**MongoDB**
- Conexão com o banco
- Contagem de documentos em cada coleção (`users`, `temas`, `classes`, `activities`, `redacoes`)

**Backend**
- Health endpoint `GET /`

**Autenticação**
- Login de professor via `POST /userLogin`
- Login de aluno via `POST /userLogin`

**Fluxo Professor** (se o login funcionar)
- `GET /temas`
- `GET /users/alunos`
- `GET /classes`
- `GET /activities`
- `GET /redacoes`
- `GET /professores/{username}/analytics`

**Fluxo Aluno** (se o login funcionar)
- `GET /temas`
- `GET /redacoes`
- `GET /students/{username}/activities`

### Saída

Cada verificação imprime `[OK]` ou `[FAIL]`. O script retorna código de saída `0` se tudo estiver ok, ou `1` se houver falhas.

```
== MongoDB ==
[OK] Conexão com MongoDB - textgrader
[OK] Coleção users - 123 documentos
...

== Resultado ==
Ambiente pronto para smoke test manual.
```

---

## Fluxo típico de preparação de oficina

```bash
# 1. Popula o banco com o corpus
python backend/scripts/load_corpus_seed.py \
  --input backend/data/tema-10.json backend/data/tema-34.json backend/data/tema-100.json \
  --mongo-uri mongodb://user:pass@host:27017/textgrader \
  --seed-batch corpus_2026_01

# 2. Valida que o ambiente está pronto
python backend/scripts/workshop_healthcheck.py \
  --backend-url http://localhost:5000 \
  --mongo-uri mongodb://user:pass@host:27017/textgrader \
  --seed-batch corpus_2026_01
```
