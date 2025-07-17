#!/bin/bash
# Script Mestre para Gerenciar Sistema de Monitoramento
# Autor: Sistema Híbrido de Monitoramento
# Data: 02/07/2025

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Função para verificar se um serviço está rodando
check_service() {
    local service_name="$1"
    local port="$2"

    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
        log_success "$service_name está rodando (porta $port)"
        return 0
    else
        log_error "$service_name não está rodando (porta $port)"
        return 1
    fi
}

# Função para iniciar um serviço
start_service() {
    local service_name="$1"
    local command="$2"
    local port="$3"
    local pidfile="$4"

    if check_service "$service_name" "$port"; then
        log_warning "$service_name já está rodando"
        return 0
    fi

    log_info "Iniciando $service_name..."
    eval "$command" &
    local pid=$!
    echo $pid > "$pidfile"
    sleep 3

    if check_service "$service_name" "$port"; then
        log_success "$service_name iniciado com sucesso (PID: $pid)"
        return 0
    else
        log_error "Falha ao iniciar $service_name"
        return 1
    fi
}

# Função para parar um serviço
stop_service() {
    local service_name="$1"
    local pidfile="$2"

    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            log_info "Parando $service_name (PID: $pid)..."
            kill $pid
            rm -f "$pidfile"
            log_success "$service_name parado"
        else
            log_warning "$service_name não estava rodando (PID inválido)"
            rm -f "$pidfile"
        fi
    else
        # Tentar parar por nome do processo
        pkill -f "$service_name" 2>/dev/null
        log_info "Tentativa de parar $service_name por nome do processo"
    fi
}

case "$1" in
    start)
        log_info "🚀 INICIANDO SISTEMA DE MONITORAMENTO"
        echo "======================================"

        # Gerar configuração do Prometheus se necessário
        if [ ! -f "configs/sites.conf" ]; then
            log_warning "Arquivo configs/sites.conf não encontrado!"
            log_info "Copiando exemplo... Configure antes de usar!"
            cp configs/sites.conf.example configs/sites.conf
        fi

        # Regenerar prometheus.yml com sites atualizados
        log_info "Atualizando configuração do Prometheus..."
        bash scripts/generate_prometheus_config.sh

        # 1. Pushgateway
        start_service "Pushgateway" "nohup ./pushgateway > logs/pushgateway.log 2>&1" "9091" "services/pushgateway.pid"

        # 2. Blackbox Exporter
        start_service "Blackbox Exporter" "nohup ./blackbox_exporter --config.file=configs/blackbox.yml > logs/blackbox.log 2>&1" "9115" "services/blackbox.pid"

        # 3. Prometheus
        start_service "Prometheus" "nohup ./prometheus --config.file=configs/prometheus.yml --storage.tsdb.path=./data > logs/prometheus.log 2>&1" "9090" "services/prometheus.pid"

        # 4. Monitor de Bots em Tempo Real
        log_info "Iniciando Monitor de Bots em Tempo Real..."
        cd scripts
        source ../venv/bin/activate
        nohup python3 realtime_bot_monitor.py --continuous 120 > ../logs/realtime_continuous.log 2>&1 &
        bot_pid=$!
        cd ..
        echo $bot_pid > services/realtime_monitor.pid
        log_success "Monitor de Bots iniciado"
        log_success "Monitor de Bots iniciado"

        echo ""
        log_success "🎉 SISTEMA DE MONITORAMENTO INICIADO!"
        echo "======================================"
        log_info "Prometheus:      http://localhost:9090"
        log_info "Pushgateway:     http://localhost:9091"
        log_info "Blackbox:        http://localhost:9115"
        log_info "Dashboards:      ./dashboards/"
        ;;

    stop)
        log_info "🛑 PARANDO SISTEMA DE MONITORAMENTO"
        echo "======================================"

        stop_service "Prometheus" "services/prometheus.pid"
        stop_service "Blackbox Exporter" "services/blackbox.pid"
        stop_service "Pushgateway" "services/pushgateway.pid"
        stop_service "Monitor de Bots" "services/realtime_monitor.pid"

        log_success "Sistema de monitoramento parado"
        ;;

    restart)
        log_info "🔄 REINICIANDO SISTEMA DE MONITORAMENTO"
        echo "========================================"

        $0 stop
        sleep 5
        $0 start
        ;;

    status)
        log_info "📊 STATUS DO SISTEMA DE MONITORAMENTO"
        echo "======================================"

        check_service "Prometheus" "9090"
        check_service "Pushgateway" "9091"
        check_service "Blackbox Exporter" "9115"

        # Verificar monitor de bots
        if [ -f "services/realtime_monitor.pid" ]; then
            local pid=$(cat "services/realtime_monitor.pid")
            if ps -p $pid > /dev/null 2>&1; then
                log_success "Monitor de Bots está rodando (PID: $pid)"
            else
                log_error "Monitor de Bots não está rodando (PID inválido)"
            fi
        else
            log_error "Monitor de Bots não está rodando"
        fi

        echo ""
        log_info "📈 MÉTRICAS ATIVAS:"
        curl -s http://localhost:9091/metrics | grep -c "^[a-zA-Z]" 2>/dev/null && echo " métricas no Pushgateway" || echo "Pushgateway inacessível"

        echo ""
        log_info "🎯 DASHBOARDS DISPONÍVEIS:"
        ls -1 dashboards/*.json | sed 's/dashboards\//  • /'
        ;;

    logs)
        log_info "📋 LOGS DO SISTEMA"
        echo "=================="

        echo "Escolha qual log visualizar:"
        echo "1) Prometheus"
        echo "2) Blackbox Exporter"
        echo "3) Pushgateway"
        echo "4) Monitor de Bots (Tempo Real)"
        echo "5) Monitor Híbrido"
        echo "6) Todos os logs recentes"

        read -p "Opção (1-6): " choice

        case $choice in
            1) tail -20 logs/prometheus.log ;;
            2) tail -20 logs/blackbox.log ;;
            3) tail -20 logs/pushgateway.log ;;
            4) tail -20 logs/realtime_continuous.log ;;
            5) tail -20 logs/hybrid_security.log ;;
            6)
                log_info "=== PROMETHEUS ==="
                tail -5 logs/prometheus.log
                log_info "=== BLACKBOX ==="
                tail -5 logs/blackbox.log
                log_info "=== PUSHGATEWAY ==="
                tail -5 logs/pushgateway.log
                log_info "=== MONITOR DE BOTS ==="
                tail -5 logs/realtime_continuous.log
                ;;
            *) log_error "Opção inválida" ;;
        esac
        ;;

    test)
        log_info "🧪 TESTANDO SISTEMA COMPLETO"
        echo "============================"

        # Testar conectividade dos serviços
        log_info "Testando conectividade dos serviços..."
        check_service "Prometheus" "9090"
        check_service "Pushgateway" "9091"
        check_service "Blackbox Exporter" "9115"

        # Testar algumas métricas
        log_info "Testando métricas..."
        metrics_count=$(curl -s http://localhost:9091/metrics | grep -c "^[a-zA-Z]" 2>/dev/null)
        if [ $metrics_count -gt 0 ]; then
            log_success "$metrics_count métricas ativas no Pushgateway"
        else
            log_error "Nenhuma métrica encontrada"
        fi

        # Testar um site
        if [ ! -f "configs/sites.conf" ]; then
            echo "❌ Arquivo configs/sites.conf não encontrado!"
            echo "💡 Copie configs/sites.conf.example para configs/sites.conf e configure"
            exit 1
        fi

        source configs/sites.conf
        TARGET_URL="${SITES_HTTP[0]}"
        if [ -z "$TARGET_URL" ]; then
            log_error "Nenhum site configurado para teste"
            exit 1
        fi
        
        log_info "Testando probe de um site..."
        if curl -s "http://localhost:9115/probe?target=${TARGET_URL}&module=http_2xx" | grep -q "probe_success 1"; then
            log_success "Probe do site funcionando"
        else
            log_error "Problema com probe do site"
        fi

        # Executar análise híbrida
        log_info "Executando análise híbrida..."
        cd scripts && source ../venv/bin/activate && python3 hybrid_security_monitor.py > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            log_success "Análise híbrida executada com sucesso"
        else
            log_error "Problema na análise híbrida"
        fi
        cd ..
        ;;

    uninstall-autostart)
        log_info "🗑️  REMOVENDO INÍCIO AUTOMÁTICO"
        echo "================================="

        # Verificar se existe
        if [ -f ~/Library/LaunchAgents/com.monitoring.autostart.plist ]; then
            # Descarregar serviço
            launchctl unload ~/Library/LaunchAgents/com.monitoring.autostart.plist 2>/dev/null
            log_success "Serviço descarregado"

            # Remover arquivos
            rm ~/Library/LaunchAgents/com.monitoring.autostart.plist
            rm ~/Library/LaunchAgents/monitoring_autostart.sh 2>/dev/null
            log_success "Arquivos de autostart removidos"

            log_success "Início automático DESABILITADO!"
            log_info "O sistema não será mais iniciado automaticamente"
        else
            log_warning "Início automático não estava configurado"
        fi
        ;;

    install-autostart)
        log_info "🔧 CONFIGURANDO INÍCIO AUTOMÁTICO"
        echo "=================================="

        # Criar script de início automático
        cat > /tmp/monitoring_autostart.sh << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
sleep 30  # Aguardar sistema inicializar
./monitor.sh start
EOF

        chmod +x /tmp/monitoring_autostart.sh

        # Configurar para macOS (launchd)
        cat > /tmp/com.monitoring.autostart.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.monitoring.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <string>/tmp/monitoring_autostart.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

        # Instalar
        cp /tmp/monitoring_autostart.sh ~/Library/LaunchAgents/monitoring_autostart.sh
        cp /tmp/com.monitoring.autostart.plist ~/Library/LaunchAgents/

        # Carregar serviço
        launchctl load ~/Library/LaunchAgents/com.monitoring.autostart.plist

        log_success "Início automático configurado!"
        log_info "O sistema de monitoramento será iniciado automaticamente após reinicialização"
        log_info "Para desabilitar: launchctl unload ~/Library/LaunchAgents/com.monitoring.autostart.plist"
        ;;

    *)
        echo "🔍 SISTEMA DE MONITORAMENTO HÍBRIDO"
        echo "=================================="
        echo ""
        echo "Uso: $0 {comando}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  start               - Iniciar todos os serviços"
        echo "  stop                - Parar todos os serviços"
        echo "  restart             - Reiniciar todos os serviços"
        echo "  status              - Ver status de todos os serviços"
        echo "  logs                - Ver logs dos serviços"
        echo "  test                - Testar funcionamento completo"
        echo "  install-autostart   - Configurar início automático"
        echo "  uninstall-autostart - Remover configuração de início automático"
        echo ""
        echo "📁 ESTRUTURA ORGANIZADA:"
        echo "========================"
        echo "📊 dashboards/     - 4 dashboards Grafana principais"
        echo "⚙️  configs/        - Configurações (prometheus.yml, blackbox.yml)"
        echo "🔧 scripts/        - Scripts Python e Shell"
        echo "📋 logs/           - Todos os arquivos de log"
        echo "🗂️  backups/       - Arquivos antigos/desnecessários"
        echo "🔧 services/       - PIDs dos serviços rodando"
        echo ""
        echo "🌐 DASHBOARDS PRINCIPAIS:"
        echo "========================"
        echo "• blackbox_exporter_dashboard.json  - 12 sites com Status/SSL/DNS"
        echo "• server_metrics_dashboard.json     - Métricas do servidor"
        echo "• hybrid_security_dashboard.json    - Segurança híbrida"
        echo "• realtime_bot_dashboard.json       - Bots em tempo real"
        ;;
esac
