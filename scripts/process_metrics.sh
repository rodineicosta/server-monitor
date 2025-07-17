#!/bin/bash
# Script para coletar métricas do servidor e processar com Python

# Usar diretório relativo baseado na localização do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Ativar ambiente virtual e executar o script Python
source venv/bin/activate
python scripts/parse_metrics.py

# Log da execução
echo "$(date): Metrics processed and sent to Prometheus" >> logs/metrics_processing.log
