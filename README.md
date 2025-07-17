# Hybrid Monitoring System

Monitoring for websites + Real-Time Security Analysis with Prometheus and Grafana

🌍 **Language:**
[English](README.md) | [Portuguese](README-pt_br.md)

## 📊 Main Dashboards

### 1. Prometheus Blackbox Exporter Dashboard

- **File:** `dashboards/blackbox_exporter_dashboard.json`
- **Monitors:** Sites with Status, SSL, DNS Lookup and response times
- **Updates:** Real-time###

### 2. Server Metrics Dashboard

- **File:** `dashboards/server_metrics_dashboard.json`
- **Monitors:** CPU, Memory, Disk, Server inodes
- **Updates:** Every 5 minutes###

### 3. Hybrid Security Dashboard

- **File:** `dashboards/hybrid_security_dashboard.json`
- **Monitors:** Hybrid security (external + internal)
- **Updates:** Every 15 minutes###

### 4. Real-Time Bot & Security Dashboard

- **File:** `dashboards/realtime_bot_dashboard.json`
- **Monitors:** Bots vs Users, Attacks, Suspicious IPs
- **Updates:** Every 2 minutes

## 🚀 Control Commands

### Main Script: `./monitor.sh`

```bash
# Start all services
./monitor.sh start

# Stop all services
./monitor.sh stop

# Restart complete system
./monitor.sh restart

# View status of all components
./monitor.sh status

# View service logs
./monitor.sh logs

# Test complete functionality
./monitor.sh test

# Configure automatic startup
./monitor.sh install-autostart

# Remove automatic startup
./monitor.sh uninstall-autostart
```

## 🔐 Configuration Setup

**IMPORTANT:** Before using the system, clone the repository and configure the data files:

### 1. Clone the repository

```bash
git clone https://github.com/rodineicosta/server-monitor.git
cd server-monitor
```

### 2. Sites and SSH Configuration

```bash
# Copy the example file
cp configs/sites.conf.example configs/sites.conf

# Edit with your real data
nano configs/sites.conf
```

### 3. Real-Time Monitoring Configuration (Optional)

```bash
# Copy the example file
cp configs/realtime_config.json.example configs/realtime_config.json

# Edit with your configurations
nano configs/realtime_config.json
```

### 4. Crontab Configuration (Optional)

```bash
# Edit the template file
nano configs/crontab/crontab.txt

# Replace [PROJECT_DIR] with absolute path
# Replace [SSH_SERVER] with your SSH server
# Then apply: crontab configs/crontab/crontab.txt
```

**⚠️ SECURITY:** These files contain sensitive data and are **NOT COMMITTED** automatically.

## 🔧 Active Services

| Service | Port | Function |
|---------|------|----------|
| **Prometheus** | 9090 | Collects and stores metrics |
| **Pushgateway** | 9091 | Receives custom metrics |
| **Blackbox Exporter** | 9115 | Monitors sites externally |
| **Bot Monitor** | - | Real-time log analysis |

## 📁 Project Structure

```
📊 dashboards/          # 4 main Grafana dashboards
⚙️ configs/             # Configurations (prometheus.yml, blackbox.yml)
🔧 scripts/             # Python and Shell scripts
📋 logs/                # All log files
🔧 services/            # Running service PIDs
```

## 🌐 Access URLs

- **Prometheus:** http://localhost:9090
- **Pushgateway:** http://localhost:9091
- **Blackbox Exporter:** http://localhost:9115

## ⚡ Automatic Startup

The system can be configured to **start automatically** after macOS reboot through LaunchAgent.

### To enable:
```bash
./monitor.sh install-autostart
```

### To disable:
```bash
./monitor.sh uninstall-autostart
```

### Manual control:
```bash
# Disable temporarily
launchctl unload ~/Library/LaunchAgents/com.monitoring.autostart.plist

# Re-enable
launchctl load ~/Library/LaunchAgents/com.monitoring.autostart.plist
```

## 🔍 Active Monitoring

### Collected Metrics

- **Uptime/Downtime** of all sites
- **HTTP response time**
- **SSL/TLS status** and certificate validity
- **Server metrics** (CPU, RAM, Disk)
- **Traffic analysis** (Bots vs Users)
- **Attack detection** and suspicious IPs
- **Hybrid security score** (0-100)

## 📈 Available Analysis

1. **External Monitoring:** Via Blackbox Exporter
2. **Internal Monitoring:** Via log analysis
3. **Hybrid Security:** Combination of both
4. **Bot Detection:** AI to classify traffic
5. **Security Alerts:** Anomalies and attacks

## 🎯 Notifications

- **Grafana:** Visual alerts in dashboards
- **System:** Detailed logs for analysis

## 🛡️ Security Features

- **Zero sensitive data exposure** in repository
- **External configuration files** for sensitive data
- **Template-based configuration** system
- **Real SSH log collection** with fallback to examples
- **Portable scripts** with relative paths

## 🔧 Installation

1. **Clone the repository**
2. **Run setup:** `bash setup.sh`
3. **Configure sites:** Copy and edit `configs/sites.conf.example`
4. **Start monitoring:** `./monitor.sh start`

---

- **Status:** ✅ System fully operational and automated
- **Last update:** July 17, 2025
- **Author:** [@rodineicosta](https://github.com/rodineicosta)
- **License:** [MIT](https://opensource.org/licenses/MIT)
