# Implantação e atualização na AWS

Este documento registra o procedimento operacional para manter a Quintana na VM AWS usada nas oficinas.

## Premissas da VM

- Sistema operacional: Ubuntu.
- Repositório instalado em `/opt/quintana`.
- Docker Compose usado para backend, frontend e Ollama.
- Nginx usado como proxy reverso público.
- Backend Flask exposto apenas localmente em `127.0.0.1:5000`.
- Frontend Next.js exposto apenas localmente em `127.0.0.1:3000`.
- API pública roteada pelo Nginx em `/api/`.
- VM com GPU NVIDIA Tesla T4 para inferência dos modelos avaliativos.

## Acessar a VM

Na máquina local:

```bash
chmod 400 ./inovaeducacao-temp-cpu.pem
ssh -i ./inovaeducacao-temp-cpu.pem ubuntu@18.229.232.193
```

Na VM:

```bash
cd /opt/quintana
```

Confirme o diretório:

```bash
pwd
ls -la
```

O diretório deve conter, entre outros:

```text
.git
.env
backend
frontend
docker-compose.yml
```

## Variáveis de ambiente

O arquivo `.env` da VM deve ficar em `/opt/quintana/.env`.

Campos críticos:

```env
APP_MODE=demo
NEXT_PUBLIC_APP_MODE=demo
NEXT_PUBLIC_APP_VERSION=1.0.0

MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=textgrader

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://18.229.232.193,http://18.229.232.193:3000

FRONTEND_URL=http://18.229.232.193
NEXT_PUBLIC_API_URL=http://18.229.232.193/api

JWT_SECRET=troque-esta-chave
OPENAI_API_KEY=...
OLLAMA_HOST=ollama
```

Observações:

- `NEXT_PUBLIC_API_URL` é incorporada no build do frontend. Se esse valor mudar, é obrigatório rebuildar o frontend.
- `FRONTEND_URL` é usado para links de redefinição de senha.
- Não versionar `.env`.
- Em ambiente público, trocar `JWT_SECRET` por uma chave segura.

Gerar `JWT_SECRET`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Docker Compose

O serviço `flask-app` deve expor a GPU:

```yaml
flask-app:
  gpus: all
```

Portas recomendadas:

```yaml
flask-app:
  ports:
    - "127.0.0.1:5000:5000"

frontend:
  ports:
    - "127.0.0.1:3000:3000"

ollama:
  ports:
    - "127.0.0.1:11434:11434"
```

Evite expor serviços internos diretamente para a Internet.

## Nginx

Conferir configuração efetiva:

```bash
sudo nginx -T | grep -n "server_name\|listen\|location\|proxy_pass\|root"
```

Configuração esperada:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3000;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
    }
}
```

Testar e recarregar Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## GPU e NVIDIA Container Toolkit

Verificar GPU no host:

```bash
nvidia-smi
```

Testar GPU via Docker:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Se aparecer erro semelhante a `failed to discover GPU vendor from CDI`, instalar/configurar o NVIDIA Container Toolkit:

```bash
sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Depois, repetir:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Verificar GPU dentro do backend:

```bash
docker compose exec -T flask-app python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda:", torch.cuda.is_available())
print("device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
PY
```

Saída esperada:

```text
cuda: True
device: Tesla T4
```

Se `torch` estiver instalado mas falhar com `libtorch_global_deps.so`, reinstalar dentro do container:

```bash
docker compose exec -T flask-app python -m pip uninstall -y torch
docker compose exec -T flask-app python -m pip install --no-cache-dir torch
docker compose restart flask-app
```

## Atualizar a aplicação

Na VM:

```bash
cd /opt/quintana
git status
git pull
docker compose up -d --build frontend flask-app
```

Se houver alteração local em `docker-compose.yml`, por exemplo `gpus: all`, preserve-a com stash:

```bash
git stash push -m "vm docker compose gpu" docker-compose.yml
git pull
git stash pop
```

Se o `stash pop` gerar conflito, resolva o conflito antes de subir os containers.

Depois:

```bash
docker compose up -d --build frontend flask-app
```

## Rebuild do frontend

Quando mudar qualquer variável `NEXT_PUBLIC_*`, o frontend precisa ser rebuildado.

```bash
docker compose exec frontend sh -lc 'rm -rf .next && yarn build'
docker compose restart frontend
```

Confirmar que a URL da API entrou no bundle:

```bash
docker compose exec frontend sh -lc 'grep -R "18.229.232.193/api" -n .next/static .next/server 2>/dev/null | head'
```

Se o navegador ainda chamar `localhost:5000`, limpar cache ou testar em aba anônima.

## Validação após atualização

Verificar containers:

```bash
docker compose ps
```

Testar frontend e backend localmente na VM:

```bash
curl -i http://127.0.0.1:3000/
curl -i http://127.0.0.1:5000/
```

Testar via Nginx:

```bash
curl -i http://18.229.232.193/
curl -i http://18.229.232.193/api/
```

Testar login direto na API:

```bash
curl -i -X POST http://18.229.232.193/api/userLogin \
  -H "Content-Type: application/json" \
  -d '{"email":"aluno001@quintana.local","password":"123456"}'
```

## Testar inferência

Acompanhar logs:

```bash
docker compose logs -f flask-app
```

Submeter uma redação pela interface.

Na primeira submissão com modelos LoRA, é normal demorar mais, pois o backend carrega:

- tokenizer;
- modelo base;
- adapters LoRA;
- janelas `sliding_window_512`, quando aplicável.

As submissões seguintes tendem a ser mais rápidas por causa do cache em memória.

## Diagnóstico rápido de 502

Se o navegador exibir:

```text
502 Bad Gateway
```

verifique:

```bash
docker compose ps
curl -i http://127.0.0.1:3000/
curl -i http://127.0.0.1:5000/
docker compose logs --tail=100 frontend
docker compose logs --tail=120 flask-app
```

Interpretação:

- `frontend` em `Restarting`: normalmente erro de build Next.js.
- `curl 127.0.0.1:3000` falha: Nginx não consegue acessar o frontend.
- `curl 127.0.0.1:5000` falha: backend não subiu.
- backend demora após rebuild: pode estar instalando dependências ou carregando modelos.

## Sequência resumida

Atualização padrão:

```bash
ssh -i ./inovaeducacao-temp-cpu.pem ubuntu@18.229.232.193
cd /opt/quintana
git status
git pull
docker compose up -d --build frontend flask-app
docker compose ps
curl -i http://127.0.0.1:3000/
curl -i http://127.0.0.1:5000/
```

Atualização com alteração local no `docker-compose.yml`:

```bash
cd /opt/quintana
git stash push -m "vm docker compose gpu" docker-compose.yml
git pull
git stash pop
docker compose up -d --build frontend flask-app
```
