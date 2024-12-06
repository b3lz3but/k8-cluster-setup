# Cross Distro Kubernetes Cluster Setup Script

A production-grade automation script for deploying and managing Kubernetes clusters across major Linux distributions with advanced monitoring, logging, and security features.

## Table of Contents
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Monitoring & Logging](#monitoring--logging)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [Support](#support)

## Features

### Core Features
- Multi-distribution support
  - Ubuntu (18.04+)
  - Debian (10+)
  - RHEL (7+)
  - CentOS (7+)
  - Fedora (32+)
  - SUSE Linux Enterprise (15+)
  - Arch Linux
- Automated system configuration
  - Kernel module management
  - Sysctl parameter optimization
  - Network configuration
  - Swap management
- Container runtime setup
  - Containerd installation
  - SystemdCgroup configuration
  - Runtime class configuration

### Network Features
- Multiple CNI plugin support
  - Calico (default)
  - Cilium
  - Flannel
- Network policy enforcement
- IPv4/IPv6 dual-stack support
- Custom CIDR configuration

### Monitoring & Observability
- Prometheus stack
  - Node exporter
  - kube-state-metrics
  - AlertManager
- Grafana dashboards
  - Node metrics
  - Pod metrics
  - Resource utilization
- EFK logging stack
  - Elasticsearch
  - Fluent Bit
  - Kibana

## System Requirements

### Hardware Requirements
- CPU:
  - Minimum: 2 cores
  - Recommended: 4+ cores
- Memory:
  - Minimum: 2GB
  - Recommended: 4GB+ (8GB+ for production)
- Disk:
  - Minimum: 20GB
  - Recommended: 50GB+ SSD

### Network Requirements
#### Required Ports
Control Plane:
- 6443: Kubernetes API server
- 2379-2380: etcd server client API
- 10250: Kubelet API
- 10257: kube-controller-manager
- 10259: kube-scheduler

Worker Nodes:
- 10250: Kubelet API
- 30000-32767: NodePort Services

### Software Requirements
- Python 3.8+
- Required packages:
  ```
  pip3 install -r requirements.txt
  ```

## Installation

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/k8s-setup
cd k8s-setup

# Install dependencies
pip3 install -r requirements.txt

# Create configuration
cp config.yml.example config.yml

# Setup control plane
sudo python3 k8s_setup.py --role master --config config.yml

# Setup worker nodes
sudo python3 k8s_setup.py --role worker --join-command "$(cat join-command.sh)"
```

### Dependencies
```txt
# requirements.txt
pyyaml>=6.0.1
psutil>=5.9.0
ipaddress>=1.0.23
requests>=2.28.0
```

## Configuration

### Basic Configuration
```yaml
# config.yml
pod_network_cidr: "192.168.0.0/16"
service_cidr: "10.96.0.0/12"
network_plugin: "calico"
kubernetes_version: "1.29.0"
enable_monitoring: true
enable_logging: false
```

### Advanced Configuration
```yaml
# advanced-config.yml
pod_network_cidr: "192.168.0.0/16"
service_cidr: "10.96.0.0/12"
network_plugin: "calico"
kubernetes_version: "1.29.0"

# Advanced features
enable_monitoring: true
enable_logging: true
enable_metrics_server: true
enable_dashboard: true

# Monitoring configuration
monitoring:
  prometheus:
    retention_days: 15
    storage_size: "50Gi"
  grafana:
    admin_password: "secure_password"
    plugins:
      - grafana-piechart-panel
      - grafana-kubernetes-app

# Logging configuration
logging:
  elasticsearch:
    replicas: 3
    storage_size: "100Gi"
  fluent_bit:
    buffer_size: "10MB"
  kibana:
    replicas: 2

# Security settings
security:
  network_policies: true
  pod_security_policies: true
  audit_logging: true
  encryption_at_rest: true

# Resource limits
resource_limits:
  control_plane:
    cpu: "2"
    memory: "4Gi"
  worker_nodes:
    cpu: "4"
    memory: "8Gi"
```

## Usage

### Basic Commands
```bash
# Control plane setup
sudo python3 k8s_setup.py --role master --config config.yml

# Worker node setup
sudo python3 k8s_setup.py --role worker --join-command "$(cat join-command.sh)"

# Enable verbose logging
sudo python3 k8s_setup.py --role master --config config.yml --verbose
```

### Advanced Usage Examples
```bash
# Custom configuration file
sudo python3 k8s_setup.py --role master --config custom-config.yml

# Specify alternate container runtime
sudo python3 k8s_setup.py --role master --config config.yml --container-runtime docker

# Skip monitoring setup
sudo python3 k8s_setup.py --role master --config config.yml --skip-monitoring

# Custom node labels
sudo python3 k8s_setup.py --role worker --join-command "$(cat join-command.sh)" --labels "node-type=compute,environment=prod"
```

## Architecture

### Component Overview
```
k8s_setup/
├── main.py
├── classes/
│   ├── system_info.py
│   ├── package_manager.py
│   ├── container_runtime.py
│   └── k8s_cluster.py
├── utils/
│   ├── command.py
│   └── validation.py
└── config/
    └── defaults.py
```

### Class Descriptions

#### SystemInfo
- System detection and validation
- Hardware resource checks
- Network configuration validation

#### PackageManager
- Distribution-specific package handling
- Repository management
- Dependency resolution

#### ContainerRuntime
- Runtime installation
- Configuration management
- System integration

#### K8sCluster
- Cluster initialization
- Component deployment
- State management

## Monitoring & Logging

### Prometheus Stack

#### Access Prometheus
```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Access: http://localhost:9090
```

#### Access Grafana
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
# Access: http://localhost:3000
# Default credentials: admin/prom-operator
```

#### Default Dashboards
- Node Overview
- Pod Resources
- Cluster Status
- Network Statistics

### EFK Stack

#### Access Kibana
```bash
kubectl port-forward -n logging svc/kibana 5601:5601
# Access: http://localhost:5601
```

#### Log Types
- Container logs
- System logs
- Audit logs
- Application logs

## Security

### Hardening Guide

1. API Server Security
```bash
# Enable audit logging
sudo vi /etc/kubernetes/audit-policy.yaml
kubectl apply -f audit-policy.yaml
```

2. Network Policies
```yaml
# default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

3. RBAC Configuration
```yaml
# restricted-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: restricted-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

### Security Checklist
- [ ] Change default passwords
- [ ] Enable RBAC
- [ ] Configure network policies
- [ ] Enable audit logging
- [ ] Implement pod security policies
- [ ] Regular security updates
- [ ] Certificate rotation
- [ ] Encryption at rest

## Troubleshooting

### Common Issues

1. Node Not Ready
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check system logs
journalctl -u kubelet

# Verify network plugin
kubectl get pods -n kube-system
```

2. Network Issues
```bash
# Check CNI pods
kubectl get pods -n kube-system -l k8s-app=calico-node

# Verify CNI configuration
ls /etc/cni/net.d/
cat /etc/cni/net.d/10-calico.conflist

# Test pod connectivity
kubectl run test-pod --image=busybox -- sleep 3600
kubectl exec test-pod -- ping 8.8.8.8
```

3. Monitoring Stack Issues
```bash
# Check Prometheus pods
kubectl get pods -n monitoring

# View Prometheus logs
kubectl logs -n monitoring prometheus-prometheus-operator-prometheus-0

# Check Grafana deployment
kubectl describe deployment -n monitoring prometheus-grafana
```

### Log Locations
- Script logs: `k8s_setup.log`
- Kubernetes logs: `/var/log/kubernetes/`
- Container runtime logs: `journalctl -u containerd`
- System logs: `journalctl -xeu kubelet`
- Audit logs: `/var/log/kubernetes/audit/`

### Debugging Tools
```bash
# Network debugging
kubectl run netshoot --rm -i --tty --image nicolaka/netshoot -- /bin/bash

# DNS debugging
kubectl run dnsutils --image=gcr.io/kubernetes-e2e-test-images/dnsutils:1.3

# Resource monitoring
kubectl top nodes
kubectl top pods --all-namespaces
```

## Advanced Usage

### Custom Configurations

#### High Availability Setup
```yaml
# ha-config.yml
control_plane:
  ha_enabled: true
  vip: "192.168.1.100"
  keepalived:
    interface: "eth0"
    virtual_router_id: 51
etcd:
  external: true
  endpoints:
    - "10.0.0.10:2379"
    - "10.0.0.11:2379"
    - "10.0.0.12:2379"
```

#### Custom Storage Class
```yaml
# storage-config.yml
storage:
  class_name: "fast-storage"
  provisioner: "kubernetes.io/aws-ebs"
  parameters:
    type: "gp2"
    fsType: "ext4"
```

### Integration Examples

#### Helm Integration
```python
def install_helm_charts():
    run_command("helm repo add stable https://charts.helm.sh/stable")
    run_command("helm repo update")
    
    # Install Ingress Controller
    run_command("""
    helm install nginx-ingress stable/nginx-ingress \
      --namespace ingress-nginx \
      --create-namespace \
      --set controller.replicaCount=2
    """)
```

#### Custom Metrics
```yaml
# custom-metrics.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-custom-metrics
data:
  custom-metrics.yaml: |
    - job_name: 'custom-endpoint'
      static_configs:
        - targets: ['custom-service:8080']
```

## Development

### Contributing Guidelines
1. Fork repository
2. Create feature branch
3. Follow coding standards:
   - Use type hints
   - Add docstrings
   - Write unit tests
4. Submit pull request

### Testing
```bash
# Run unit tests
python3 -m pytest tests/

# Run integration tests
./integration-tests.sh

# Run linting
flake8 .
mypy .
```

### Building Documentation
```bash
# Generate API documentation
sphinx-build -b html docs/source/ docs/build/html

# Build distribution package
python3 setup.py sdist bdist_wheel
```

## Support

### Community Resources
- GitHub Issues
- Stack Overflow Tags
- Community Forums
- Documentation Wiki

### Commercial Support
- Enterprise Support Options
- Training Services
- Consulting Services

### Reporting Issues
1. Check existing issues
2. Include system information
3. Provide logs
4. Create reproducible example

## License

MIT License - See LICENSE file for details

## Authors

Original Author: [Your Name]
Contributors: [List of Contributors]

---

For more information, visit our [documentation](https://your-docs-url.com).