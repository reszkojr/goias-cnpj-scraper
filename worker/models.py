from typing import Dict, List, Optional

from pydantic import BaseModel


class AtividadeEconomica(BaseModel):
    atividade_principal: List[Dict[str, str]]
    atividade_secundaria: List[Dict[str, str]]


class ScrapedCNPJ(BaseModel):
    cnpj: str
    atividade_economica: AtividadeEconomica
    inscricao_estadual: Optional[str] = None
    cadastro_atualizado_em: Optional[str] = None
    nome_empresarial: Optional[str] = None
    contribuinte: Optional[str] = None
    nome_da_propriedade: Optional[str] = None
    endereco_estabelecimento: Optional[str] = None
    unidade_auxiliar: Optional[str] = None
    condicao_de_uso: Optional[str] = None
    data_final_de_contrato: Optional[str] = None
    regime_de_apuracao: Optional[str] = None
    situacao_cadastral_vigente: Optional[str] = None
    data_desta_situacao_cadastral: Optional[str] = None
    data_de_cadastramento: Optional[str] = None
    operacoes_com_nfe: Optional[str] = None
    data_da_consulta: Optional[str] = None
