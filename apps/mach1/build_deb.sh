#!/bin/bash
# Script para empacotar o MACH1 DIG Linux em um arquivo .deb
# Este script deve ser executado em um ambiente Linux (ou WSL).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/dist/mach1"

PACKAGE_NAME="mach1-dig-linux"
VERSION="1.7"
REVISION="1"
ARCH="all"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}-${REVISION}_${ARCH}"

echo "Limpando diretórios de build anteriores..."
rm -rf "${OUTPUT_DIR}/${BUILD_DIR}"
rm -f "${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}-${REVISION}_${ARCH}.deb"

mkdir -p "${OUTPUT_DIR}"

echo "Criando estrutura de diretórios do pacote..."
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/DEBIAN"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/etc/udev/rules.d"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/etc/systemd/system"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/usr/share/applications"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/usr/share/pixmaps"
mkdir -p "${OUTPUT_DIR}/${BUILD_DIR}/etc/xdg/autostart"

echo "Criando arquivo de controle (DEBIAN/control)..."
cat <<EOF > "${OUTPUT_DIR}/${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}-${REVISION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-tk, python3-psutil, python3-hid | python3-hidapi, libhidapi-hidraw0, python3-pystray, python3-pil
Maintainer: Seu Nome <seu.email@exemplo.com>
Description: Driver e Interface Gráfica Linux para display de cooler MACH1 DIG
 Driver em user-space e GUI no estilo Windows para controle de
 temperatura, unidade °C/°F, ligar/desligar display e exibição de
 consumo (Watts) ou rotação de ventoinha (RPM).
EOF

echo "Criando script de pós-instalação (DEBIAN/postinst)..."
cat <<EOF > "${OUTPUT_DIR}/${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
# Recarregar as regras do udev
udevadm control --reload-rules || true
udevadm trigger || true
# Habilitar e iniciar o serviço, se o systemd estiver rodando
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload || true
fi
EOF
chmod 755 "${OUTPUT_DIR}/${BUILD_DIR}/DEBIAN/postinst"

echo "Copiando os arquivos do driver e interface gráfica..."
cp "${SCRIPT_DIR}/mach1-control.py" "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-control"
chmod 755 "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-control"

cp "${SCRIPT_DIR}/mach1-gui.py" "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-gui"
chmod 755 "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-gui"

cp "${SCRIPT_DIR}/mach1-tray.py" "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-tray"
chmod 755 "${OUTPUT_DIR}/${BUILD_DIR}/usr/bin/mach1-tray"

if [ -f "${SCRIPT_DIR}/packaging/mach1-gui.desktop" ]; then
    cp "${SCRIPT_DIR}/packaging/mach1-gui.desktop" "${OUTPUT_DIR}/${BUILD_DIR}/usr/share/applications/mach1-gui.desktop"
    
    echo "Criando entrada de autostart para o Tray Icon..."
    cat <<EOF > "${OUTPUT_DIR}/${BUILD_DIR}/etc/xdg/autostart/mach1-tray.desktop"
[Desktop Entry]
Name=MACH1 Tray Icon
Comment=Ícone da bandeja do sistema para o cooler MACH1 DIG
Exec=python3 /usr/bin/mach1-tray
Icon=/usr/share/pixmaps/mach1-icon.png
Terminal=false
Type=Application
NoDisplay=true
EOF
fi

if [ -f "${SCRIPT_DIR}/mach1-icon.png" ]; then
    cp "${SCRIPT_DIR}/mach1-icon.png" "${OUTPUT_DIR}/${BUILD_DIR}/usr/share/pixmaps/mach1-icon.png"
fi

echo "Criando regras do UDEV..."
cat <<EOF > "${OUTPUT_DIR}/${BUILD_DIR}/etc/udev/rules.d/99-mach1-cooler.rules"
# Regra UDEV para o Cooler MACH1 DIG
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4d84", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4c84", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="1a2c", MODE="0666"

# Desativação do USB Autosuspend / Selecionado no kernel Linux (evita travamento do display / erro -71)
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTR{power/control}="on"
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTR{power/autosuspend}="-1"
EOF

echo "Criando serviço base do Systemd..."
cat <<EOF > "${OUTPUT_DIR}/${BUILD_DIR}/etc/systemd/system/mach1-lcd.service"
[Unit]
Description=MACH1 DIG LCD Temperature Display
After=multi-user.target

[Service]
Type=simple
User=root
# Usa "-s auto" para detecção automática de sensores em AMD e Intel
ExecStart=/usr/bin/python3 /usr/bin/mach1-control on -s "auto" -u c
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Construindo pacote .deb..."
dpkg-deb --root-owner-group --build "${OUTPUT_DIR}/${BUILD_DIR}"

echo "Sucesso! Arquivo gerado: ${OUTPUT_DIR}/${BUILD_DIR}.deb"
echo "Para instalar: sudo apt install ${OUTPUT_DIR}/${BUILD_DIR}.deb"
