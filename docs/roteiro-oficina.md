# Roteiro de oficina

Este documento descreve como preparar e conduzir uma demonstração do Quintana em modo oficina.

## Objetivo

O modo oficina reduz ruído operacional durante demonstrações e formações. Ele prioriza os fluxos pedagógicos:

- estudante acompanhando progresso e reescrita;
- professor analisando padrões da turma;
- revisão humana sobre a avaliação da IA;
- geração de relatórios.

## Configuração

No `.env`, use:

```env
APP_MODE=workshop
NEXT_PUBLIC_APP_MODE=workshop
PASSWORD_RESET_DEV_MODE=true
```

Reinicie backend e frontend depois de alterar o `.env`.

## Carga de dados

Execute a carga com o atalho `--workshop`, que ativa trajetórias controladas de progresso:

```bash
python backend/scripts/load_corpus_seed.py \
  --input backend/data/tema-10.json backend/data/tema-34.json backend/data/tema-100.json \
  --mongo-uri mongodb://localhost:27017 \
  --workshop
```

O batch padrão do modo oficina é `workshop_demo`, a menos que `--seed-batch` seja informado explicitamente.

## Contas de demonstração

Senha padrão:

```text
123456
```

Contas recomendadas:

```text
Aluno: aluno001@quintana.local
Professor: mariana.oliveira@quintana.local
```

No modo oficina, a tela de login mostra botões de acesso rápido para essas contas.

## Fluxo sugerido

1. Entrar como aluno demo.
2. Abrir `Minhas redações`.
3. Observar radar agregado das competências.
4. Abrir uma redação.
5. Ver plano de ação, checklist e feedback por competência.
6. Abrir a aba `Versões`.
7. Mostrar comparação textual entre versões e evolução das notas.
8. Sair e entrar como professor demo.
9. Abrir `Análise da turma`.
10. Mostrar alertas, ranking, heatmap, distribuição por competência e grupos pedagógicos.
11. Baixar relatório da turma.
12. Selecionar um aluno e baixar relatório do aluno.
13. Abrir uma redação recebida.
14. Demonstrar `Aceitar notas IA` ou `Salvar revisão`.

## Proteções do modo oficina

Quando `APP_MODE=workshop`:

- o backend bloqueia remoção de temas, turmas e atividades;
- o frontend oculta botões de exclusão dessas entidades;
- a interface exibe um banner indicando que o modo oficina está ativo;
- a tela inicial e o login destacam o contexto de demonstração.

Essas proteções evitam perda acidental dos dados curados durante a oficina.

## Observações

- As notas dos painéis do professor continuam baseadas na avaliação automática da IA.
- As avaliações marcadas como `Requer revisão` devem ser usadas para explicar que a IA apoia, mas não substitui, o professor.
- Para restaurar o cenário, rode novamente o comando de carga com `--workshop`.
