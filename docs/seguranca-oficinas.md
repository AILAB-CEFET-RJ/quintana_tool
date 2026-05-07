# Segurança para oficinas

Este documento descreve a configuração mínima recomendada para usar o Quintana em oficinas com dados fictícios ou anonimizados.

## Modos de operação

A aplicação usa a variável `APP_MODE` para diferenciar execução de demonstração e execução mais restrita.

```env
APP_MODE=demo
```

No modo `demo`, o backend permite, por padrão, chamadas vindas de:

```text
http://localhost:3000
http://127.0.0.1:3000
```

Em uso real ou em rede compartilhada, configure explicitamente:

```env
APP_MODE=production
CORS_ORIGINS=http://<host-do-frontend>:3000
```

## Variáveis de ambiente

Use `.env.example` como base:

```bash
cp .env.example .env
```

Variáveis principais:

```env
APP_MODE=demo
FLASK_DEBUG=false
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=textgrader
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
JWT_SECRET=troque-esta-chave
JWT_EXPIRATION_HOURS=8
ANALYTICS_CACHE_TTL_SECONDS=300
FRONTEND_URL=http://localhost:3000
PASSWORD_RESET_DEV_MODE=true
PASSWORD_RESET_EXPIRATION_MINUTES=30
OPENAI_API_KEY=dummy
SUBSCRIPTION_KEY=
ENDPOINT=
```

Gere um `JWT_SECRET` aleatório antes de subir o backend:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use a string gerada no `.env` ou no comando de subida. Se a chave for alterada, os tokens existentes deixam de valer e os usuários precisam fazer login novamente.

Para redefinição de senha em oficina, mantenha `PASSWORD_RESET_DEV_MODE=true`. Nesse modo, o backend não envia e-mail real: ele imprime no terminal um link como `/quintana/redefinir-senha?token=...`. O link expira conforme `PASSWORD_RESET_EXPIRATION_MINUTES` e o token é salvo no MongoDB apenas em formato derivado, não em texto puro.

`MONGO_DB_NAME` permite separar bancos por oficina:

```env
MONGO_DB_NAME=textgrader_oficina_escola_a
```

## CORS

O backend não usa mais CORS aberto. As origens aceitas vêm de `CORS_ORIGINS`.

Exemplo para uma máquina servindo o frontend na rede local:

```env
CORS_ORIGINS=http://192.168.0.20:3000
```

Para múltiplas origens:

```env
CORS_ORIGINS=http://localhost:3000,http://192.168.0.20:3000
```

## MongoDB com autenticação

Para oficinas com múltiplos dispositivos, prefira MongoDB com usuário e senha:

```bash
docker run -d \
  --name quintana-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=quintana \
  -e MONGO_INITDB_ROOT_PASSWORD=<senha-forte> \
  mongo:7
```

URI correspondente:

```env
MONGO_URI=mongodb://quintana:<senha-forte>@localhost:27017/?authSource=admin
```

## Carga e limpeza de dados fictícios

O script de carga aceita `MONGO_URI`, `MONGO_DB_NAME` e `seed_batch`.

Carga:

```bash
python3 backend/scripts/load_corpus_seed.py \
  --input backend/data/tema-10.json backend/data/tema-34.json backend/data/tema-100.json \
  --mongo-uri mongodb://localhost:27017 \
  --db-name textgrader \
  --seed-batch corpus_2026_01
```

Limpeza apenas do batch:

```bash
python3 backend/scripts/load_corpus_seed.py \
  --mongo-uri mongodb://localhost:27017 \
  --db-name textgrader \
  --seed-batch corpus_2026_01 \
  --clear-only
```

O script também garante índices básicos para consultas por aluno, professor, turma, atividade, tema, versão e `seed_batch`.

## Dados sensíveis

Para oficinas, use dados fictícios ou anonimizados.

Cuidados mínimos:

- não exponha MongoDB diretamente à internet;
- não use chaves reais de serviços externos quando elas não forem necessárias;
- não reutilize a senha padrão dos dados fictícios em ambiente real;
- crie um `seed_batch` por oficina;
- limpe o batch ao final da atividade, quando apropriado.

## Endurecimentos já implementados

- `MONGO_DB_NAME` configurável por ambiente.
- CORS configurável via `CORS_ORIGINS`.
- Remoção de CORS manual com `*` em respostas específicas.
- Login retorna token assinado para uso em `Authorization: Bearer`.
- Endpoints de aluno e professor validam perfil e propriedade do recurso no backend.
- O backend deixa de confiar em `user`, `teacher` e `aluno` enviados pelo frontend como fonte de identidade.
- Mensagem de login genérica para evitar enumeração direta de usuários.
- Respostas de erro com detalhes técnicos apenas em `APP_MODE=demo` ou `FLASK_DEBUG=true`.
- Serialização defensiva removendo `password` de documentos retornados por helpers do banco.
- Índices básicos no script de carga.
- Modo `--clear-only` para limpeza por `seed_batch`.
