#!/bin/bash
# Script para coletar logs de acesso dos sites via SSH

# Usar diretório relativo baseado na localização do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Carregar configuração dos sites
if [ ! -f "configs/sites.conf" ]; then
    echo "❌ Arquivo configs/sites.conf não encontrado!" >> logs/web_collection.log
    echo "💡 Copie configs/sites.conf.example para configs/sites.conf e configure" >> logs/web_collection.log
    exit 1
fi

source configs/sites.conf

echo "$(date): Starting log collection..." >> logs/web_collection.log

# Arquivo combinado de logs
> logs/web_access.log

# Coletar logs de diferentes sites usando configuração externa
# Coletar logs de cada site (últimas 500 linhas de cada)
for site_info in "${SITES_LOGS[@]}"; do
    site_name="${site_info%%:*}"
    log_path="${site_info##*:}"
    echo "Collecting logs from $site_name ($log_path)..."

    # Tentar coletar log do site específico
    ssh "$SSH_SERVER" "tail -500 '$log_path' 2>/dev/null" >> logs/web_access.log 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ $site_name logs collected" >> logs/web_collection.log
    else
        echo "❌ Failed to collect $site_name logs" >> logs/web_collection.log
    fi
done

# Se não conseguiu coletar nenhum log específico, tentar log principal
if [ ! -s logs/web_access.log ]; then
    echo "Trying main access log..."
    ssh "$SSH_SERVER" "tail -1000 /home/*/access-logs/*.log 2>/dev/null | head -1000" >> logs/web_access.log 2>/dev/null

    if [ -s logs/web_access.log ]; then
        echo "✅ Main access logs collected" >> logs/web_collection.log
    else
        echo "❌ No logs could be collected" >> logs/web_collection.log
    fi
fi

# Processar métricas se temos logs
if [ -s logs/web_access.log ]; then
    echo "Processing web analytics..."
    source venv/bin/activate
    python scripts/web_analytics.py
    echo "$(date): Web analytics processed successfully" >> logs/web_collection.log
else
    echo "$(date): No logs to process" >> logs/web_collection.log
fi
