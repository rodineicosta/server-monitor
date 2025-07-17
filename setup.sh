#!/bin/bash
# Script de setup inicial para o sistema de monitoramento

echo "🚀 SETUP INICIAL - SISTEMA DE MONITORAMENTO"
echo "==========================================="

# Usar diretório relativo baseado na localização do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
cd "$PROJECT_DIR"

# Verificar se os binários necessários existem
echo "🔍 Verificando binários necessários..."
missing_binaries=()
if [ ! -f "prometheus" ]; then missing_binaries+=("prometheus"); fi
if [ ! -f "promtool" ]; then missing_binaries+=("promtool"); fi
if [ ! -f "blackbox_exporter" ]; then missing_binaries+=("blackbox_exporter"); fi
if [ ! -f "pushgateway" ]; then missing_binaries+=("pushgateway"); fi

if [ ${#missing_binaries[@]} -gt 0 ]; then
    echo ""
    echo "❌ Binários ausentes: ${missing_binaries[*]}"
    echo ""
    echo "📥 DOWNLOAD NECESSÁRIO:"
    echo "======================="
    echo ""
    echo "1️⃣ Prometheus & Promtool:"
    echo "   https://github.com/prometheus/prometheus/releases/latest"
    echo ""
    echo "2️⃣ Blackbox Exporter:"
    echo "   https://github.com/prometheus/blackbox_exporter/releases/latest"
    echo ""
    echo "3️⃣ Pushgateway:"
    echo "   https://github.com/prometheus/pushgateway/releases/latest"
    echo ""
    echo "📋 INSTRUÇÕES:"
    echo "- Baixe os arquivos apropriados para sua plataforma (macOS/Linux/Windows)"
    echo "- Extraia os binários para a raiz deste diretório: $PROJECT_DIR"
    echo "- Execute este script novamente após o download"
    echo ""
    exit 1
else
    echo "✅ Todos os binários encontrados!"
fi
echo ""

# 1. Verificar se arquivo de configuração existe
if [ ! -f "configs/sites.conf" ]; then
    echo "📋 Criando arquivo de configuração..."
    cp configs/sites.conf.example configs/sites.conf
    echo "✅ Arquivo configs/sites.conf criado"
    echo ""
    echo "⚠️  IMPORTANTE: Configure os sites em configs/sites.conf antes de prosseguir!"
    echo "   Edite o arquivo e substitua os exemplos pelos seus sites reais."
    echo ""
    read -p "Pressione ENTER após configurar os sites..."
fi

# 2. Gerar configuração do Prometheus
echo "⚙️  Gerando configuração do Prometheus..."
bash scripts/generate_prometheus_config.sh

# 3. Verificar ambiente virtual Python
if [ ! -d "venv" ]; then
    echo "🐍 Criando ambiente virtual Python..."
    python3 -m venv venv
    source venv/bin/activate
    pip install prometheus-client requests beautifulsoup4
    echo "✅ Ambiente virtual criado e configurado"
else
    echo "✅ Ambiente virtual já existe"
fi

# 4. Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p logs services data

# 5. Verificar executáveis
echo "🔍 Verificando executáveis..."
if [ ! -f "prometheus" ]; then
    echo "❌ Executável 'prometheus' não encontrado!"
    echo "   Baixe de: https://prometheus.io/download/"
fi

if [ ! -f "blackbox_exporter" ]; then
    echo "❌ Executável 'blackbox_exporter' não encontrado!"
    echo "   Baixe de: https://prometheus.io/download/"
fi

if [ ! -f "pushgateway" ]; then
    echo "❌ Executável 'pushgateway' não encontrado!"
    echo "   Baixe de: https://prometheus.io/download/"
fi

# 6. Teste de configuração
echo "🧪 Testando configuração..."
source configs/sites.conf

if [ ${#SITES_HTTP[@]} -gt 0 ]; then
    echo "✅ ${#SITES_HTTP[@]} sites HTTP configurados"
else
    echo "⚠️  Nenhum site HTTP configurado"
fi

if [ ${#SITES_LOGS[@]} -gt 0 ]; then
    echo "✅ ${#SITES_LOGS[@]} sites de log configurados"
else
    echo "⚠️  Nenhum site de log configurado"
fi

echo ""
echo "🎉 SETUP CONCLUÍDO!"
echo "=================="
echo ""
echo "Próximos passos:"
echo "1. ./monitor.sh start     - Iniciar sistema"
echo "2. ./monitor.sh status    - Verificar status"
echo "3. ./monitor.sh test      - Testar funcionamento"
echo ""
echo "📊 Dashboards disponíveis em: ./dashboards/"
echo "📋 Logs centralizados em: ./logs/"
echo "⚙️  Configurações em: ./configs/"
