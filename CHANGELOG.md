# Changelog

Todas as mudanças relevantes do Quintana devem ser registradas neste arquivo.

O projeto adota versionamento semântico simplificado (`MAJOR.MINOR.PATCH`):

- `MAJOR`: mudanças grandes de arquitetura, fluxo principal ou compatibilidade.
- `MINOR`: novas funcionalidades visíveis para estudantes, professores ou equipe de oficina.
- `PATCH`: correções, ajustes visuais e melhorias pequenas.

## [1.0.0] - 2026-05-24

Versão inicial considerada madura para uso em oficinas.

### Adicionado

- Fluxo do estudante com submissão de redação, radar de competências, linha do tempo de progresso, prioridades de estudo, mapa de feedback e checklist de reescrita.
- Comparação entre versões de uma redação, incluindo evolução por competência e comparação textual com trechos adicionados/removidos.
- Fluxo do professor com análise da turma, heatmap aluno por competência, ranking de competências problemáticas, alertas pedagógicos e agrupamentos por necessidade pedagógica.
- Cadastro de temas, turmas e atividades.
- Status de submissões por atividade.
- Relatórios PDF por turma e por aluno.
- Revisão do professor sobre avaliação da IA, com ações para aceitar notas IA ou registrar ajustes próprios.
- Registro da origem da avaliação IA (`ai_evaluation`) e da revisão humana (`teacher_review`).
- Validação de qualidade da avaliação IA (`ai_quality`), com sinalização de avaliações que requerem revisão.
- Modo oficina, com banner, atalhos de login, dados curados e bloqueio de remoções destrutivas.
- Recuperação de senha por token, com modo local via log do backend e suporte a SMTP.
- Documentação de instalação, segurança, desempenho, funcionalidades, esquema do banco, quick start, checklist e roteiro de oficina.

### Alterado

- Interface principal, login, criação de temas e página de redação foram refinadas para um visual mais consistente.
- Página `Sobre` passou a explicar o nome Quintana e a homenagem a Mário Quintana.
- Notas automáticas foram rotuladas explicitamente como `Nota IA`; avaliações humanas foram rotuladas como `Nota professor`.
- Listagem de redações do estudante passou a mostrar data de submissão e ordenação por coluna.
- Seleção de alunos em turmas passou a ter busca por nome.
- Professores passaram a visualizar todos os temas disponíveis, editando/removendo apenas os próprios.

### Corrigido

- Ordem das notas por competência na submissão, evitando permutação entre visualizações.
- Erro no status de submissões de atividades.
- Logout exigindo dois cliques.
- Exposição desnecessária de e-mails de alunos em listas pedagógicas.
- Fallback de feedback quando a chave da API da OpenAI está ausente ou inválida.

### Impacto no manual

- Documentar o modo oficina, incluindo banner, atalhos de login e bloqueio de remoções.
- Documentar relatórios PDF por turma e por aluno.
- Documentar comparação textual entre versões de redação.
- Documentar o aviso `Avaliação IA requer revisão`.
- Documentar a diferença entre `Nota IA`, `Nota professor`, `Feedback IA` e `Feedback professor`.
- Documentar o fluxo de revisão do professor: aceitar notas IA ou salvar revisão ajustada.
- Atualizar telas de login, tema, redação, minhas redações, análise da turma e turmas/atividades.

### Observações para comunicação

- Esta versão deve ser usada como referência inicial para atualização do manual do usuário.
- Mudanças futuras com impacto em tela, fluxo ou regra de negócio devem trazer uma seção `Impacto no manual`.
