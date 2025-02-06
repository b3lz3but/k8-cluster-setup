#!/bin/bash

# Kubernetes Certificate Management Script for All Linux Distros
# This script generates, renews, verifies, and backs up Kubernetes certificates for your cluster nodes interactively.

set -e

# Variables
date=$(date +"%Y-%m-%d %H:%M:%S")
cfg_dir="/etc/kubernetes/pki"
etcd_dir="/etc/kubernetes/pki/etcd"
log_file="/var/log/k8s_cert_management.log"
backup_dir="/etc/kubernetes/pki/backup"
expiration_warning_days=30
retention_days=90
current_context=$(kubectl config current-context)
config_file="/etc/k8s_cert_script.conf"

# Function to log messages to the console and log file
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$log_file"
}

# Function to detect the package manager
install_packages() {
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        for package in "$@"; do
            if ! dpkg -l | grep -qw "$package"; then
                apt-get install -y "$package"
            else
                log "$package is already installed. Skipping."
            fi
        done
    elif [ -f /etc/redhat-release ]; then
        # RedHat/CentOS/Fedora
        yum install -y "$@"
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        pacman -Sy --noconfirm "$@"
    else
        log "Unsupported Linux distribution. Please install the required packages manually."
        exit 1
    fi
}

# Function to load configuration from file
load_config() {
    # Load configuration values if the config file exists
    if [ -f "$config_file" ]; then
        source "$config_file"
        log "Configuration loaded from $config_file."
    else
        log "Configuration file $config_file not found. Using default values."
    fi
}

# Function to create a backup of current certificates
backup_certs() {
    log "Creating a backup of current certificates..."
    backup_path="$backup_dir/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_path"
    # Use rsync for efficient and robust copying
    if rsync -a $cfg_dir/ "$backup_path"; then
        log "Backup completed successfully. Certificates saved in $backup_path"
    else
        log "ERROR: Failed to create a backup of certificates. Exiting..."
        exit 1
    fi
}

# Function to clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $retention_days days..."
    # Prompt user for confirmation, timeout after 30 seconds
    read -t 30 -p "Are you sure you want to delete backups older than $retention_days days? [y/N]: " confirm
    if [[ $? -ne 0 ]]; then
        log "Cleanup prompt timed out. No backups were deleted."
        return
    fi
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        # Dry-run to show what would be deleted
        log "The following backups would be deleted:"
        find "$backup_dir" -type d -mtime +$retention_days -print
        read -t 30 -p "Proceed with deletion? [y/N]: " confirm_delete
        if [[ "$confirm_delete" =~ ^[Yy]$ ]]; then
            # Find and delete old backups, and log any errors
            if find "$backup_dir" -type d -mtime +$retention_days -exec rm -rf {} +; then
                log "Old backups cleaned up successfully."
            else
                log "ERROR: Failed to clean up old backups. Check for permission issues or missing directories."
            fi
        else
            log "Cleanup of old backups canceled by user after dry-run."
        fi
    else
        log "Cleanup of old backups canceled by user."
    fi
}

# Function to generate new certificates
generate_certs() {
    log "Starting certificate generation..."
    certificates=(
        "all"
        "etcd-ca"
        "etcd-server"
        "etcd-peer"
        "etcd-healthcheck-client"
        "apiserver-etcd-client"
        "front-proxy-ca"
        "front-proxy-client"
        "sa"
        "apiserver-kubelet-client"
        "kube-controller-manager"
        "kube-scheduler"
        "admin"
    )

    # Check if kubeadm-config.yaml exists
    if [ ! -f kubeadm-config.yaml ]; then
        log "ERROR: kubeadm-config.yaml not found. Exiting certificate generation."
        exit 1
    fi

    # Loop through each certificate type and generate it
    for cert in "${certificates[@]}"; do
        kubeadm init phase certs $cert --config kubeadm-config.yaml || {
            log "ERROR: Failed to generate certificate for $cert."
            exit 1
        }
    done
    log "Certificate generation completed successfully."
}

# Function to renew certificates
renew_certs() {
    log "Starting certificate renewal..."
    certificates=(
        "all"
        "etcd-server"
        "etcd-peer"
        "etcd-healthcheck-client"
        "apiserver-etcd-client"
        "front-proxy-client"
        "apiserver-kubelet-client"
        "kube-controller-manager"
        "kube-scheduler"
        "admin"
    )

    # Loop through each certificate type and renew it
    for cert in "${certificates[@]}"; do
        kubeadm certs renew $cert || {
            log "ERROR: Failed to renew certificate for $cert."
            exit 1
        }
    done
    log "Certificate renewal completed successfully."
}

# Function to verify certificate expiration dates
verify_certs() {
    log "Verifying certificate expiration dates..."
    # Loop through each certificate and check its expiration date
    for cert in $cfg_dir/*.crt $etcd_dir/*.crt; do
        expiration_date=$(openssl x509 -noout -enddate -in "$cert" | cut -d'=' -f2)
        if [ $? -ne 0 ]; then
            log "ERROR: Failed to retrieve expiration date for certificate $(basename $cert)."
            continue
        fi
        expiration_epoch=$(date -d "$expiration_date" +%s)
        current_epoch=$(date +%s)
        days_until_expiration=$(( (expiration_epoch - current_epoch) / 86400 ))

        log "Certificate: $(basename $cert) expires on $expiration_date (in $days_until_expiration days)"

        # Warn if the certificate is expiring soon
        if [ $days_until_expiration -le $expiration_warning_days ]; then
            log "WARNING: Certificate $(basename $cert) expires in $days_until_expiration days. Consider renewing it soon."
            send_notification "WARNING: Certificate $(basename $cert) expires in $days_until_expiration days."
        fi
    done
}

# Function to check certificate health
check_cert_health() {
    log "Checking certificate health..."
    # Loop through each certificate and validate it
    for cert in $cfg_dir/*.crt $etcd_dir/*.crt; do
        if ! openssl x509 -noout -text -in "$cert" 2>> "$log_file"; then
            log "ERROR: Certificate $(basename $cert) is not valid."
            send_notification "ERROR: Certificate $(basename $cert) is not valid."
        else
            log "Certificate $(basename $cert) is valid."
        fi
    done
    log "Certificate health check completed."
}

# Function to send notifications (extensible for multiple channels)
send_notification() {
    message="$1"
    # Email notification
    echo "$message" | mail -s "Kubernetes Certificate Alert" admin@example.com
    # Slack notification (example integration)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' --data "{\"text\": \"$message\"}" "$SLACK_WEBHOOK_URL"
    fi
    # Microsoft Teams notification (example integration)
    if [ -n "$TEAMS_WEBHOOK_URL" ]; then
        curl -H 'Content-Type: application/json' -d "{\"text\": \"$message\"}" "$TEAMS_WEBHOOK_URL"
    fi
}

# Function to display detailed certificate information
detailed_cert_info() {
    log "Displaying detailed certificate information..."
    # Loop through each certificate and display detailed information
    for cert in $cfg_dir/*.crt $etcd_dir/*.crt; do
        if ! openssl x509 -in "$cert" -text -noout 2>> "$log_file"; then
            log "ERROR: Failed to parse certificate: $(basename $cert). Check log file for details."
        else
            log "Details for certificate: $(basename $cert)"
            openssl x509 -in "$cert" -text -noout | tee -a "$log_file"
        fi
    done
    log "Detailed certificate information displayed."
}

# Function to check if required commands are available
check_dependencies() {
    local dependencies=("kubectl" "kubeadm" "openssl" "rsync" "mail" "curl")
    for cmd in "${dependencies[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            log "ERROR: $cmd is not installed. Please install it and try again."
            exit 1
        fi
    done
}

# Function to display an interactive menu
interactive_menu() {
    while true; do
        # Display menu options to the user
        echo -e "\nKubernetes Certificate Management Script"
        echo "--------------------------------------"
        echo "Current Kubernetes Context: $current_context"
        echo "--------------------------------------"
        echo "1) Generate new certificates"
        echo "2) Renew existing certificates"
        echo "3) Verify certificate expiration dates"
        echo "4) Backup current certificates"
        echo "5) Check certificate health"
        echo "6) Display detailed certificate information"
        echo "7) Clean up old backups"
        echo "8) Exit"
        echo "--------------------------------------"
        read -p "Please enter your choice [1-8]: " choice

        # Validate input
        if ! [[ "$choice" =~ ^[1-8]$ ]]; then
            echo "Invalid choice, please enter a number between 1 and 8."
            continue
        fi

        # Execute the selected action
        case "$choice" in
            1)
                backup_certs
                generate_certs
                ;;
            2)
                backup_certs
                renew_certs
                ;;
            3)
                verify_certs
                ;;
            4)
                backup_certs
                ;;
            5)
                check_cert_health
                ;;
            6)
                detailed_cert_info
                ;;
            7)
                cleanup_old_backups
                ;;
            8)
                log "Exiting script. Goodbye!"
                exit 0
                ;;
        esac
    done
}

# Check for root privileges
if [[ $EUID -ne 0 ]]; then
    log "This script must be run as root. Exiting..."
    exit 1
fi

# Check for required dependencies
check_dependencies

# Load configuration from file
load_config

# Install required packages if they are not already installed
required_packages=("kubeadm" "kubectl" "openssl" "rsync" "mail" "curl")
install_packages "${required_packages[@]}"

# Main script logic
if [ $# -eq 0 ]; then
    interactive_menu
else
    # Execute the requested command based on command-line arguments
    case "$1" in
        generate)
            backup_certs
            generate_certs
            ;;
        renew)
            backup_certs
            renew_certs
            ;;
        verify)
            verify_certs
            ;;
        backup)
            backup_certs
            ;;
        check-health)
            check_cert_health
            ;;
        detailed-info)
            detailed_cert_info
            ;;
        cleanup-old-backups)
            cleanup_old_backups
            ;;
        *)
            log "Invalid option provided. Please use the interactive menu or a valid command."
            ;;
    esac
fi
