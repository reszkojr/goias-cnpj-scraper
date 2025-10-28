#!/bin/bash

pip install -r requirements-test.txt

echo "Rodando testes da API..."
python test_api_simple.py

echo "Rodando testes de scraping..."
python test_scraping.py

echo "Testes concluídos."
