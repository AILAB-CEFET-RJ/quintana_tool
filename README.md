
# Quintana

**Quintana** é uma ferramenta de avaliação automatizada de redações em língua portuguesa, baseada nas cinco competências do Exame Nacional do Ensino Médio (ENEM). Desenvolvida com foco educacional, permite a submissão de textos dissertativo-argumentativos por alunos e retorna, de forma automática, as notas preditas por competência e sugestões de melhoria.

Este projeto visa demonstrar como técnicas modernas de Processamento de Linguagem Natural podem ser aplicadas para ampliar o acesso a ferramentas educacionais com retorno formativo, objetivo e explicável.

## 🚀 Como executar a aplicação

Para executar a aplicação localmente, é necessário ter o Docker instalado e um servidor MongoDB acessível.

1. Defina a variável `MONGO_URI` com o endereço do seu MongoDB.
2. Execute o seguinte comando para subir a aplicação com Docker Compose:

```bash
MONGO_URI=<endereço_do_mongodb> docker compose up --build
```
3. Em seguida, baixe o modelo de linguagem utilizado para geração de feedbacks:
```bash
docker exec -it ollama ollama pull gemma:7b
```
A aplicação será iniciada com o frontend disponível em `http://localhost:3000`.

Obs.: Certifique-se de que a porta do MongoDB está acessível e que o Docker está rodando corretamente em sua máquina.


## 📹 Demonstração

- Vídeo no YouTube: [https://youtu.be/RLO5hGGK63c](https://youtu.be/RLO5hGGK63c)


## 📄 Licença

Distribuído sob a licença [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---

Projeto desenvolvido por pesquisadores do Programa de Pós-Graduação em Ciência da Computação do CEFET/RJ.
