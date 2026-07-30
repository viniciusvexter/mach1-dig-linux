#!/usr/bin/env python3
"""
mach1-gui.py
---------------------------------
Interface Gráfica (GUI) para o Cooler MACH1 DIG no Linux.
Fidelidade visual idêntica à versão oficial do Windows.
"""

import os
import sys
import time
import threading
import json

# Fallback automático para variável de ambiente DISPLAY se executado via sudo/terminal
if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

import tkinter as tk
from tkinter import messagebox


# A GUI agora funciona de forma assíncrona com o serviço do systemd via IPC em JSON


class Mach1AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MACH 1 Control Center")
        self.geometry("520x420")
        self.configure(bg="#0a0a0c")
        self.resizable(False, False)

        # Configurar ícone da janela
        try:
            icon_path = "/usr/share/pixmaps/mach1-icon.png"
            if not os.path.exists(icon_path):
                # Fallback para desenvolvimento local
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mach1-icon.png")
            
            icon_image = tk.PhotoImage(file=icon_path)
            self.iconphoto(False, icon_image)
        except Exception as e:
            print(f"Não foi possível carregar o ícone: {e}")

        # Tratar o estilo de janela para compatibilidade total com Wayland/GNOME/KDE
        try:
            self.overrideredirect(True)
        except Exception:
            pass

        # Garante que a janela fique em primeiro plano ao abrir
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

        # Variáveis de estado
        self.display_on = True
        self.unit_celsius = True  # True: °C, False: °F
        self.mode_power = True    # True: Watts, False: RPM Fan

        # Dados em tempo real
        self.current_temp = 0.0
        self.current_watts = 0.0
        self.current_rpm = 0.0
        self.device_connected = False
        self.status_msg = "Inicializando..."

        # Dragging da janela
        self._drag_data = {"x": 0, "y": 0}

        # Inicializar UI e threads
        self.create_widgets()
        self.center_window()

        self.running = True
        self.worker_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self.worker_thread.start()
        
        # Sincroniza o estado inicial com o arquivo caso já exista
        self._load_initial_state()

    def _load_initial_state(self):
        try:
            if os.path.exists("/tmp/mach1_state.json"):
                with open("/tmp/mach1_state.json", "r") as f:
                    state = json.load(f)
                self.display_on = state.get("display_on", True)
                self.unit_celsius = (state.get("unit", "c") == "c")
                self.mode_power = (state.get("mode", "power") == "power")
                self.update_switch_styles()
        except Exception:
            pass

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        # Canvas de fundo para linhas geométricas diagonais idênticas à imagem
        self.canvas = tk.Canvas(self, width=520, height=420, bg="#0a0a0c", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Permitir arrastar a janela clicando no fundo
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)

        # Desenhar linhas geométricas diagonais finas (estilo MACH 1)
        line_color = "#1e2025"
        self.canvas.create_line(0, 40, 180, 0, fill=line_color, width=1)
        self.canvas.create_line(0, 60, 240, 0, fill=line_color, width=1)
        self.canvas.create_line(0, 80, 280, 0, fill=line_color, width=1)
        self.canvas.create_line(0, 200, 520, 90, fill=line_color, width=1)
        self.canvas.create_line(0, 220, 520, 110, fill=line_color, width=1)
        self.canvas.create_line(0, 270, 450, 360, fill=line_color, width=1)
        self.canvas.create_line(0, 310, 520, 210, fill=line_color, width=1)
        self.canvas.create_line(300, 380, 520, 330, fill=line_color, width=1)

        # Botão Fechar [ X ] no canto superior direito
        self.close_btn = tk.Label(
            self, text="✕", font=("Helvetica", 11, "bold"),
            fg="#cccccc", bg="#0a0a0c", bd=1, relief="solid",
            width=3, height=1, cursor="hand2"
        )
        self.close_btn.place(x=475, y=15)
        self.close_btn.bind("<Button-1>", lambda e: self.on_close())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(bg="#e74c3c", fg="#ffffff"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(bg="#0a0a0c", fg="#cccccc"))

        # Logotipo MACH 1
        self.logo_label = tk.Label(
            self, text="M\u039BCH 1", font=("Arial", 28, "bold"),
            fg="#ffffff", bg="#0a0a0c"
        )
        self.logo_label.place(x=260, y=35, anchor="center")

        self.sub_logo = tk.Label(
            self, text="beyond performance, beyond limits", font=("Helvetica", 8, "italic"),
            fg="#888888", bg="#0a0a0c"
        )
        self.sub_logo.place(x=260, y=65, anchor="center")

        # --- SEÇÃO DE CONTROLES ---
        # 1. Row DISPLAY
        self.lbl_display = tk.Label(
            self, text="DISPLAY", font=("Helvetica", 14, "bold"),
            fg="#ffffff", bg="#0a0a0c"
        )
        self.lbl_display.place(x=70, y=130, anchor="w")

        # Toggle DISPLAY: [ OFF | ON ]
        self.frame_toggle_display = tk.Frame(self, bg="#2b2b2b", bd=1, relief="solid")
        self.frame_toggle_display.place(x=230, y=115, width=170, height=36)

        self.btn_disp_off = tk.Label(
            self.frame_toggle_display, text="off", font=("Helvetica", 10, "bold"),
            cursor="hand2"
        )
        self.btn_disp_off.place(x=0, y=0, width=84, height=34)
        self.btn_disp_off.bind("<Button-1>", lambda e: self.set_display(False))

        self.btn_disp_on = tk.Label(
            self.frame_toggle_display, text="on", font=("Helvetica", 10, "bold"),
            cursor="hand2"
        )
        self.btn_disp_on.place(x=84, y=0, width=84, height=34)
        self.btn_disp_on.bind("<Button-1>", lambda e: self.set_display(True))

        # 2. Row TEMP.
        self.lbl_temp = tk.Label(
            self, text="TEMP.", font=("Helvetica", 14, "bold"),
            fg="#ffffff", bg="#0a0a0c"
        )
        self.lbl_temp.place(x=70, y=190, anchor="w")

        # Toggle TEMP.: [ °C | °F ]
        self.frame_toggle_temp = tk.Frame(self, bg="#2b2b2b", bd=1, relief="solid")
        self.frame_toggle_temp.place(x=230, y=175, width=170, height=36)

        self.btn_temp_c = tk.Label(
            self.frame_toggle_temp, text="°C", font=("Helvetica", 11, "bold"),
            cursor="hand2"
        )
        self.btn_temp_c.place(x=0, y=0, width=84, height=34)
        self.btn_temp_c.bind("<Button-1>", lambda e: self.set_unit(True))

        self.btn_temp_f = tk.Label(
            self.frame_toggle_temp, text="°F", font=("Helvetica", 11, "bold"),
            cursor="hand2"
        )
        self.btn_temp_f.place(x=84, y=0, width=84, height=34)
        self.btn_temp_f.bind("<Button-1>", lambda e: self.set_unit(False))

        # 3. Row MODO INFERIOR: [ W (Power) | RPM (Cooler) ]
        self.lbl_mode = tk.Label(
            self, text="INFERIOR", font=("Helvetica", 14, "bold"),
            fg="#ffffff", bg="#0a0a0c"
        )
        self.lbl_mode.place(x=70, y=250, anchor="w")

        self.frame_toggle_mode = tk.Frame(self, bg="#2b2b2b", bd=1, relief="solid")
        self.frame_toggle_mode.place(x=230, y=235, width=170, height=36)

        self.btn_mode_w = tk.Label(
            self.frame_toggle_mode, text="W (Power)", font=("Helvetica", 9, "bold"),
            cursor="hand2"
        )
        self.btn_mode_w.place(x=0, y=0, width=84, height=34)
        self.btn_mode_w.bind("<Button-1>", lambda e: self.set_mode(True))

        self.btn_mode_rpm = tk.Label(
            self.frame_toggle_mode, text="RPM (Cooler)", font=("Helvetica", 9, "bold"),
            cursor="hand2"
        )
        self.btn_mode_rpm.place(x=84, y=0, width=84, height=34)
        self.btn_mode_rpm.bind("<Button-1>", lambda e: self.set_mode(False))

        # Painel Inferior de Telemetria e Status
        self.status_bar = tk.Frame(self, bg="#141519", height=90)
        self.status_bar.place(x=0, y=330, width=520, height=90)

        self.lbl_telemetry = tk.Label(
            self.status_bar, text="CPU: 0.0°C | Potência: 0.0W | Ventoinha: 0 RPM",
            font=("Helvetica", 10, "bold"), fg="#3498db", bg="#141519"
        )
        self.lbl_telemetry.place(x=260, y=25, anchor="center")

        self.lbl_status = tk.Label(
            self.status_bar, text="Procurando dispositivo MACH1 USB...",
            font=("Helvetica", 9), fg="#888888", bg="#141519"
        )
        self.lbl_status.place(x=260, y=55, anchor="center")

        self.update_switch_styles()

    def update_switch_styles(self):
        # Estilos do seletor DISPLAY
        if not self.display_on:
            self.btn_disp_off.configure(bg="#ffffff", fg="#000000")
            self.btn_disp_on.configure(bg="#1c1c1c", fg="#555555")
        else:
            self.btn_disp_off.configure(bg="#1c1c1c", fg="#555555")
            self.btn_disp_on.configure(bg="#ffffff", fg="#000000")

        # Estilos do seletor TEMP
        if self.unit_celsius:
            self.btn_temp_c.configure(bg="#ffffff", fg="#000000")
            self.btn_temp_f.configure(bg="#1c1c1c", fg="#555555")
        else:
            self.btn_temp_c.configure(bg="#1c1c1c", fg="#555555")
            self.btn_temp_f.configure(bg="#ffffff", fg="#000000")

        # Estilos do seletor MODO INFERIOR
        if self.mode_power:
            self.btn_mode_w.configure(bg="#ffffff", fg="#000000")
            self.btn_mode_rpm.configure(bg="#1c1c1c", fg="#555555")
        else:
            self.btn_mode_w.configure(bg="#1c1c1c", fg="#555555")
            self.btn_mode_rpm.configure(bg="#ffffff", fg="#000000")

    def _save_state(self):
        state = {
            "display_on": self.display_on,
            "unit": "c" if self.unit_celsius else "f",
            "mode": "power" if self.mode_power else "fan"
        }
        try:
            with open("/tmp/mach1_state.json", "w") as f:
                json.dump(state, f)
        except Exception as e:
            print("Erro ao salvar estado:", e)

    def set_display(self, state: bool):
        self.display_on = state
        self.update_switch_styles()
        self._save_state()

    def set_unit(self, is_celsius: bool):
        self.unit_celsius = is_celsius
        self.update_switch_styles()
        self._save_state()

    def set_mode(self, is_power: bool):
        self.mode_power = is_power
        self.update_switch_styles()
        self._save_state()

    def on_close(self):
        self.running = False
        self.destroy()

    def _telemetry_loop(self):
        """Thread que lê os dados de telemetria do serviço em background continuamente."""
        while self.running:
            try:
                if os.path.exists("/tmp/mach1_telemetry.json"):
                    with open("/tmp/mach1_telemetry.json", "r") as f:
                        data = json.load(f)
                    
                    self.device_connected = data.get("connected", False)
                    temp_c = data.get("temp_c", 0.0)
                    watts = data.get("watts", 0.0)
                    rpm = data.get("rpm", 0.0)
                    
                    if self.device_connected:
                        self.status_msg = "MACH1 Conectado (Sincronizado com serviço)"
                    else:
                        self.status_msg = "Aguardando sincronização com serviço de background..."
                        
                    self._update_gui_telemetry(temp_c, watts, rpm)
                else:
                    self.device_connected = False
                    self.status_msg = "Serviço mach1-lcd não está rodando."
                    self._update_gui_telemetry(0.0, 0.0, 0.0)
            except Exception as e:
                self.status_msg = f"Aguardando dados... ({e})"
                
            time.sleep(1.0)

    def _update_gui_telemetry(self, temp_c: float, watts: float, rpm: float):
        unit_sym = "°C" if self.unit_celsius else "°F"
        disp_temp = temp_c if self.unit_celsius else temp_c * 9 / 5 + 32

        def update():
            if not self.winfo_exists():
                return
            self.lbl_telemetry.configure(
                text=f"CPU: {disp_temp:.1f}{unit_sym}  |  Potência: {watts:.1f}W  |  Cooler: {rpm:.0f} RPM"
            )
            color = "#2ecc71" if self.device_connected else "#e74c3c"
            self.lbl_status.configure(text=self.status_msg, fg=color)

        self.after(0, update)


if __name__ == "__main__":
    app = Mach1AppGUI()
    app.mainloop()
