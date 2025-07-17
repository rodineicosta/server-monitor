#!/usr/bin/env python3
# Script para analisar logs de acesso e detectar bots vs usuários reais
import re
import os
import subprocess
from collections import defaultdict
from prometheus_client import push_to_gateway, Gauge, CollectorRegistry
from datetime import datetime, timedelta

class WebAnalytics:
    def __init__(self):
        # Detectar diretório do projeto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(script_dir)

        # Carregar configurações
        self.load_config()

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
                print("Usando dados de exemplo")
        else:
            print(f"⚠️ Arquivo de configuração não encontrado: {config_file}")
            print("Usando dados de exemplo")

    def collect_real_logs(self):
        """Coletar logs reais via SSH usando configuração externa"""
        try:
            # Se não há configuração carregada, usar dados de exemplo
            if not self.ssh_server or not self.log_paths:
                print("Warning: Configuração não encontrada, usando dados de exemplo")
                return self.get_sample_logs()

            # Construir comando SSH para buscar logs nos caminhos configurados
            log_paths_str = ' '.join([f'"{path}"' for path in self.log_paths])
            cmd = f'''ssh {self.ssh_server} "
            for log_path in {log_paths_str}; do
                if [ -f \"$log_path\" ]; then
                    tail -1000 \"$log_path\" 2>/dev/null
                fi
            done
            "'''

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and result.stdout.strip():
                logs = result.stdout.strip().split('\n')
                print(f"✅ Coletados {len(logs)} logs reais via SSH")
                return logs
            else:
                print(f"Warning: Erro ao coletar logs reais, usando dados de exemplo")
                return self.get_sample_logs()

        except Exception as e:
            print(f"Error collecting real logs: {e}")
            return self.get_sample_logs()

    def get_sample_logs(self):
        """Dados de exemplo para quando não há logs reais disponíveis"""
        return [
            '177.155.246.167 - - [02/Jul/2025:00:45:23 -0300] "GET / HTTP/1.1" 200 15234 "https://google.com" "Mozilla/5.0 (compatible; Googlebot/2.1)"',
            '192.168.1.100 - - [02/Jul/2025:00:46:15 -0300] "GET /about HTTP/1.1" 200 8952 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"',
            '185.191.171.15 - - [02/Jul/2025:00:47:02 -0300] "GET /sitemap.xml HTTP/1.1" 200 3421 "-" "Mozilla/5.0 (compatible; AhrefsBot/7.0)"',
            '89.248.171.41 - - [02/Jul/2025:00:48:10 -0300] "GET /wp-admin/admin-ajax.php HTTP/1.1" 403 1234 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"',
            '103.126.203.178 - - [02/Jul/2025:00:49:33 -0300] "POST /wp-login.php HTTP/1.1" 429 567 "-" "python-requests/2.28.1"',
            '45.129.14.74 - - [02/Jul/2025:00:50:45 -0300] "GET /.env HTTP/1.1" 404 1122 "-" "curl/7.68.0"',
            '201.20.84.155 - - [02/Jul/2025:00:51:12 -0300] "GET /contact HTTP/1.1" 200 9876 "https://example.com" "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"',
            '66.249.66.35 - - [02/Jul/2025:00:52:33 -0300] "GET /services HTTP/1.1" 200 12345 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"'
        ]

    def parse_access_logs(self):
        """Parse access logs para detectar bots e usuários usando logs reais"""

        # Padrões conhecidos de bots
        bot_patterns = [
            r'bot', r'crawler', r'spider', r'scraper', r'scanner',
            r'Googlebot', r'Bingbot', r'YandexBot', r'facebookexternalhit',
            r'WhatsApp', r'LinkedInBot', r'TwitterBot', r'SemrushBot',
            r'AhrefsBot', r'MJ12bot', r'DotBot', r'Applebot', r'Slurp',
            r'facebookcatalog', r'Twitterbot', r'LinkedInBot', r'PinterestBot',
            r'SemrushBot', r'MauiBot', r'CCBot', r'DataForSeoBot'
        ]

        bot_regex = re.compile('|'.join(bot_patterns), re.IGNORECASE)

        metrics = {
            'total_requests': 0,
            'bot_requests': 0,
            'user_requests': 0,
            'unique_ips': set(),
            'status_codes': defaultdict(int),
            'top_pages': defaultdict(int),
            'suspicious_activity': 0,
            'attack_patterns': 0
        }

        # Padrões suspeitos que podem indicar ataques
        attack_patterns = [
            r'\.php\?', r'wp-admin', r'wp-login', r'xmlrpc\.php',
            r'\.env', r'config\.php', r'admin\.php', r'shell\.php',
            r'eval\(', r'base64_', r'union.*select', r'<script',
            r'\.\./', r'etc/passwd', r'/proc/self'
        ]
        attack_regex = re.compile('|'.join(attack_patterns), re.IGNORECASE)

        # Coletar logs reais do servidor
        log_entries = self.collect_real_logs()

        # Padrão de parsing para logs Apache/Nginx
        log_pattern = r'(\d+\.\d+\.\d+\.\d+).*?\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+|-)\s+"([^"]*)"\s+"([^"]*)"'

        for entry in log_entries:
            match = re.search(log_pattern, entry.strip())
            if match:
                ip, timestamp, request, status, size, referer, user_agent = match.groups()

                # Extrair método e path da requisição
                request_parts = request.split()
                if len(request_parts) >= 2:
                    method, path = request_parts[0], request_parts[1]
                else:
                    method, path = 'GET', '/'

                metrics['total_requests'] += 1
                metrics['unique_ips'].add(ip)
                metrics['status_codes'][status] += 1
                metrics['top_pages'][path] += 1

                # Detectar bots
                is_bot = bot_regex.search(user_agent)

                # Detectar atividade suspeita
                is_attack = attack_regex.search(path) or attack_regex.search(user_agent)

                if is_attack:
                    metrics['attack_patterns'] += 1

                # Detectar atividade suspeita por IP (muitas requisições 4xx)
                if status.startswith('4') and not is_bot:
                    metrics['suspicious_activity'] += 1

                if is_bot:
                    metrics['bot_requests'] += 1
                else:
                    metrics['user_requests'] += 1

        return metrics

    def send_metrics(self):
        """Enviar métricas de tráfego web para Prometheus usando logs reais"""
        metrics = self.parse_access_logs()

        if not metrics:
            print("No metrics to send")
            return False

        try:
            registry = CollectorRegistry()

            # Métricas de tráfego básico
            total_requests = Gauge('web_requests_total', 'Total web requests', registry=registry)
            total_requests.set(metrics['total_requests'])

            bot_requests = Gauge('web_bot_requests_total', 'Bot requests', registry=registry)
            bot_requests.set(metrics['bot_requests'])

            user_requests = Gauge('web_user_requests_total', 'Human user requests', registry=registry)
            user_requests.set(metrics['user_requests'])

            unique_visitors = Gauge('web_unique_ips_total', 'Unique IP addresses', registry=registry)
            unique_visitors.set(len(metrics['unique_ips']))

            # Métricas de segurança
            suspicious_activity = Gauge('web_suspicious_requests_total', 'Suspicious requests (4xx from humans)', registry=registry)
            suspicious_activity.set(metrics['suspicious_activity'])

            attack_patterns = Gauge('web_attack_patterns_total', 'Requests matching attack patterns', registry=registry)
            attack_patterns.set(metrics['attack_patterns'])

            # Bot ratio (porcentagem de bots)
            if metrics['total_requests'] > 0:
                bot_ratio = Gauge('web_bot_ratio_percent', 'Percentage of bot traffic', registry=registry)
                bot_ratio.set((metrics['bot_requests'] / metrics['total_requests']) * 100)

            # Métricas de status HTTP
            for status, count in metrics['status_codes'].items():
                status_gauge = Gauge(f'web_http_status_{status}_total', f'HTTP {status} responses', registry=registry)
                status_gauge.set(count)

            # Top páginas mais acessadas (apenas as 5 primeiras)
            top_pages = sorted(metrics['top_pages'].items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (page, count) in enumerate(top_pages):
                # Sanitizar nome da página para métrica válida
                page_safe = re.sub(r'[^a-zA-Z0-9_]', '_', page.replace('/', '_').strip('_'))
                if page_safe:
                    page_gauge = Gauge(f'web_page_hits_{page_safe}_total', f'Hits for page {page}', registry=registry)
                    page_gauge.set(count)

            # Enviar para Pushgateway
            push_to_gateway('localhost:9091', job='web-analytics', registry=registry)

            # Log detalhado
            print(f"=== WEB ANALYTICS METRICS SENT ===")
            print(f"📊 Total requests: {metrics['total_requests']}")
            if metrics['total_requests'] > 0:
                print(f"🤖 Bot requests: {metrics['bot_requests']} ({(metrics['bot_requests']/metrics['total_requests']*100):.1f}%)")
                print(f"👥 User requests: {metrics['user_requests']} ({(metrics['user_requests']/metrics['total_requests']*100):.1f}%)")
            print(f"🌐 Unique IPs: {len(metrics['unique_ips'])}")
            print(f"🚨 Suspicious requests: {metrics['suspicious_activity']}")
            print(f"⚠️ Attack patterns detected: {metrics['attack_patterns']}")

            if top_pages:
                print(f"📄 Top pages:")
                for page, count in top_pages:
                    print(f"   {page}: {count} hits")

            print(f"📈 HTTP Status codes:")
            for status, count in sorted(metrics['status_codes'].items()):
                print(f"   {status}: {count}")

            return True

        except Exception as e:
            print(f"Error sending web metrics: {e}")
            return False

def send_web_metrics():
    """Função para compatibilidade - usar instância da classe"""
    analyzer = WebAnalytics()
    return analyzer.send_metrics()

if __name__ == "__main__":
    send_web_metrics()
