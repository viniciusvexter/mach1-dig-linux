# Arquitetura do Repositorio

## Objetivo

Drivers de coolers com display LCD, com foco principal no MACH1 DIG.

## Principios

- Um app por pasta em `apps/`
- Artefatos compilados em `dist/`
- Documentacao e decisoes tecnicas em `docs/`
- Scripts de automacao em `scripts/`

## Apps

### apps/mach1

Modulo principal do projeto. Contem:

- Interface Gráfica (GUI) em Tkinter (`mach1-gui.py`) no estilo oficial Windows
- CLI de controle do display MACH1 (`mach1-control.py`)
- Integracao de sensores (Temperatura °C/°F, Potência Watts e Ventoinha RPM)
- Build de pacote Debian (`mach1-dig-linux_1.7-1_all.deb`)
- Estrutura de empacotamento em `packaging/deb/` e atalho `.desktop`

### apps/ocypus

Modulo secundario para hardware Ocypus A40, mantido no mesmo padrao operacional.

## Distribuicao

- Pacotes `.deb` produzidos pelo app MACH1 sao exportados para `dist/mach1/`.
- O codigo fonte e os artefatos de release ficam separados para facilitar manutencao.

## Evolucao recomendada

- Criar `libs/displaystorm_common` para reduzir duplicacao entre apps
- Adicionar testes automatizados por app
- Adicionar pipeline CI para lint, teste e build
