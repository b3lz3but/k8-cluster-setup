# Kubernetes Cluster Automation

An enterprise-grade Python script for automating Kubernetes cluster deployment and configuration on Ubuntu/Debian systems.

## Table of Contents
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Network Plugins](#network-plugins)
- [Security Features](#security-features)
- [Error Handling](#error-handling)
- [Backup and Recovery](#backup-and-recovery)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting Guide](#troubleshooting-guide)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Features
- Automated master and worker node setup
- Network plugin deployment and configuration
- System requirements validation
- Automated prerequisites installation
- Configuration management
- Health monitoring
- Backup and recovery
- Error handling with retries

### Advanced Features
- Custom network CIDR configuration
- Multiple network plugin support
- Automated swap management
- Command validation and sanitization
- Configuration versioning
- Cluster health diagnostics
- Resource monitoring

## System Requirements

### Hardware Requirements
- CPU: Minimum 2 cores (4+ recommended for production)
- RAM: Minimum 2GB (4GB+ recommended for production)
- Storage: 20GB+ available space
- Network: Stable internet connection

### Software Requirements
- Operating System:
  - Ubuntu 20.04+ LTS
  - Debian 10+
- Python 3.6+
- Required Packages:
  ```
  python3-pip
  python3-yaml
  python3-psutil
  ```

## Installation

### Basic Installation
```bash
# Clone repository
git clone https://github.com/your-org/kubernetes-automation.git
cd kubernetes-automation

# Install dependencies
pip3 install -r requirements.txt

# Verify installation
python3 k8s_setup.py --version
```

### Requirements File (requirements.txt)
```
PyYAML>=5.4.1
psutil>=5.8.0
ipaddress>=1.0.23
```

## Configuration

### Basic Configuration
Create `config.yml`:
```yaml
# Network Configuration
pod_network_cidr: "192.168.0.0/16"
network_plugin: "calico"

# Cluster Configuration
cluster_name: "production-cluster"
kubernetes_version: "1.21.0"

# Resource Limits
max_pods: 110
node_cidr_mask_size: 24

# Advanced Options
enable_monitoring: true
backup_enabled: true
retry_attempts: 3
command_timeout: 300
```

### Advanced Configuration Options

#### Network Configuration
```yaml
network:
  pod_network_cidr: "192.168.0.0/16"
  service_cidr: "10.96.0.0/12"
  dns_domain: "cluster.local"
  network_plugin: "calico"
  plugin_options:
    calico:
      ipv6_enabled: false
      mtu: 1440
    flannel:
      backend: "vxlan"
```

#### Security Configuration
```yaml
security:
  audit_logging: true
  pod_security_policy: true
  network_policies: true
  encryption_at_rest: true
```

## Usage

### Master Node Deployment
```bash
# Basic setup
sudo python3 k8s_setup.py --role master --config config.yml

# Advanced setup with custom options
sudo python3 k8s_setup.py --role master \
    --config config.yml \
    --pod-network-cidr "10.244.0.0/16" \
    --network-plugin flannel \
    --enable-monitoring
```

### Worker Node Deployment
```bash
# Join worker node
sudo python3 k8s_setup.py --role worker \
    --join-command "kubeadm join ..." \
    --config config.yml
```

### Common Operations
```bash
# Verify cluster health
python3 k8s_setup.py --health-check

# Backup configuration
python3 k8s_setup.py --backup

# Reset cluster
python3 k8s_setup.py --reset
```

## Network Plugins

### Supported Plugins
1. Calico
   - Default plugin
   - Advanced network policy support
   - IPv6 support
   - Configuration options:
     ```yaml
     calico_options:
       mtu: 1440
       ipv6: true
       cross_subnet: true
     ```

2. Flannel
   - Simplified networking
   - Multiple backend support
   - Configuration options:
     ```yaml
     flannel_options:
       backend: "vxlan"
       port: 8472
     ```

## Security Features

### Access Control
- Root access validation
- Secure file permissions (600 for sensitive files)
- Command injection prevention

### Network Security
- CIDR validation
- Network policy support
- Secure communication channels

### Configuration Security
- Backup encryption
- Secure token handling
- Certificate management

## Error Handling

### Retry Mechanism
```python
retry_config:
  max_attempts: 3
  delay: 5
  timeout: 300
```

### Error Categories
1. Installation Errors
   - Package installation failures
   - Dependency issues
   - Version conflicts

2. Network Errors
   - CIDR configuration issues
   - Plugin deployment failures
   - Connection timeouts

3. System Errors
   - Resource constraints
   - Permission issues
   - Configuration conflicts

## Backup and Recovery

### Backup Features
- Configuration backups
- Certificate backups
- State preservation
- Version control

### Recovery Procedures
1. Configuration Recovery
   ```bash
   python3 k8s_setup.py --restore-config <backup_path>
   ```

2. Cluster Reset
   ```bash
   python3 k8s_setup.py --reset --clean
   ```

## Monitoring and Health Checks

### Health Check Components
- Node status
- Pod health
- Network connectivity
- Resource utilization
- API server response

### Monitoring Features
- Resource tracking
- Performance metrics
- Error logging
- Alert generation

## Troubleshooting Guide

### Common Issues

1. Installation Failures
   ```bash
   # Verify system requirements
   python3 k8s_setup.py --check-requirements
   
   # Clean installation
   python3 k8s_setup.py --clean-install
   ```

2. Network Issues
   ```bash
   # Validate network configuration
   python3 k8s_setup.py --validate-network
   
   # Reset network configuration
   python3 k8s_setup.py --reset-network
   ```

3. Permission Issues
   ```bash
   # Check permissions
   python3 k8s_setup.py --check-permissions
   
   # Fix permissions
   python3 k8s_setup.py --fix-permissions
   ```

### Logging
- Location: `/var/log/k8s_setup.log`
- Log levels: INFO, WARNING, ERROR, CRITICAL
- Log rotation: 7 days

## API Reference

### Main Functions
```python
def initialize_master(config: Dict) -> None
def join_worker(join_command: str) -> None
def deploy_network(plugin: str) -> None
def check_health() -> Dict[str, bool]
def backup_config() -> str
def restore_config(backup_path: str) -> None
```

### Configuration Interface
```python
class ClusterConfig:
    def validate() -> bool
    def apply() -> None
    def backup() -> str
    def restore(backup_path: str) -> None
```

## Contributing

### Development Setup
1. Fork repository
2. Create virtual environment
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Testing
```bash
# Run tests
pytest tests/

# Run linting
flake8 .

# Run type checking
mypy .
```

### Pull Request Process
1. Update documentation
2. Add tests
3. Pass CI/CD checks
4. Get review approval

## License

MIT License

Copyright (c) 2024