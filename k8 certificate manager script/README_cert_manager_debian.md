# Kubernetes Certificate Management Tool

A comprehensive automation tool for managing Kubernetes cluster certificates with enterprise-grade features for certificate lifecycle management.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Certificate Operations](#certificate-operations)
- [Monitoring & Alerts](#monitoring--alerts)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [Support](#support)


## Introduction

The Kubernetes Certificate Management Tool is designed to automate the lifecycle management of Kubernetes certificates. It provides features for generating, renewing, verifying, and backing up certificates, along with monitoring and alerting capabilities.

## Features

### Core Features

- Automated certificate lifecycle management
  - Generation of new certificates
  - Certificate renewal automation
  - Expiration monitoring
  - Health verification
- Backup management
  - Automated backups
  - Configurable retention policies
  - Secure backup storage
- Monitoring and alerts
  - Multi-channel notifications
  - Configurable warning thresholds
  - Detailed health checks

### Advanced Features

- Custom certificate configurations
- Integration with external PKI systems
- Automatic recovery procedures
- Audit logging
- Certificate rotation scheduling
- High availability support

## Requirements

### System Requirements

- Operating System:
  - Ubuntu 20.04+ (recommended)
  - Debian 10+
  - RHEL/CentOS 7+
- Memory: 512MB minimum
- Disk Space: 1GB+ for backups
- Network: Outbound access for notifications

### Software Dependencies

```bash
# Core dependencies
kubeadm
kubectl
openssl
rsync

# Notification dependencies
mailutils
curl

# Optional dependencies
jq              # JSON processing
yamllint        # YAML validation
cfssl           # Additional certificate tools
```

### Kubernetes Requirements

- Kubernetes 1.19+
- Access to cluster PKI directory
- kubeadm configuration access
- Cluster admin privileges

## Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/k8s-cert-management
cd k8s-cert-management

# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y kubeadm openssl rsync mailutils curl

# Set up configuration
sudo cp config/k8s_cert_script.conf.example /etc/k8s_cert_script.conf
sudo chmod 600 /etc/k8s_cert_script.conf

# Make script executable
chmod +x k8s_certificate_management.sh
```

### Advanced Installation

```bash
# Create secure backup directory
sudo mkdir -p /etc/kubernetes/pki/backup
sudo chmod 700 /etc/kubernetes/pki/backup

# Set up logging
sudo mkdir -p /var/log/k8s_cert_management
sudo chown $(whoami):$(whoami) /var/log/k8s_cert_management

# Install additional tools
sudo apt-get install -y jq yamllint cfssl

# Configure systemd service (optional)
sudo cp systemd/k8s-cert-management.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable k8s-cert-management
```

## Configuration

### Basic Configuration

```bash
# /etc/k8s_cert_script.conf
expiration_warning_days=30
retention_days=90
backup_dir="/etc/kubernetes/pki/backup"
log_level="INFO"
```

### Advanced Configuration

```bash
# /etc/k8s_cert_script.conf
# Certificate settings
expiration_warning_days=30
retention_days=90
min_key_size=2048
preferred_chain_length=3

# Directory settings
backup_dir="/etc/kubernetes/pki/backup"
temp_dir="/tmp/k8s_cert_ops"
log_dir="/var/log/k8s_cert_management"

# Notification settings
notification_email="admin@example.com"
slack_webhook_url="https://hooks.slack.com/services/xxx"
teams_webhook_url="https://outlook.office.com/webhook/xxx"

# Advanced settings
backup_compression=true
backup_encryption=true
encryption_key_file="/etc/kubernetes/pki/backup-encryption-key"
concurrent_backups=3
health_check_interval=3600

# HA settings
ha_enabled=true
ha_nodes=["node1:6443", "node2:6443", "node3:6443"]
```

### Environment Variables

```bash
# Notification settings
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/xxx"
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="notifications@example.com"
export SMTP_PASSWORD="secure_password"

# Authentication settings
export KUBECONFIG="/etc/kubernetes/admin.conf"
export PKI_DIR="/etc/kubernetes/pki"
```

## Usage

### Interactive Mode

```bash
sudo ./k8s_certificate_management.sh
```

### Command Line Operations

```bash
# Basic operations
sudo ./k8s_certificate_management.sh generate
sudo ./k8s_certificate_management.sh renew
sudo ./k8s_certificate_management.sh verify
sudo ./k8s_certificate_management.sh backup

# Advanced operations
sudo ./k8s_certificate_management.sh check-health --detailed
sudo ./k8s_certificate_management.sh rotate --component etcd
sudo ./k8s_certificate_management.sh restore --backup-id 20240305-120000
```

### Automation Examples

```bash
# Cron job for daily health check
0 0 * * * /path/to/k8s_certificate_management.sh check-health >> /var/log/cert-health.log 2>&1

# Weekly backup
0 0 * * 0 /path/to/k8s_certificate_management.sh backup --compress --encrypt
```

## Certificate Operations

### Generation

```bash
# Generate all certificates
sudo ./k8s_certificate_management.sh generate

# Generate specific certificate
sudo ./k8s_certificate_management.sh generate --component apiserver
```

### Renewal

```bash
# Renew all certificates
sudo ./k8s_certificate_management.sh renew

# Renew specific certificate
sudo ./k8s_certificate_management.sh renew --component etcd
```

### Verification

```bash
# Check expiration
sudo ./k8s_certificate_management.sh verify

# Detailed certificate info
sudo ./k8s_certificate_management.sh detailed-info
```

### Backup

```bash
# Create backup
sudo ./k8s_certificate_management.sh backup

# Restore from backup
sudo ./k8s_certificate_management.sh restore --backup-id 20240305-120000
```

## Monitoring & Alerts

### Health Checks

```bash
# Basic health check
sudo ./k8s_certificate_management.sh check-health

# Detailed health analysis
sudo ./k8s_certificate_management.sh check-health --detailed --output-format json
```

### Notification Configuration

```yaml
# notifications.yaml
email:
  enabled: true
  recipients:
    - admin@example.com
    - ops@example.com
  alerts:
    - expiration
    - health_check
    - backup_failure

slack:
  enabled: true
  channels:
    - "#k8s-alerts"
    - "#ops-critical"
  mention_users:
    - "@oncall"

teams:
  enabled: true
  channels:
    - "Kubernetes Operations"
```

## Security

### Best Practices

1. File Permissions

```bash
# Certificate files
sudo chmod 600 /etc/kubernetes/pki/*.key
sudo chmod 644 /etc/kubernetes/pki/*.crt

# Backup directory
sudo chmod 700 /etc/kubernetes/pki/backup
```

2. Encryption

```bash
# Generate encryption key
sudo openssl rand -base64 32 > /etc/kubernetes/pki/backup-encryption-key
sudo chmod 600 /etc/kubernetes/pki/backup-encryption-key

# Enable backup encryption
echo "backup_encryption=true" >> /etc/k8s_cert_script.conf
```

3. Access Control

```bash
# Create dedicated service account
sudo useradd -r -s /bin/false cert-manager
sudo chown -R cert-manager:cert-manager /etc/kubernetes/pki/backup
```

## Troubleshooting

### Common Issues

1. Certificate Generation Failures

```bash
# Check PKI directory permissions
ls -la /etc/kubernetes/pki/

# Verify kubeadm configuration
kubeadm config print init-defaults

# Check system requirements
openssl version
kubeadm version
```

```bash
2. Backup Failures

# Check disk space
df -h /etc/kubernetes/pki/backup

# Verify backup permissions
ls -la /etc/kubernetes/pki/backup

# Test backup command manually
sudo rsync -av --delete /etc/kubernetes/pki/ /etc/kubernetes/pki/backup/test/
```

3. Notification Issues

```bash
# Test email
echo "Test" | mail -s "Test Alert" admin@example.com

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' $SLACK_WEBHOOK_URL

# Check logs
tail -f /var/log/k8s_cert_management.log
```

### Logging

```bash
# Enable debug logging
sed -i 's/log_level=.*/log_level=DEBUG/' /etc/k8s_cert_script.conf

# View logs
tail -f /var/log/k8s_cert_management.log

# Rotate logs
logrotate /etc/logrotate.d/k8s-cert-management
```

## Advanced Usage

### Custom Certificate Configurations

```yaml
# custom-cert-config.yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
certificatesDir: /etc/kubernetes/pki
etcd:
  local:
    extraArgs:
      cert-file: /etc/kubernetes/pki/etcd/server.crt
      key-file: /etc/kubernetes/pki/etcd/server.key
```

### High Availability Setup

```bash
# Configure HA nodes
sudo ./k8s_certificate_management.sh configure-ha --nodes "node1,node2,node3"

# Synchronize certificates
sudo ./k8s_certificate_management.sh sync-certificates --target node2
```

### Integration Examples

```bash
# External PKI integration
sudo ./k8s_certificate_management.sh integrate-pki \
  --ca-url "https://ca.example.com" \
  --auth-token "token123"

# Monitoring integration
sudo ./k8s_certificate_management.sh configure-monitoring \
  --prometheus-url "http://prometheus:9090" \
  --grafana-url "http://grafana:3000"
```

## Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/your-org/k8s-cert-management
cd k8s-cert-management

# Run tests
./run-tests.sh

# Build documentation
make docs
```

### Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

### Testing

```bash
# Unit tests
./test/run-unit-tests.sh

# Integration tests
./test/run-integration-tests.sh

# End-to-end tests
./test/run-e2e-tests.sh
```
