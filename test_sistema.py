"""
SCRIPT DE TESTE - Validação de Idempotência
============================================

RACIOCÍNIO:
Este script testa se o servidor realmente garante idempotência.

TESTES:
1. Envio único - Deve retornar 201 Created
2. Envio duplicado (mesmo UUID) - Deve retornar 200 OK com idempotent=True
3. Múltiplos sensores - Deve aceitar UUIDs diferentes mesmo com mesma temperatura
4. Validação de dados - Deve rejeitar payloads inválidos

Executar APÓS iniciar o servidor.
"""

import requests
import uuid
import json


# Configuração
SERVER_URL = "http://localhost:5000"


def test_envio_unico():
    """
    TESTE 1: Envio de leitura única
    Espera-se: 201 Created, idempotent=False
    """
    print("\n" + "=" * 60)
    print("TESTE 1: Envio único de leitura")
    print("=" * 60)
    
    payload = {
        'uuid': str(uuid.uuid4()),
        'sensor_id': 'TEST-SENSOR-001',
        'temperatura': 12.5
    }
    
    print(f"Enviando: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201, "Esperado status 201"
    assert response.json()['idempotent'] == False, "Esperado idempotent=False"
    print("✅ TESTE PASSOU!")
    
    return payload['uuid']


def test_envio_duplicado(uuid_original):
    """
    TESTE 2: Reenvio da mesma requisição (idempotência)
    Espera-se: 200 OK, idempotent=True
    """
    print("\n" + "=" * 60)
    print("TESTE 2: Reenvio da mesma requisição (idempotência)")
    print("=" * 60)
    
    payload = {
        'uuid': uuid_original,  # MESMO UUID!
        'sensor_id': 'TEST-SENSOR-001',
        'temperatura': 12.5
    }
    
    print(f"Reenviando UUID: {uuid_original}")
    
    response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Esperado status 200"
    assert response.json()['idempotent'] == True, "Esperado idempotent=True"
    print("✅ TESTE PASSOU! (Sistema é idempotente)")


def test_multiplos_sensores():
    """
    TESTE 3: Múltiplos sensores com mesma temperatura
    Espera-se: Aceitar todos (UUIDs diferentes)
    """
    print("\n" + "=" * 60)
    print("TESTE 3: Múltiplos sensores, mesma temperatura")
    print("=" * 60)
    
    temperatura = 15.0
    
    for i in range(3):
        payload = {
            'uuid': str(uuid.uuid4()),  # UUID DIFERENTE para cada
            'sensor_id': f'TEST-SENSOR-{i:03d}',
            'temperatura': temperatura
        }
        
        response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
        
        print(f"Sensor {i}: Status {response.status_code}")
        assert response.status_code == 201, f"Sensor {i} deveria retornar 201"
    
    print("✅ TESTE PASSOU! (Aceita múltiplos sensores)")


def test_validacao_dados():
    """
    TESTE 4: Validação de dados inválidos
    Espera-se: 400 Bad Request
    """
    print("\n" + "=" * 60)
    print("TESTE 4: Validação de dados inválidos")
    print("=" * 60)
    
    # Teste 4a: UUID inválido
    print("\n4a) UUID inválido:")
    payload = {
        'uuid': 'not-a-valid-uuid',
        'sensor_id': 'TEST-SENSOR',
        'temperatura': 20.0
    }
    response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, "Esperado 400 para UUID inválido"
    print("✅ Rejeitou UUID inválido")
    
    # Teste 4b: Temperatura fora do range
    print("\n4b) Temperatura fora do range:")
    payload = {
        'uuid': str(uuid.uuid4()),
        'sensor_id': 'TEST-SENSOR',
        'temperatura': 150.0  # Fora do range
    }
    response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, "Esperado 400 para temperatura inválida"
    print("✅ Rejeitou temperatura fora do range")
    
    # Teste 4c: Campo faltando
    print("\n4c) Campo obrigatório faltando:")
    payload = {
        'uuid': str(uuid.uuid4()),
        # sensor_id FALTANDO
        'temperatura': 20.0
    }
    response = requests.post(f"{SERVER_URL}/sensor/reading", json=payload)
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, "Esperado 400 para campo faltando"
    print("✅ Rejeitou payload incompleto")
    
    print("\n✅ TODOS OS TESTES DE VALIDAÇÃO PASSARAM!")


def test_health_check():
    """
    TESTE 5: Health check
    Espera-se: 200 OK
    """
    print("\n" + "=" * 60)
    print("TESTE 5: Health Check")
    print("=" * 60)
    
    response = requests.get(f"{SERVER_URL}/health")
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Esperado status 200"
    assert response.json()['status'] == 'healthy', "Esperado status='healthy'"
    print("✅ TESTE PASSOU!")


def test_historico():
    """
    TESTE 6: Consulta de histórico
    Espera-se: 200 OK com lista de leituras
    """
    print("\n" + "=" * 60)
    print("TESTE 6: Consulta de histórico")
    print("=" * 60)
    
    response = requests.get(f"{SERVER_URL}/sensor/history?limit=5")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total de leituras: {data['total']}")
    print(f"Retornadas: {len(data['leituras'])}")
    
    assert response.status_code == 200, "Esperado status 200"
    assert 'leituras' in data, "Esperado campo 'leituras'"
    print("✅ TESTE PASSOU!")


def test_estatisticas():
    """
    TESTE 7: Estatísticas agregadas
    Espera-se: 200 OK com stats
    """
    print("\n" + "=" * 60)
    print("TESTE 7: Estatísticas agregadas")
    print("=" * 60)
    
    response = requests.get(f"{SERVER_URL}/sensor/stats")
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Esperado status 200"
    assert 'total_leituras' in response.json(), "Esperado 'total_leituras'"
    print("✅ TESTE PASSOU!")


def main():
    """Executar todos os testes"""
    print("\n" + "🧪" * 30)
    print("INICIANDO BATERIA DE TESTES")
    print("🧪" * 30)
    
    try:
        # Verificar se servidor está rodando
        requests.get(f"{SERVER_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Servidor não está rodando!")
        print("Execute 'python server.py' primeiro.")
        return
    
    try:
        # Executar testes
        uuid_original = test_envio_unico()
        test_envio_duplicado(uuid_original)
        test_multiplos_sensores()
        test_validacao_dados()
        test_health_check()
        test_historico()
        test_estatisticas()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES PASSARAM! 🎉")
        print("=" * 60)
        print("\nO sistema está funcionando corretamente:")
        print("✅ Idempotência garantida")
        print("✅ Validação de dados funcionando")
        print("✅ Endpoints respondendo corretamente")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")


if __name__ == '__main__':
    main()
