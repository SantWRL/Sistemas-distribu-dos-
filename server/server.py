"""
SERVIDOR FLASK - Sistema Distribuído de Monitoramento de Sensores
==================================================================

RACIOCÍNIO LÓGICO APLICADO:
--------------------------

1. IDEMPOTÊNCIA (Princípio fundamental em sistemas distribuídos)
   - UUID como chave primária previne duplicação de dados
   - Se a rede falhar após processar mas antes de responder, o cliente
     pode reenviar a mesma requisição sem criar registros duplicados
   - Implementação: Verificação de UUID antes de INSERT

2. REGRAS DE NEGÓCIO CENTRALIZADAS
   - Servidor é fonte única de verdade para classificação de status
   - Cliente NÃO decide se é alerta/crítico (evita inconsistência)
   - Lógica: temperatura <= 10°C = Normal
             10°C < temperatura <= 15°C = Alerta  
             temperatura > 15°C = Crítico

3. TRANSAÇÕES ATÔMICAS
   - Operação de verificação + inserção é atômica (previne race conditions)
   - Se falhar qualquer etapa, rollback automático

4. STATELESS DESIGN
   - Cada requisição é independente (não há sessão)
   - Escalável horizontalmente (pode ter múltiplas instâncias do servidor)

5. VALIDAÇÃO RIGOROSA
   - Valida estrutura JSON, tipos de dados, ranges válidos
   - Retorna erros HTTP apropriados (400 Bad Request, 409 Conflict)
"""

from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import os
import uuid as uuid_lib

app = Flask(__name__)

# Configuração do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'sensor_data.db')


def init_database():
    """
    RACIOCÍNIO: Inicialização do schema com constraints apropriados
    
    - UUID como TEXT e PRIMARY KEY (garante unicidade)
    - NOT NULL em campos críticos (integridade referencial)
    - CHECK constraint poderia ser adicionado para validar temperatura
    - Index em timestamp para queries de histórico rápidas
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id TEXT PRIMARY KEY,           -- UUID da requisição (idempotência)
            sensor_id TEXT NOT NULL,        -- Identificador do sensor
            temperatura REAL NOT NULL,      -- Valor em °C
            status_logico TEXT NOT NULL,    -- Normal/Alerta/Crítico
            timestamp DATETIME NOT NULL     -- Data/hora da leitura
        )
    ''')
    
    # Criar índice para otimizar buscas por timestamp
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON leituras(timestamp DESC)
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Banco de dados inicializado: {DB_PATH}")


def calcular_status(temperatura):
    """
    RACIOCÍNIO: Lógica de classificação de alertas
    
    Centraliza a regra de negócio no servidor (single source of truth)
    Facilita manutenção: mudar threshold só precisa modificar aqui
    
    Args:
        temperatura (float): Temperatura em °C
        
    Returns:
        str: 'Normal', 'Alerta' ou 'Crítico'
    """
    if temperatura <= 10:
        return 'Normal'
    elif temperatura <= 15:
        return 'Alerta'
    else:
        return 'Crítico'


def validar_uuid(uuid_str):
    """
    RACIOCÍNIO: Validação de formato UUID
    
    Previne tentativas de SQL injection ou dados malformados
    UUID v4 tem formato específico: 8-4-4-4-12 caracteres hexadecimais
    """
    try:
        uuid_obj = uuid_lib.UUID(uuid_str, version=4)
        return str(uuid_obj) == uuid_str
    except (ValueError, AttributeError):
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """
    RACIOCÍNIO: Endpoint de healthcheck
    
    Essencial para sistemas distribuídos:
    - Load balancers verificam se servidor está vivo
    - Monitoramento pode alertar se servidor cai
    - Kubernetes/Docker usa para liveness/readiness probes
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


@app.route('/sensor/reading', methods=['POST'])
def receive_reading():
    """
    RACIOCÍNIO: Endpoint principal de recepção de leituras
    
    FLUXO DE PROCESSAMENTO:
    1. Validação de payload (estrutura JSON)
    2. Validação de campos obrigatórios
    3. Validação de tipos e ranges
    4. Verificação de idempotência (UUID já existe?)
    5. Aplicação de lógica de negócio (cálculo de status)
    6. Persistência atômica no banco
    7. Resposta estruturada ao cliente
    
    TRATAMENTO DE ERROS:
    - 400: Dados inválidos (cliente deve corrigir)
    - 409: UUID duplicado (requisição já foi processada)
    - 500: Erro interno (cliente pode tentar novamente)
    """
    try:
        # 1. VALIDAÇÃO DE PAYLOAD
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'JSON payload esperado',
                'code': 'INVALID_PAYLOAD'
            }), 400
        
        # 2. VALIDAÇÃO DE CAMPOS OBRIGATÓRIOS
        required_fields = ['uuid', 'sensor_id', 'temperatura']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({
                'error': f'Campos obrigatórios faltando: {", ".join(missing)}',
                'code': 'MISSING_FIELDS'
            }), 400
        
        # 3. EXTRAÇÃO E VALIDAÇÃO DE DADOS
        req_uuid = data['uuid']
        sensor_id = data['sensor_id']
        temperatura = data['temperatura']
        
        # Validação de UUID
        if not validar_uuid(req_uuid):
            return jsonify({
                'error': 'UUID inválido (esperado UUID v4)',
                'code': 'INVALID_UUID'
            }), 400
        
        # Validação de temperatura (tipo e range realista)
        try:
            temperatura = float(temperatura)
            if temperatura < -50 or temperatura > 100:
                return jsonify({
                    'error': 'Temperatura fora do range válido (-50°C a 100°C)',
                    'code': 'TEMPERATURE_OUT_OF_RANGE'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Temperatura deve ser um número',
                'code': 'INVALID_TEMPERATURE_TYPE'
            }), 400
        
        # Validação de sensor_id
        if not isinstance(sensor_id, str) or len(sensor_id) == 0:
            return jsonify({
                'error': 'sensor_id deve ser uma string não vazia',
                'code': 'INVALID_SENSOR_ID'
            }), 400
        
        # 4. VERIFICAÇÃO DE IDEMPOTÊNCIA
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM leituras WHERE id = ?', (req_uuid,))
        existing = cursor.fetchone()
        
        if existing:
            # UUID já foi processado - retornar sucesso (idempotente)
            cursor.execute(
                'SELECT status_logico FROM leituras WHERE id = ?', 
                (req_uuid,)
            )
            status = cursor.fetchone()[0]
            conn.close()
            
            return jsonify({
                'message': 'Leitura já processada (requisição duplicada)',
                'uuid': req_uuid,
                'status': status,
                'idempotent': True
            }), 200
        
        # 5. APLICAÇÃO DE LÓGICA DE NEGÓCIO
        status = calcular_status(temperatura)
        timestamp = datetime.now().isoformat()
        
        # 6. PERSISTÊNCIA ATÔMICA
        try:
            cursor.execute('''
                INSERT INTO leituras (id, sensor_id, temperatura, status_logico, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (req_uuid, sensor_id, temperatura, status, timestamp))
            
            conn.commit()
            
        except sqlite3.IntegrityError as e:
            # Race condition improvável (outro processo inseriu o mesmo UUID)
            conn.rollback()
            conn.close()
            return jsonify({
                'error': 'UUID duplicado (race condition)',
                'code': 'DUPLICATE_UUID'
            }), 409
        
        finally:
            conn.close()
        
        # 7. RESPOSTA ESTRUTURADA
        return jsonify({
            'message': 'Leitura processada com sucesso',
            'uuid': req_uuid,
            'sensor_id': sensor_id,
            'temperatura': temperatura,
            'status': status,
            'timestamp': timestamp,
            'idempotent': False
        }), 201
    
    except Exception as e:
        # Log do erro (em produção, usar logging adequado)
        print(f"ERRO INTERNO: {str(e)}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'code': 'INTERNAL_ERROR'
        }), 500


@app.route('/sensor/history', methods=['GET'])
def get_history():
    """
    RACIOCÍNIO: Endpoint de consulta histórica
    
    Permite análise posterior dos dados
    Implementa paginação via query params (limit/offset)
    Ordenação DESC por timestamp (mais recentes primeiro)
    
    Query params:
    - limit: número de registros (default: 100)
    - offset: pular N registros (default: 0)
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Validação de parâmetros
    if limit < 1 or limit > 1000:
        return jsonify({
            'error': 'Limit deve estar entre 1 e 1000',
            'code': 'INVALID_LIMIT'
        }), 400
    
    if offset < 0:
        return jsonify({
            'error': 'Offset não pode ser negativo',
            'code': 'INVALID_OFFSET'
        }), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Retorna dicts em vez de tuplas
        cursor = conn.cursor()
        
        # Buscar com paginação
        cursor.execute('''
            SELECT id, sensor_id, temperatura, status_logico, timestamp
            FROM leituras
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        
        # Converter para lista de dicts
        leituras = [dict(row) for row in rows]
        
        # Contar total de registros
        cursor.execute('SELECT COUNT(*) FROM leituras')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'leituras': leituras,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        print(f"ERRO ao buscar histórico: {str(e)}")
        return jsonify({
            'error': 'Erro ao buscar histórico',
            'code': 'QUERY_ERROR'
        }), 500


@app.route('/sensor/stats', methods=['GET'])
def get_stats():
    """
    RACIOCÍNIO: Endpoint de estatísticas agregadas
    
    Fornece visão geral do sistema:
    - Total de leituras
    - Distribuição por status
    - Temperatura mínima/máxima/média
    
    Útil para dashboards e monitoramento
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total de leituras
        cursor.execute('SELECT COUNT(*) FROM leituras')
        total = cursor.fetchone()[0]
        
        # Distribuição por status
        cursor.execute('''
            SELECT status_logico, COUNT(*) as count
            FROM leituras
            GROUP BY status_logico
        ''')
        status_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Estatísticas de temperatura
        cursor.execute('''
            SELECT 
                MIN(temperatura) as min_temp,
                MAX(temperatura) as max_temp,
                AVG(temperatura) as avg_temp
            FROM leituras
        ''')
        temp_stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'total_leituras': total,
            'distribuicao_status': status_dist,
            'temperatura': {
                'minima': round(temp_stats[0], 2) if temp_stats[0] else None,
                'maxima': round(temp_stats[1], 2) if temp_stats[1] else None,
                'media': round(temp_stats[2], 2) if temp_stats[2] else None
            }
        }), 200
    
    except Exception as e:
        print(f"ERRO ao calcular estatísticas: {str(e)}")
        return jsonify({
            'error': 'Erro ao calcular estatísticas',
            'code': 'STATS_ERROR'
        }), 500


if __name__ == '__main__':
    """
    RACIOCÍNIO: Configuração de execução
    
    - host='0.0.0.0': Aceita conexões de qualquer IP (necessário para rede)
    - port=5000: Porta padrão Flask
    - debug=True: Apenas para desenvolvimento (desabilitar em produção)
    - threaded=True: Suporta múltiplas requisições simultâneas
    """
    print("=" * 60)
    print("SERVIDOR DE MONITORAMENTO DE SENSORES - INICIALIZANDO")
    print("=" * 60)
    
    init_database()
    
    print("\n🚀 Servidor Flask rodando em http://0.0.0.0:5000")
    print("📊 Endpoints disponíveis:")
    print("   POST   /sensor/reading  - Receber leitura de sensor")
    print("   GET    /sensor/history  - Consultar histórico")
    print("   GET    /sensor/stats    - Estatísticas gerais")
    print("   GET    /health          - Health check")
    print("\nPressione CTRL+C para encerrar\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
