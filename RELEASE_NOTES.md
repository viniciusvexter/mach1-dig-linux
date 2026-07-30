# Release Notes

## Version 1.7.0 (Latest)

### ✨ Features & Fixes
- **Mach1**: Refatoração da comunicação IPC assíncrona.
- **Mach1**: Implementação de um novo Tray Icon.
- **Mach1**: Correção na leitura e exibição do display de RPM.

### ♻️ Refactoring
- Reorganização de toda a estrutura do repositório (formato monorepo).
- Separação clara e modular entre os aplicativos `mach1` e `ocypus`.
- Limpeza e remoção de artefatos obsoletos (ex: versão v1.0-1).

---

## Histórico de Versões Anteriores (v1.0.0 - v1.6.0)

Nas versões anteriores, o projeto estabeleceu toda a fundação para o controle avançado dos coolers no Linux:

### ✨ Funcionalidades Base
- **Interface Gráfica (GUI)**: Desenvolvida uma interface visual idêntica à versão oficial do Windows (MACH1 Control Center).
- **Comunicação HID**: Implementação de auto-detecção da interface USB (VID: 0x1A2C).
- **Estabilidade e Resiliência**: 
  - Validação avançada de retornos HID (tratamento robusto de falhas `-1` e erros de kernel USB `-71`).
  - Loop inteligente de reconexão automática em casos de desconexão física do cabo ou instabilidade.
- **Sensores em Tempo Real**: 
  - Leitura e exibição precisa da temperatura da CPU (suporte a °C e °F).
  - Leitura de métricas como consumo de energia (Watts) e velocidade da ventoinha (RPM).
- **Suporte Expandido de Hardware**: Inclusão de suporte paralelo ao cooler Ocypus A40.
- **Integração com o Sistema Operacional**: 
  - Scripts para instalação e configuração de regras do `udev`.
  - Configuração como serviço via `systemd`.
  - Pipeline e scripts para build automatizado de pacotes de distribuição Debian (`.deb`).

---

> *Este é um arquivo de Release Notes criado para manter um histórico profissional e transparente das atualizações do DisplayStorm.*
