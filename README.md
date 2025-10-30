# CNPJ Scraper API - Sintegra Goiás

## Visão Geral

API REST para consultas assíncronas de CNPJ do estado de Goiás via Sintegra, com processamento em filas visando performance e escalabilidade.

## Arquitetura do Sistema

### Componentes Principais

**API FastAPI** (`app/main.py`): Interface REST responsável por receber requisições de consulta e fornecer resultados
**Worker de Scraping** (`worker/consumer.py && worker/scraper.py`): Serviço dedicado que executa o web scraping do portal Sintegra
**RabbitMQ**: Sistema de filas para processamento assíncrono das tarefas de scraping
**Redis**: Cache para armazenamento temporário dos resultados e controle de estado das tarefas

### Fluxo de Processamento

1. Cliente envia requisição POST contendo o CNPJ desejado para o endpoint `/scrape`
2. API gera um ID único para a tarefa e a armazena no Redis com status "pending"
3. Mensagem é enviada para a fila RabbitMQ contendo o ID da tarefa e CNPJ
4. Worker consome a mensagem da fila e executa o scraping
5. Resultado é armazenado no Redis e status atualizado para "completed" ou "failed"
6. Cliente consulta o resultado através do endpoint `/results/{task_id}`

## Funcionalidades

### API Endpoints

**GET /** - Verificação de status da API

**POST /scrape** - Criação de nova tarefa de scraping

**GET /results/{task_id}** - Consulta de resultado de tarefa

**GET /docs** - Documentação Swagger da API em OpenAPI

### Dados Extraídos

- CNPJ formatado
- Inscrição Estadual
- Nome Empresarial
- Endereço do estabelecimento
- Atividades econômicas
- Situação cadastral
- Dados de cadastramento
- Status de operações com NF-e

## Tecnologias Utilizadas

### Backend
- **Python 3.11**
- **FastAPI** - Framework web
- **BeautifulSoup4** - Parser HTML para extração de dados
- **Requests** - Cliente HTTP para requisições ao Sintegra

### Infraestrutura
- **Docker & Docker Compose** - Containerização
- **RabbitMQ** - Message broker para filas assíncronas
- **Redis** - Armazenamento em memória para cache e sessões

### Desenvolvimento
- **Pytest** - Framework de testes
- **Python Ruff** - Formatação & linter rápidos de código
- **PEP8** - Padrões de código Python

## Instalação e Execução

### Pré-requisitos

- Docker
- Docker Compose 
- Git

### Instruções de Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/reszkojr/goias-cnpj-scraper.git
cd goias-cnpj-scraper
```

2. **Inicie os serviços com Docker Compose**
```bash
docker-compose up --build
```

> Para melhor performance, é possível escalar o número de workers:
```bash
docker-compose up --build --scale worker=3
```

3. **Verificar se os serviços estão funcionando**
```bash
curl http://localhost:8000/
```

### Configuração de Ambiente

O sistema utiliza as seguintes variáveis de ambiente (disponíveis no `.env.example`):

```bash
RABBITMQ_HOST=rabbitmq
REDIS_HOST=redis
RABBITMQ_DEFAULT_USER=user
RABBITMQ_DEFAULT_PASS=password
```

## Uso da API

Existem três maneiras de consumir a API. Uma é utilizando o `curl`, outra com o Postman, e outra com o Bruno (meu preferido).

Caso você queira consumi-la utilizando o Bruno ou o Postman, ambas as collections estão presentes para importação na raiz do projeto. 

**Importante**: Para usar as collections do Postman ou Bruno, você precisa criar um **environment** com uma variável chamada `API_URL` que deve conter a URL da API, por exemplo: `http://localhost:8000`

Caso opte por utilizar o `curl`, continue lendo.

### Exemplo de Consulta

**Criar nova tarefa de scraping:**
```bash
curl -X POST "http://localhost:8000/scrape" \
     -H "Content-Type: application/json" \
     -d '{"cnpj": "00012377000160"}'
```

**Resposta:**
```json
{
  "message": "Webscraping iniciado",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Consultar resultado:**
```bash
curl "http://localhost:8000/results/550e8400-e29b-41d4-a716-446655440000"
```

> Recomendo a utilização do json_pp no final do comando do curl com um pipe para que a saída em json fique formatada.

**Resposta:**
```json
{
  "task_id": "8fae8c89-a0a1-4702-bd55-7dd8aa6b080f",
  "status": "completed",
  "result": {
    "cnpj": "00.012.377/0001-60",
    "atividade_economica": {
      "atividade_principal": [
        {
          "1041400": "Fabricação de óleos vegetais em bruto, exceto óleo de milho"
        }
      ],
      "atividade_secundaria": [
        {
          "4930202": "Transporte rodoviário de carga, exceto produtos perigosos e mudanças, intermunicipal, interestadual e internacional"
        },
        {
          "4683400": "Comércio atacadista de defensivos agrícolas, adubos, fertilizantes e corretivos do solo"
        },
        ...
      ]
    },
    "inscricao_estadual": "10.107.310-0",
    "cadastro_atualizado_em": "29/09/2025 16:12:41",
    "nome_empresarial": "CEREAL COMERCIO EXPORTACAO E REPRESENTACAO AGROPECUARIA SA",
    "contribuinte": "Sim",
    "nome_da_propriedade": "FAZ RIO VERDINHO BARRA GRANDE",
    "endereco_estabelecimento": "RODOVIA BR-060, no SN, KM 381, SETOR INDUSTRIAL - RIO VERDE GO, CEP: 75.905-025",
    "unidade_auxiliar": "UNIDADE PRODUTIVA",
    "condicao_de_uso": "",
    "data_final_de_contrato": "",
    "regime_de_apuracao": "Normal",
    "situacao_cadastral_vigente": "Ativo - HABILITADO",
    "data_desta_situacao_cadastral": "30/01/2009",
    "data_de_cadastramento": "10/12/1981",
    "operacoes_com_nfe": "Habilitado",
    "data_da_consulta": "30/10/2025 11:47:48"
  },
  "created_at": 1761835667.7155886
}
```

## Estrutura do Projeto

```bash
../goias-cnpj-scraper
├── app  
│   ├── Dockerfile                # Imagem Docker para o serviço da API
│   ├── main.py                   # Código da API em FastAPI
│   └── models.py                 # Modelos da API 
├── worker  
│   ├── Dockerfile                # Imagem Docker para o worker de scraping 
│   ├── consumer.py               # Consumer/worker de tarefas do RabbitMQ 
│   ├── models.py                 # Modelos do worker 
│   └── scraper.py                # Lógica de scraping do Sintegra 
├── tests  
│   ├── test_api_simple.py        # Testes dos endpoints da API 
│   └── test_scraping.py          # Testes das funcionalidades de scraping 
├── README.md                     # Documentação do projeto
├── compose.yml                   # Docker compose dos serviços
├── pyproject.toml                # Configuração do projeto Python
├── pytest.ini                    # Configuração do Pytest 
├── requirements-test.txt         # Dependências para testes 
├── requirements.txt              # Dependências principais do projeto 
├── sintegra-scraper-api.bruno_collection.json   # Collection para testes no Bruno API Client 
└── sintegra-scraper-api.postman_collection.json # Collection para testes no Postman 

```

## Testes Automatizados

### Execução dos Testes

**Instalar dependências de teste:**
```bash
pip install -r requirements-test.txt
```

**Executar testes:**
```bash
pytest -v tests/
```

### Cobertura de Testes

- **Testes de API**: verificação dos endpoints e fluxo de dados
- **Testes de Scraping**: validação das funções de extração e parsing

## Monitoramento e Logs

### Logs da Aplicação

```bash
docker-compose logs -f
```

## Escalabilidade

### Múltiplos Workers

O sistema foi projetado para ser escalável. Você pode executar múltiplos workers para processar mais tarefas simultaneamente:

```bash
# Executar com 3 workers
docker-compose up --scale worker=3

# Executar com 5 workers  
docker-compose up --scale worker=5
```

Cada worker processará tarefas independentemente da fila RabbitMQ, permitindo maior throughput de processamento de CNPJs.

### Monitoramento de Performance

Para monitorar a fila e workers:

```bash
# Acessar o painel do RabbitMQ
http://localhost:15672
# Usuário: user | Senha: password
```

## Tratamento de Erros

### Status de Tarefas

- **pending**: Tarefa criada, aguardando processamento
- **processing**: Worker está executando o scraping
- **completed**: Scraping finalizado com sucesso
- **failed**: Erro durante o processamento

## Qualidade do Código

### Padrões Seguidos

- **PEP8**: estilo de código Python padrão
- **Type Hints**: tipagem estática para melhor documentação
- **Docstrings**: documentação de funções e classes
- **Separação de Responsabilidades**: módulos especializados
- **Tratamento de Exceções**: captura e logging adequados

### Ferramentas de Qualidade

- **Ruff**: Linting, formatação e verificação de estilo
