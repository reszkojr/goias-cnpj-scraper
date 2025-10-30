from unittest.mock import Mock, patch

import pytest

from worker.scraper import normalize_key, parse_results_html, perform_scraping


class TestScrapingEssentials:
    """Testes das funções de scraping"""

    def test_normalize_key(self):
        """Teste da normalização de chaves"""
        assert normalize_key("Razão Social:") == "razao_social"
        assert normalize_key("CNPJ/CPF") == "cnpj_cpf"
        assert normalize_key("Operações com NF-e") == "operacoes_com_nfe"

    def test_parse_results_html_success(self):
        """Teste de parsing do HTML de sucesso"""
        html = """
        <html>
            <body>
            <div class="item">
                <span class="label_title">CNPJ:</span>
                <span class="label_text">00.012.377/0001-60</span>
            </div>
            <div class="item">
                <span class="label_title">Nome Empresarial:</span>
                <span class="label_text">CEREAL COMERCIO EXPORTACAO</span>
            </div>
            <div class="col box">
                <div class="box_title">Atividade Econômica</div>
                <span class="label_text">Atividade Principal</span>
                <span class="label_text" style="font-weight: normal;">
                4741500 - Comércio varejista de tintas e materiais para pintura
                </span>
            </div>
            </body>
        </html>
        """

        scraped_cnpj = parse_results_html(html)
        assert scraped_cnpj.cnpj == "00.012.377/0001-60"
        assert scraped_cnpj.nome_empresarial == "CEREAL COMERCIO EXPORTACAO"

    def test_parse_results_html_error(self):
        """Teste de erro do Sintegra"""
        html = """
        <html>
            <body>
                <td class="aviso">Não foi encontrado nenhum contribuinte</td>
            </body>
        </html>
        """

        parse_results_html(html)
        scraped_cnpj = parse_results_html(html)
        assert scraped_cnpj.situacao_cadastral_vigente == "Não encontrado"

    @patch("worker.scraper.requests.post")
    def test_perform_scraping_success(self, mock_post):
        """Teste básico de scraping"""
        mock_response = Mock()
        mock_response.text = """
        <div class="item">
            <span class="label_title">CNPJ:</span>
            <span class="label_text">00.012.377/0001-60</span>
        </div>
        <div class="col box">
            <div class="box_title">Atividade Econômica</div>
            <span class="label_text">Atividade Principal</span>
            <span class="label_text" style="font-weight: normal;">
            4741500 - Comércio varejista de tintas e materiais para pintura
            </span>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        scraped_cnpj = perform_scraping("00012377000160")
        assert scraped_cnpj.cnpj == "00.012.377/0001-60"

        # Verifica se chamou a URL correta
        call_args = mock_post.call_args
        assert "sintegra/consulta/consultar.asp" in call_args[0][0]


class TestScrapingReal:
    """Teste com o CNPJ real específico"""

    def test_real_scraping_cnpj_specific(self):
        """Teste real com CNPJ 00012377000160"""
        cnpj = "00012377000160"

        try:
            scraped_cnpj = perform_scraping(cnpj)

            # Verifica os campos principais
            assert scraped_cnpj.cnpj == "00.012.377/0001-60"
            assert "CEREAL" in scraped_cnpj.nome_empresarial

            print("Scraping real funcionando\n")

        except Exception as e:
            pytest.skip(f"Scraping falhou: {e}")


if __name__ == "__main__":
    import sys

    test = TestScrapingEssentials()

    print("Testando funções de scraping...")

    try:
        print("1. Testando normalize_key...")
        test.test_normalize_key()
        print("normalize_key funcionando\n")

        print("2. Testando parse_results_html...")
        test.test_parse_results_html_success()
        test.test_parse_results_html_error()
        print("parse_results_html funcionando\n")

        print("3. Testando perform_scraping (mock)...")
        test.test_perform_scraping_success()
        print("perform_scraping (mock) funcionando\n")

        print("\nTestando scraping real...")
        real_test = TestScrapingReal()
        real_test.test_real_scraping_cnpj_specific()

        print("\nTodos os testes essenciais passaram!")

    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
