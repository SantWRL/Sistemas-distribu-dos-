import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = "leituras.db"

def init_db():
    """Cria a tabela de leituras no banco de dados SQLite caso não exista."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leituras (
                id TEXT PRIMARY KEY,
                sensor_id TEXT,
                temperatura REAL,
                status_logico TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
init_db()

def get_status_from_temp(temp: float) -> str:
    """Classifica a temperatura recebida com base nas regras de negócio."""
    if temp <= 10:
        return "Normal"
    elif temp <= 15:
        return "Alerta"
    return "Crítico"

@app.route('/reading', methods=['POST'])
def receive_reading():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    reading_uuid = data.get('uuid')
    sensor_id = data.get('sensor_id')
    temperature = data.get('temperature')

    if not all([reading_uuid, sensor_id, temperature is not None]):
        return jsonify({"error": "Campos ausentes"}), 400

    # Idempotência: Checa se este evento (UUID) já foi processado anteriormente
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT status_logico FROM leituras WHERE id = ?", (reading_uuid,))
        existing = cur.fetchone()

    if existing:
        # Se já existe, apenas devolve o status antigo, não duplica a entrada
        return jsonify({
            "status": "duplicado",
            "reading_status": existing[0],
            "message": "UUID já processado"
        }), 200

    status = get_status_from_temp(temperature)

    # Salva a nova leitura no banco de dados
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO leituras (id, sensor_id, temperatura, status_logico) VALUES (?, ?, ?, ?)",
            (reading_uuid, sensor_id, temperature, status)
        )

    return jsonify({
        "status": "sucesso",
        "reading_status": status,
        "message": f"Leitura salva. Status: {status}"
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # 0.0.0.0 permite receber conexões de qualquer IP na rede local
    app.run(host='0.0.0.0', port=5000, debug=False) 