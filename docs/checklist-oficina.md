# Checklist operacional de oficina

Use este roteiro antes de cada oficina para reduzir risco de falha durante a atividade.

## Antes de abrir a sala

1. Subir o MongoDB.
2. Subir o backend com as variáveis corretas:

```bash
cd backend
MONGO_URI=mongodb://localhost:27017 \
MONGO_DB_NAME=textgrader \
CORS_ORIGINS=http://localhost:3000 \
JWT_SECRET=<chave-gerada> \
ANALYTICS_CACHE_TTL_SECONDS=300 \
OPENAI_API_KEY=dummy \
python3 app.py
```

3. Subir o frontend em modo produção:

```bash
cd frontend
npm run build
npm run start
```

4. Confirmar que o frontend abre em:

```text
http://localhost:3000/quintana/login
```

## Health check automático

Com MongoDB, backend e frontend rodando, execute:

```bash
python3 backend/scripts/workshop_healthcheck.py \
  --backend-url http://localhost:5000 \
  --mongo-uri mongodb://localhost:27017 \
  --db-name textgrader \
  --seed-batch corpus_2026_01 \
  --professor-email rafael.mendes@quintana.local \
  --student-email aluno001@quintana.local \
  --password 123456
```

O script verifica:

- conexão com MongoDB;
- existência de usuários, temas, turmas, atividades e redações;
- health endpoint do backend;
- login de professor;
- login de aluno;
- endpoints principais do professor;
- endpoints principais do aluno.

Se algum item aparecer como `FAIL`, corrija antes da oficina.

## Smoke test manual

Depois do health check automático, faça este teste de 5 minutos:

1. Entrar como professor.
2. Abrir `Painel`.
3. Abrir aba `Análise da turma`.
4. Confirmar que distribuição, heatmap, ranking e alertas aparecem.
5. Abrir aba `Turmas e atividades`.
6. Confirmar que turmas e atividades aparecem.
7. Sair.
8. Entrar como aluno.
9. Abrir `Minhas redações`.
10. Confirmar que radar médio, linha do tempo e tabela aparecem.
11. Abrir uma redação.
12. Confirmar que o modal mostra resumo, notas, plano de ação e feedback.

## Plano de contingência

Tenha disponível antes da oficina:

- usuários e senhas de teste;
- comando de carga do corpus;
- comando de limpeza por `seed_batch`;
- screenshots dos painéis principais;
- cópia local dos arquivos JSON do corpus;
- chave `JWT_SECRET` usada na execução;
- instrução para reiniciar backend e frontend.

## Comandos úteis

Gerar `JWT_SECRET`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Limpar um batch:

```bash
python3 backend/scripts/load_corpus_seed.py \
  --mongo-uri mongodb://localhost:27017 \
  --db-name textgrader \
  --seed-batch corpus_2026_01 \
  --clear-only
```

Recarregar corpus:

```bash
python3 backend/scripts/load_corpus_seed.py \
  --input backend/data/tema-10.json backend/data/tema-34.json backend/data/tema-100.json \
  --mongo-uri mongodb://localhost:27017 \
  --db-name textgrader \
  --seed-batch corpus_2026_01
```
