import re
import unicodedata
from collections import defaultdict

import requests
from bs4 import BeautifulSoup, Tag

from worker.models import AtividadeEconomica, ScrapedCNPJ

NORMALIZE_KEY_EXCEPTIONS = {
    "operacoes com nf-e": "operacoes_com_nfe",
}


def normalize_key(text: str) -> str:
    """
    Normaliza uma string para ser usada como chave de dicionário.

    Args:
        text: Texto a ser normalizado

    Returns:
        String normalizada em snake_case, sem acentos e caracteres especiais
    """

    if not text:
        return ""

    # Converter para lowercase e remover dois pontos
    key = text.lower().replace(":", "").strip()

    # Normalizar acentos (NFD - Normalization Form Decomposed)
    key = unicodedata.normalize("NFKD", key)

    # Remover caracteres de combinação (acentos)
    key = "".join(ch for ch in key if not unicodedata.combining(ch))

    # Checar se a chave se encaixa em alguma das exceções
    if key in NORMALIZE_KEY_EXCEPTIONS:
        return NORMALIZE_KEY_EXCEPTIONS[key]

    # Substituir caracteres especiais por underscore
    key = re.sub(r"[^a-z0-9_\-]", "_", key)

    # Converter hífens para underscores
    key = key.replace("-", "_")

    # Substituir múltiplos underscores consecutivos por um único underscore
    key = re.sub(r"_+", "_", key)

    # Remover underscores do início e fim
    key = key.strip("_")

    return key


def parse_atividade_economica(
    atividadeEconomicaElement: Tag,
) -> AtividadeEconomica:
    """
    Recebe o elemento HTML que contém as Atividades Econômicas
    e extrai as informações dos CNAE's para cada tipo de atividade

    Args:
        atividadeEconomicaElement: Elemento HTML contendo as Atividades Econômicas
    Returns:
        Dicionário com os tipos de atividades como chaves e listas de CNAE's como valores
    """
    labelTexts = atividadeEconomicaElement.find_all("span", class_="label_text")
    atividadesEconomicas = defaultdict(list)
    tipo_atividade = None
    for element in labelTexts:
        conteudoElemento = element.get_text(strip=True)
        stylesElemento = element.get_attribute_list("style")

        if len(stylesElemento) == 0 or stylesElemento[0] is None:
            tipo_atividade = normalize_key(conteudoElemento)
            continue

        cnae = conteudoElemento
        codigo_cnae, descricao_cane = map(str.strip, cnae.split(" - ", 1))
        atividadesEconomicas[tipo_atividade].append({codigo_cnae: descricao_cane})

    return AtividadeEconomica.model_validate(atividadesEconomicas)


def parse_results_html(html_content: str) -> ScrapedCNPJ:
    """
    Recebe o HTML de resposta do Sintegra e extrai os dados
    da tabela, transformando em um dicionário.
    Args:
        html_content: HTML retornado pela API do Sintegra
    Returns:
        Dicionário bonitinho com os dados extraídos do HTML
    """
    soup = BeautifulSoup(html_content, "html.parser")
    results = {}

    if "Não foi encontrado nenhum contribuinte" in html_content:
        return ScrapedCNPJ(
            cnpj="",
            atividade_economica=AtividadeEconomica(
                atividade_principal=[], atividade_secundaria=[]
            ),
            situacao_cadastral_vigente="Não encontrado",
        )

    items = soup.select("div.item, div.col.box")

    for item in items:
        titulo_tag = (
            item.find("span", class_="label_title")
            or item.find("div", class_="label_title")
            or item.find("div", class_="box_title")
        )

        if titulo_tag.attrs.get("class") == ["box_title"]:
            atividades_economicas = parse_atividade_economica(item)
            key = normalize_key(titulo_tag.get_text(strip=True))
            results[key] = atividades_economicas
            continue
        else:
            valor_tag = item.find("span", class_="label_text")

        if titulo_tag and valor_tag:
            key = normalize_key(titulo_tag.get_text(strip=True))

            value = valor_tag.get_text(strip=True)
            value = unicodedata.normalize("NFKD", value)
            value = re.sub(r"\s+", " ", value)
            value = re.sub(r"---", "", value)
            value = "".join(ch for ch in value if not unicodedata.combining(ch))

            results[key] = value

    if not results:
        error_tag = soup.find("td", class_="aviso")
        if error_tag:
            error_msg = error_tag.get_text(strip=True)
            raise Exception(f"Erro retornado pelo Sintegra: {error_msg}")
        raise Exception("Não foi possível parsear o HTML de resultado.")

    return ScrapedCNPJ.model_validate(results)


def perform_scraping(cnpj: str) -> ScrapedCNPJ:
    """
    Função que faz o scraping no site do Sintegra-GO.

    Args:
        cnpj: CNPJ a ser consultado
    Returns:
        Dicionário bonitinho com os dados extraídos do site
    """
    clean_cnpj = "".join(filter(str.isdigit, cnpj))
    formatted_cnpj = f"{clean_cnpj[:2]}.{clean_cnpj[2:5]}.{clean_cnpj[5:8]}/{clean_cnpj[8:12]}-{clean_cnpj[12:14]}"

    url = "https://appasp.sefaz.go.gov.br/sintegra/consulta/consultar.asp"

    payload = {
        "rTipoDoc": "2",
        "tDoc": formatted_cnpj,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
        "Referer": "https://appasp.sefaz.go.gov.br/sintegra/consulta/default.html",
    }

    print(f"SCRAPER - (CNPJ: {clean_cnpj}) Consultando Sintegra-GO...")

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"SCRAPER - (CNPJ: {clean_cnpj}) Resposta recebida. Parseando HTML...")

        data = parse_results_html(response.text)

        return data

    except requests.exceptions.HTTPError as e:
        raise Exception(f"Erro HTTP ao consultar o Sintegra: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro de rede ao consultar o Sintegra: {e}")
    except Exception as e:
        raise Exception(f"Erro no processamento do scraping: {e}")
