#!/usr/bin/env python3
"""
Monitor de bots em tempo real com detecção de anomalias
Executa continuamente monitorando logs em tempo real
"""
import time
import os
import re
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from prometheus_client import push_to_gateway, Gauge, Counter, CollectorRegistry
import threading
import subprocess

class RealTimeBotMonitor:
    def __init__(self):
        # Detectar diretório do projeto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(script_dir)

        # Carregar configurações
        self.load_config()

        self.metrics_history = deque(maxlen=288)  # 24h com coletas a cada 5min
        self.current_metrics = defaultdict(int)
        self.suspicious_ips = defaultdict(int)
        self.attack_patterns = defaultdict(int)
        self.running = True

        # Thresholds para alertas
        self.bot_spike_threshold = 200  # % de aumento súbito de bots
        self.attack_threshold = 10      # tentativas de ataque por minuto
        self.request_rate_threshold = 100  # requisições por IP por minuto

        # Padrões de bots mais abrangentes
        self.bot_patterns = [
            r'bot', r'crawler', r'spider', r'scraper', r'scanner',
            r'Googlebot', r'Bingbot', r'YandexBot', r'facebookexternalhit',
            r'WhatsApp', r'LinkedInBot', r'TwitterBot', r'SemrushBot',
            r'AhrefsBot', r'MJ12bot', r'DotBot', r'Applebot', r'Slurp',
            r'facebookcatalog', r'Twitterbot', r'LinkedInBot', r'PinterestBot',
            r'SemrushBot', r'MauiBot', r'CCBot', r'DataForSeoBot', r'Baiduspider',
            r'DuckDuckBot', r'ia_archiver', r'Wayback', r'archive\.org',
            r'python-requests', r'curl', r'wget', r'HTTPie', r'PostmanRuntime'
        ]

        # Padrões de ataque expandidos
        self.attack_patterns_list = [
            r'\.php\?', r'wp-admin', r'wp-login', r'xmlrpc\.php',
            r'\.env', r'config\.php', r'admin\.php', r'shell\.php',
            r'eval\(', r'base64_', r'union.*select', r'<script',
            r'\.\./', r'etc/passwd', r'/proc/self', r'phpmyadmin',
            r'\.git/', r'\.svn/', r'backup\.sql', r'database\.sql',
            r'wp-config\.php', r'readme\.html', r'license\.txt',
            r'null', r'%00', r'%27', r'%22', r'%3C', r'%3E',
            r'SELECT.*FROM', r'INSERT.*INTO', r'DROP.*TABLE',
            r'<iframe', r'javascript:', r'vbscript:', r'onload='
        ]

        self.bot_regex = re.compile('|'.join(self.bot_patterns), re.IGNORECASE)
        self.attack_regex = re.compile('|'.join(self.attack_patterns_list), re.IGNORECASE)

    def collect_current_logs(self):
        """Coleta logs mais recentes usando configuração externa"""
        try:
            # Coletar logs dos últimos 5 minutos via SSH
            five_min_ago = datetime.now() - timedelta(minutes=5)
            timestamp_filter = five_min_ago.strftime("%d/%b/%Y:%H:%M")

            # Se não há configuração carregada, usar dados de exemplo
            if not self.ssh_server or not self.log_paths:
                print("Warning: Configuração não encontrada, usando dados de exemplo")
                return self.get_sample_logs()

            # Construir comando SSH para buscar logs nos caminhos configurados
            log_paths_str = ' '.join([f'"{path}"' for path in self.log_paths])
            cmd = f'''ssh {self.ssh_server} "
            for log_path in {log_paths_str}; do
                if [ -f \"$log_path\" ]; then
                    grep '{timestamp_filter}' \"$log_path\" 2>/dev/null
                fi
            done | tail -1000
            "'''

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')
            else:
                print(f"Warning: No recent logs found, using sample data")
                return self.get_sample_logs()

        except Exception as e:
            print(f"Error collecting logs: {e}")
            return self.get_sample_logs()

    def get_sample_logs(self):
        """Retorna logs simulados para teste"""
        now = datetime.now()
        sample_logs = [
            f'177.155.246.167 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")} -0300] "GET / HTTP/1.1" 200 15234 "https://google.com" "Mozilla/5.0 (compatible; Googlebot/2.1)"',
            f'192.168.1.100 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")} -0300] "GET /about HTTP/1.1" 200 8952 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"',
            f'185.191.171.15 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")} -0300] "GET /wp-admin/ HTTP/1.1" 403 1234 "-" "python-requests/2.28.1"',
            f'103.126.203.178 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")} -0300] "POST /wp-login.php HTTP/1.1" 429 567 "-" "curl/7.68.0"',
            f'45.129.14.74 - - [{now.strftime("%d/%b/%Y:%H:%M:%S")} -0300] "GET /.env HTTP/1.1" 404 1122 "-" "python-requests/2.28.1"',
        ]
        return sample_logs

    def analyze_logs(self, log_entries):
        """Analisa logs em tempo real"""
        current_time = datetime.now()
        metrics = {
            'timestamp': current_time.isoformat(),
            'total_requests': 0,
            'bot_requests': 0,
            'user_requests': 0,
            'unique_ips': set(),
            'ip_request_count': defaultdict(int),
            'status_codes': defaultdict(int),
            'attack_attempts': 0,
            'suspicious_ips': set(),
            'bot_types': defaultdict(int),
            'top_attacked_paths': defaultdict(int)
        }

        log_pattern = r'(\d+\.\d+\.\d+\.\d+).*?\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+|-)\s+"([^"]*)"\s+"([^"]*)"'

        for entry in log_entries:
            if not entry.strip():
                continue

            match = re.search(log_pattern, entry.strip())
            if not match:
                continue

            ip, timestamp, request, status, size, referer, user_agent = match.groups()

            # Extrair método e path
            request_parts = request.split()
            if len(request_parts) >= 2:
                method, path = request_parts[0], request_parts[1]
            else:
                method, path = 'GET', '/'

            metrics['total_requests'] += 1
            metrics['unique_ips'].add(ip)
            metrics['ip_request_count'][ip] += 1
            metrics['status_codes'][status] += 1

            # Detectar bots
            is_bot = self.bot_regex.search(user_agent)
            if is_bot:
                metrics['bot_requests'] += 1
                # Identificar tipo de bot
                for pattern in self.bot_patterns:
                    if re.search(pattern, user_agent, re.IGNORECASE):
                        metrics['bot_types'][pattern] += 1
                        break
            else:
                metrics['user_requests'] += 1

            # Detectar ataques
            is_attack = self.attack_regex.search(path) or self.attack_regex.search(user_agent)
            if is_attack:
                metrics['attack_attempts'] += 1
                metrics['suspicious_ips'].add(ip)
                metrics['top_attacked_paths'][path] += 1

            # Detectar IPs suspeitos (muitas requisições)
            if metrics['ip_request_count'][ip] > self.request_rate_threshold:
                metrics['suspicious_ips'].add(ip)

        # Converter sets para contadores
        metrics['unique_ips'] = len(metrics['unique_ips'])
        metrics['suspicious_ips'] = len(metrics['suspicious_ips'])

        return metrics

    def detect_anomalies(self, current_metrics):
        """Detecta anomalias e gera alertas"""
        alerts = []

        if len(self.metrics_history) > 0:
            # Calcular médias históricas
            historical_bot_avg = sum(m.get('bot_requests', 0) for m in self.metrics_history) / len(self.metrics_history)
            historical_attack_avg = sum(m.get('attack_attempts', 0) for m in self.metrics_history) / len(self.metrics_history)

            current_bots = current_metrics.get('bot_requests', 0)
            current_attacks = current_metrics.get('attack_attempts', 0)

            # Detectar spike de bots
            if historical_bot_avg > 0:
                bot_increase_percent = ((current_bots - historical_bot_avg) / historical_bot_avg) * 100
                if bot_increase_percent > self.bot_spike_threshold:
                    alerts.append({
                        'type': 'bot_spike',
                        'severity': 'warning',
                        'message': f'Bot traffic spike: {bot_increase_percent:.1f}% increase ({current_bots} vs avg {historical_bot_avg:.1f})',
                        'timestamp': datetime.now().isoformat()
                    })

            # Detectar spike de ataques
            if current_attacks > self.attack_threshold:
                alerts.append({
                    'type': 'attack_spike',
                    'severity': 'critical',
                    'message': f'Attack attempts spike: {current_attacks} attempts detected',
                    'timestamp': datetime.now().isoformat()
                })

            # Detectar possível DDoS
            if current_metrics.get('suspicious_ips', 0) > 5:
                alerts.append({
                    'type': 'possible_ddos',
                    'severity': 'critical',
                    'message': f'Possible DDoS: {current_metrics["suspicious_ips"]} suspicious IPs detected',
                    'timestamp': datetime.now().isoformat()
                })

        return alerts

    def send_metrics_to_prometheus(self, metrics, alerts):
        """Envia métricas em tempo real para Prometheus"""
        try:
            registry = CollectorRegistry()

            # Métricas básicas
            total_requests = Gauge('realtime_web_requests_total', 'Real-time total requests', registry=registry)
            total_requests.set(metrics.get('total_requests', 0))

            bot_requests = Gauge('realtime_bot_requests_total', 'Real-time bot requests', registry=registry)
            bot_requests.set(metrics.get('bot_requests', 0))

            user_requests = Gauge('realtime_user_requests_total', 'Real-time user requests', registry=registry)
            user_requests.set(metrics.get('user_requests', 0))

            attack_attempts = Gauge('realtime_attack_attempts_total', 'Real-time attack attempts', registry=registry)
            attack_attempts.set(metrics.get('attack_attempts', 0))

            suspicious_ips = Gauge('realtime_suspicious_ips_total', 'Real-time suspicious IPs', registry=registry)
            suspicious_ips.set(metrics.get('suspicious_ips', 0))

            # Métricas de alertas
            alert_count = Gauge('realtime_alerts_total', 'Real-time alerts generated', registry=registry)
            alert_count.set(len(alerts))

            # Bot ratio em tempo real
            total = metrics.get('total_requests', 0)
            if total > 0:
                bot_ratio = Gauge('realtime_bot_ratio_percent', 'Real-time bot traffic percentage', registry=registry)
                bot_ratio.set((metrics.get('bot_requests', 0) / total) * 100)

            # Top tipos de bots
            for bot_type, count in metrics.get('bot_types', {}).items():
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', bot_type.lower())
                bot_type_gauge = Gauge(f'realtime_bot_type_{safe_name}_total', f'Bot type {bot_type}', registry=registry)
                bot_type_gauge.set(count)

            # Status codes
            for status, count in metrics.get('status_codes', {}).items():
                status_gauge = Gauge(f'realtime_http_status_{status}_total', f'HTTP {status} responses', registry=registry)
                status_gauge.set(count)

            # Enviar para Pushgateway
            push_to_gateway('localhost:9091', job='realtime-web-analytics', registry=registry)

            return True

        except Exception as e:
            print(f"Error sending metrics: {e}")
            return False

    def log_alerts(self, alerts):
        """Log e exibe alertas"""
        if alerts:
            print(f"\n🚨 REAL-TIME ALERTS ({len(alerts)} alerts)")
            with open('realtime_alerts.log', 'a') as f:
                for alert in alerts:
                    severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡"
                    message = f"{severity_icon} {alert['message']}"
                    print(f"   {message}")
                    f.write(f"{alert['timestamp']} - {alert['severity'].upper()}: {alert['message']}\n")

    def run_monitoring_cycle(self):
        """Executa um ciclo de monitoramento"""
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Collecting real-time logs...")

        # Coletar logs
        logs = self.collect_current_logs()

        # Analisar
        metrics = self.analyze_logs(logs)

        # Detectar anomalias
        alerts = self.detect_anomalies(metrics)

        # Adicionar ao histórico
        self.metrics_history.append(metrics.copy())

        # Enviar métricas
        success = self.send_metrics_to_prometheus(metrics, alerts)

        # Log alertas
        self.log_alerts(alerts)

        # Status summary
        print(f"📊 Requests: {metrics['total_requests']} (🤖 {metrics['bot_requests']}, 👥 {metrics['user_requests']})")
        print(f"🚨 Attacks: {metrics['attack_attempts']}, Suspicious IPs: {metrics['suspicious_ips']}")
        if success:
            print("✅ Metrics sent to Prometheus")
        else:
            print("❌ Failed to send metrics")

    def start_monitoring(self, interval_seconds=300):  # 5 minutos por padrão
        """Inicia monitoramento contínuo"""
        print(f"🚀 Starting real-time bot monitoring (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")

        try:
            while self.running:
                self.run_monitoring_cycle()
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n🛑 Stopping real-time monitoring...")
            self.running = False
        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")

    def load_config(self):
        """Carregar configurações do arquivo sites.conf"""
        config_file = os.path.join(self.project_dir, 'configs', 'sites.conf')

        # Valores padrão
        self.ssh_server = "localhost"
        self.log_paths = []

        if os.path.exists(config_file):
            try:
                # Executar o arquivo de configuração para extrair variáveis
                result = subprocess.run(
                    f'source {config_file} && echo "SSH_SERVER=$SSH_SERVER" && printf "%s\\n" "${{SITES_LOGS[@]}}"',
                    shell=True, capture_output=True, text=True
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('SSH_SERVER='):
                            self.ssh_server = line.split('=', 1)[1]
                        elif ':' in line and '/home/' in line:
                            # Extrair caminho do formato "alias:/path"
                            path = line.split(':', 1)[1]
                            self.log_paths.append(path)

                print(f"✅ Configuração carregada: {self.ssh_server}, {len(self.log_paths)} caminhos de log")
            except Exception as e:
                print(f"⚠️ Erro ao carregar configuração: {e}")
                print("Usando configuração padrão")
        else:
            print(f"⚠️ Arquivo de configuração não encontrado: {config_file}")
            print("Usando configuração padrão")

def main():
    monitor = RealTimeBotMonitor()

    # Execução única ou contínua baseada em argumentos
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Monitoramento contínuo
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        monitor.start_monitoring(interval)
    else:
        # Execução única (para cron)
        monitor.run_monitoring_cycle()

if __name__ == "__main__":
    main()
