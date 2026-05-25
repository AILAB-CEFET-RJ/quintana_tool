# Controle de versões

Este documento define como registrar versões, comunicar mudanças e manter o manual do usuário alinhado à evolução do Quintana.

## Política de versionamento

O Quintana usa versionamento semântico simplificado:

```text
MAJOR.MINOR.PATCH
```

Exemplos:

```text
1.0.0
1.1.0
1.1.1
```

## Critérios

### MAJOR

Use quando houver mudança grande de arquitetura, fluxo principal ou compatibilidade.

Exemplos:

- nova estrutura de autenticação;
- migração incompatível de banco de dados;
- reformulação completa dos fluxos de estudante ou professor;
- mudança relevante no contrato das APIs.

### MINOR

Use quando houver nova funcionalidade visível ao usuário, sem quebrar o uso atual.

Exemplos:

- relatórios PDF;
- modo oficina;
- comparação textual entre versões;
- nova visualização para professores;
- novo fluxo de revisão.

### PATCH

Use para correções, ajustes visuais e melhorias pequenas.

Exemplos:

- correção de bug;
- ajuste de texto;
- melhoria de layout;
- melhoria de mensagem de erro;
- ajuste de documentação sem mudança funcional.

## Arquivos obrigatórios por release

Toda nova versão deve atualizar:

- `CHANGELOG.md`

Quando houver mudança operacional ou de uso, também atualizar:

- `README.md`, se a mudança afetar visão geral ou documentação listada;
- `docs/instalacao-e-execucao.md`, se a mudança afetar instalação/subida;
- documentação funcional em `docs/`, se a mudança afetar estudantes, professores ou oficinas;
- manual do usuário, quando mantido em artefato separado.

## Quando há impacto no manual

Considere que há impacto no manual quando a mudança inclui:

- nova tela;
- novo botão;
- nova aba;
- novo campo visível;
- mudança em texto de tela;
- mudança em fluxo de login, cadastro, senha ou navegação;
- mudança em submissão, feedback, nota, revisão ou relatório;
- mudança em funcionalidades de professor;
- mudança em modo oficina;
- nova regra de permissão;
- nova mensagem de erro ou alerta importante.

Nesses casos, o `CHANGELOG.md` deve conter uma seção:

```md
### Impacto no manual
```

## Checklist de release

Antes de liberar uma nova versão:

- [ ] Definir número da versão.
- [ ] Atualizar `NEXT_PUBLIC_APP_VERSION` no `.env` do ambiente de release.
- [ ] Atualizar o valor padrão de `APP_VERSION` em `frontend/src/config/config.js`, quando necessário.
- [ ] Atualizar `.env.example` com a versão corrente.
- [ ] Atualizar `CHANGELOG.md`.
- [ ] Registrar impactos no manual.
- [ ] Atualizar documentação técnica afetada.
- [ ] Rodar validações de backend.
- [ ] Rodar validações de frontend.
- [ ] Testar fluxos principais afetados.
- [ ] Comunicar responsáveis pelo manual.
- [ ] Criar tag Git da versão, quando aplicável.

## Validações recomendadas

Backend:

```bash
python3 -m py_compile backend/app.py backend/database.py backend/schemas.py
```

Frontend:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

## Tags Git

Para marcar uma versão:

```bash
git tag -a v1.0.0 -m "Versão inicial para oficinas"
git push origin v1.0.0
```

Para listar versões:

```bash
git tag
```

## Modelo de comunicação para o manual

```text
Olá, Jorge.

A versão vX.Y.Z do Quintana foi liberada.

Mudanças com impacto no manual:
- ...
- ...
- ...

Arquivo de referência:
CHANGELOG.md, seção vX.Y.Z.

Abraços,
Eduardo
```

## Versão de referência

A versão `v1.0.0` corresponde à primeira versão considerada madura para uso em oficinas.

## Versão exibida na aplicação

A página `Sobre` exibe a versão corrente a partir da variável pública:

```env
NEXT_PUBLIC_APP_VERSION=1.0.0
```

Se a variável não estiver definida, o frontend usa o valor padrão em `frontend/src/config/config.js`.

Ao liberar uma nova versão, mantenha sincronizados:

- tag Git;
- seção correspondente em `CHANGELOG.md`;
- `NEXT_PUBLIC_APP_VERSION` no ambiente;
- `.env.example`;
- versão exibida na página `Sobre`.
