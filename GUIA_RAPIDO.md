# 🚀 GUIA RÁPIDO DE EXECUÇÃO

## CENÁRIO 1: Teste Local (Um Computador)

### 1️⃣ Abrir Terminal 1 - SERVIDOR
```bash
cd sensor-monitoring-system/server
pip install -r requirements.txt
python server.py
```

**Aguarde ver**: 
```
✓ Banco de dados inicializado
🚀 Servidor Flask rodando em http://0.0.0.0:5000
```

### 2️⃣ Abrir Terminal 2 - CLIENTE
```bash
cd sensor-monitoring-system/client
pip install -r requirements.txt
python client.py
```

**Na interface do cliente**:
- URL do Servidor: `http://localhost:5000`
- Clicar em "🔌 Testar Conexão" → deve aparecer "Conexão OK"

### 3️⃣ Testar
- Ajustar temperatura no slider
- Clicar em "📤 Enviar Leitura"
- Observar status retornado

### 4️⃣ (Opcional) Executar Testes Automatizados
```bash
# Em um terceiro terminal
cd sensor-monitoring-system
python test_sistema.py
```

---

## CENÁRIO 2: Dois Computadores na Rede

### 📍 Computador 1 - SERVIDOR

#### Passo 1: Descobrir IP
```bash
# Linux/Mac
hostname -I
# Exemplo de saída: 192.168.1.100

# Windows
ipconfig
# Procurar por "IPv4 Address"
```

#### Passo 2: Liberar Firewall
```bash
# Linux (Ubuntu)
sudo ufw allow 5000/tcp

# Windows
# Ir em: Firewall → Regras de Entrada → Nova Regra → Porta 5000

# Mac
# Ir em: Preferências → Segurança → Firewall → Opções → Permitir porta 5000
```

#### Passo 3: Executar Servidor
```bash
cd sensor-monitoring-system/server
pip install -r requirements.txt
python server.py
```

---

### 💻 Computador 2 - CLIENTE

#### Passo 1: Executar Cliente
```bash
cd sensor-monitoring-system/client
pip install -r requirements.txt
python client.py
```

#### Passo 2: Configurar URL
Na interface do cliente:
- URL do Servidor: `http://192.168.1.100:5000` 
  (substituir pelo IP do Computador 1)
- Clicar em "🔌 Testar Conexão"

#### Passo 3: Usar o Sistema
- Enviar leituras normalmente

---

## 🐛 TROUBLESHOOTING

### Problema: "Connection refused"
**Causa**: Servidor não está rodando ou firewall bloqueando

**Solução**:
1. Verificar se servidor está rodando
2. Testar com `curl http://IP_SERVIDOR:5000/health`
3. Liberar porta 5000 no firewall

### Problema: Cliente congela ao enviar
**Causa**: URL do servidor incorreto

**Solução**:
- Verificar se o IP está correto
- Verificar se incluiu `http://` no início
- Verificar se incluiu `:5000` no final

### Problema: "UUID duplicado"
**Causa**: Isso é **NORMAL** quando há retry!

**Solução**: Não fazer nada, o sistema está funcionando corretamente (idempotência)

---

## 📊 VERIFICAR SE ESTÁ FUNCIONANDO

### No Servidor
Você deve ver logs como:
```
127.0.0.1 - - [31/Mar/2024 14:30:00] "POST /sensor/reading HTTP/1.1" 201 -
127.0.0.1 - - [31/Mar/2024 14:30:05] "POST /sensor/reading HTTP/1.1" 201 -
```

### No Cliente
- Status deve mudar de "Aguardando..." para "Normal/Alerta/Crítico"
- Histórico deve ser preenchido com leituras
- Indicador circular deve mudar de cor

---

## 🎯 COMANDOS ÚTEIS

### Ver histórico no servidor via curl
```bash
curl http://localhost:5000/sensor/history?limit=5 | python -m json.tool
```

### Ver estatísticas
```bash
curl http://localhost:5000/sensor/stats | python -m json.tool
```

### Enviar leitura via curl (teste manual)
```bash
curl -X POST http://localhost:5000/sensor/reading \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "sensor_id": "CURL-TEST",
    "temperatura": 18.5
  }'
```

---

## 💡 DICAS

1. **Sempre execute o SERVIDOR primeiro**, depois o CLIENTE
2. **Teste a conexão** antes de enviar leituras
3. Use o **envio automático** para simular sensor real
4. **Monitore os logs** do servidor para debug
5. Execute **test_sistema.py** para validar idempotência
