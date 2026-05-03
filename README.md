
# Quintana

**Quintana** é uma ferramenta de avaliação automatizada de redações em língua portuguesa, baseada nas cinco competências do Exame Nacional do Ensino Médio (ENEM). Desenvolvida com foco educacional, permite a submissão de textos dissertativo-argumentativos por alunos e retorna, de forma automática, as notas preditas por competência e sugestões de melhoria.

Este projeto visa demonstrar como técnicas modernas de Processamento de Linguagem Natural podem ser aplicadas para ampliar o acesso a ferramentas educacionais com retorno formativo, objetivo e explicável.

## ✨ Por que Quintana?

O nome **Quintana** é uma homenagem a **Mário Quintana**, escritor, poeta, jornalista e tradutor brasileiro. Reconhecido como o poeta das “coisas simples”, Quintana construiu uma obra marcada pela delicadeza, pela ironia, pela profundidade e pelo cuidado técnico com a linguagem.

Ao adotar esse nome, a ferramenta busca fazer referência a essa relação sensível e rigorosa com a escrita. Assim como a obra de Mário Quintana valoriza a expressão em língua portuguesa e a capacidade de comunicar ideias com clareza, simplicidade e profundidade, a ferramenta **Quintana** tem como propósito apoiar estudantes no desenvolvimento de suas redações, oferecendo avaliações e sugestões que contribuam para o aprimoramento da escrita.

A escolha do nome também reforça a intenção educacional do projeto: não substituir o olhar humano sobre o texto, mas oferecer um apoio formativo que ajude o estudante a refletir sobre sua produção escrita e a aperfeiçoá-la ao longo do processo de aprendizagem.

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

## 📚 Documentação

- [Instalação e execução](docs/instalacao-e-execucao.md)
- [Funcionalidades para estudantes](docs/funcionalidades-estudante.md)
- [Arquitetura das funcionalidades para estudantes](docs/arquitetura-funcionalidades-estudante.md)
- [Funcionalidades para professores](docs/funcionalidades-professor.md)
- [Arquitetura das funcionalidades para professores](docs/arquitetura-funcionalidades-professor.md)
- [Esquema lógico do banco de dados](docs/esquema-banco.md)
- [Segurança para oficinas](docs/seguranca-oficinas.md)
- [Checklist operacional de oficina](docs/checklist-oficina.md)


## 📄 Licença

Distribuído sob a licença [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---

Projeto desenvolvido por pesquisadores do Programa de Pós-Graduação em Ciência da Computação do CEFET/RJ.
