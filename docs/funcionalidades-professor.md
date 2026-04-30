# Funcionalidades para professores

Este documento descreve os recursos disponíveis para professores no Quintana.

## Visão geral

A área do professor permite acompanhar temas, redações recebidas, turmas, atividades e análises pedagógicas da turma. O objetivo é transformar as correções individuais em informações úteis para planejamento docente.

## Temas

O professor pode criar temas de redação que ficam disponíveis para os estudantes.

Cada tema possui:

- professor responsável;
- título;
- descrição/proposta.

Os temas são usados tanto no envio de redações quanto nas análises por desempenho temático.

## Redações recebidas

A aba `Redações recebidas` lista submissões feitas pelos estudantes.

O professor pode:

- filtrar redações;
- abrir os detalhes de uma redação;
- consultar notas do modelo;
- inserir notas por competência;
- registrar feedback do professor.

## Turmas

A aba `Turmas e atividades` permite cadastrar turmas.

Cada turma possui:

- nome;
- professor responsável;
- lista de alunos.

A lista de alunos é usada para organizar atividades e, em análises futuras, identificar estudantes esperados em uma entrega.

Também é possível editar e remover turmas pela interface.

## Atividades

Uma atividade vincula uma turma a um tema.

Cada atividade possui:

- título;
- turma;
- tema;
- prazo opcional.

Após criar uma atividade, a interface mostra um link de envio. Esse link já contém:

- `id` do tema;
- `classId` da turma;
- `activityId` da atividade.

Quando o estudante envia uma redação por esse link, a submissão fica vinculada à turma e à atividade.

Também é possível editar e remover atividades pela interface.

Cada atividade possui um botão `Status`, que mostra:

- alunos esperados;
- alunos que enviaram;
- alunos pendentes;
- alunos atrasados, quando o prazo já passou.

## Análise da turma

A aba `Análise da turma` reúne visualizações e indicadores pedagógicos.

Ela pode ser filtrada por:

- todas as turmas;
- uma turma específica;
- todas as atividades;
- uma atividade específica.

## Distribuição da turma por competência

Mostra um boxplot por competência, com:

- mínimo;
- Q1;
- mediana;
- Q3;
- máximo;
- outliers;
- média.

Essa visualização ajuda o professor a responder:

- qual competência está mais fraca;
- se uma dificuldade parece coletiva;
- qual habilidade deve ser priorizada em aula.

## Heatmap aluno x competência

Mostra uma matriz com estudantes nas linhas e competências nas colunas.

As células usam cores para indicar faixas de desempenho:

- notas muito baixas;
- notas de atenção;
- desempenho intermediário;
- bom desempenho.

O professor consegue identificar:

- estudantes com dificuldade geral;
- estudantes com dificuldade específica;
- padrões coletivos por competência;
- casos fora da curva.

## Ranking de competências problemáticas

Lista as competências com menor média da turma.

Cada item mostra:

- competência;
- média da turma;
- percentual de estudantes abaixo de 120.

Essa funcionalidade conecta diretamente a análise ao planejamento de intervenção.

## Agrupamento de alunos por necessidade pedagógica

O sistema forma grupos automaticamente por perfil pedagógico.

Exemplo:

- Reforço geral;
- Proposta de intervenção;
- Desenvolvimento argumentativo;
- Coesão textual;
- Tema e repertório;
- Norma escrita;
- Alta performance.

O agrupamento é útil para:

- oficinas;
- atividades em sala;
- reescritas orientadas;
- atendimento por necessidade.

## Evolução da turma ao longo das atividades

Mostra a evolução da média geral da turma ao longo de temas/atividades.

O professor pode alternar o agrupamento da evolução por:

- atividade;
- tema;
- dia.

Esse recurso ajuda a observar se uma intervenção pedagógica teve efeito. Por exemplo, após uma aula sobre proposta de intervenção, o professor pode verificar se a média de C5 melhorou nas entregas seguintes.

## Comparação entre tema e desempenho

Mostra uma tabela comparando desempenho por tema.

Campos exibidos:

- tema;
- média geral;
- média de C1;
- média de C2;
- média de C3;
- média de C4;
- média de C5;
- quantidade de envios.

Essa visualização ajuda a distinguir dificuldade de escrita de dificuldade com um tema específico.

## Alertas pedagógicos

O sistema gera alertas automáticos.

Alertas implementados:

- percentual elevado da turma abaixo de 120 em uma competência;
- alta dispersão em uma competência;
- queda em C3 nas duas últimas redações;
- queda brusca na nota total;
- estudante sem evolução relevante nas últimas três redações;
- baixa taxa de submissão em uma atividade;
- tema ou atividade com desempenho abaixo do padrão da turma;
- alunos sem submissão em uma atividade, quando a análise está filtrada por turma e atividade.

Os alertas ajudam o professor a identificar rapidamente pontos de atenção.
