# mach1-dig-linux

Controle de coolers LCD baseados em HID.

Foco principal deste projeto: versao Linux do aplicativo do MACH1 DIG, que hoje possui software oficial somente para Windows.

## Estrutura adotada

```text
displaystorm-linux/
	apps/
		mach1/
			mach1-control.py
			build_deb.sh
			requirements.txt
			packaging/
				deb/
					mach1-dig-linux_1.7-1_all/
			README.md
		ocypus/
			ocypus-control.py
			requirements.txt
			README.md
			LICENSE
	dist/
		mach1/
			mach1-dig-linux_1.7-1_all.deb
	docs/
		architecture.md
	scripts/
	.gitignore
	README.md
```

## Modulos

### apps/mach1 (principal)

Driver Linux e Interface Gráfica para cooler MACH1 DIG:

- Interface Gráfica (GUI) idêntica à versão oficial do Windows (`mach1-gui.py` / MACH1 Control Center)
- Comunicacao HID com auto-deteccao de interface
- Validacao de retorno HID (tratamento de falhas `-1` / USB `-71`)
- Loop com reconexao automatica em caso de desconexao ou erro USB
- Exibicao de temperatura da CPU (°C / °F)
- Exibicao de consumo em Watts (W) ou Rotação da Ventoinha (RPM)
- Instalacao de regra udev
- Instalacao de servico systemd
- Build de pacote .deb

Hardware:

- VID: 0x1A2C
- PID: 0x4D84 e 0x4C84

### apps/ocypus (secundario)

Driver Linux para Ocypus A40:

- Comunicacao HID com auto-deteccao de interface
- Validacao de retorno HID (tratamento de falhas `-1` / USB `-71`)
- Loop com reconexao automatica em caso de desconexao ou erro USB
- Exibicao de temperatura da CPU
- Instalacao de regra udev
- Instalacao de servico systemd

Hardware:

- VID: 0x1A2C
- PID: 0x434D

## Dependencias de sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-tk libhidapi-hidraw0
```

## Uso rapido

### MACH1 DIG

**Interface Gráfica (GUI):**
```bash
python3 apps/mach1/mach1-gui.py
```

**Linha de Comando (CLI):**
```bash
cd apps/mach1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo python3 mach1-control.py list
sudo python3 mach1-control.py on -u c -s auto -r 1.0 -m power
sudo python3 mach1-control.py off
```

### Ocypus

```bash
cd apps/ocypus
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo python3 ocypus-control.py list
sudo python3 ocypus-control.py on -u c -s auto -r 1.0
sudo python3 ocypus-control.py off
```

## Build .deb do MACH1

```bash
cd apps/mach1
chmod +x build_deb.sh
./build_deb.sh
```

O artefato gerado fica em `dist/mach1/`.

## Proximos passos recomendados

- Extrair codigo compartilhado de HID/sensores para uma biblioteca comum
- Criar CI para lint/test e build de pacote
- Publicar release automatizada do pacote .deb
