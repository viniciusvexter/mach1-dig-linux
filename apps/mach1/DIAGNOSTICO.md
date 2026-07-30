# Relatório de Diagnóstico e Solução: Display Cooler MACH1 DIG

**Data do Diagnóstico:** 28/07/2026  
**Status do Serviço:** Ativo (`mach1-lcd.service`), porém display inoperante (sem exibir informações).

---

## 1. Sintoma

O display digital do cooler parou de apresentar as informações de temperatura da CPU e consumo em Watts, mesmo com o serviço `mach1-lcd.service` rodando com status `active (running)`.

---

## 2. Investigação e Causa Raiz

Após análise dos logs do sistema (`dmesg` e `journalctl`), identificou-se que o problema é composto por **duas causas principais**:

### A. Erro de Comunicação USB no Kernel (`EPROTO / Erro -71`)
Nos logs do kernel (`dmesg`), foram registradas falhas de protocolo USB na porta física onde o controlador do display (China Resource Semico Co., Ltd., VID: `0x1A2C`, PID: `0x4D84`) está conectado:

```text
[ 4478.350354] usbhid 1-8:1.0: can't add hid device: -71
[ 4478.350394] usbhid 1-8:1.0: probe with driver usbhid failed with error -71
[ 5206.389633] usb 1-8: can't set config #1, error -71
```

- **Significado:** O erro `-71` no subsistema USB do Linux refere-se a `EPROTO` (Protocol Error / erro de temporização/CRC elétrico).
- **Causa:** O microcontrolador do cooler travou o estado USB interno ou houve instabilidade física na conexão do conector USB de 9 pinos na placa-mãe.

### B. Falha Silenciosa no Driver Python (`mach1-control.py`)
Ao inspecionar o código do driver [mach1-control.py](file:///home/vinicius-ferreira/Projects/displaystorm-linux/apps/mach1/mach1-control.py):

1. **Tratamento Falso de Sucesso:** A biblioteca `hidapi` em Python não lança exceções quando a chamada `send_feature_report()` falha; ela retorna um valor inteiro negativo (`-1`).
2. O código antigo não validava se o retorno de `send_feature_report()` era menor que 0. Em Python, `-1` é avaliado como um valor *truthy* (`bool(-1) == True`).
3. Por conta disso, o driver reportava no log do `systemd`:
   `Conectado ao cooler MACH1 (PID: 0x4d84) na interface 1` e `Sensor: k10temp | Temp: 35.0°C`
   ...dando a falsa impressão de que a comunicação estava ocorrendo com sucesso, enquanto as transmissões para o display falhavam silenciosamente.

---

## 3. Correções Aplicadas no Código

Foram efetuadas as seguintes correções no arquivo [mach1-control.py](file:///home/vinicius-ferreira/Projects/displaystorm-linux/apps/mach1/mach1-control.py):

1. **Validação de Código de Retorno HID:**
   - Adicionada verificação estrita `if res < 0:` em todas as chamadas de `send_feature_report()`.
   - Se a interface falhar no teste inicial, a conexão é abortada e a próxima interface é testada.

2. **Tentativa de Reconexão Automática:**
   - Atualizado o loop principal `run_display_loop()` para detectar falhas de envio ou desconexão.
   - Quando ocorre falha de transmissão, a conexão HID é fechada e o driver tenta reconectar automaticamente a cada 2 segundos.

3. **Atualização dos Artefatos do Projeto:**
   - O arquivo executável `/usr/bin/mach1-control` foi atualizado com o código corrigido.
   - O pacote `.deb` foi reconstruído em `dist/mach1/mach1-dig-linux_1.7-1_all.deb`.

---

## 5. Solução para Falha Intermitente Pós-Tempo de Uso (USB Autosuspend)

**Data do Ajuste:** 30/07/2026

### Causa Raiz Adicional Identificada:
O congelamento do display que ocorria após algum tempo de uso do computador no Linux (mas não no Windows) devia-se ao **USB Autosuspend / Selective Suspend do kernel Linux**:
- O Linux (ou gerenciadores como TLP / powertop) coloca dispositivos USB sem atividade constante em modo de economia de energia (`autosuspend_delay_ms` = 2000ms).
- Ao ser colocado em *suspend*, o microcontrolador Semico 0x1A2C trava seu estado USB interno e causa o erro `EPROTO / -71` ao ser acordado para novos dados.
- No Windows, a suspensão seletiva USB não entra em sleep para essa classe de dispositivo.

### Correções Implementadas:
1. **Regras UDEV com Desativação de Autosuspend:**
   - Adicionadas regras udev para desativar o autosuspend no barramento USB:
     ```udev
     ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTR{power/control}="on"
     ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTR{power/autosuspend}="-1"
     ```
2. **Forçagem via Sysfs e Resiliência HID:**
   - O driver tenta definir `/sys/bus/usb/devices/.../power/control` como `on` em runtime.
   - Adicionado mecanismo de 3 retentativas por pacote com **fallback automático para `write()` (Output Report)** caso o `send_feature_report()` retorne erro.
   - Tratamento de estouro de contador 32-bit (wraparound a cada ~70 min) no leitor de energia RAPL (`PowerReader`).
   - Atualização periódica do timestamp de keepalive e reconstrução do pacote `.deb` em `dist/mach1/mach1-dig-linux_1.7-1_all.deb`.
