# Driver Linux para Cooler MACH1 DIG

Este é um projeto em Python para permitir que você controle o display do seu cooler da marca MACH1 (modelo DIG) usando o sistema operacional Linux, sem depender do software original do Windows.

A comunicação com a tela é feita via protocolo USB HID. O cooler utiliza internamente uma placa controladora fabricada pela *China Resource Semico* com IDs:
- **VID:** `1A2C`
- **PID:** `4D84` ou `4C84`

## Dependências

O script foi escrito em Python 3 e requer os seguintes pacotes para rodar:
- `hid` (para comunicação USB HID)
- `psutil` (para ler a temperatura da CPU do sistema)
- `libhidapi-hidraw0` (ou similar na sua distribuição Linux)

### Instalação no Linux (Ubuntu/Debian, Fedora, Arch)

1. Instale o HIDAPI do seu sistema operacional:
   ```bash
   # Debian / Ubuntu / Mint
   sudo apt install libhidapi-hidraw0 python3-pip python3-venv

   # Fedora
   sudo dnf install hidapi python3-pip

   # Arch Linux
   sudo pacman -S hidapi python-pip
   ```

2. Clone este repositório ou navegue até esta pasta:
   ```bash
   cd mach1-dig-linux
   ```

3. Crie um ambiente virtual (opcional, mas recomendado) e instale as dependências Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Interface Gráfica (GUI Estilo Windows)

Agora o driver conta com uma **Interface Gráfica (GUI)** com o mesmo design futurista do aplicativo original do Windows para fácil controle dos seletores:

- **DISPLAY**: Ativar (`ON`) ou desativar (`OFF`) a tela LCD.
- **TEMP.**: Alternar a unidade entre Celsius (`°C`) e Fahrenheit (`°F`).
- **INFERIOR**: Alternar os dígitos inferiores entre Consumo em Watts (`W`) e Velocidade do Cooler (`RPM`).

Para executar a interface gráfica:

```bash
python3 mach1-gui.py
```

Ou através do menu de aplicações do seu sistema após instalar o pacote `.deb` (**MACH1 Control Center**).

## Uso Manual (CLI)

Você pode executar o script via terminal para testar se ele consegue se comunicar com o seu display:

```bash
# Listar se o cooler foi encontrado e em qual interface USB ele está plugado
sudo python3 mach1-control.py list

# Ligar o display e transmitir a temperatura em Celsius
sudo python3 mach1-control.py on

# Ligar usando Fahrenheit em vez de Celsius
sudo python3 mach1-control.py on -u f

# Exibir a rotação da ventoinha (RPM) na linha inferior em vez de Watts
sudo python3 mach1-control.py on -m fan

# Usar um sensor específico, como k10temp para processadores AMD
sudo python3 mach1-control.py on -s "k10temp"

# Desligar a tela do display
sudo python3 mach1-control.py off
```

> [!TIP]
> Você geralmente precisa rodar com `sudo` no Linux para acessar dispositivos USB crus (raw HID). Se não quiser usar `sudo`, será necessário criar uma regra no `udev`.

## Regra do UDEV (Para executar sem Sudo)

Para permitir que qualquer usuário consiga acessar o cooler MACH1 sem precisar de permissões root, crie o arquivo `/etc/udev/rules.d/99-mach1-cooler.rules` e adicione as linhas:

```text
# Regra UDEV para o Cooler MACH1 DIG
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4d84", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4c84", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="1a2c", MODE="0666"
```

Depois, aplique a regra e desconecte/reconecte o cabo USB do cooler na placa mãe (ou reinicie o PC):
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Como executar como Serviço (Rodar ao Ligar o PC)

Para que o Linux ligue o display automaticamente quando o PC iniciar, crie um serviço Systemd:

1. Certifique-se de estar dentro da pasta do projeto e com o ambiente virtual ativado (se aplicável).
2. Rode o comando de instalação:
   ```bash
   # Exemplo exibindo consumo em Watts:
   sudo python3 mach1-control.py install-service -s "auto" -u c -m power

   # Exemplo exibindo velocidade do cooler (RPM):
   sudo python3 mach1-control.py install-service -s "auto" -u c -m fan
   ```
   *(Substitua "auto" pelo nome do seu sensor preferido de acordo com sua CPU).*

3. Ative o serviço gerado:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now mach1-lcd.service
   ```
   
A partir de agora, o display funcionará automaticamente no fundo!

## Como empacotar para .deb (Debian/Ubuntu/Mint)

Para facilitar a distribuição e instalação em sistemas baseados em Debian, criamos um script de build automático.

1. No terminal do seu Linux (ou WSL), dê permissão de execução ao script de build:
   ```bash
   chmod +x build_deb.sh
   ```

2. Execute o script:
   ```bash
   ./build_deb.sh
   ```

3. O script criará o pacote **versão 1.7-1** chamado `mach1-dig-linux_1.7-1_all.deb` em `../../dist/mach1/`. Para instalar ou fazer upgrade, basta rodar:
   ```bash
   cp ../../dist/mach1/mach1-dig-linux_1.7-1_all.deb /tmp/
   sudo apt install /tmp/mach1-dig-linux_1.7-1_all.deb
   ```

Ao instalar o pacote, ele já coloca a interface gráfica (`mach1-gui`), o atalho no menu de aplicações, as regras do `udev` no lugar certo e prepara o serviço `systemd`. Você só precisará habilitar e iniciar o serviço:
```bash
sudo systemctl enable --now mach1-lcd.service
```

## Solução de Problemas e Diagnóstico

Se o display parar de atualizar ou apresentar congelamentos por erros no barramento USB do Linux (ex.: erro `-71 / EPROTO`), consulte o relatório detalhado em [DIAGNOSTICO.md](file:///home/vinicius-ferreira/Projects/displaystorm-linux/apps/mach1/DIAGNOSTICO.md).

O driver conta com as seguintes melhorias de resiliência:
- **Validação de retorno HID:** Verificação do código de retorno de `send_feature_report()` para identificar transmissões com falha (`res < 0`).
- **Reconexão automática:** Em caso de perda de comunicação ou desconexão física, a conexão HID é resetada e o driver tenta reconectar continuamente a cada 2 segundos.

