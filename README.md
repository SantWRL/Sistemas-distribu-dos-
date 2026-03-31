# 🌡️ Sistema Distribuído de Monitoramento de Sensores de Temperatura

## 📋 Descrição do Projeto

Sistema cliente/servidor em **três camadas** para monitoramento distribuído de sensores de temperatura, implementando conceitos avançados de **sistemas distribuídos** como:

- ✅ **Idempotência** via UUID (tolerância a falhas de rede)
- ✅ **Retry com Exponential Backoff** (resiliência)
- ✅ **Transparência de Distribuição** (cliente não sabe como dados são armazenados)
- ✅ **Processamento Centralizado** (servidor como fonte única de verdade)
- ✅ **Comunicação Stateless** (escalabilidade horizontal)

---

## 🏗️ Arquitetura

```
┌─────────────────┐          HTTP/JSON           ┌─────────────────┐
│                 │  ─────────────────────────>   │                 │
│  CLIENTE        │                               │    SERVIDOR     │
│  (Tkinter)      │  <─────────────────────────   │    (Flask)      │
│                 │       Resposta Status         │                 │
└─────────────────┘                               └────────┬────────┘
                                                           │
     Gera UUID único                                       │ SQL
     Simula temperatura                                    │ Transações
     Retry automático                                      ▼
     Interface gráfica                           ┌─────────────────┐
                                                 │   BANCO DADOS   │
                                                 │    (SQLite)     │
                                                 └─────────────────┘
                                                   
                                                   Persistência ACID
                                                   UUID = PK (idempotência)
                                                   Índices otimizados
```

### 🔹 **Camada 1 - Cliente (Simulador de Sensor)**
- Interface gráfica em **Tkinter**
- Gera dados simulados de temperatura (-10°C a 40°C)
- Gera **UUID v4** para cada leitura (garantia de idempotência)
- Envia via **HTTP POST** para o servidor
- **Retry automático** com exponential backoff (5 tentativas: 0s, 1s, 2s, 4s, 8s)
- Exibe status retornado pelo servidor em tempo real
- Mantém histórico local das últimas 50 leituras

### 🔹 **Camada 2 - Servidor (Processamento de Lógica)**
- API REST em **Flask**
- **Valida requisições** (estrutura JSON, tipos, ranges)
- **Verificação de idempotência**: consulta UUID no banco antes de processar
- **Regras de negócio centralizadas**:
  - `Temperatura ≤ 10°C` → **Normal** 🟢
  - `10°C < Temperatura ≤ 15°C` → **Alerta** 🟡
  - `Temperatura > 15°C` → **Crítico** 🔴
- **Transações atômicas** no banco de dados

### 🔹 **Camada 3 - Banco de Dados (Persistência)**
- **SQLite** com schema otimizado
- UUID como **chave primária** (previne duplicação)
- Índice em `timestamp` para queries rápidas
- Constraints de integridade (NOT NULL)

---

## 🧠 Raciocínio Lógico - Sistemas Distribuídos

### 1️⃣ **Idempotência (Problema de Rede Não Confiável)**
**Cenário**: Cliente envia requisição → Servidor processa → Rede falha antes de responder

**Sem UUID**:
```
Cliente envia temp=25°C → Timeout → Cliente reenvia temp=25°C
Servidor insere registro 1: temp=25°C
Servidor insere registro 2: temp=25°C  ❌ DUPLICADO!
```

**Com UUID**:
```
Cliente envia {uuid: abc123, temp: 25°C} → Timeout → Cliente reenvia {uuid: abc123, temp: 25°C}
Servidor insere registro 1: uuid=abc123, temp=25°C
Servidor detecta uuid=abc123 já existe → Retorna sucesso sem inserir ✅
```

**Código relevante** (servidor):
```python
# Verificação de idempotência
cursor.execute('SELECT id FROM leituras WHERE id = ?', (req_uuid,))
existing = cursor.fetchone()

if existing:
    # UUID já processado - retornar sucesso (operação idempotente)
    return jsonify({'message': 'Leitura já processada', 'idempotent': True}), 200
```

---

### 2️⃣ **Retry com Exponential Backoff**
**Por quê?** Evitar sobrecarga do servidor em caso de instabilidade transitória.

**Progressão**:
- Tentativa 1: delay = 0s (imediato)
- Tentativa 2: delay = 1s
- Tentativa 3: delay = 2s
- Tentativa 4: delay = 4s
- Tentativa 5: delay = 8s

**Código relevante** (cliente):
```python
for attempt in range(1, max_retries + 1):
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return  # Sucesso!
    except ConnectionError:
        if attempt < max_retries:
            delay = 2 ** (attempt - 1)  # Exponencial
            time.sleep(delay)
```

---

### 3️⃣ **Transparência de Distribuição**
**Princípio**: Cliente não deve saber detalhes de implementação do servidor.

✅ Cliente só sabe:
- Endpoint: `POST /sensor/reading`
- Formato: JSON com `{uuid, sensor_id, temperatura}`
- Resposta: `{status, timestamp}`

❌ Cliente NÃO sabe:
- Que existe banco SQLite
- Como status é calculado (≤10°C = Normal)
- Que há verificação de UUID duplicado

**Benefício**: Servidor pode mudar BD (SQLite → PostgreSQL) sem alterar cliente!

---

### 4️⃣ **Fonte Única de Verdade (Single Source of Truth)**
**Por quê?** Evitar inconsistências entre cliente e servidor.

❌ **Ruim**: Cliente calcula status localmente
```python
# CLIENTE
if temp <= 10:
    status = 'Normal'  # E se servidor usar > 10?
```

✅ **Bom**: Servidor calcula e retorna status
```python
# SERVIDOR (fonte única de verdade)
status = calcular_status(temperatura)
return jsonify({'status': status})

# CLIENTE (confia na resposta)
status = response.json()['status']
```

---

### 5️⃣ **Stateless Design (Escalabilidade)**
Cada requisição é **independente** (não há sessão).

**Benefícios**:
- ✅ Pode ter múltiplas instâncias do servidor (load balancer)
- ✅ Se servidor cair, cliente continua enviando para outro
- ✅ Não há "perda de estado" (tudo está no BD)

---

## 🚀 Instruções de Execução

### 📦 **Pré-requisitos**
- Python 3.8 ou superior
- Dois computadores na mesma rede (ou usar `localhost` para testes)

---

### 🖥️ **1. Configurar o Servidor**

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

🚀 Servidor Flask rodando em http://0.0.0.0:5000
📊 Endpoints disponíveis:
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

### 💻 **2. Configurar o Cliente**

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
2. Clicar em **"🔌 Testar Conexão"** para validar

---

### 🎮 **3. Usar o Sistema**

#### **Enviar leitura manual**:
1. Ajustar temperatura usando o slider
2. Clicar em **"📤 Enviar Leitura"**
3. Observar status retornado (Normal/Alerta/Crítico)

#### **Gerar temperatura aleatória**:
- Clicar em **"🎯 Temperatura Aleatória"**

#### **Envio automático**:
- Marcar **"🔄 Envio Automático (5s)"**
- Sistema envia leitura a cada 5 segundos

#### **Ver histórico**:
- Tabela mostra últimas 50 leituras
- Marca duplicadas com `(DUP)`

---

## 📊 Endpoints da API

### `POST /sensor/reading`
Recebe leitura de sensor.

**Request**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "sensor_id": "SENSOR-1234",
  "temperatura": 22.5
}
```

**Response (201 Created)**:
```json
{
  "message": "Leitura processada com sucesso",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "sensor_id": "SENSOR-1234",
  "temperatura": 22.5,
  "status": "Crítico",
  "timestamp": "2024-03-31T14:30:00.123456",
  "idempotent": false
}
```

**Response (200 OK - UUID duplicado)**:
```json
{
  "message": "Leitura já processada (requisição duplicada)",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "Crítico",
  "idempotent": true
}
```

---

### `GET /sensor/history?limit=10&offset=0`
Consulta histórico de leituras.

**Response**:
```json
{
  "leituras": [
    {
      "id": "550e8400-...",
      "sensor_id": "SENSOR-1234",
      "temperatura": 22.5,
      "status_logico": "Crítico",
      "timestamp": "2024-03-31T14:30:00.123456"
    }
  ],
  "total": 150,
  "limit": 10,
  "offset": 0
}
```

---

### `GET /sensor/stats`
Estatísticas agregadas.

**Response**:
```json
{
  "total_leituras": 150,
  "distribuicao_status": {
    "Normal": 90,
    "Alerta": 45,
    "Crítico": 15
  },
  "temperatura": {
    "minima": -8.5,
    "maxima": 38.2,
    "media": 12.7
  }
}
```

---

### `GET /health`
Health check.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-31T14:30:00.123456",
  "version": "1.0.0"
}
```

---

## 🗄️ Schema do Banco de Dados

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

## 🧪 Testes de Idempotência

### **Teste 1: Envio duplicado intencional**

1. Cliente envia leitura com UUID `abc-123`
2. Cliente envia **novamente** com UUID `abc-123`
3. **Resultado esperado**: Servidor retorna `idempotent: true`, sem inserir duplicata

### **Teste 2: Simulação de timeout**

1. Cliente envia leitura
2. **Desconectar rede** após servidor processar mas antes de responder
3. Cliente executa retry automático
4. **Resultado esperado**: Servidor detecta UUID já processado, retorna sucesso

---

## 📸 Demonstração Visual

### **Interface do Cliente**
```
┌──────────────────────────────────────────────────────┐
│  🌡️ Simulador de Sensor de Temperatura              │
├──────────────────────────────────────────────────────┤
│  ⚙️ Configuração                                     │
│  URL do Servidor: http://192.168.1.100:5000          │
│  ID do Sensor: SENSOR-3847       [🔌 Testar Conexão] │
├──────────────────────────────────────────────────────┤
│  🎲 Simulação de Temperatura                         │
│  Temperatura: [========|====] 22.5°C                 │
│  [🎯 Aleatória] [📤 Enviar] [🔄 Auto (5s)]           │
├──────────────────────────────────────────────────────┤
│  📊 Status Atual                                     │
│   ⬤  Status: Crítico                                 │
│  🔴  UUID: 550e8400-e29b-...                         │
│      Timestamp: 2024-03-31 14:30:00                  │
├──────────────────────────────────────────────────────┤
│  📜 Histórico de Leituras                            │
│  ┌────────────┬──────┬──────────┬─────────────────┐ │
│  │ Data/Hora  │ Temp │ Status   │ UUID            │ │
│  ├────────────┼──────┼──────────┼─────────────────┤ │
│  │ 14:30:00   │ 22.5 │ Crítico  │ 550e8400...     │ │
│  │ 14:29:55   │ 8.3  │ Normal   │ 6ba7b810...     │ │
│  └────────────┴──────┴──────────┴─────────────────┘ │
│                          [🗑️ Limpar Histórico]      │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Cliente** | Tkinter | Interface gráfica nativa Python, multiplataforma |
| **Servidor** | Flask | Framework leve, ideal para APIs REST |
| **Comunicação** | HTTP/JSON | Protocolo stateless, interoperável |
| **Banco de Dados** | SQLite | Embedded, transacional (ACID), sem setup |
| **UUID** | uuid4 | 128-bit único, collision-proof |

---

## 📚 Conceitos de Sistemas Distribuídos Aplicados

✅ **Idempotência** - Operações podem ser repetidas sem efeitos colaterais  
✅ **Retry Logic** - Resiliência a falhas transitórias de rede  
✅ **Exponential Backoff** - Evita sobrecarga do servidor  
✅ **Stateless Communication** - Escalabilidade horizontal  
✅ **Single Source of Truth** - Consistência de dados  
✅ **Transparência de Distribuição** - Cliente não conhece implementação  
✅ **Transações Atômicas** - ACID no banco de dados  
✅ **Validação de Entrada** - Prevenção de SQL injection e dados malformados  

---

## 🎯 Funcionalidades Implementadas

- [x] Cliente gera UUID único por leitura
- [x] Servidor valida UUID antes de inserir (idempotência)
- [x] Regras de negócio centralizadas (Normal/Alerta/Crítico)
- [x] Retry automático com exponential backoff
- [x] Interface gráfica responsiva (threading)
- [x] Histórico local no cliente (últimas 50 leituras)
- [x] API REST com 4 endpoints
- [x] Health check endpoint
- [x] Validação rigorosa de dados
- [x] Transações atômicas no BD
- [x] Índices otimizados para queries
- [x] Tratamento de erros com códigos HTTP apropriados

---

## 📹 Vídeo Demonstrativo

*[Incluir link do vídeo mostrando cliente e servidor em execução]*

---

## 👨‍💻 Autor

Sistema desenvolvido como projeto de **Sistemas Distribuídos**, demonstrando conceitos avançados de arquitetura cliente/servidor, idempotência, e comunicação resiliente.

---

## 📄 Licença

MIT License - Livre para uso educacional e comercial.

---

## 🐛 Troubleshooting

### Problema: "Erro de conexão"
**Solução**: 
1. Verificar se servidor está rodando (`python server.py`)
2. Verificar firewall (liberar porta 5000)
3. Testar com `curl http://IP_SERVIDOR:5000/health`

### Problema: "UUID duplicado"
**Solução**: Isso é **normal** em caso de retry! O sistema está funcionando corretamente (idempotência).

### Problema: Cliente congela ao enviar
**Solução**: Verificar se está usando `_enviar_leitura_thread()` (executa em thread separada).

---

## 🚀 Melhorias Futuras

- [ ] Autenticação JWT entre cliente e servidor
- [ ] Migrar de SQLite para PostgreSQL (produção)
- [ ] Implementar WebSocket para push de alertas
- [ ] Dashboard web com gráficos em tempo real
- [ ] Rate limiting no servidor (prevenir DDoS)
- [ ] Criptografia TLS/SSL (HTTPS)
- [ ] Containerização com Docker
- [ ] Orquestração com Kubernetes
- [ ] Monitoramento com Prometheus + Grafana
