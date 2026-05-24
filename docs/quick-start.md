# Quick start local

Este guia resume os comandos mínimos para iniciar o Quintana em ambiente local.
Para instalação completa, configuração de variáveis e alternativas com Docker Compose,
consulte [`docs/instalacao-e-execucao.md`](./instalacao-e-execucao.md).

## Pré-requisitos

- Docker instalado, para subir o MongoDB local.
- Dependências do backend instaladas.
- Dependências do frontend instaladas com `npm install`.
- Arquivo `.env` configurado na raiz do projeto.

O `.env` deve conter, no mínimo:

```env
MONGO_URI=mongodb://localhost:27017
JWT_SECRET=troque-esta-chave
OPENAI_API_KEY=dummy
```

Se você tiver uma chave real da OpenAI configurada no `.env`, use-a no lugar de
`dummy`. Para testar apenas navegação, cadastro, login e dados já carregados,
`dummy` é suficiente.

## 1. Iniciar o MongoDB

Se o container `quintana-mongo` já existe:

```bash
docker start quintana-mongo
```

Se o container ainda não existe:

```bash
docker run -d --name quintana-mongo -p 27017:27017 mongo:7
```

## 2. Iniciar o backend

Em um segundo terminal, a partir da raiz do projeto:

```bash
cd backend
python3 app.py
```

Por padrão, o backend Flask fica disponível em:

```text
http://localhost:5000
```

## 3. Iniciar o frontend

Em um terceiro terminal, a partir da raiz do projeto:

```bash
cd frontend
npm run dev
```

Por padrão, o frontend Next.js fica disponível em:

```text
http://localhost:3000
```

## 4. Acessar a aplicação

Abra no navegador:

```text
http://localhost:3000/quintana/login
```

## Observações rápidas

- Depois de alterar o `.env`, reinicie o backend.
- Se o MongoDB já estiver rodando, não é necessário recriar o container.
- Para parar o MongoDB:

```bash
docker stop quintana-mongo
```

- Para testar recuperação de senha localmente, use `PASSWORD_RESET_DEV_MODE=true`
  no `.env`; nesse modo, o link de redefinição aparece no terminal do backend.
