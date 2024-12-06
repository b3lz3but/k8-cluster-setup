# Kubernetes Certificate Management Script

A robust, enterprise-grade tool for managing Kubernetes cluster certificates across all Linux distributions with comprehensive backup, monitoring, and notification capabilities.

## Table of Contents
- [Kubernetes Certificate Management Script](#kubernetes-certificate-management-script)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Purpose](#purpose)
    - [Key Benefits](#key-benefits)
  - [Features](#features)
    - [Certificate Management](#certificate-management)
    - [Backup System](#backup-system)
    - [Notification System](#notification-system)
  - [System Requirements](#system-requirements)
    - [Hardware Requirements](#hardware-requirements)
    - [Software Requirements](#software-requirements)
    - [Network Requirements](#network-requirements)
  - [Installation](#installation)
    - [Quick Start](#quick-start)
    - [Advanced Installation](#advanced-installation)
      - [Custom Installation Path](#custom-installation-path)
      - [Systemd Service Setup](#systemd-service-setup)
      - [Cron Job Setup](#cron-job-setup)
  - [Configuration](#configuration)
    - [Basic Configuration](#basic-configuration)
    - [Advanced Configuration](#advanced-configuration)
      - [Notification Settings](#notification-settings)
      - [Backup Configuration](#backup-configuration)
      - [Advanced Certificate Settings](#advanced-certificate-settings)
  - [Usage](#usage)
    - [Interactive Mode](#interactive-mode)
    - [CLI Operations](#cli-operations)
      - [Basic Operations](#basic-operations)
      - [Advanced Operations](#advanced-operations)
  - [Certificate Operations](#certificate-operations)
    - [Generation Process](#generation-process)
    - [Certificate Types](#certificate-types)
    - [Renewal Process](#renewal-process)
    - [Verification Operations](#verification-operations)
  - [Backup Management](#backup-management)
    - [Backup Strategy](#backup-strategy)
    - [Retention Policy](#retention-policy)
    - [Restore Operations](#restore-operations)
  - [Monitoring \& Alerts](#monitoring--alerts)
    - [Monitoring Setup](#monitoring-setup)
    - [Alert Configuration](#alert-configuration)
    - [Metrics Collection](#metrics-collection)
  - [Security Considerations](#security-considerations)
    - [Access Control](#access-control)
    - [Encryption](#encryption)
    - [Security Best Practices](#security-best-practices)
  - [Troubleshooting Guide](#troubleshooting-guide)
    - [Common Issues](#common-issues)
    - [Log Analysis](#log-analysis)
    - [Health Checks](#health-checks)
  - [Advanced Usage](#advanced-usage)
    - [Custom Certificates](#custom-certificates)
    - [Integration Examples](#integration-examples)
    - [Automation Scripts](#automation-scripts)
  - [Development](#development)
    - [Building from Source](#building-from-source)
    - [Testing](#testing)
    - [Contributing Guidelines](#contributing-guidelines)
  - [Support \& Maintenance](#support--maintenance)
    - [Regular Maintenance](#regular-maintenance)
    - [Backup Maintenance](#backup-maintenance)
  - [License](#license)

## Overview

### Purpose
This script automates the complete lifecycle management of Kubernetes certificates, including generation, renewal, verification, and backup operations across different Linux distributions.

### Key Benefits
- Automated certificate management
- Cross-distribution compatibility
- Robust backup system
- Multi-channel notifications
- Comprehensive logging
- Security-focused design

## Features

### Certificate Management
- **Generation**
  - Complete certificate suite creation
  - Custom certificate parameters
  - Automated validation
  - Integration with existing PKI

- **Renewal**
  - Automated renewal process
  - Pre-expiry notifications
  - Rolling updates support
  - Backup before renewal

- **Verification**
  - Expiration monitoring
  - Certificate chain validation
  - Key usage verification
  - Health checks

### Backup System
- **Automated Backups**
  - Pre-operation backups
  - Scheduled backups
  - Incremental backups
  - Compression support

- **Retention Management**
  - Configurable retention periods
  - Automated cleanup
  - Space monitoring
  - Backup validation

### Notification System
- **Channels**
  - Email notifications
  - Slack integration
  - Microsoft Teams integration
  - Custom webhook support

- **Alert Types**
  - Expiration warnings
  - Operation results
  - Health check alerts
  - Backup status

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM recommended
- **Storage**: 
  - System: 10GB+ free space
  - Backup: 20GB+ recommended
  - Log storage: 5GB+ recommended

### Software Requirements
- **Operating System**
  - Ubuntu 18.04+
  - Debian 10+
  - RHEL/CentOS 7+
  - Fedora 30+
  - Arch Linux (latest)

- **Required Packages**
  ```bash
  kubeadm (1.19+)
  kubectl (1.19+)
  openssl (1.1.1+)
  rsync (3.1+)
  mail
  curl
  ```

- **Optional Packages**
  ```bash
  jq (JSON processing)
  yq (YAML processing)
  gpg (encryption)
  ```

### Network Requirements
- Outbound internet access for package installation
- Access to notification endpoints (SMTP, Slack, Teams)
- Cluster API server access
- Node-to-node communication for HA setups

## Installation

### Quick Start
```bash
# Clone repository
git clone https://github.com/org/k8s-cert-management
cd k8s-cert-management

# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y kubeadm kubectl openssl rsync mailutils curl

# Set up configuration
sudo mkdir -p /etc/kubernetes/cert-management
sudo cp config.example.conf /etc/k8s_cert_script.conf
sudo chmod 600 /etc/k8s_cert_script.conf

# Set up logging
sudo mkdir -p /var/log/k8s_cert_management
sudo chmod 750 /var/log/k8s_cert_management

# Make script executable
chmod +x k8s_certificate_management.sh
```

### Advanced Installation

#### Custom Installation Path
```bash
# Create dedicated directory
sudo mkdir -p /opt/k8s-cert-management
sudo cp k8s_certificate_management.sh /opt/k8s-cert-management/
sudo ln -s /opt/k8s-cert-management/k8s_certificate_management.sh /usr/local/bin/k8s-cert-manage
```

#### Systemd Service Setup
```bash
# Create service file
cat << EOF | sudo tee /etc/systemd/system/k8s-cert-management.service
[Unit]
Description=Kubernetes Certificate Management Service
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/k8s-cert-management/k8s_certificate_management.sh verify
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable k8s-cert-management
```

#### Cron Job Setup
```bash
# Add daily certificate check
echo "0 0 * * * root /opt/k8s-cert-management/k8s_certificate_management.sh verify >> /var/log/k8s_cert_management/daily-check.log 2>&1" | sudo tee /etc/cron.d/k8s-cert-check
```

## Configuration

### Basic Configuration
```bash
# /etc/k8s_cert_script.conf
# Certificate settings
expiration_warning_days=30
retention_days=90
min_cert_validity_days=7

# Directory settings
backup_dir="/etc/kubernetes/pki/backup"
cert_dir="/etc/kubernetes/pki"
etcd_cert_dir="/etc/kubernetes/pki/etcd"

# Logging settings
log_file="/var/log/k8s_cert_management.log"
log_level="INFO"
log_max_size="100M"
log_max_files=10

# Notification settings
admin_email="admin@example.com"
notification_prefix="[K8s Cert Alert]"
```

### Advanced Configuration

#### Notification Settings
```bash
# Email configuration
smtp_server="smtp.example.com"
smtp_port=587
smtp_user="notifications@example.com"
smtp_password="secure_password"
smtp_use_tls=true

# Slack configuration
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"
slack_channel="#k8s-alerts"
slack_username="K8s Cert Bot"

# Teams configuration
TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/xxx"
```

#### Backup Configuration
```bash
# Backup settings
backup_compression=true
backup_encryption=true
encryption_key_file="/etc/kubernetes/pki/backup-encryption-key"
max_concurrent_backups=3
backup_retention_count=10

# Backup schedule
backup_schedule="0 0 * * *"
cleanup_schedule="0 1 * * 0"
```

#### Advanced Certificate Settings
```bash
# Certificate parameters
cert_key_size=4096
cert_sig_algorithm="sha512WithRSAEncryption"
cert_country="US"
cert_state="California"
cert_locality="San Francisco"
cert_org="Example Org"
cert_org_unit="DevOps"
```

## Usage

### Interactive Mode
```bash
sudo k8s-cert-manage
```

### CLI Operations

#### Basic Operations
```bash
# Generate certificates
sudo k8s-cert-manage generate

# Renew certificates
sudo k8s-cert-manage renew

# Verify certificates
sudo k8s-cert-manage verify

# Backup certificates
sudo k8s-cert-manage backup
```

#### Advanced Operations
```bash
# Check specific certificate
sudo k8s-cert-manage check-health --cert apiserver

# Rotate specific certificate
sudo k8s-cert-manage rotate --component etcd

# Force renewal
sudo k8s-cert-manage renew --force

# Restore from backup
sudo k8s-cert-manage restore --backup-id 20240305-120000
```

## Certificate Operations

### Generation Process
```bash
# Generate all certificates
sudo k8s-cert-manage generate --all

# Generate specific certificates
sudo k8s-cert-manage generate --component apiserver,etcd
```

### Certificate Types
- **Core Certificates**
  - API Server (`apiserver.crt`)
  - Controller Manager (`controller-manager.crt`)
  - Scheduler (`scheduler.crt`)
  - Kubelet (`kubelet.crt`)

- **ETCD Certificates**
  - Server (`etcd/server.crt`)
  - Peer (`etcd/peer.crt`)
  - Client (`etcd/client.crt`)

- **Service Account**
  - Private key (`sa.key`)
  - Public key (`sa.pub`)

### Renewal Process
```bash
# Check expiration status
sudo k8s-cert-manage verify

# Renew specific certificate
sudo k8s-cert-manage renew --component apiserver

# Force renewal
sudo k8s-cert-manage renew --force --component etcd
```

### Verification Operations
```bash
# Comprehensive health check
sudo k8s-cert-manage check-health --verbose

# Certificate chain validation
sudo k8s-cert-manage verify --chain

# Export certificate details
sudo k8s-cert-manage detailed-info --output json > cert-details.json
```

## Backup Management

### Backup Strategy
- **Pre-operation Backups**
  ```bash
  # Manual backup
  sudo k8s-cert-manage backup --compress
  
  # Encrypted backup
  sudo k8s-cert-manage backup --encrypt --key /path/to/key
  ```

- **Scheduled Backups**
  ```bash
  # Configure cron job
  echo "0 0 * * * root /usr/local/bin/k8s-cert-manage backup --compress" | sudo tee /etc/cron.d/k8s-cert-backup
  ```

### Retention Policy
```bash
# Set retention period
sudo k8s-cert-manage config set retention_days 90

# Clean old backups
sudo k8s-cert-manage cleanup-old-backups --dry-run
sudo k8s-cert-manage cleanup-old-backups --force
```

### Restore Operations
```bash
# List available backups
sudo k8s-cert-manage backup list

# Restore specific backup
sudo k8s-cert-manage restore --backup-id 20240305-120000

# Verify restored certificates
sudo k8s-cert-manage verify --after-restore
```

## Monitoring & Alerts

### Monitoring Setup
```yaml
# monitoring-config.yaml
monitoring:
  enabled: true
  interval: 3600
  metrics:
    - certificate_expiration
    - backup_status
    - operation_status
```

### Alert Configuration
```yaml
# alerts-config.yaml
alerts:
  email:
    enabled: true
    recipients:
      - admin@example.com
      - ops@example.com
    triggers:
      - expiration_warning
      - backup_failure
      - health_check_failure

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
      - "K8s Operations"
```

### Metrics Collection
```bash
# Enable Prometheus metrics
sudo k8s-cert-manage monitoring enable --prometheus

# Configure custom metrics
sudo k8s-cert-manage monitoring add-metric --name cert_rotation_success_rate
```

## Security Considerations

### Access Control
```bash
# Set secure permissions
sudo chmod 600 /etc/kubernetes/pki/*.key
sudo chmod 644 /etc/kubernetes/pki/*.crt
sudo chown -R root:root /etc/kubernetes/pki

# Audit access
sudo k8s-cert-manage audit --report
```

### Encryption
```bash
# Generate encryption key
sudo openssl rand -base64 32 > /etc/kubernetes/pki/backup-encryption-key

# Enable backup encryption
sudo k8s-cert-manage config set backup_encryption true
```

### Security Best Practices
1. **Certificate Management**
   - Regular rotation schedule
   - Minimum 2048-bit keys
   - Secure private key storage
   - Access logging

2. **Backup Security**
   - Encrypted backups
   - Secure transfer protocols
   - Access control
   - Audit trails

3. **Operational Security**
   - Principle of least privilege
   - Multi-factor authentication
   - Secure communication channels
   - Regular security audits

## Troubleshooting Guide

### Common Issues

1. **Certificate Generation Failures**
   ```bash
   # Check prerequisites
   sudo k8s-cert-manage check-prereqs
   
   # Verify configuration
   sudo k8s-cert-manage verify-config
   
   # Debug certificate generation
   sudo k8s-cert-manage generate --debug
   ```

2. **Renewal Issues**
   ```bash
   # Check certificate status
   sudo k8s-cert-manage verify --verbose
   
   # Force renewal
   sudo k8s-cert-manage renew --force
   ```

3. **Backup Failures**
   ```bash
   # Check disk space
   df -h /etc/kubernetes/pki/backup
   
   # Verify permissions
   ls -la /etc/kubernetes/pki/backup
   ```

### Log Analysis
```bash
# View recent logs
sudo tail -f /var/log/k8s_cert_management.log

# Search for errors
sudo grep ERROR /var/log/k8s_cert_management.log

# Export logs
sudo k8s-cert-manage logs export --start-date 2024-03-01
```

### Health Checks
```bash
# System health check
sudo k8s-cert-manage health-check

# Certificate validation
sudo k8s-cert-manage verify --comprehensive

# Configuration validation
sudo k8s-cert-manage validate-config
```

## Advanced Usage

### Custom Certificates
```bash
# Generate custom certificate
sudo k8s-cert-manage generate-custom \
  --name "custom-cert" \
  --cn "custom.example.com" \
  --org "Example Org" \
  --key-size 4096
```

### Integration Examples
```bash
# Vault integration
sudo k8s-cert-manage integrate vault \
  --addr "https://vault.example.com" \
  --path "secret/k8s-certs"

# External CA integration
sudo k8s-cert-manage integrate external-ca \
  --ca-url "https://ca.example.com" \
  --auth-token "token123"
```

### Automation Scripts
```bash
# Certificate rotation script
#!/bin/bash
sudo k8s-cert-manage verify --quiet || {
  sudo k8s-cert-manage backup --compress
  sudo k8s-cert-manage renew --all
  sudo k8s-cert-manage verify --after-renewal
}
```

## Development

### Building from Source
```bash
# Clone repository
git clone https://github.com/org/k8s-cert-management
cd k8s-cert-management

# Install development dependencies
sudo apt-get install shellcheck bats

# Run tests
./run-tests.sh
```

### Testing
```bash
# Unit tests
./test/unit-tests.sh

# Integration tests
./test/integration-tests.sh

# End-to-end tests
./test/e2e-tests.sh
```

### Contributing Guidelines
1. Fork repository
2. Create feature branch
3. Follow coding standards
4. Add tests
5. Submit pull request

## Support & Maintenance

### Regular Maintenance
```bash
# Update script
git pull
sudo k8s-cert-manage update

# Verify installation
sudo k8s-cert-manage verify-installation
```

### Backup Maintenance
```bash
# Verify backups
sudo k8s-cert-manage verify-backups

# Clean old backups
sudo k8s-cert-manage cleanup-backups
```
---

## License
MIT License - See [LICENSE](LICENSE) file