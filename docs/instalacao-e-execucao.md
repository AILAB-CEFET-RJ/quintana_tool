# Instalação e execução

Este documento descreve como preparar e executar o Quintana localmente.

## Visão geral dos serviços

A aplicação possui quatro partes principais:

- MongoDB: banco de dados usado para usuários, temas e redações (executado separadamente).
- Backend Flask: API em `http://localhost:5000`.
- Frontend Next.js: interface Web em `http://localhost:3000`.
- Ollama: serviço local de LLM em `http://localhost:11434`.

Backend, frontend e Ollama são gerenciados pelo Docker Compose. O MongoDB precisa estar acessível externamente.

## Pré-requisitos

- Docker e Docker Compose.
- Make (para atalhos de comando).

## Subir o MongoDB

O `docker-compose.yml` não inclui um serviço MongoDB. Suba-o separadamente antes de iniciar os demais serviços.

### Opção 1 — via Docker

```bash
docker run -d --name quintana-mongo -p 27017:27017 mongo:7
```

Para verificar se está rodando:

```bash
docker ps
```

Para parar e reiniciar:

```bash
docker stop quintana-mongo
docker start quintana-mongo
```

### Opção 2 — instalação local

Se preferir rodar o MongoDB diretamente na máquina, sem Docker:

**Ubuntu/Debian:**

```bash
sudo apt-get install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```

Iniciar o serviço:

```bash
sudo systemctl start mongod
sudo systemctl enable mongod  # opcional: inicia automaticamente com o sistema
```

Verificar se está rodando:

```bash
sudo systemctl status mongod
```

Nesse caso, mantenha `MONGO_URI=mongodb://localhost:27017` no `.env`. Como o MongoDB roda no host (não em container), `localhost` funciona diretamente tanto para acesso local quanto para os containers via `host.docker.internal`.

O banco `textgrader` e as coleções são criados automaticamente quando a aplicação grava os primeiros dados.

## Configurar variáveis de ambiente

Na raiz do repositório, copie o arquivo de exemplo:

```bash
make setup-env
```

Isso cria o arquivo `.env` a partir do `.env.example`. Em seguida, edite o `.env` conforme necessário.

### Variáveis disponíveis

```bash
# Modo de operação: demo para oficinas com dados fictícios; production para uso real.
APP_MODE=demo
FLASK_DEBUG=false

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=textgrader

# Origens autorizadas a chamar o backend, separadas por vírgula.
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Token de autenticação. Troque JWT_SECRET fora do modo demo.
JWT_SECRET=troque-esta-chave
JWT_EXPIRATION_HOURS=8
ANALYTICS_CACHE_TTL_SECONDS=300

# Serviços externos.
OPENAI_API_KEY=dummy
SUBSCRIPTION_KEY=
ENDPOINT=
OLLAMA_HOST=ollama
```

**Observação sobre `MONGO_URI` no Docker:** ao rodar via Docker Compose, os containers não enxergam `localhost` como o host da máquina. Se o MongoDB estiver rodando no host, use:

- Linux: o IP da interface `docker0` (tipicamente `172.17.0.1`) ou `host.docker.internal` se disponível.
- WSL2: `host.docker.internal` costuma funcionar.

Exemplo para WSL2:

```bash
MONGO_URI=mongodb://host.docker.internal:27017
```

**`JWT_SECRET`** assina os tokens de login. Para gerar uma chave segura:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Substitua `troque-esta-chave` pelo valor gerado. Se `JWT_SECRET` for alterado, os tokens existentes deixam de valer e os usuários precisam fazer login novamente.

**`ANALYTICS_CACHE_TTL_SECONDS`** controla por quantos segundos o backend reaproveita resultados dos painéis de análise do professor. Use `0` para desabilitar o cache.

**`OPENAI_API_KEY`** é obrigatória para geração real de feedback via LLM. Para testar apenas cadastro, login e navegação, use `dummy`.

**`SUBSCRIPTION_KEY` e `ENDPOINT`** são opcionais, usadas apenas no fluxo de OCR por imagem (Azure).

## Subir os serviços

Com o `.env` configurado e o MongoDB rodando, execute na raiz do repositório:

```bash
docker compose up --build
```

Ou pelo atalho do Make:

```bash
make up
```

O primeiro build pode demorar alguns minutos enquanto as dependências são instaladas.

Após subir, os serviços ficam disponíveis em:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5000`
- Ollama: `http://localhost:11434`

Para verificar o backend:

```bash
curl http://localhost:5000/
```

Resposta esperada:

```json
{
  "database": "connected",
  "status": "ok"
}
```

## Comandos do Make

O `Makefile` na raiz do repositório oferece atalhos para as operações mais comuns:

| Comando | O que faz |
|---|---|
| `make setup-env` | Copia `.env.example` para `.env`. Execute uma vez antes de subir os serviços pela primeira vez. |
| `make up` | Executa `docker compose up --build`, construindo as imagens e subindo todos os serviços. |
| `make down` | Executa `docker compose down --remove-orphans`, parando e removendo os containers, incluindo containers órfãos. |
| `make remove-logs` | Remove os arquivos de log (`*_log.txt`) gerados pelo backend em `backend/src/`. |

## Parar os serviços

```bash
docker compose down
```

Ou pelo Make (remove também containers órfãos):

```bash
make down
```

## Primeiro teste manual

1. Acesse `http://localhost:3000/quintana/cadastro`.
2. Crie um usuário do tipo `Aluno`.
3. Faça login.
4. Para submeter redações, é necessário existir pelo menos um tema.
5. Crie um usuário do tipo `Professor`.
6. Faça login como professor e cadastre um tema em `Criar novo tema`.
7. Volte ao usuário aluno, escolha o tema e envie uma redação.

## Problemas comuns

### Erro de conexão com MongoDB

Verifique se o container do Mongo está rodando:

```bash
docker ps
```

Confirme se a variável `MONGO_URI` no `.env` está apontando para o endereço correto. Em WSL2, tente `host.docker.internal` no lugar de `localhost`.

### `database: disconnected` no `/`

O backend subiu, mas não conseguiu se conectar ao MongoDB. Verifique o valor de `MONGO_URI` e se o container do Mongo está acessível na rede do Docker.

### Feedback textual indisponível

Se `OPENAI_API_KEY=dummy` estiver sendo usado, cadastro, login e persistência funcionam, mas a geração real de feedback textual por LLM irá falhar. Configure uma chave real para testar esse fluxo.

### Porta já em uso

Se `5000` ou `3000` já estiverem ocupadas, pare o processo que as utiliza ou ajuste o mapeamento de portas no `docker-compose.yml`.
