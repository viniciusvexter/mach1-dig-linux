#!/bin/bash
# Script para empacotar o MACH1 DIG Linux em um arquivo .deb
# Este script deve ser executado em um ambiente Linux (ou WSL).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/dist/mach1"

PACKAGE_NAME="mach1-dig-linux"
VERSION="1.0"
REVISION="2"
ARCH="all"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}-${REVISION}_${ARCH}"

echo "Limpando diretórios de build anteriores..."
rm -rf "${SCRIPT_DIR}/${BUILD_DIR}"
rm -f "${SCRIPT_DIR}/${BUILD_DIR}.deb"

mkdir -p "${OUTPUT_DIR}"

echo "Criando estrutura de diretórios do pacote..."
mkdir -p "${SCRIPT_DIR}/${BUILD_DIR}/DEBIAN"
mkdir -p "${SCRIPT_DIR}/${BUILD_DIR}/usr/bin"
mkdir -p "${SCRIPT_DIR}/${BUILD_DIR}/etc/udev/rules.d"
mkdir -p "${SCRIPT_DIR}/${BUILD_DIR}/lib/systemd/system"

echo "Criando arquivo de controle (DEBIAN/control)..."
cat <<EOF > "${SCRIPT_DIR}/${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}-${REVISION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-psutil, python3-hid | python3-hidapi, libhidapi-hidraw0
Maintainer: Seu Nome <seu.email@exemplo.com>
Description: Driver Linux para display de cooler MACH1 DIG
 Driver em user-space que envia a temperatura da CPU
 para o display LCD de coolers MACH1 DIG.
EOF

echo "Criando script de pós-instalação (DEBIAN/postinst)..."
cat <<EOF > "${SCRIPT_DIR}/${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
# Recarregar as regras do udev
udevadm control --reload-rules || true
udevadm trigger || true
# Habilitar e iniciar o serviço, se o systemd estiver rodando
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload || true
    # Vamos deixar o serviço desabilitado por padrão para que o usuário
    # configure qual sensor usar editando o arquivo, mas se preferir,
    # descomente a linha abaixo para iniciar automaticamente:
    # systemctl enable --now mach1-lcd.service || true
fi
EOF
chmod 755 "${SCRIPT_DIR}/${BUILD_DIR}/DEBIAN/postinst"

echo "Copiando os arquivos do driver..."
# Copia o script Python
cp "${SCRIPT_DIR}/mach1-control.py" "${SCRIPT_DIR}/${BUILD_DIR}/usr/bin/mach1-control"
chmod 755 "${SCRIPT_DIR}/${BUILD_DIR}/usr/bin/mach1-control"

echo "Criando regras do UDEV..."
cat <<EOF > "${SCRIPT_DIR}/${BUILD_DIR}/etc/udev/rules.d/99-mach1-cooler.rules"
# Regra UDEV para o Cooler MACH1 DIG
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4d84", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4c84", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="1a2c", MODE="0666"
EOF

echo "Criando serviço base do Systemd..."
cat <<EOF > "${SCRIPT_DIR}/${BUILD_DIR}/lib/systemd/system/mach1-lcd.service"
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
dpkg-deb --root-owner-group --build "${SCRIPT_DIR}/${BUILD_DIR}"

mv -f "${SCRIPT_DIR}/${BUILD_DIR}.deb" "${OUTPUT_DIR}/${BUILD_DIR}.deb"

echo "Sucesso! Arquivo gerado: ${OUTPUT_DIR}/${BUILD_DIR}.deb"
echo "Para instalar: sudo apt install ${OUTPUT_DIR}/${BUILD_DIR}.deb"
