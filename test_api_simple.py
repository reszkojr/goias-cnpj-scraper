import json
import time

import pytest
import requests


class TestAPISimple:
    """Testes básicos da API"""

    BASE_URL = "http://localhost:8000"
    TEST_CNPJ = "00012377000160"

    def test_api_health(self):
        """Teste se a API está funcionando"""
        try:
            response = requests.get(f"{self.BASE_URL}/")
            assert response.status_code == 200
            assert response.json() == {"message": "API is running"}
        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")

    @pytest.mark.filterwarnings("ignore:Expected None")
    def test_create_scrape_task(self) -> str:
        """Teste de criação de tarefa de scraping"""
        try:
            payload = {"cnpj": self.TEST_CNPJ}
            response = requests.post(f"{self.BASE_URL}/scrape", json=payload)

            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
            assert "message" in data
            assert data["message"] == "Tarefa de scraping criada com sucesso"

            return data["task_id"]
        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")

    def test_get_task_result_pending(self):
        """Teste de busca de resultado (status pending)"""
        try:
            # Cria a tarefa
            task_id = self.test_create_scrape_task()

            # Busca o resultado imediatamente (deve estar pending)
            response = requests.get(f"{self.BASE_URL}/results/{task_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["task_id"] == task_id
            assert data["status"] in ["pending", "processing", "completed"]

        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")

    def test_scrape_specific_cnpj_complete_flow(self):
        """
        Teste completo: criar tarefa, aguardar processamento e verificar resultado
        para o CNPJ específico 00012377000160
        """
        try:
            # 1. Cria a tarefa
            payload = {"cnpj": self.TEST_CNPJ}
            response = requests.post(f"{self.BASE_URL}/scrape", json=payload)
            assert response.status_code == 202

            task_id = response.json()["task_id"]
            print(f"Tarefa criada: {task_id}")

            # 2. Aguarda o processamento
            max_wait = 5
            wait_time = 0

            while wait_time < max_wait:
                response = requests.get(f"{self.BASE_URL}/results/{task_id}")
                assert response.status_code == 200

                data = response.json()
                status = data["status"]

                print(f"Status após {wait_time}s: {status}")

                if status == "completed":
                    break
                elif status == "failed":
                    pytest.fail(
                        f"Tarefa falhou: {data.get('data', {}).get('error', 'Erro desconhecido')}"
                    )

                time.sleep(2)
                wait_time += 2

            # 3. Verifica se completou
            assert status == "completed", (
                f"Tarefa não completou em {max_wait}s. Status final: {status}"
            )

            # 4. Verifica a estrutura do resultado
            result = data["result"]

            # Campos obrigatórios
            expected_fields = [
                "cnpj",
                "inscricao_estadual",
                "nome_empresarial",
                "endereco_estabelecimento",
                "atividade_economica",
                "situacao_cadastral_vigente",
            ]

            for field in expected_fields:
                assert field in result, (
                    f"Campo obrigatório '{field}' não encontrado no resultado"
                )

            # 5. Verifica os dados específicos esperados
            assert result["cnpj"] == "00.012.377/0001-60"
            assert (
                result["nome_empresarial"]
                == "CEREAL COMERCIO EXPORTACAO E REPRESENTACAO AGROPECUARIA SA"
            )
            assert result["inscricao_estadual"] == "10.107.310-0"

            # 6. Verifica as atividades econômicas
            atividades = result["atividade_economica"]
            assert "atividade_principal" in atividades
            assert "atividade_secundaria" in atividades

            # Verifica a atividade principal
            atividade_principal = atividades["atividade_principal"]
            assert len(atividade_principal) > 0

            # Verifica se a chave "1041400" existe
            # Verifica se a chave "1041400" existe em alguma das atividades principais
            assert any("1041400" in atividade for atividade in atividade_principal), (
                "Código de atividade principal '1041400' não encontrado"
            )

            # Verifica as atividades secundárias
            atividade_secundaria = atividades["atividade_secundaria"]
            assert len(atividade_secundaria) > 0

            # Validação de key-value igual para atividades secundárias
            expected_secundarias = ["4930202", "4683400", "4692300"]
            codigos_atividades_secundarias = []

            for atividade in atividade_secundaria:
                for codigo, _ in atividade.items():
                    codigos_atividades_secundarias.append(codigo)

            assert all(
                codigo in codigos_atividades_secundarias
                for codigo in expected_secundarias
            )

            print("Teste completo passou! Resultado:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")

    def test_invalid_cnpj(self):
        """Teste com CNPJ inválido"""
        try:
            payload = {"cnpj": "123"}
            response = requests.post(f"{self.BASE_URL}/scrape", json=payload)

            # Pode retornar 422 (validation error) ou 202 (processado mas vai falhar)
            assert response.status_code in [202, 422]

        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")

    def test_nonexistent_task(self):
        """Teste com task_id inexistente"""
        try:
            fake_task_id = "00000000-0000-0000-0000-000000000000"
            response = requests.get(f"{self.BASE_URL}/results/{fake_task_id}")
            assert response.status_code == 404

        except requests.exceptions.ConnectionError:
            pytest.skip("API não está rodando")


if __name__ == "__main__":
    test = TestAPISimple()

    print("🚀 Testando API...")

    try:
        print("1. Testando health da api...")
        test.test_api_health()
        print("API está funcionando")

        print("2. Testando criação de tarefa...")
        task_id = test.test_create_scrape_task()
        print(f"Tarefa criada: {task_id}")

        print("3. Testando fluxo completo...")
        test.test_scrape_specific_cnpj_complete_flow()
        print("Fluxo completo funcionando")

    except Exception as e:
        print(f"❌ Erro: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")
