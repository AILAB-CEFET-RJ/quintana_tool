# Instalação e execução

Este documento descreve como preparar e executar o Quintana localmente.

## Visão geral dos serviços

A aplicação possui três partes principais:

- MongoDB: banco de dados usado para usuários, temas e redações.
- Backend Flask: API em `http://localhost:5000`.
- Frontend Next.js: interface Web em `http://localhost:3000`.

## Pré-requisitos

- Python 3.10 ou superior.
- Node.js e npm.
- Docker, recomendado para subir o MongoDB local.

Em ambientes Linux/WSL, caso `pip` não esteja instalado:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip
```

## Subir o MongoDB

Em um terminal separado:

```bash
docker run --rm --name quintana-mongo -p 27017:27017 mongo:7
```

Se o nome `quintana-mongo` já estiver em uso, verifique se o container já está rodando:

```bash
docker ps
```

Se existir um container parado com esse nome, remova ou inicie novamente:

```bash
docker start quintana-mongo
```

ou:

```bash
docker rm quintana-mongo
docker run --rm --name quintana-mongo -p 27017:27017 mongo:7
```

O banco `textgrader` e as coleções são criados automaticamente quando a aplicação grava os primeiros dados.

## Instalar e subir o backend

Use outro terminal.

Entre na pasta do backend:

```bash
cd ~/ailab/quintana_tool/backend
```

Instale as dependências:

```bash
python3 -m pip install -r requirements.txt
```

Suba o backend:

```bash
MONGO_URI=mongodb://localhost:27017 OPENAI_API_KEY=dummy python3 app.py
```

O backend ficará disponível em:

```text
http://localhost:5000
```

Para testar:

```bash
curl http://localhost:5000/
```

A resposta esperada é:

```text
OK!
```

### Variáveis de ambiente do backend

Obrigatórias para cadastro, login, temas e persistência:

```bash
MONGO_URI=mongodb://localhost:27017
```

Obrigatória para geração real de feedback textual por LLM:

```bash
OPENAI_API_KEY=<sua_chave>
```

Para testar apenas cadastro, login e navegação, pode usar:

```bash
OPENAI_API_KEY=dummy
```

Opcionais, usadas apenas no fluxo de OCR por imagem:

```bash
SUBSCRIPTION_KEY=<chave_azure>
ENDPOINT=<endpoint_azure>
```

## Instalar e subir o frontend

Use outro terminal.

Entre na pasta do frontend:

```bash
cd ~/ailab/quintana_tool/frontend
```

Instale as dependências:

```bash
npm install --no-package-lock
```

Para desenvolvimento:

```bash
npm run dev
```

Para executar a versão de produção local:

```bash
npm run build
npm run start
```

O frontend ficará disponível em:

```text
http://localhost:3000
```

A API consumida pelo frontend está configurada em:

```text
frontend/src/config/config.js
```

Valor padrão:

```js
export const API_URL = 'http://localhost:5000';
```

## Ordem recomendada de subida local

1. Subir o MongoDB.
2. Subir o backend Flask.
3. Subir o frontend Next.js.
4. Acessar `http://localhost:3000`.

## Primeiro teste manual

1. Acesse `http://localhost:3000/quintana/cadastro`.
2. Crie um usuário do tipo `Aluno`.
3. Faça login.
4. Para submeter redações, é necessário existir pelo menos um tema.
5. Crie um usuário do tipo `Professor`.
6. Faça login como professor e cadastre um tema em `Criar novo tema`.
7. Volte ao usuário aluno, escolha o tema e envie uma redação.

## Reiniciar serviços

### Backend

No terminal onde o backend está rodando:

```bash
Ctrl+C
```

Depois:

```bash
cd ~/ailab/quintana_tool/backend
MONGO_URI=mongodb://localhost:27017 OPENAI_API_KEY=dummy python3 app.py
```

### Frontend

No terminal onde o frontend está rodando:

```bash
Ctrl+C
```

Depois:

```bash
cd ~/ailab/quintana_tool/frontend
npm run build
npm run start
```

### MongoDB

Se o Mongo foi iniciado com `--rm`, parar o container remove a instância, mas os dados também serão perdidos caso não haja volume configurado.

Para parar:

```bash
docker stop quintana-mongo
```

Para subir novamente:

```bash
docker run --rm --name quintana-mongo -p 27017:27017 mongo:7
```

## Execução com Docker Compose

O repositório possui um `docker-compose.yml` com serviços para backend, frontend e Ollama.

Exemplo:

```bash
MONGO_URI=mongodb://host.docker.internal:27017 OPENAI_API_KEY=<sua_chave> docker compose up --build
```

Observação: o `docker-compose.yml` atual não declara um serviço MongoDB. Por isso, o Mongo precisa estar acessível externamente e o valor de `MONGO_URI` deve apontar para ele.

Em Linux, dependendo da configuração do Docker, `host.docker.internal` pode não estar disponível. Nesses casos, prefira o fluxo local descrito acima ou ajuste o compose para incluir um serviço MongoDB na mesma rede.

## Problemas comuns

### `ModuleNotFoundError: No module named 'pymongo'`

As dependências do backend não foram instaladas.

```bash
cd ~/ailab/quintana_tool/backend
python3 -m pip install -r requirements.txt
```

### `No module named pip`

Instale o `pip`:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip
```

### Cadastro não faz nada ou mostra erro de conexão

Verifique se o backend está rodando em `http://localhost:5000`:

```bash
curl http://localhost:5000/
```

### Erro de conexão com MongoDB

Verifique se o container está rodando:

```bash
docker ps
```

E confirme se o backend foi iniciado com:

```bash
MONGO_URI=mongodb://localhost:27017
```

### Feedback textual indisponível

Se `OPENAI_API_KEY=dummy` estiver sendo usado, cadastro/login e persistência funcionam, mas a geração real de feedback textual por LLM pode falhar. Configure uma chave real para testar esse fluxo.
