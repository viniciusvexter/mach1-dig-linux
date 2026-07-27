# Arquitetura do Repositorio

## Objetivo

Manter um monorepo Linux para drivers de coolers com display LCD, com foco principal no MACH1 DIG.

## Principios

- Um app por pasta em `apps/`
- Artefatos compilados em `dist/`
- Documentacao e decisoes tecnicas em `docs/`
- Scripts de automacao em `scripts/`

## Apps

### apps/mach1

Modulo principal do projeto. Contem:

- CLI de controle do display MACH1
- Integracao de sensores e logica de exibicao
- Build de pacote Debian
- Estrutura de empacotamento em `packaging/deb/`

### apps/ocypus

Modulo secundario para hardware Ocypus A40, mantido no mesmo padrao operacional.

## Distribuicao

- Pacotes `.deb` produzidos pelo app MACH1 sao exportados para `dist/mach1/`.
- O codigo fonte e os artefatos de release ficam separados para facilitar manutencao.

## Evolucao recomendada

- Criar `libs/displaystorm_common` para reduzir duplicacao entre apps
- Adicionar testes automatizados por app
- Adicionar pipeline CI para lint, teste e build