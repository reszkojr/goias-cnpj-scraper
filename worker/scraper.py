import re
import unicodedata

import requests
from bs4 import BeautifulSoup


def parse_results_html(html_content: str) -> dict:
    """
    Recebe o HTML de resposta do Sintegra e extrai os dados
    da tabela, transformando em um dicionário.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    results = {}

    items = soup.select("div.item, div.col.box")

    for item in items:
        titulo_tag = (
            item.find("span", class_="label_title")
            or item.find("div", class_="label_title")
            or item.find("div", class_="box_title")
        )

        if titulo_tag.attrs.get("class") == ["box_title"]:
            valor_tag = item.find_all("span", class_="label_title")[:-1]
        else:
            valor_tag = item.find("span", class_="label_text")

        if titulo_tag and valor_tag:
            key = titulo_tag.get_text(strip=True).replace(":", "").strip().lower()

            key = unicodedata.normalize("NFKD", key)
            key = "".join(ch for ch in key if not unicodedata.combining(ch))

            key = re.sub(r"[^a-z0-9_]", "_", key.replace("-", ""))
            key = re.sub(r"_+", "_", key).strip("_")

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

    return results


def perform_scraping(cnpj: str) -> dict:
    """Função que faz o scraping no site do Sintegra-GO."""
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
        data["cnpj_consultado"] = clean_cnpj
        data["cnpj_formatado"] = formatted_cnpj

        return data

    except requests.exceptions.HTTPError as e:
        raise Exception(f"Erro HTTP ao consultar o Sintegra: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro de rede ao consultar o Sintegra: {e}")
    except Exception as e:
        raise Exception(f"Erro no processamento do scraping: {e}")
