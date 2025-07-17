# Sistema de Monitoramento Híbrido

Monitoramento local de sites + Análise de Segurança em Tempo Real com Prometheus e Grafana

🌍 **Idioma:**
[English](README.md) | [Português](README-pt_br.md)

## 📊 Dashboards Principais

### 1. Prometheus Blackbox Exporter Dashboard*

- **Arquivo:** `dashboards/blackbox_exporter_dashboard.json`
- **Monitora:** Sites com Status, SSL, DNS Lookup e durações
- **Atualização:** Tempo real

### 2. Server Metrics Dashboard

- **Arquivo:** `dashboards/server_metrics_dashboard.json`
- **Monitora:** CPU, Memória, Disco, Inodes do servidor
- **Atualização:** A cada 5 minutos

### 3. Hybrid Security Dashboard

- **Arquivo:** `dashboards/hybrid_security_dashboard.json`
- **Monitora:** Segurança híbrida (externa + interna)
- **Atualização:** A cada 15 minutos

### 4. Real-Time Bot & Security Dashboard

- **Arquivo:** `dashboards/realtime_bot_dashboard.json`
- **Monitora:** Bots vs Usuários, Ataques, IPs suspeitos
- **Atualização:** A cada 2 minutos

## 🚀 Comandos de Controle

### Script Principal: `./monitor.sh`

```bash
# Iniciar todos os serviços
./monitor.sh start

# Parar todos os serviços
./monitor.sh stop

# Reiniciar sistema completo
./monitor.sh restart

# Ver status de todos os componentes
./monitor.sh status

# Ver logs dos serviços
./monitor.sh logs

# Testar funcionamento completo
./monitor.sh test

# Configurar início automático
./monitor.sh install-autostart

# Remover início automático
./monitor.sh uninstall-autostart
```

## 🔐 Configuração de Arquivos

**IMPORTANTE:** Antes de usar o sistema, clone este repositório e configure os arquivos de dados:

### 1. Clone o repositório

```bash
git clone https://github.com/rodineicosta/server-monitor.git
cd server-monitor
```

### 2. Configuração de Sites e SSH

```bash
# Copie o arquivo de exemplo
cp configs/sites.conf.example configs/sites.conf

# Edite com seus dados reais
nano configs/sites.conf
```

### 3. Configuração do Monitoramento em Tempo Real (Opcional)

```bash
# Copie o arquivo de exemplo
cp configs/realtime_config.json.example configs/realtime_config.json

# Edite com suas configurações
nano configs/realtime_config.json
```

### 4. Configuração de Crontab (Opcional)

```bash
# Edite o arquivo template
nano configs/crontab/crontab.txt

# Substitua [PROJECT_DIR] pelo caminho absoluto
# Substitua [SSH_SERVER] pelo seu servidor SSH
# Depois aplique: crontab configs/crontab/crontab.txt
```

**⚠️ SEGURANÇA:** Estes arquivos contêm dados sensíveis e **NÃO SÃO COMMITADOS** automaticamente.

## 🔧 Serviços Ativos

| Serviço | Porta | Função |
|---------|-------|--------|
| **Prometheus** | 9090 | Coleta e armazena métricas |
| **Pushgateway** | 9091 | Recebe métricas personalizadas |
| **Blackbox Exporter** | 9115 | Monitora sites externamente |
| **Monitor de Bots** | - | Análise de logs em tempo real |

## 📁 Estrutura

```
📊 dashboards/          # 4 dashboards Grafana principais
⚙️ configs/             # Configurações (prometheus.yml, blackbox.yml)
🔧 scripts/             # Scripts Python e Shell
📋 logs/                # Todos os arquivos de log
🔧 services/            # PIDs dos serviços rodando
```

## 🌐 URLs de Acesso

- **Prometheus:** http://localhost:9090
- **Pushgateway:** http://localhost:9091
- **Blackbox Exporter:** http://localhost:9115

## ⚡ Início Automático

O sistema pode ser configurado para **iniciar automaticamente** após reinicialização do macOS através do LaunchAgent.

### Para habilitar

```bash
./monitor.sh install-autostart
```

### Para desabilitar

```bash
./monitor.sh uninstall-autostart
```

### Controle manual

```bash
# Desabilitar temporariamente
launchctl unload ~/Library/LaunchAgents/com.monitoring.autostart.plist

# Reabilitar
launchctl load ~/Library/LaunchAgents/com.monitoring.autostart.plist
```

## 🔍 Monitoramento Ativo

### Métricas Coletadas

- **Uptime/Downtime** de todos os sites
- **Tempo de resposta** HTTP
- **Status SSL/TLS** e validade de certificados
- **Métricas do servidor** (CPU, RAM, Disco)
- **Análise de tráfego** (Bots vs Usuários)
- **Detecção de ataques** e IPs suspeitos
- **Score de segurança** híbrido (0-100)

## 📈 Análises Disponíveis

1. **Monitoramento Externo:** Via Blackbox Exporter
2. **Monitoramento Interno:** Via análise de logs
3. **Segurança Híbrida:** Combinação de ambos
4. **Detecção de Bots:** IA para classificar tráfego
5. **Alertas de Segurança:** Anomalias e ataques

## 🎯 Notificações

- **Grafana:** Alertas visuais nos dashboards
- **Sistema:** Logs detalhados para análise

## 🛡️ Recursos de Segurança

- **Zero exposição de dados sensíveis** no repositório
- **Arquivos de configuração externos** para dados sensíveis
- **Sistema baseado em templates** de configuração
- **Coleta real de logs SSH** com fallback para exemplos
- **Scripts portáveis** com caminhos relativos

## 🔧 Instalação

1. **Clone o repositório**
2. **Execute o setup:** `bash setup.sh`
3. **Configure os sites:** Copie e edite `configs/sites.conf.example`
4. **Inicie o monitoramento:** `./monitor.sh start`

---

- **Status:** ✅ Sistema totalmente operacional e automatizado
- **Última atualização:** 17 de julho de 2025
- **Autor:** [@rodineicosta](https://github.com/rodineicosta)
- **Licença:** [MIT](https://opensource.org/licenses/MIT)
