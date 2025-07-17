#!/bin/bash
# Script de controle para o Sistema Híbrido de Segurança

# Usar diretório relativo baseado na localização do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

case "$1" in
    test)
        echo "🧪 Executando análise híbrida de segurança..."
        source venv/bin/activate && python3 hybrid_security_monitor.py
        ;;

    status)
        echo "📊 STATUS DO SISTEMA HÍBRIDO"
        echo "=============================="

        # Verificar se Prometheus está rodando
        if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
            echo "✅ Prometheus: RODANDO"
        else
            echo "❌ Prometheus: PARADO"
        fi

        # Verificar se Blackbox está rodando
        if curl -s http://localhost:9115/ > /dev/null 2>&1; then
            echo "✅ Blackbox Exporter: RODANDO"
        else
            echo "❌ Blackbox Exporter: PARADO"
        fi

        # Verificar métricas híbridas
        hybrid_metrics=$(curl -s http://localhost:9091/metrics | grep -c "hybrid_")
        if [ $hybrid_metrics -gt 0 ]; then
            echo "✅ Métricas Híbridas: $hybrid_metrics métricas ativas"
        else
            echo "❌ Métricas Híbridas: Nenhuma métrica encontrada"
        fi

        # Verificar jobs de segurança no Prometheus
        echo ""
        echo "🔍 JOBS DE SEGURANÇA ATIVOS:"
        curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | grep -E "(probe_success|hybrid_)" | head -5
        ;;

    blackbox-test)
        echo "🔍 Testando módulos de segurança do Blackbox..."

        # Carregar configuração dos sites
        if [ ! -f "configs/sites.conf" ]; then
            echo "❌ Arquivo configs/sites.conf não encontrado!"
            echo "💡 Copie configs/sites.conf.example para configs/sites.conf e configure"
            exit 1
        fi

        source configs/sites.conf

        # Usar o primeiro site da lista para testes
        if [ ${#SITES_HTTP[@]} -gt 0 ]; then
            TEST_SITE="${SITES_HTTP[0]}"

            # Testar alguns módulos específicos
            echo "Testing sensitive files check on $TEST_SITE..."
            curl -s "http://localhost:9115/probe?target=$TEST_SITE/.env&module=security_sensitive_files" | grep "probe_success"

            echo "Testing security headers on $TEST_SITE..."
            curl -s "http://localhost:9115/probe?target=$TEST_SITE&module=security_headers" | grep "probe_success"
        else
            echo "❌ Nenhum site configurado para teste!"
        fi
        ;;

    logs)
        echo "📋 LOGS DO SISTEMA HÍBRIDO:"
        echo "=========================="
        if [ -f hybrid_security.log ]; then
            echo "Últimas 20 linhas:"
            tail -20 hybrid_security.log
        else
            echo "Nenhum log encontrado ainda"
        fi
        ;;

    metrics)
        echo "📊 MÉTRICAS HÍBRIDAS ATUAIS:"
        echo "============================="
        curl -s http://localhost:9091/metrics | grep hybrid_ | while read line; do
            echo "$line"
        done
        ;;

    dashboard)
        echo "📱 INFORMAÇÕES DO DASHBOARD:"
        echo "============================"
        echo "Dashboard Grafana: hybrid_security_dashboard.json"
        echo "Importe este arquivo no Grafana para visualizar:"
        echo "• Scores de segurança (geral, externo, interno)"
        echo "• Status de compliance"
        echo "• Vulnerabilidades detectadas"
        echo "• Timeline de ameaças"
        echo "• Status dos checks do Blackbox"
        ;;

    restart-services)
        echo "🔄 Reiniciando serviços do sistema híbrido..."

        # Parar serviços
        pkill -f blackbox_exporter
        pkill -f prometheus

        sleep 3

        # Iniciar Blackbox
        nohup ./blackbox_exporter --config.file=blackbox.yml > blackbox.log 2>&1 &
        echo "✅ Blackbox Exporter reiniciado"

        # Iniciar Prometheus
        nohup ./prometheus --config.file=prometheus.yml --storage.tsdb.path=./data > prometheus.log 2>&1 &
        echo "✅ Prometheus reiniciado"

        sleep 5

        # Testar conectividade
        if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
            echo "✅ Prometheus operacional"
        else
            echo "❌ Problema com Prometheus"
        fi

        if curl -s http://localhost:9115/ > /dev/null 2>&1; then
            echo "✅ Blackbox Exporter operacional"
        else
            echo "❌ Problema com Blackbox Exporter"
        fi
        ;;

    security-report)
        echo "🔒 RELATÓRIO DE SEGURANÇA COMPLETO"
        echo "=================================="
        source venv/bin/activate && python3 hybrid_security_monitor.py | grep -A 50 "HYBRID SECURITY REPORT"
        ;;

    check-sites)
        echo "🌐 VERIFICANDO SITES INDIVIDUALMENTE:"
        echo "====================================="

        # Carregar configuração dos sites
        if [ ! -f "configs/sites.conf" ]; then
            echo "❌ Arquivo configs/sites.conf não encontrado!"
            echo "💡 Copie configs/sites.conf.example para configs/sites.conf e configure"
            exit 1
        fi

        source configs/sites.conf

        for site in "${SITES_HTTP[@]}"; do
            echo "Checking $site..."

            # Teste básico de conectividade
            if curl -s --max-time 5 "$site" > /dev/null; then
                echo "  ✅ Online"
            else
                echo "  ❌ Offline/Problemas"
            fi

            # Teste de arquivos sensíveis
            status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$site/.env")
            if [ "$status" = "404" ] || [ "$status" = "403" ]; then
                echo "  ✅ .env protegido ($status)"
            else
                echo "  ⚠️ .env acessível ($status)"
            fi
        done
        ;;

    *)
        echo "🔒 SISTEMA HÍBRIDO DE SEGURANÇA"
        echo "==============================="
        echo ""
        echo "Uso: $0 {comando}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  test              - Executar análise híbrida completa"
        echo "  status            - Ver status de todos os componentes"
        echo "  blackbox-test     - Testar módulos específicos do Blackbox"
        echo "  logs              - Ver logs do sistema híbrido"
        echo "  metrics           - Ver métricas híbridas atuais"
        echo "  dashboard         - Informações sobre o dashboard Grafana"
        echo "  restart-services  - Reiniciar Prometheus e Blackbox"
        echo "  security-report   - Gerar relatório completo de segurança"
        echo "  check-sites       - Verificar sites individualmente"
        echo ""
        echo "📊 DASHBOARDS DISPONÍVEIS:"
        echo "• hybrid_security_dashboard.json - Dashboard principal"
        echo "• realtime_bot_dashboard.json - Monitoramento de bots"
        echo "• web_traffic_dashboard.json - Análise de tráfego"
        echo "• all_sites_dashboard.json - Visão geral dos sites"
        ;;
esac
