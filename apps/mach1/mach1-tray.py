#!/usr/bin/env python3
"""
mach1-tray.py
---------------------------------
System Tray Icon para o cooler MACH1 DIG (Linux).
"""

import os
import sys
import json
import subprocess
from PIL import Image

try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    print("A biblioteca pystray não está instalada. Instale com 'sudo apt install python3-pystray' ou 'pip install pystray'")
    sys.exit(1)

STATE_FILE = "/tmp/mach1_state.json"

def get_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"display_on": True, "unit": "c", "mode": "power"}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Erro ao salvar estado: {e}")

def open_gui(icon, item):
    """Abre a Interface Gráfica principal."""
    subprocess.Popen(["/usr/bin/mach1-gui"])

def toggle_display(icon, item):
    """Liga ou desliga o display via JSON de estado."""
    state = get_state()
    state["display_on"] = not state.get("display_on", True)
    save_state(state)

def on_quit(icon, item):
    icon.stop()

def get_display_text(item):
    state = get_state()
    if state.get("display_on", True):
        return "Desligar Display"
    return "Ligar Display"

def main():
    icon_path = "/usr/share/pixmaps/mach1-icon.png"
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mach1-icon.png")

    try:
        image = Image.open(icon_path)
    except Exception as e:
        print(f"Não foi possível carregar o ícone: {e}")
        # Cria uma imagem de fallback preta
        image = Image.new('RGB', (64, 64), color = 'black')

    menu = pystray.Menu(
        item('Abrir Control Center', open_gui, default=True),
        pystray.Menu.SEPARATOR,
        item(get_display_text, toggle_display),
        pystray.Menu.SEPARATOR,
        item('Sair', on_quit)
    )

    icon = pystray.Icon("mach1-tray", image, "MACH1 Control Center", menu)
    icon.run()

if __name__ == "__main__":
    main()
