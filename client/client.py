"""
CLIENTE TKINTER - Simulador de Sensor de Temperatura
====================================================

RACIOCÍNIO LÓGICO APLICADO:
--------------------------

1. GERAÇÃO DE UUID (Garantia de Idempotência)
   - Cada leitura gera um UUID v4 único
   - UUID é enviado com a requisição
   - Se houver timeout/erro, cliente pode reenviar a MESMA requisição
   - Servidor detecta UUID duplicado e não cria registro duplicado

2. RETRY COM EXPONENTIAL BACKOFF
   - Em caso de falha de rede, tenta novamente automaticamente
   - Intervalo aumenta exponencialmente: 1s, 2s, 4s, 8s, 16s
   - Evita sobrecarregar servidor em caso de instabilidade
   - Máximo de 5 tentativas antes de desistir

3. INTERFACE RESPONSIVA (Threading)
   - Requisições HTTP executam em thread separada
   - GUI não congela durante envio
   - Feedback visual em tempo real (spinners, cores)

4. VALIDAÇÃO LOCAL
   - Valida range de temperatura ANTES de enviar
   - Evita requisições desnecessárias ao servidor
   - UX melhor (feedback imediato)

5. HISTÓRICO LOCAL
   - Mantém cache das últimas 50 leituras
   - Permite análise offline
   - Reduz necessidade de queries ao servidor
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import uuid
import random
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any


class SensorSimulator:
    """
    RACIOCÍNIO: Classe principal do simulador
    
    Responsabilidades:
    - Gerenciar interface gráfica
    - Simular geração de temperatura
    - Comunicar com servidor via HTTP
    - Manter histórico local de leituras
    """
    
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("🌡️ Simulador de Sensor de Temperatura")
        self.master.geometry("800x700")
        self.master.resizable(True, True)
        
        # Configuração do servidor 
        self.server_url = "http://localhost:5000" 
        self.sensor_id = f"SENSOR-{random.randint(1000, 9999)}"
        
        # Histórico local (máximo 50 leituras)
        self.history = []
        self.max_history = 50
        
        # Estado de envio automático
        self.auto_send_active = False
        self.auto_send_interval = 5  # segundos
        
        # Configuração de cores por status
        self.status_colors = {
            'Normal': '#28a745',      # Verde
            'Alerta': '#ffc107',      # Amarelo
            'Crítico': '#dc3545',     # Vermelho
            'Erro': '#6c757d'         # Cinza
        }
        
        self._criar_interface()
    
    def _criar_interface(self):
        """
        RACIOCÍNIO: Construção da interface
        
        Layout organizado em frames:
        1. Configuração (URL servidor, ID sensor)
        2. Controles de simulação (temp, botões)
        3. Status atual (última leitura)
        4. Histórico (tabela de leituras)
        """
        
        # ===== FRAME DE CONFIGURAÇÃO =====
        config_frame = ttk.LabelFrame(self.master, text="⚙️ Configuração", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # URL do servidor
        ttk.Label(config_frame, text="URL do Servidor:").grid(row=0, column=0, sticky='w', padx=5)
        self.server_entry = ttk.Entry(config_frame, width=40)
        self.server_entry.insert(0, self.server_url)
        self.server_entry.grid(row=0, column=1, padx=5, pady=3)
        
        # ID do sensor
        ttk.Label(config_frame, text="ID do Sensor:").grid(row=1, column=0, sticky='w', padx=5)
        self.sensor_entry = ttk.Entry(config_frame, width=40)
        self.sensor_entry.insert(0, self.sensor_id)
        self.sensor_entry.grid(row=1, column=1, padx=5, pady=3)
        
        # Botão de testar conexão
        ttk.Button(
            config_frame, 
            text="🔌 Testar Conexão",
            command=self._testar_conexao
        ).grid(row=0, column=2, rowspan=2, padx=5)
        
        # ===== FRAME DE SIMULAÇÃO =====
        sim_frame = ttk.LabelFrame(self.master, text="🎲 Simulação de Temperatura", padding=10)
        sim_frame.pack(fill='x', padx=10, pady=5)
        
        # Controle de temperatura
        ttk.Label(sim_frame, text="Temperatura (°C):").grid(row=0, column=0, sticky='w', padx=5)
        
        self.temp_var = tk.DoubleVar(value=20.0)
        self.temp_scale = ttk.Scale(
            sim_frame,
            from_=-10,
            to=40,
            orient='horizontal',
            variable=self.temp_var,
            length=300,
            command=self._atualizar_label_temp
        )
        self.temp_scale.grid(row=0, column=1, padx=5, pady=5)
        
        self.temp_label = ttk.Label(sim_frame, text="20.0°C", font=('Arial', 14, 'bold'))
        self.temp_label.grid(row=0, column=2, padx=10)
        
        # Botões de ação
        button_frame = ttk.Frame(sim_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(
            button_frame,
            text="🎯 Temperatura Aleatória",
            command=self._gerar_temperatura_aleatoria
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="📤 Enviar Leitura",
            command=self._enviar_leitura_thread,
            style='Accent.TButton'
        ).pack(side='left', padx=5)
        
        # Envio automático
        self.auto_send_var = tk.BooleanVar()
        ttk.Checkbutton(
            button_frame,
            text="🔄 Envio Automático (5s)",
            variable=self.auto_send_var,
            command=self._toggle_auto_send
        ).pack(side='left', padx=5)
        
        # ===== FRAME DE STATUS ATUAL =====
        status_frame = ttk.LabelFrame(self.master, text="📊 Status Atual", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Canvas para indicador visual
        self.status_canvas = tk.Canvas(status_frame, width=100, height=100, bg='white')
        self.status_canvas.pack(side='left', padx=10)
        
        # Texto de status
        status_text_frame = ttk.Frame(status_frame)
        status_text_frame.pack(side='left', fill='both', expand=True)
        
        self.status_label = ttk.Label(
            status_text_frame,
            text="Aguardando primeira leitura...",
            font=('Arial', 12)
        )
        self.status_label.pack(anchor='w', pady=2)
        
        self.uuid_label = ttk.Label(
            status_text_frame,
            text="UUID: -",
            font=('Arial', 9),
            foreground='gray'
        )
        self.uuid_label.pack(anchor='w', pady=2)
        
        self.timestamp_label = ttk.Label(
            status_text_frame,
            text="Timestamp: -",
            font=('Arial', 9),
            foreground='gray'
        )
        self.timestamp_label.pack(anchor='w', pady=2)
        
        # Desenhar círculo inicial
        self._desenhar_indicador('gray')
        
        # ===== FRAME DE HISTÓRICO =====
        history_frame = ttk.LabelFrame(self.master, text="📜 Histórico de Leituras", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Tabela de histórico
        columns = ('Timestamp', 'Temperatura', 'Status', 'UUID')
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        # Configurar colunas
        self.history_tree.heading('Timestamp', text='Data/Hora')
        self.history_tree.heading('Temperatura', text='Temp (°C)')
        self.history_tree.heading('Status', text='Status')
        self.history_tree.heading('UUID', text='UUID')
        
        self.history_tree.column('Timestamp', width=150)
        self.history_tree.column('Temperatura', width=100)
        self.history_tree.column('Status', width=100)
        self.history_tree.column('UUID', width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botão de limpar histórico
        ttk.Button(
            history_frame,
            text="🗑️ Limpar Histórico",
            command=self._limpar_historico
        ).pack(pady=5)
    
    def _atualizar_label_temp(self, value):
        """Atualiza label com valor atual da temperatura"""
        temp = float(value)
        self.temp_label.config(text=f"{temp:.1f}°C")
    
    def _gerar_temperatura_aleatoria(self):
        """
        RACIOCÍNIO: Geração de temperatura aleatória
        
        Distribui valores em ranges diferentes:
        - 60% Normal (-10 a 10°C)
        - 30% Alerta (10 a 15°C)
        - 10% Crítico (15 a 40°C)
        
        Simula distribuição realista de eventos
        """
        rand = random.random()
        if rand < 0.6:  # 60% Normal
            temp = random.uniform(-10, 10)
        elif rand < 0.9:  # 30% Alerta
            temp = random.uniform(10, 15)
        else:  # 10% Crítico
            temp = random.uniform(15, 40)
        
        self.temp_var.set(round(temp, 1))

        self._atualizar_label_temp(round(temp, 1))
    
    def _desenhar_indicador(self, cor: str):
        """
        RACIOCÍNIO: Indicador visual de status
        
        Feedback visual imediato do status:
        - Verde: Normal
        - Amarelo: Alerta
        - Vermelho: Crítico
        - Cinza: Erro/Aguardando
        """
        self.status_canvas.delete('all')
        self.status_canvas.create_oval(10, 10, 90, 90, fill=cor, outline='black', width=2)
    
    def _testar_conexao(self):
        """
        RACIOCÍNIO: Health check do servidor
        
        Verifica conectividade antes de enviar dados
        Evita frustração do usuário ao detectar problemas cedo
        """
        server_url = self.server_entry.get().strip()
        
        try:
            response = requests.get(f"{server_url}/health", timeout=3)
            if response.status_code == 200:
                messagebox.showinfo(
                    "Conexão OK",
                    f"✅ Servidor respondeu:\n{response.json()}"
                )
            else:
                messagebox.showwarning(
                    "Conexão com Problema",
                    f"⚠️ Servidor retornou status {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Erro de Conexão",
                "❌ Não foi possível conectar ao servidor.\n"
                "Verifique se o servidor está rodando e o URL está correto."
            )
        except requests.exceptions.Timeout:
            messagebox.showerror(
                "Timeout",
                "⏱️ Servidor não respondeu a tempo (timeout 3s)"
            )
        except Exception as e:
            messagebox.showerror(
                "Erro Desconhecido",
                f"❌ Erro ao testar conexão:\n{str(e)}"
            )
    
    def _enviar_leitura_thread(self):
        """
        RACIOCÍNIO: Execução em thread separada
        
        Evita congelar a GUI durante requisição HTTP
        Thread permite feedback visual (spinner) sem bloquear UI
        """
        thread = threading.Thread(target=self._enviar_leitura, daemon=True)
        thread.start()
    
    def _enviar_leitura(self):
        """
        RACIOCÍNIO: Lógica de envio com retry exponencial
        
        FLUXO:
        1. Gerar UUID único (garantia de idempotência)
        2. Preparar payload JSON
        3. Tentar enviar (máx 5 tentativas)
        4. Em caso de falha: esperar 2^tentativa segundos
        5. Processar resposta do servidor
        6. Atualizar GUI com resultado
        
        RETRY EXPONENCIAL:
        - Tentativa 1: 0s delay
        - Tentativa 2: 1s delay  
        - Tentativa 3: 2s delay
        - Tentativa 4: 4s delay
        - Tentativa 5: 8s delay
        
        Evita sobrecarga em caso de instabilidade
        """
        server_url = self.server_entry.get().strip()
        sensor_id = self.sensor_entry.get().strip()
        temperatura = self.temp_var.get()
        
        # Gerar UUID único para esta leitura (IDEMPOTÊNCIA)
        reading_uuid = str(uuid.uuid4())
        
        # Payload JSON
        payload = {
            'uuid': reading_uuid,
            'sensor_id': sensor_id,
            'temperatura': temperatura
        }
        
        # Atualizar UI - início de envio
        self.master.after(0, lambda: self.status_label.config(
            text="⏳ Enviando leitura ao servidor..."
        ))
        
        # Retry com exponential backoff
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    f"{server_url}/sensor/reading",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    status = data.get('status', 'Desconhecido')
                    is_duplicate = data.get('idempotent', False)
                    
                    # Adicionar ao histórico local
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._adicionar_ao_historico(
                        timestamp, temperatura, status, reading_uuid, is_duplicate
                    )
                    
                    # Atualizar UI
                    cor = self.status_colors.get(status, 'gray')
                    self.master.after(0, lambda: self._atualizar_status_ui(
                        status, reading_uuid, timestamp, cor, is_duplicate
                    ))
                    
                    return  # Sucesso - sair do loop de retry
                
                elif response.status_code == 409:
                    data = response.json()
                    status = data.get('status', 'Desconhecido')
                    
                    self.master.after(0, lambda: messagebox.showinfo(
                        "Leitura Duplicada",
                        f"⚠️ Esta leitura já foi processada anteriormente.\n"
                        f"UUID: {reading_uuid}\n"
                        f"Status: {status}"
                    ))
                    return
                
                else:
                    # Erro HTTP (4xx, 5xx)
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    raise Exception(f"HTTP {response.status_code}: {error_msg}")
            
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    delay = 2 ** (attempt - 1)  # Exponential backoff
                    self.master.after(0, lambda a=attempt, d=delay: self.status_label.config(
                        text=f"⚠️ Falha na conexão. Tentativa {a}/{max_retries}. Retry em {d}s..."
                    ))
                    time.sleep(delay)
                else:
                    # Última tentativa falhou
                    self.master.after(0, lambda: self._atualizar_status_erro(
                        "❌ Erro de conexão após 5 tentativas"
                    ))
                    return
            
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    delay = 2 ** (attempt - 1)
                    self.master.after(0, lambda a=attempt, d=delay: self.status_label.config(
                        text=f"⏱️ Timeout. Tentativa {a}/{max_retries}. Retry em {d}s..."
                    ))
                    time.sleep(delay)
                else:
                    self.master.after(0, lambda: self._atualizar_status_erro(
                        "❌ Timeout após 5 tentativas"
                    ))
                    return
            
            except Exception as e:
                self.master.after(0, lambda err=str(e): self._atualizar_status_erro(
                    f"❌ Erro: {err}"
                ))
                return
    
    def _atualizar_status_ui(self, status: str, uuid_str: str, timestamp: str, cor: str, is_duplicate: bool):
        """Atualiza interface com resultado do envio"""
        dup_text = " (DUPLICADA)" if is_duplicate else ""
        self.status_label.config(text=f"Status: {status}{dup_text}")
        self.uuid_label.config(text=f"UUID: {uuid_str}")
        self.timestamp_label.config(text=f"Timestamp: {timestamp}")
        self._desenhar_indicador(cor)
    
    def _atualizar_status_erro(self, mensagem: str):
        """Atualiza interface em caso de erro"""
        self.status_label.config(text=mensagem)
        self._desenhar_indicador('gray')
    
    def _adicionar_ao_historico(self, timestamp: str, temp: float, status: str, 
                                 uuid_str: str, is_duplicate: bool):
        """
        RACIOCÍNIO: Manutenção de histórico local
        
        - Limita a 50 entradas (evita consumo excessivo de memória)
        - FIFO: remove mais antigas quando excede limite
        - Thread-safe (executa no main thread via 'after')
        """
        # Adicionar ao histórico
        entry = {
            'timestamp': timestamp,
            'temperatura': temp,
            'status': status,
            'uuid': uuid_str,
            'is_duplicate': is_duplicate
        }
        self.history.insert(0, entry)  # Inserir no início (mais recente primeiro)
        
        # Limitar tamanho
        if len(self.history) > self.max_history:
            self.history.pop()  # Remover mais antigo
        
        # Atualizar tabela na GUI
        self.master.after(0, lambda: self._atualizar_tabela_historico())
    
    def _atualizar_tabela_historico(self):
        """Atualiza tabela de histórico na GUI"""
        # Limpar tabela
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Preencher com histórico
        for entry in self.history:
            status_display = entry['status']
            if entry['is_duplicate']:
                status_display += " (DUP)"
            
            self.history_tree.insert('', 'end', values=(
                entry['timestamp'],
                f"{entry['temperatura']:.1f}",
                status_display,
                entry['uuid']
            ))
    
    def _limpar_historico(self):
        """Limpa histórico local"""
        if messagebox.askyesno("Confirmar", "Limpar todo o histórico local?"):
            self.history.clear()
            self._atualizar_tabela_historico()
    
    def _toggle_auto_send(self):
        """
        RACIOCÍNIO: Envio automático periódico
        
        Simula sensor real que envia dados continuamente
        Intervalo configurável (default: 5 segundos)
        """
        if self.auto_send_var.get():
            self.auto_send_active = True
            self._auto_send_loop()
        else:
            self.auto_send_active = False
    
    def _auto_send_loop(self):
        """Loop de envio automático"""
        if self.auto_send_active:
            # Gerar temperatura aleatória e enviar
            self._gerar_temperatura_aleatoria()
            self._enviar_leitura_thread()
            
            # Agendar próximo envio
            self.master.after(self.auto_send_interval * 1000, self._auto_send_loop)


def main():
    """
    RACIOCÍNIO: Ponto de entrada da aplicação
    
    - Configura estilo do Tkinter
    - Cria janela principal
    - Inicia event loop
    """
    root = tk.Tk()
    
    # Estilo
    style = ttk.Style()
    style.theme_use('clam')  # Tema moderno
    
    # Criar aplicação
    app = SensorSimulator(root)
    
    # Iniciar loop
    root.mainloop()


if __name__ == '__main__':
    main()
