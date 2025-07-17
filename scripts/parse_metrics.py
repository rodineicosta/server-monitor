#!/usr/bin/env python3
# Script Python para parsear metrics.txt e enviar ao Prometheus
import re
import os
from prometheus_client import push_to_gateway, Gauge, CollectorRegistry

def parse_metrics():
    """Parse metrics.txt file and return extracted metrics"""
    # Usar caminho relativo baseado no diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    metrics_file = os.path.join(project_dir, 'logs', 'metrics.txt')

    if not os.path.exists(metrics_file):
        print(f"Error: {metrics_file} not found")
        return None

    try:
        with open(metrics_file, 'r') as f:
            content = f.read()

        metrics = {}

        # Parse memory information (free -m output)
        mem_match = re.search(r'Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', content)
        if mem_match:
            metrics['mem_total'] = int(mem_match.group(1))
            metrics['mem_used'] = int(mem_match.group(2))
            metrics['mem_free'] = int(mem_match.group(3))
            metrics['mem_shared'] = int(mem_match.group(4))
            metrics['mem_buff_cache'] = int(mem_match.group(5))
            metrics['mem_available'] = int(mem_match.group(6))

        # Parse swap information
        swap_match = re.search(r'Swap:\s+(\d+)\s+(\d+)\s+(\d+)', content)
        if swap_match:
            metrics['swap_total'] = int(swap_match.group(1))
            metrics['swap_used'] = int(swap_match.group(2))
            metrics['swap_free'] = int(swap_match.group(3))

        # Parse vmstat information (last line of vmstat output)
        vmstat_lines = [line for line in content.split('\n') if line.strip() and not line.startswith('procs') and not line.startswith(' r')]
        if len(vmstat_lines) >= 2:  # Get the second line (actual data)
            vmstat_data = vmstat_lines[1].split()
            if len(vmstat_data) >= 17:
                metrics['procs_running'] = int(vmstat_data[0])
                metrics['procs_blocked'] = int(vmstat_data[1])
                metrics['memory_swpd'] = int(vmstat_data[2])
                metrics['memory_free_kb'] = int(vmstat_data[3])
                metrics['memory_buff'] = int(vmstat_data[4])
                metrics['memory_cache'] = int(vmstat_data[5])
                metrics['cpu_us'] = int(vmstat_data[12])
                metrics['cpu_sy'] = int(vmstat_data[13])
                metrics['cpu_id'] = int(vmstat_data[14])
                metrics['cpu_wa'] = int(vmstat_data[15])

        # Parse disk inodes information
        inode_matches = re.findall(r'/dev/\w+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(.+)', content)
        if inode_matches:
            # Take the first disk (usually root)
            inodes_total, inodes_used, inodes_free, inodes_usage, mount_point = inode_matches[0]
            metrics['inodes_total'] = int(inodes_total)
            metrics['inodes_used'] = int(inodes_used)
            metrics['inodes_free'] = int(inodes_free)
            metrics['inodes_usage_percent'] = int(inodes_usage)

        return metrics

    except Exception as e:
        print(f"Error parsing metrics: {e}")
        return None

def send_to_prometheus():
    """Send parsed metrics to Prometheus via Pushgateway"""
    metrics = parse_metrics()

    if not metrics:
        print("No metrics to send")
        return False

    try:
        # Create a new registry to avoid conflicts
        registry = CollectorRegistry()

        # Create gauges for each metric
        gauges = {}

        # Memory metrics (MB)
        if 'mem_total' in metrics:
            gauges['mem_total'] = Gauge('server_memory_total_mb', 'Total memory in MB', registry=registry)
            gauges['mem_total'].set(metrics['mem_total'])

        if 'mem_used' in metrics:
            gauges['mem_used'] = Gauge('server_memory_used_mb', 'Used memory in MB', registry=registry)
            gauges['mem_used'].set(metrics['mem_used'])

        if 'mem_free' in metrics:
            gauges['mem_free'] = Gauge('server_memory_free_mb', 'Free memory in MB', registry=registry)
            gauges['mem_free'].set(metrics['mem_free'])

        if 'mem_available' in metrics:
            gauges['mem_available'] = Gauge('server_memory_available_mb', 'Available memory in MB', registry=registry)
            gauges['mem_available'].set(metrics['mem_available'])

        # CPU metrics (percentage)
        if 'cpu_us' in metrics:
            gauges['cpu_user'] = Gauge('server_cpu_user_percent', 'CPU user percentage', registry=registry)
            gauges['cpu_user'].set(metrics['cpu_us'])

        if 'cpu_sy' in metrics:
            gauges['cpu_system'] = Gauge('server_cpu_system_percent', 'CPU system percentage', registry=registry)
            gauges['cpu_system'].set(metrics['cpu_sy'])

        if 'cpu_id' in metrics:
            gauges['cpu_idle'] = Gauge('server_cpu_idle_percent', 'CPU idle percentage', registry=registry)
            gauges['cpu_idle'].set(metrics['cpu_id'])

        if 'cpu_wa' in metrics:
            gauges['cpu_wait'] = Gauge('server_cpu_wait_percent', 'CPU wait percentage', registry=registry)
            gauges['cpu_wait'].set(metrics['cpu_wa'])

        # Process metrics
        if 'procs_running' in metrics:
            gauges['procs_running'] = Gauge('server_processes_running', 'Running processes', registry=registry)
            gauges['procs_running'].set(metrics['procs_running'])

        if 'procs_blocked' in metrics:
            gauges['procs_blocked'] = Gauge('server_processes_blocked', 'Blocked processes', registry=registry)
            gauges['procs_blocked'].set(metrics['procs_blocked'])

        # Inode metrics
        if 'inodes_usage_percent' in metrics:
            gauges['inodes_usage'] = Gauge('server_inodes_usage_percent', 'Inodes usage percentage', registry=registry)
            gauges['inodes_usage'].set(metrics['inodes_usage_percent'])

        # Send to Pushgateway
        push_to_gateway('localhost:9091', job='server-metrics', registry=registry)

        print(f"Successfully sent {len(gauges)} metrics to Prometheus")
        print("Metrics sent:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"Error sending metrics to Prometheus: {e}")
        return False

if __name__ == "__main__":
    send_to_prometheus()