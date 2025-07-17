#!/bin/bash
# Script para gerar prometheus.yml baseado no template e configuração de sites

# Usar diretório relativo em vez de absoluto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Carregar configuração dos sites
if [ ! -f "configs/sites.conf" ]; then
    echo "❌ Arquivo configs/sites.conf não encontrado!"
    echo "💡 Copie configs/sites.conf.example para configs/sites.conf e configure"
    exit 1
fi

source configs/sites.conf

# Verificar se template existe
if [ ! -f "configs/prometheus.yml.template" ]; then
    echo "❌ Template configs/prometheus.yml.template não encontrado!"
    exit 1
fi

# Gerar targets para cada seção em arquivos temporários
echo -n "" > /tmp/sites_http.tmp
for site in "${SITES_HTTP[@]}"; do
    echo "        - $site" >> /tmp/sites_http.tmp
done

echo -n "" > /tmp/security_sensitive.tmp
for site in "${SITES_HTTP[@]}"; do
    for path in "${SENSITIVE_PATHS[@]}"; do
        echo "        - $site$path" >> /tmp/security_sensitive.tmp
    done
done

echo -n "" > /tmp/security_wp.tmp
for site in "${SITES_HTTP[@]}"; do
    echo "        - $site/wp-login.php" >> /tmp/security_wp.tmp
    echo "        - $site/wp-admin/" >> /tmp/security_wp.tmp
done

echo -n "" > /tmp/security_rate.tmp
for site in "${SITES_HTTP[@]}"; do
    echo "        - $site" >> /tmp/security_rate.tmp
done

echo -n "" > /tmp/security_headers.tmp
for site in "${SITES_HTTP[@]}"; do
    echo "        - $site" >> /tmp/security_headers.tmp
done

echo -n "" > /tmp/security_waf.tmp
for site in "${SITES_HTTP[@]}"; do
    echo "        - $site" >> /tmp/security_waf.tmp
done

# Gerar prometheus.yml usando substituições de arquivos
sed -e '/{{SITES_HTTP_TARGETS}}/r /tmp/sites_http.tmp' \
    -e '/{{SITES_HTTP_TARGETS}}/d' \
    -e '/{{SECURITY_SENSITIVE_TARGETS}}/r /tmp/security_sensitive.tmp' \
    -e '/{{SECURITY_SENSITIVE_TARGETS}}/d' \
    -e '/{{SECURITY_WP_LOGIN_TARGETS}}/r /tmp/security_wp.tmp' \
    -e '/{{SECURITY_WP_LOGIN_TARGETS}}/d' \
    -e '/{{SECURITY_RATE_LIMIT_TARGETS}}/r /tmp/security_rate.tmp' \
    -e '/{{SECURITY_RATE_LIMIT_TARGETS}}/d' \
    -e '/{{SECURITY_HEADERS_TARGETS}}/r /tmp/security_headers.tmp' \
    -e '/{{SECURITY_HEADERS_TARGETS}}/d' \
    -e '/{{SECURITY_WAF_TARGETS}}/r /tmp/security_waf.tmp' \
    -e '/{{SECURITY_WAF_TARGETS}}/d' \
    configs/prometheus.yml.template > configs/prometheus.yml

# Limpar arquivos temporários
rm -f /tmp/sites_http.tmp /tmp/security_sensitive.tmp /tmp/security_wp.tmp /tmp/security_rate.tmp /tmp/security_headers.tmp /tmp/security_waf.tmp

echo "✅ prometheus.yml gerado com sucesso!"
echo "📊 Sites configurados: ${#SITES_HTTP[@]}"
echo "📋 Logs configurados: ${#SITES_LOGS[@]}"
