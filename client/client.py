import tkinter as tk
from tkinter import ttk, messagebox
import requests
import uuid
import random
import threading
from datetime import datetime

class SensorClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Sensor")
        self.root.geometry("750x500")

        self.server_url = tk.StringVar(value="http://192.168.1.100:5000")
        self.sensor_id = tk.StringVar(value="sensor_01")
        self.auto_send = tk.BooleanVar(value=False)
        self.interval_sec = tk.IntVar(value=5)
        self.after_id = None
        
        # Uso de uma lista padrão para armazenar o histórico
        self.history = []
        self.last_sent = None 

        self.build_gui()

    def build_gui(self):
        settings_frame = ttk.LabelFrame(self.root, text="Configurações", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(settings_frame, text="URL:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(settings_frame, textvariable=self.server_url, width=40).grid(row=0, column=1, padx=5)
        ttk.Label(settings_frame, text="Sensor ID:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(settings_frame, textvariable=self.sensor_id, width=20).grid(row=1, column=1, padx=5, sticky=tk.W)

        control_frame = ttk.LabelFrame(self.root, text="Controles", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.send_btn = ttk.Button(control_frame, text="Enviar Leitura", command=self.send_reading_threaded)
        self.send_btn.grid(row=0, column=0, padx=5)

        self.resend_btn = ttk.Button(control_frame, text="Reenviar Última", command=self.resend_last_threaded, state=tk.DISABLED)
        self.resend_btn.grid(row=0, column=1, padx=5)

        ttk.Checkbutton(control_frame, text="Automático", variable=self.auto_send, command=self.update_auto_send).grid(row=0, column=2, padx=10)
        ttk.Label(control_frame, text="Intervalo (s):").grid(row=0, column=3, padx=(10,2))
        ttk.Spinbox(control_frame, from_=1, to=30, textvariable=self.interval_sec, width=5).grid(row=0, column=4)

        status_frame = ttk.LabelFrame(self.root, text="Resposta", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Aguardando...", font=("Arial", 12, "bold"))
        self.status_label.pack()

        # Atualizado para indicar 50 leituras
        history_frame = ttk.LabelFrame(self.root, text="Histórico (últimas 50)", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("Time", "Temperature", "Status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        self.history_tree.heading("Time", text="Hora")
        self.history_tree.heading("Temperature", text="Temperatura (°C)")
        self.history_tree.heading("Status", text="Status")
        
        for col in columns:
            self.history_tree.column(col, width=150)
        self.history_tree.pack(fill=tk.BOTH, expand=True)

    def update_auto_send(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.auto_send.get():
            self.schedule_auto_send()

    def schedule_auto_send(self):
        if self.auto_send.get():
            self.send_reading_threaded()
            self.after_id = self.root.after(self.interval_sec.get() * 1000, self.schedule_auto_send)

    def send_reading(self, custom_uuid=None, custom_temp=None):
        """Envia os dados via POST. Executa de forma bloqueante."""
        temp = custom_temp if custom_temp is not None else round(random.uniform(-10.0, 40.0), 1)
        uid = custom_uuid if custom_uuid is not None else str(uuid.uuid4())
        sensor = self.sensor_id.get().strip()

        payload = {"uuid": uid, "sensor_id": sensor, "temperature": temp}
        url = self.server_url.get().rstrip('/') + "/reading"

        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return (True, data.get("reading_status", "Desconhecido"), data.get("message", ""), temp, uid)
            return (False, f"HTTP {response.status_code}", response.text, temp, uid)
        except requests.exceptions.RequestException as e:
            return (False, "Erro de Conexão", str(e), temp, uid)

    def send_reading_threaded(self):
        """Usa threads para evitar que a requisição de rede trave a interface."""
        threading.Thread(target=self._do_send, args=(None, None), daemon=True).start()

    def resend_last_threaded(self):
        if self.last_sent:
            threading.Thread(target=self._do_send, args=(self.last_sent[0], self.last_sent[1]), daemon=True).start()

    def _do_send(self, forced_uuid, forced_temp):
        success, status_info, details, temp, uid = self.send_reading(forced_uuid, forced_temp)
        # Atualiza a interface gráfica usando a thread principal (after)
        if success:
            self.root.after(0, self.update_gui_on_success, temp, uid, status_info, details)
        else:
            self.root.after(0, self.update_gui_on_failure, status_info, details, temp)

    def append_to_history(self, timestamp, temp, status):
        """Adiciona um item ao histórico e mantém o limite de 50 itens."""
        # Insere no início da lista para o mais recente ficar no topo
        self.history.insert(0, (timestamp, temp, status))
        
        # Mantém o tamanho da lista em no máximo 50
        if len(self.history) > 50:
            self.history.pop()
            
        self.refresh_history_display()

    def update_gui_on_success(self, temp, uid, server_status, message):
        self.last_sent = (uid, temp, self.sensor_id.get())
        self.resend_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"✓ {message}", foreground="green")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append_to_history(timestamp, temp, server_status)

    def update_gui_on_failure(self, error_type, details, temp):
        self.status_label.config(text=f"✗ {error_type}: {details}", foreground="red")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append_to_history(timestamp, temp, "FALHOU")

    def refresh_history_display(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for entry in self.history:
            self.history_tree.insert("", tk.END, values=entry)

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorClient(root)
    root.mainloop()