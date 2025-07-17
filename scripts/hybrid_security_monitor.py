#!/usr/bin/env python3
"""
Hybrid Security Monitor - Combina Blackbox Exporter com análise de logs
Integra dados de segurança externos (Blackbox) com análise interna (logs)
"""
import requests
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
from prometheus_client import push_to_gateway, Gauge, CollectorRegistry

class HybridSecurityMonitor:
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.pushgateway_url = "localhost:9091"

    def get_blackbox_security_metrics(self):
        """Coleta métricas de segurança do Blackbox via Prometheus"""
        metrics = {}

        queries = {
            'sensitive_files_exposed': 'probe_success{job="security-sensitive-files"}',
            'wp_login_exposed': 'probe_success{job="security-wp-login"}',
            'rate_limiting_active': 'probe_success{job="security-rate-limiting"}',
            'security_headers_present': 'probe_success{job="security-headers"}',
            'waf_detected': 'probe_success{job="security-waf-detection"}',
            'ssl_issues': 'probe_ssl_earliest_cert_expiry',
            'response_times': 'probe_duration_seconds{job=~"security-.*"}'
        }

        try:
            for metric_name, query in queries.items():
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': query},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'success' and data['data']['result']:
                        metrics[metric_name] = self.parse_prometheus_result(data['data']['result'])
                    else:
                        metrics[metric_name] = []
                else:
                    print(f"Error querying {metric_name}: {response.status_code}")
                    metrics[metric_name] = []

        except Exception as e:
            print(f"Error collecting Blackbox metrics: {e}")

        return metrics

    def parse_prometheus_result(self, result):
        """Parse resultados do Prometheus"""
        parsed = []
        for item in result:
            instance = item['metric'].get('instance', 'unknown')
            value = float(item['value'][1])
            parsed.append({'instance': instance, 'value': value})
        return parsed

    def get_realtime_log_metrics(self):
        """Coleta métricas dos logs em tempo real"""
        try:
            # Buscar métricas de logs já coletadas
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': 'realtime_attack_attempts_total'},
                timeout=10
            )

            log_metrics = {
                'attack_attempts': 0,
                'suspicious_ips': 0,
                'bot_ratio': 0,
                'total_requests': 0
            }

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    for metric in data['data']['result']:
                        log_metrics['attack_attempts'] = float(metric['value'][1])

            # Buscar outras métricas
            other_queries = {
                'suspicious_ips': 'realtime_suspicious_ips_total',
                'bot_ratio': 'realtime_bot_ratio_percent',
                'total_requests': 'realtime_web_requests_total'
            }

            for key, query in other_queries.items():
                try:
                    response = requests.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={'query': query},
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'success' and data['data']['result']:
                            log_metrics[key] = float(data['data']['result'][0]['value'][1])
                except:
                    pass

            return log_metrics

        except Exception as e:
            print(f"Error collecting log metrics: {e}")
            return {'attack_attempts': 0, 'suspicious_ips': 0, 'bot_ratio': 0, 'total_requests': 0}

    def calculate_security_scores(self, blackbox_metrics, log_metrics):
        """Calcula scores de segurança combinados"""
        scores = {
            'overall_security_score': 0,
            'external_security_score': 0,
            'internal_security_score': 0,
            'vulnerability_count': 0,
            'protection_level': 0
        }

        # Score externo (Blackbox)
        external_points = 0
        total_external_checks = 0

        # Verificar arquivos sensíveis (peso: 30 pontos)
        if 'sensitive_files_exposed' in blackbox_metrics:
            for result in blackbox_metrics['sensitive_files_exposed']:
                total_external_checks += 1
                if result['value'] == 0:  # 0 = failed probe = good (file not accessible)
                    external_points += 30
                else:
                    scores['vulnerability_count'] += 1

        # Verificar headers de segurança (peso: 25 pontos)
        if 'security_headers_present' in blackbox_metrics:
            for result in blackbox_metrics['security_headers_present']:
                total_external_checks += 1
                if result['value'] == 1:  # 1 = success = headers present
                    external_points += 25
                else:
                    scores['vulnerability_count'] += 1

        # Verificar rate limiting (peso: 20 pontos)
        if 'rate_limiting_active' in blackbox_metrics:
            for result in blackbox_metrics['rate_limiting_active']:
                total_external_checks += 1
                if result['value'] == 1 or result['value'] == 0:  # Ambos OK
                    external_points += 20

        # Verificar WAF (peso: 25 pontos)
        if 'waf_detected' in blackbox_metrics:
            for result in blackbox_metrics['waf_detected']:
                total_external_checks += 1
                if result['value'] == 0:  # 0 = blocked = good (WAF working)
                    external_points += 25
                    scores['protection_level'] += 1

        # Calcular score externo (0-100)
        if total_external_checks > 0:
            scores['external_security_score'] = min(100, (external_points / total_external_checks))

        # Score interno (Logs)
        internal_points = 100  # Começar com 100 e subtrair por problemas

        # Penalizar ataques (cada ataque = -2 pontos)
        internal_points -= min(50, log_metrics.get('attack_attempts', 0) * 2)

        # Penalizar IPs suspeitos (cada IP = -5 pontos)
        internal_points -= min(30, log_metrics.get('suspicious_ips', 0) * 5)

        # Penalizar alto ratio de bots (>80% = -20 pontos)
        bot_ratio = log_metrics.get('bot_ratio', 0)
        if bot_ratio > 80:
            internal_points -= 20
        elif bot_ratio > 60:
            internal_points -= 10

        scores['internal_security_score'] = max(0, internal_points)

        # Score geral (média ponderada: 60% externo, 40% interno)
        scores['overall_security_score'] = (
            scores['external_security_score'] * 0.6 +
            scores['internal_security_score'] * 0.4
        )

        return scores

    def send_hybrid_metrics(self, blackbox_metrics, log_metrics, security_scores):
        """Envia métricas híbridas para Prometheus"""
        try:
            registry = CollectorRegistry()

            # Scores de segurança
            overall_score = Gauge('hybrid_security_score_overall', 'Overall security score (0-100)', registry=registry)
            overall_score.set(security_scores['overall_security_score'])

            external_score = Gauge('hybrid_security_score_external', 'External security score from Blackbox', registry=registry)
            external_score.set(security_scores['external_security_score'])

            internal_score = Gauge('hybrid_security_score_internal', 'Internal security score from logs', registry=registry)
            internal_score.set(security_scores['internal_security_score'])

            # Contadores de problemas
            vulnerability_count = Gauge('hybrid_vulnerabilities_total', 'Total vulnerabilities detected', registry=registry)
            vulnerability_count.set(security_scores['vulnerability_count'])

            protection_level = Gauge('hybrid_protection_level', 'Protection systems detected (WAF, etc)', registry=registry)
            protection_level.set(security_scores['protection_level'])

            # Métricas específicas do Blackbox
            if 'sensitive_files_exposed' in blackbox_metrics:
                files_exposed = sum(1 for r in blackbox_metrics['sensitive_files_exposed'] if r['value'] == 1)
                files_protected = sum(1 for r in blackbox_metrics['sensitive_files_exposed'] if r['value'] == 0)

                files_exposed_gauge = Gauge('hybrid_sensitive_files_exposed_total', 'Sensitive files accessible', registry=registry)
                files_exposed_gauge.set(files_exposed)

                files_protected_gauge = Gauge('hybrid_sensitive_files_protected_total', 'Sensitive files protected', registry=registry)
                files_protected_gauge.set(files_protected)

            # Métricas combinadas
            combined_attacks = Gauge('hybrid_combined_attack_indicators', 'Combined attack indicators', registry=registry)
            combined_attacks.set(
                log_metrics.get('attack_attempts', 0) +
                security_scores.get('vulnerability_count', 0)
            )

            # Status de conformidade (0-1)
            compliance_status = Gauge('hybrid_security_compliance', 'Security compliance status', registry=registry)
            compliance_status.set(1 if security_scores['overall_security_score'] >= 80 else 0)

            # Enviar para Pushgateway
            push_to_gateway(self.pushgateway_url, job='hybrid-security-monitor', registry=registry)

            return True

        except Exception as e:
            print(f"Error sending hybrid metrics: {e}")
            return False

    def generate_security_report(self, blackbox_metrics, log_metrics, security_scores):
        """Gera relatório de segurança combinado"""
        print(f"\n🔒 HYBRID SECURITY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Scores
        print(f"📊 SECURITY SCORES:")
        print(f"   Overall Security Score: {security_scores['overall_security_score']:.1f}/100")
        print(f"   External (Blackbox):    {security_scores['external_security_score']:.1f}/100")
        print(f"   Internal (Logs):        {security_scores['internal_security_score']:.1f}/100")

        # Status
        if security_scores['overall_security_score'] >= 90:
            status = "🟢 EXCELENTE"
        elif security_scores['overall_security_score'] >= 75:
            status = "🟡 BOM"
        elif security_scores['overall_security_score'] >= 60:
            status = "🟠 REGULAR"
        else:
            status = "🔴 CRÍTICO"

        print(f"   Security Status:        {status}")

        # Problemas detectados
        print(f"\n🚨 ISSUES DETECTED:")
        print(f"   Vulnerabilities:        {security_scores['vulnerability_count']}")
        print(f"   Attack Attempts:        {log_metrics.get('attack_attempts', 0)}")
        print(f"   Suspicious IPs:         {log_metrics.get('suspicious_ips', 0)}")
        print(f"   Protection Systems:     {security_scores['protection_level']}")

        # Detalhes do Blackbox
        if blackbox_metrics:
            print(f"\n🔍 EXTERNAL SECURITY CHECKS:")

            if 'sensitive_files_exposed' in blackbox_metrics:
                exposed = sum(1 for r in blackbox_metrics['sensitive_files_exposed'] if r['value'] == 1)
                protected = sum(1 for r in blackbox_metrics['sensitive_files_exposed'] if r['value'] == 0)
                print(f"   Sensitive Files - Protected: {protected}, Exposed: {exposed}")

            if 'security_headers_present' in blackbox_metrics:
                with_headers = sum(1 for r in blackbox_metrics['security_headers_present'] if r['value'] == 1)
                without_headers = sum(1 for r in blackbox_metrics['security_headers_present'] if r['value'] == 0)
                print(f"   Security Headers - Present: {with_headers}, Missing: {without_headers}")

        # Recomendações
        print(f"\n💡 RECOMMENDATIONS:")
        if security_scores['vulnerability_count'] > 0:
            print("   • Fix exposed sensitive files immediately")
        if log_metrics.get('attack_attempts', 0) > 5:
            print("   • Consider implementing additional WAF rules")
        if log_metrics.get('bot_ratio', 0) > 70:
            print("   • Review bot management and rate limiting")
        if security_scores['protection_level'] == 0:
            print("   • Consider implementing a Web Application Firewall")

        print("\n" + "=" * 60)

    def run_hybrid_analysis(self):
        """Executa análise híbrida completa"""
        print("🔄 Starting hybrid security analysis...")

        # Coletar métricas do Blackbox
        print("📡 Collecting Blackbox security metrics...")
        blackbox_metrics = self.get_blackbox_security_metrics()

        # Coletar métricas dos logs
        print("📋 Collecting real-time log metrics...")
        log_metrics = self.get_realtime_log_metrics()

        # Calcular scores
        print("🧮 Calculating security scores...")
        security_scores = self.calculate_security_scores(blackbox_metrics, log_metrics)

        # Enviar métricas
        print("📤 Sending hybrid metrics to Prometheus...")
        success = self.send_hybrid_metrics(blackbox_metrics, log_metrics, security_scores)

        # Gerar relatório
        self.generate_security_report(blackbox_metrics, log_metrics, security_scores)

        if success:
            print("✅ Hybrid security analysis completed successfully")
        else:
            print("❌ Some errors occurred during analysis")

        return success

def main():
    monitor = HybridSecurityMonitor()
    monitor.run_hybrid_analysis()

if __name__ == "__main__":
    main()
