#!/bin/bash
# Script para controlar o monitoramento em tempo real

case "$1" in
    start)
        echo "🚀 Iniciando monitoramento contínuo..."
        source venv/bin/activate && nohup python3 realtime_bot_monitor.py --continuous 120 > realtime_continuous.log 2>&1 &
        echo $! > realtime_monitor.pid
        echo "✅ Monitor iniciado em background (PID: $(cat realtime_monitor.pid))"
        ;;
    stop)
        if [ -f realtime_monitor.pid ]; then
            PID=$(cat realtime_monitor.pid)
            kill $PID 2>/dev/null
            rm -f realtime_monitor.pid
            echo "🛑 Monitor parado (PID: $PID)"
        else
            echo "❌ Monitor não está rodando"
        fi
        ;;
    status)
        if [ -f realtime_monitor.pid ]; then
            PID=$(cat realtime_monitor.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "✅ Monitor rodando (PID: $PID)"
                echo "📊 Últimas métricas:"
                tail -5 realtime_continuous.log
            else
                echo "❌ Monitor não está rodando (PID inválido)"
                rm -f realtime_monitor.pid
            fi
        else
            echo "❌ Monitor não está rodando"
        fi
        ;;
    logs)
        echo "📋 Últimas 20 linhas do log:"
        tail -20 realtime_continuous.log
        ;;
    alerts)
        if [ -f realtime_alerts.log ]; then
            echo "🚨 Últimos alertas:"
            tail -10 realtime_alerts.log
        else
            echo "✅ Nenhum alerta registrado"
        fi
        ;;
    test)
        echo "🧪 Executando teste único..."
        source venv/bin/activate && python3 realtime_bot_monitor.py
        ;;
    *)
        echo "Uso: $0 {start|stop|status|logs|alerts|test}"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia monitoramento contínuo em background"
        echo "  stop    - Para o monitoramento contínuo"
        echo "  status  - Mostra status do monitor"
        echo "  logs    - Mostra logs recentes"
        echo "  alerts  - Mostra alertas recentes"
        echo "  test    - Executa um teste único"
        exit 1
        ;;
esac
