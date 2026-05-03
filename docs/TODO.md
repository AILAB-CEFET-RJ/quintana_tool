# TODO

Este arquivo registra melhorias planejadas que não bloqueiam o uso atual em oficinas com dados fictícios, mas devem ser consideradas antes de uso com dados reais ou em ambiente exposto.

## Segurança

### Alta prioridade antes de uso com dados reais

- Exigir MongoDB com autenticação em ambientes compartilhados.
- Usar HTTPS quando a aplicação sair de `localhost` ou de uma rede controlada.
- Trocar `JWT_SECRET` por uma chave aleatória forte e mantê-la fora do Git.
- Definir política de retenção e limpeza de dados por escola, oficina ou turma.
- Garantir consentimento e anonimização quando houver qualquer dado real de estudante.

### Próxima rodada técnica

- Implementar política de senha no cadastro:
  - tamanho mínimo;
  - bloqueio de senhas triviais;
  - validação de confirmação de senha no frontend.
- Impedir cadastro duplicado por `email` e `username` com tratamento amigável de erro.
- Adicionar rate limiting em:
  - `/userLogin`;
  - `/userRegister`;
  - `/model`;
  - `/model_ocr`.
- Criar testes automatizados de autorização:
  - aluno não acessa redação de outro aluno;
  - aluno não acessa analytics de professor;
  - professor não acessa turma/atividade de outro professor;
  - professor não edita tema de outro professor;
  - endpoint protegido retorna `401` sem token.
- Registrar logs estruturados de ações sensíveis sem expor texto completo da redação:
  - login bem-sucedido;
  - falha de login;
  - criação/edição de turma;
  - criação/edição de atividade;
  - submissão de redação;
  - correção de redação pelo professor.

### Melhorias de operação

- Criar script dedicado de limpeza de dados por `seed_batch`, separado do script de carga.
- Documentar rotação de `JWT_SECRET` e impacto em sessões ativas.
- Documentar procedimento de backup e restauração do MongoDB.
- Criar checklist operacional para oficinas:
  - conferir `APP_MODE`;
  - conferir `CORS_ORIGINS`;
  - conferir `MONGO_DB_NAME`;
  - carregar dados fictícios;
  - testar login de aluno e professor;
  - limpar dados ao final, quando necessário.

### Futuro

- Avaliar login institucional ou SSO para uso contínuo em escolas.
- Implementar papéis mais granulares, como `admin`, `coordenador` e `professor`.
- Adicionar auditoria consultável por administradores.
- Avaliar expiração curta com refresh token se a ferramenta passar a ser usada fora de oficinas.

## Desempenho

### Antes de oficinas maiores

- Executar teste operacional com volume maior que o esperado na oficina:
  - login de professor;
  - abertura da aba `Análise da turma`;
  - segunda abertura da mesma análise para verificar ganho do cache;
  - login de aluno;
  - abertura de `Minhas redações`;
  - abertura do detalhe de uma redação.
- Registrar tempos aproximados de resposta dos endpoints principais:
  - `/redacoes`;
  - `/redacoes/<id>`;
  - `/professores/<professor>/analytics`;
  - `/classes`;
  - `/activities`;
  - `/students/<username>/activities`.
- Testar o acesso com múltiplos dispositivos na mesma rede local.

### Próxima rodada técnica

- Adicionar logs estruturados de tempo por endpoint no backend, incluindo:
  - usuário;
  - perfil;
  - endpoint;
  - filtros usados;
  - tempo total;
  - quantidade de documentos retornados.
- Implementar cache mais robusto para analytics, caso a aplicação tenha múltiplos processos ou instâncias:
  - Redis;
  - MongoDB como cache persistente;
  - cache por `teacher`, `class_id`, `activity_id` e `group_by`.
- Pré-calcular painéis de professor por atividade ou turma quando houver grande volume de redações.
- Criar invalidação mais seletiva do cache:
  - invalidar apenas professor afetado;
  - invalidar apenas turma/atividade afetada;
  - manter cache de consultas independentes.
- Avaliar paginação server-side também para:
  - alunos;
  - temas;
  - submissões de atividade.

### Futuro

- Criar script de teste de carga simples para simular acessos simultâneos.
- Adicionar métricas de observabilidade:
  - tempo médio por endpoint;
  - percentil 95;
  - taxa de erro;
  - número de documentos processados por analytics.
- Avaliar workers/background jobs para geração de analytics pesados.
- Avaliar pré-agregações no MongoDB para dashboards de professor em bases grandes.

## Confiabilidade da oficina

### Próxima frente prática

- Criar checklist operacional para executar antes de cada oficina:
  - MongoDB ativo;
  - backend ativo;
  - frontend ativo;
  - login de professor funcionando;
  - login de aluno funcionando;
  - dados fictícios carregados;
  - analytics de professor abrindo;
  - página `Minhas redações` abrindo para aluno.
- Criar script de health check para validar automaticamente:
  - conexão com MongoDB;
  - resposta do backend;
  - autenticação de professor;
  - autenticação de aluno;
  - existência de temas, turmas, atividades e redações;
  - acesso aos endpoints principais com token.
- Documentar um plano de contingência para oficina:
  - banco previamente semeado;
  - usuários e senhas impressos ou salvos localmente;
  - screenshots dos painéis principais;
  - alternativa de demonstração caso a rede falhe.
- Registrar um roteiro de smoke test manual de 5 minutos antes da oficina.

## Usabilidade

### Melhorias futuras

- Revisar textos dos painéis para reduzir ambiguidade.
- Melhorar estados vazios:
  - aluno sem redações;
  - professor sem turmas;
  - turma sem atividade;
  - atividade sem submissões.
- Melhorar mensagens de erro no frontend para diferenciar:
  - backend fora do ar;
  - MongoDB indisponível;
  - sessão expirada;
  - acesso negado.
- Testar layout em:
  - notebooks antigos;
  - tablets;
  - celulares;
  - projetor.
- Criar fluxo guiado para primeiro acesso de professor e aluno.

## Qualidade pedagógica

### Melhorias futuras

- Revisar com professores as interpretações dos painéis:
  - radar médio;
  - linha do tempo por competência;
  - grupos pedagógicos;
  - alertas;
  - prioridades de estudo.
- Evitar conclusões fortes quando há poucas redações por estudante ou turma.
- Indicar explicitamente quando uma análise usa poucos dados.
- Melhorar textos de diagnóstico e próxima ação.
- Criar material de apoio explicando:
  - diferença entre nota total e competências;
  - como interpretar radar;
  - como usar heatmap;
  - como transformar alertas em planejamento docente.

## Governança de dados

### Melhorias futuras

- Padronizar nomes de `seed_batch` por oficina, escola e data.
- Registrar metadados de carga:
  - corpus usado;
  - data da carga;
  - responsável;
  - quantidade de usuários, turmas, atividades e redações criadas.
- Criar script para exportar resumo de uma oficina sem expor textos completos.
- Impedir mistura acidental de dados fictícios e dados reais.
- Definir política de limpeza e retenção por oficina.

## Observabilidade e suporte

### Melhorias futuras

- Criar endpoint de health check mais completo:
  - versão da aplicação;
  - banco configurado;
  - status do MongoDB;
  - modo de operação;
  - cache de analytics habilitado ou não.
- Registrar versão ou commit do código usado na oficina.
- Adicionar logs mínimos para falhas de autenticação, erro de banco e erro de analytics.
- Criar checklist de diagnóstico para suporte durante a oficina.

## Reprodutibilidade

### Melhorias futuras

- Permitir configurar seed aleatória no script de carga.
- Documentar corpus e arquivos usados em cada carga.
- Gerar relatório final da carga com:
  - usuários criados;
  - professores;
  - turmas;
  - atividades;
  - temas;
  - contagem de redações por aluno e por professor.
- Permitir recriar exatamente a mesma base fictícia quando necessário.

## Qualidade de código e testes

### Melhorias futuras

- Criar testes de backend para:
  - login;
  - autorização;
  - paginação de redações;
  - analytics;
  - cache de analytics;
  - limpeza por `seed_batch`.
- Criar testes mínimos de frontend para:
  - login;
  - home do aluno;
  - home do professor;
  - abertura de detalhes da redação;
  - checklist de reescrita.
- Criar smoke test automatizado para o fluxo principal da oficina.

## Ética e comunicação

### Melhorias futuras

- Incluir aviso de que a avaliação automática não substitui o professor.
- Explicitar quando os dados são fictícios.
- Para uso com dados reais, documentar necessidade de consentimento e anonimização.
- Criar texto curto para professores apresentarem a ferramenta aos estudantes.
- Evitar linguagem que sugira que a nota automática é uma verdade absoluta.
