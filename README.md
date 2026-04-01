# Sistema Distribuído de Monitoramento de Sensores de Temperatura

## Descrição do Projeto

Sistema cliente/servidor em **três camadas** para monitoramento distribuído de sensores de temperatura, implementando conceitos avançados de **sistemas distribuídos** como:

- **Idempotência** via UUID (tolerância a falhas de rede)
- **Retry com Exponential Backoff** (resiliência)
- **Transparência de Distribuição** (cliente não sabe como dados são armazenados)
- **Processamento Centralizado** (servidor como fonte única de verdade)
- **Comunicação Stateless** (escalabilidade horizontal)

---

##  Arquitetura

###  **Camada 1 - Cliente (Simulador de Sensor)**
- Interface gráfica em **Tkinter**
- Gera dados simulados de temperatura (-10°C a 40°C)
- Gera **UUID v4** para cada leitura (garantia de idempotência)
- Envia via **HTTP POST** para o servidor
- **Retry automático** com exponential backoff (5 tentativas: 0s, 1s, 2s, 4s, 8s)
- Exibe status retornado pelo servidor em tempo real
- Mantém histórico local das últimas 50 leituras

###  **Camada 2 - Servidor (Processamento de Lógica)**
- API REST em **Flask**
- **Valida requisições** (estrutura JSON, tipos, ranges)
- **Verificação de idempotência**: consulta UUID no banco antes de processar
- **Regras de negócio centralizadas**:
  - `Temperatura ≤ 10°C` → **Normal** 
  - `10°C < Temperatura ≤ 15°C` → **Alerta** 
  - `Temperatura > 15°C` → **Crítico** 
- **Transações atômicas** no banco de dados

###  **Camada 3 - Banco de Dados (Persistência)**
- **SQLite** com schema otimizado
- UUID como **chave primária** (previne duplicação)
- Índice em `timestamp` para queries rápidas
- Constraints de integridade (NOT NULL)

---



## Instruções de Execução

### *Pré-requisitos**
- Python 3.8 ou superior
- Dois computadores na mesma rede (ou usar `localhost` para testes)

---

### **1. Configurar o Servidor**

#### **Passo 1**: Instalar dependências
```bash
cd server/
pip install -r requirements.txt
```

#### **Passo 2**: Executar servidor
```bash
python server.py
```

**Saída esperada**:
```
============================================================
SERVIDOR DE MONITORAMENTO DE SENSORES - INICIALIZANDO
============================================================
✓ Banco de dados inicializado: /caminho/sensor_data.db

Servidor Flask rodando em http://0.0.0.0:5000
Endpoints disponíveis:
   POST   /sensor/reading  - Receber leitura de sensor
   GET    /sensor/history  - Consultar histórico
   GET    /sensor/stats    - Estatísticas gerais
   GET    /health          - Health check

Pressione CTRL+C para encerrar
```

#### **Passo 3**: Descobrir IP do servidor
```bash
# Linux/Mac
hostname -I

# Windows
ipconfig
```

**Exemplo**: `192.168.1.100`

---

### **2. Configurar o Cliente**

#### **Passo 1**: Instalar dependências
```bash
cd client/
pip install -r requirements.txt
```

#### **Passo 2**: Executar cliente
```bash
python client.py
```

#### **Passo 3**: Configurar URL do servidor na interface
1. No campo **"URL do Servidor"**, alterar para: `http://192.168.1.100:5000`
2. Clicar em **"Testar Conexão"** para validar

---

### **3. Usar o Sistema**

#### **Enviar leitura manual**:
1. Ajustar temperatura usando o slider
2. Clicar em **"Enviar Leitura"**
3. Observar status retornado (Normal/Alerta/Crítico)

#### **Gerar temperatura aleatória**:
- Clicar em **"Temperatura Aleatória"**

#### **Envio automático**:
- Marcar **"Envio Automático (5s)"**
- Sistema envia leitura a cada 5 segundos

#### **Ver histórico**:
- Tabela mostra últimas 50 leituras
- Marca duplicadas com `(DUP)`

------

## Schema do Banco de Dados

```sql
CREATE TABLE leituras (
    id TEXT PRIMARY KEY,           -- UUID da requisição (chave de idempotência)
    sensor_id TEXT NOT NULL,        -- Identificador do sensor
    temperatura REAL NOT NULL,      -- Valor em °C
    status_logico TEXT NOT NULL,    -- Normal | Alerta | Crítico
    timestamp DATETIME NOT NULL     -- Data/hora da leitura
);

CREATE INDEX idx_timestamp ON leituras(timestamp DESC);
```

**Exemplo de dados**:
```
id                                   | sensor_id   | temperatura | status_logico | timestamp
-------------------------------------|-------------|-------------|---------------|-------------------
550e8400-e29b-41d4-a716-446655440000 | SENSOR-1234 | 22.5        | Crítico       | 2024-03-31 14:30:00
6ba7b810-9dad-11d1-80b4-00c04fd430c8 | SENSOR-1234 | 8.3         | Normal        | 2024-03-31 14:29:55
```

---


- [ ] Containerização com Docker
- [ ] Orquestração com Kubernetes
- [ ] Monitoramento com Prometheus + Grafana
