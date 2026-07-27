#!/bin/bash
# Script para empacotar o MACH1 DIG Linux em um arquivo .deb
# Este script deve ser executado em um ambiente Linux (ou WSL).

PACKAGE_NAME="mach1-dig-linux"
VERSION="1.0"
REVISION="2"
ARCH="all"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}-${REVISION}_${ARCH}"

echo "Limpando diretórios de build anteriores..."
rm -rf ${BUILD_DIR}
rm -f ${BUILD_DIR}.deb

echo "Criando estrutura de diretórios do pacote..."
mkdir -p ${BUILD_DIR}/DEBIAN
mkdir -p ${BUILD_DIR}/usr/bin
mkdir -p ${BUILD_DIR}/etc/udev/rules.d
mkdir -p ${BUILD_DIR}/lib/systemd/system

echo "Criando arquivo de controle (DEBIAN/control)..."
cat <<EOF > ${BUILD_DIR}/DEBIAN/control
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
cat <<EOF > ${BUILD_DIR}/DEBIAN/postinst
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
chmod 755 ${BUILD_DIR}/DEBIAN/postinst

echo "Copiando os arquivos do driver..."
# Copia o script Python
cp mach1-control.py ${BUILD_DIR}/usr/bin/mach1-control
chmod 755 ${BUILD_DIR}/usr/bin/mach1-control

echo "Criando regras do UDEV..."
cat <<EOF > ${BUILD_DIR}/etc/udev/rules.d/99-mach1-cooler.rules
# Regra UDEV para o Cooler MACH1 DIG
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4d84", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4c84", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="1a2c", MODE="0666"
EOF

echo "Criando serviço base do Systemd..."
cat <<EOF > ${BUILD_DIR}/lib/systemd/system/mach1-lcd.service
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
dpkg-deb --root-owner-group --build ${BUILD_DIR}

echo "Sucesso! Arquivo gerado: ${BUILD_DIR}.deb"
echo "Para instalar: sudo apt install ./${BUILD_DIR}.deb"
