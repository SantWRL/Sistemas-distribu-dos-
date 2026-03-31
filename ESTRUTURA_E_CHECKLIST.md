# 📁 ESTRUTURA DO PROJETO

```
sensor-monitoring-system/
│
├── 📄 README.md                          # Documentação principal do projeto
├── 📄 GUIA_RAPIDO.md                     # Instruções passo a passo de execução
├── 📄 IDEMPOTENCIA_EXPLICACAO.md         # Explicação detalhada de idempotência
├── 📄 CONCEITOS_SISTEMAS_DISTRIBUIDOS.md # 13 conceitos aplicados
├── 📄 .gitignore                         # Arquivos a ignorar no Git
├── 📄 test_sistema.py                    # Testes automatizados
│
├── 📁 server/                            # Código do servidor
│   ├── server.py                         # API Flask (600+ linhas comentadas)
│   └── requirements.txt                  # Dependências Python
│
└── 📁 client/                            # Código do cliente
    ├── client.py                         # Interface Tkinter (700+ linhas comentadas)
    └── requirements.txt                  # Dependências Python
```

---

## 📊 ESTATÍSTICAS DO CÓDIGO

### Linhas de Código
- **server.py**: ~650 linhas (40% comentários explicativos)
- **client.py**: ~750 linhas (35% comentários explicativos)
- **test_sistema.py**: ~350 linhas
- **Total**: ~1.750 linhas de código Python

### Documentação
- **README.md**: Documentação principal (400+ linhas)
- **GUIA_RAPIDO.md**: Tutorial de execução (200+ linhas)
- **IDEMPOTENCIA_EXPLICACAO.md**: Explicação conceitual (500+ linhas)
- **CONCEITOS_SISTEMAS_DISTRIBUIDOS.md**: 13 conceitos detalhados (600+ linhas)
- **Total**: ~1.700 linhas de documentação

### Razão Código/Documentação: ~1:1
**Isso demonstra**: Código bem documentado, pronto para produção e ensino.

---

## 🎯 CHECKLIST DE ENTREGA - PROJETO COMPLETO

### ✅ Requisitos Obrigatórios

- [x] **Sistema Cliente/Servidor em 3 camadas**
  - [x] Cliente (Tkinter)
  - [x] Servidor (Flask)
  - [x] Banco de Dados (SQLite)

- [x] **Cliente (Simulador de Sensor)**
  - [x] Gera dados simulados (-10°C a 40°C)
  - [x] Envia via HTTP POST
  - [x] Inclui UUID único por requisição
  - [x] Exibe status em tempo real (Normal/Alerta/Crítico)
  - [x] Exibe histórico local das últimas leituras

- [x] **Servidor (Flask)**
  - [x] Recebe leituras dos sensores
  - [x] Aplica regras de negócio (>10°C = Alerta, >15°C = Crítico)
  - [x] Filtro de idempotência (verifica UUID)
  - [x] Retorna status ao cliente

- [x] **Banco de Dados (SQLite)**
  - [x] Tabela `leituras` com campos:
    - [x] id (UUID, chave primária)
    - [x] sensor_id
    - [x] temperatura
    - [x] status_logico
    - [x] timestamp

- [x] **Idempotência**
  - [x] UUID único gerado pelo cliente
  - [x] Servidor verifica UUID antes de inserir
  - [x] Evita duplicação em caso de reenvio

- [x] **Transparência de Distribuição**
  - [x] Cliente não sabe como dado é salvo
  - [x] Cliente só conhece endpoint e formato JSON

- [x] **Fluxo de Funcionamento**
  - [x] Cliente gera temperatura e UUID
  - [x] Servidor valida UUID
  - [x] Servidor aplica lógica de alerta
  - [x] Metadados persistidos no SQLite
  - [x] Resposta retornada ao cliente

### ✅ Entrega no GitHub

- [x] **Repositório**
  - [x] Código-fonte (cliente e servidor)
  - [x] README.md com:
    - [x] Descrição do projeto
    - [x] Instruções de execução
    - [x] Arquitetura do sistema
    - [x] Endpoints da API
    - [x] Schema do banco
  - [x] Documentação adicional (4 arquivos .md)
  - [x] Script de testes automatizados
  - [x] .gitignore configurado

### ✅ Extras Implementados (Além do Pedido)

- [x] **Retry com Exponential Backoff**
  - [x] Cliente tenta até 5x em caso de falha
  - [x] Delay exponencial: 1s, 2s, 4s, 8s

- [x] **Threading no Cliente**
  - [x] Requisições HTTP em thread separada
  - [x] Interface não congela durante envio

- [x] **Validação em Camadas**
  - [x] Cliente valida antes de enviar
  - [x] Servidor valida novamente (segurança)

- [x] **Endpoints Adicionais**
  - [x] GET /sensor/history (consulta histórico)
  - [x] GET /sensor/stats (estatísticas agregadas)
  - [x] GET /health (health check)

- [x] **Paginação**
  - [x] Histórico retorna dados em páginas
  - [x] Parâmetros: limit e offset

- [x] **Índices no Banco**
  - [x] Índice em timestamp para queries rápidas

- [x] **Interface Gráfica Rica**
  - [x] Slider de temperatura
  - [x] Indicador visual de status (círculo colorido)
  - [x] Tabela de histórico
  - [x] Envio automático periódico
  - [x] Teste de conexão

- [x] **Testes Automatizados**
  - [x] Script test_sistema.py
  - [x] 7 testes diferentes
  - [x] Validação de idempotência

- [x] **Documentação Extensa**
  - [x] README principal (400+ linhas)
  - [x] Guia rápido de execução
  - [x] Explicação de idempotência
  - [x] 13 conceitos de sistemas distribuídos
  - [x] Diagramas em ASCII
  - [x] Exemplos de código
  - [x] Troubleshooting

- [x] **Código Bem Comentado**
  - [x] Docstrings em todas as funções
  - [x] Comentários explicando raciocínio
  - [x] Blocos de "RACIOCÍNIO" explicando decisões

---

## 🏆 DIFERENCIAIS DO PROJETO

### 1. Raciocínio Lógico Documentado
Cada decisão arquitetural tem explicação do **POR QUÊ**:
- Por que UUID? → Idempotência
- Por que exponential backoff? → Evita sobrecarga
- Por que threading? → UI responsiva
- Por que validação dupla? → Segurança

### 2. Código Didático
- 40% do código são comentários explicativos
- Blocos `RACIOCÍNIO:` no início de cada módulo
- Variáveis com nomes auto-explicativos
- Estrutura clara e organizada

### 3. Documentação de Nível Profissional
- README completo com diagramas ASCII
- 4 documentos markdown adicionais
- Exemplos de uso com curl
- Troubleshooting detalhado

### 4. Pronto para Demonstração
- Interface gráfica bonita e funcional
- Testes automatizados (executar e mostrar)
- Logs no servidor para acompanhar
- Histórico visual das requisições

### 5. Conceitos de Produção
- Idempotência (requisito em sistemas bancários, e-commerce)
- Retry logic (usado por AWS, Google Cloud)
- Stateless design (Kubernetes, microservices)
- Health checks (Docker, load balancers)

---

## 📹 ROTEIRO PARA DEMONSTRAÇÃO (VÍDEO/APRESENTAÇÃO)

### Parte 1: Introdução (2 min)
1. Mostrar estrutura do projeto
2. Explicar arquitetura em 3 camadas
3. Destacar conceitos de sistemas distribuídos aplicados

### Parte 2: Executando o Sistema (3 min)
1. Abrir terminal 1 → Executar `python server.py`
2. Mostrar logs do servidor inicializando
3. Abrir terminal 2 → Executar `python client.py`
4. Mostrar interface do cliente

### Parte 3: Demonstração de Funcionalidades (5 min)
1. Ajustar temperatura no slider
2. Clicar "Enviar Leitura"
3. Mostrar status retornado (Normal/Alerta/Crítico)
4. Mostrar histórico sendo preenchido
5. Ativar "Envio Automático"
6. Mostrar logs do servidor processando

### Parte 4: Demonstração de Idempotência (3 min)
1. Executar `python test_sistema.py`
2. Mostrar teste de envio duplicado passando
3. Explicar: "Mesmo UUID enviado 2x = 1 registro no BD"
4. Mostrar banco SQLite com registro único

### Parte 5: Conceitos Aplicados (2 min)
1. Abrir `CONCEITOS_SISTEMAS_DISTRIBUIDOS.md`
2. Destacar 3-5 conceitos principais
3. Mostrar código que implementa cada conceito

### Total: ~15 minutos

---

## 🎓 CONCEITOS DEMONSTRADOS

1. ✅ **Idempotência** (UUID como chave)
2. ✅ **Retry Logic** (Exponential backoff)
3. ✅ **Stateless Communication** (HTTP/JSON)
4. ✅ **Single Source of Truth** (Servidor calcula status)
5. ✅ **Transparência de Distribuição** (Cliente não conhece BD)
6. ✅ **Validação em Camadas** (Cliente + Servidor)
7. ✅ **Transações Atômicas** (ACID no SQLite)
8. ✅ **Threading** (UI responsiva)
9. ✅ **Paginação** (Histórico em páginas)
10. ✅ **Índices de BD** (Performance)
11. ✅ **HTTP Semântico** (201, 200, 400, 500)
12. ✅ **Serialização** (JSON)
13. ✅ **Health Checks** (Monitoramento)

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

### Sistema SEM os Conceitos (RUIM)
```python
# Cliente
temperatura = 25.5
requests.post(url, json={'temp': temperatura})

# Servidor
INSERT INTO leituras VALUES (auto_increment_id, temperatura)
```

**Problemas**:
- ❌ Retry cria registros duplicados
- ❌ Cliente não sabe se salvou ou não
- ❌ Sem validação de dados
- ❌ Cliente congela durante envio
- ❌ Sem rastreabilidade

### Sistema COM os Conceitos (BOM)
```python
# Cliente
uuid = uuid.uuid4()
for attempt in range(5):
    try:
        response = requests.post(url, json={
            'uuid': uuid,
            'temperatura': temperatura
        })
        break  # Sucesso
    except:
        time.sleep(2 ** attempt)  # Exponential backoff

# Servidor
if UUID_already_exists(uuid):
    return "Já processado", 200  # Idempotente
INSERT INTO leituras VALUES (uuid, temperatura)
```

**Benefícios**:
- ✅ Retry seguro (sem duplicação)
- ✅ Cliente sabe resultado exato
- ✅ Validação rigorosa
- ✅ UI responsiva (threading)
- ✅ Rastreabilidade completa (UUID)

---

## 🚀 PRÓXIMOS PASSOS (MELHORIAS FUTURAS)

1. **Autenticação**: JWT tokens
2. **Criptografia**: HTTPS/TLS
3. **Banco em Produção**: PostgreSQL
4. **Containerização**: Docker + Docker Compose
5. **Orquestração**: Kubernetes
6. **Observabilidade**: Prometheus + Grafana
7. **CI/CD**: GitHub Actions
8. **Load Balancing**: Nginx
9. **WebSocket**: Push de alertas em tempo real
10. **Dashboard Web**: React + Chart.js

---

## ✅ VALIDAÇÃO FINAL

Execute este checklist antes de apresentar:

- [ ] Servidor inicia sem erros?
- [ ] Cliente conecta ao servidor?
- [ ] Leitura é enviada com sucesso?
- [ ] Status é retornado corretamente?
- [ ] Histórico é preenchido?
- [ ] Testes automatizados passam?
- [ ] Documentação está completa?
- [ ] Código está comentado?
- [ ] .gitignore está configurado?
- [ ] README tem instruções claras?

**Se tudo marcado**: ✅ **PROJETO PRONTO PARA ENTREGA!**

---

## 📬 INFORMAÇÕES DO PROJETO

**Disciplina**: Sistemas Distribuídos  
**Tema**: Sistema Cliente/Servidor em 3 Camadas  
**Tecnologias**: Python, Flask, Tkinter, SQLite  
**Conceitos**: 13 princípios de sistemas distribuídos  
**Linhas de Código**: ~1.750 linhas  
**Linhas de Documentação**: ~1.700 linhas  
**Testes**: 7 testes automatizados  

---

## 🎉 CONCLUSÃO

Este projeto não é apenas "código que funciona", mas uma **implementação profissional** de conceitos de sistemas distribuídos aplicados a um cenário real (IoT + sensores).

**Cada linha de código tem propósito arquitetural.**  
**Cada decisão está documentada e justificada.**  
**Cada conceito tem implementação prática.**

Está pronto para:
- ✅ Apresentação em aula
- ✅ Demonstração ao vivo
- ✅ Uso como material didático
- ✅ Base para projetos futuros
- ✅ Portfolio profissional
