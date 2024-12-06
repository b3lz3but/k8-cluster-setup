import os
import sys
import yaml
import logging
import argparse
import shutil
import subprocess
import psutil
import ipaddress
from datetime import datetime
from subprocess import run, CalledProcessError
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
)


class K8sSetupError(Exception):
    """Custom exception for Kubernetes setup errors"""

    pass


def load_config(config_file: str = "config.yml") -> Dict:
    """
    Load and validate configuration from YAML file
    Raises ValueError if required fields are missing
    """
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file) or {}
            required_fields = ["pod_network_cidr", "network_plugin"]
            missing = [field for field in required_fields if field not in config]
            if missing:
                raise ValueError(
                    f"Missing required config fields: {', '.join(missing)}"
                )
            return config
    except FileNotFoundError:
        logging.warning(f"Config file {config_file} not found. Using defaults.")
        return {"pod_network_cidr": "192.168.0.0/16", "network_plugin": "calico"}


def run_command(
    command: str, suppress_output: bool = False, retries: int = 3, timeout: int = 300
) -> str:
    """
    Run shell command with retry logic and timeout
    Returns command output if successful
    Raises CalledProcessError after all retries fail
    """
    if not isinstance(command, str) or ";" in command:
        raise ValueError("Invalid command format")

    for attempt in range(retries):
        try:
            result = run(
                command,
                shell=True,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            if not suppress_output:
                logging.info(result.stdout)
            return result.stdout.strip()
        except CalledProcessError as e:
            logging.error(f"Command failed: {e.stderr}")
            if attempt < retries - 1:
                logging.warning(f"Retrying ({attempt + 2}/{retries})...")
            else:
                raise K8sSetupError(f"Command failed after {retries} attempts")


def check_system_requirements():
    """Verify system meets minimum requirements"""
    if os.geteuid() != 0:
        raise K8sSetupError("Must run as root")

    min_memory_gb = 2
    min_cpu_cores = 2

    memory = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()

    if memory < min_memory_gb or cpu_count < min_cpu_cores:
        raise K8sSetupError(
            f"Insufficient resources. Required: {min_memory_gb}GB RAM, {min_cpu_cores} cores"
        )

    required_commands = ["kubeadm", "kubectl", "apt-get", "curl"]
    missing = [cmd for cmd in required_commands if not shutil.which(cmd)]
    if missing:
        raise K8sSetupError(f"Missing commands: {', '.join(missing)}")


def backup_kubernetes_config():
    """Backup Kubernetes configuration"""
    backup_dir = f"/opt/k8s_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists("/etc/kubernetes"):
        shutil.copytree("/etc/kubernetes", backup_dir)
        logging.info(f"Config backed up to {backup_dir}")
    return backup_dir


def install_prerequisites():
    """Install Kubernetes prerequisites"""
    commands = [
        "apt-get update && apt-get install -y apt-transport-https curl",
        "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -",
        "echo 'deb https://apt.kubernetes.io/ kubernetes-xenial main' > /etc/apt/sources.list.d/kubernetes.list",
        "apt-get update && apt-get install -y kubelet kubeadm kubectl",
    ]
    for cmd in commands:
        run_command(cmd)


def disable_swap():
    """Disable swap and update fstab"""
    run_command("swapoff -a")
    run_command("sed -i '/ swap / s/^/#/' /etc/fstab")


def validate_network_config(pod_network_cidr: str):
    """Validate pod network CIDR"""
    try:
        ipaddress.ip_network(pod_network_cidr)
    except ValueError:
        raise ValueError(f"Invalid pod network CIDR: {pod_network_cidr}")


def initialize_master(pod_network_cidr: str):
    """Initialize Kubernetes master node"""
    validate_network_config(pod_network_cidr)
    run_command(f"kubeadm init --pod-network-cidr={pod_network_cidr}")
    configure_kubectl()


def configure_kubectl():
    """Configure kubectl for root user"""
    kube_dir = f"{os.environ['HOME']}/.kube"
    os.makedirs(kube_dir, exist_ok=True)
    run_command(f"cp -i /etc/kubernetes/admin.conf {kube_dir}/config")
    run_command(f"chown $(id -u):$(id -g) {kube_dir}/config")


def deploy_network_plugin(plugin: str = "calico"):
    """Deploy network plugin"""
    plugins = {
        "calico": "https://docs.projectcalico.org/manifests/calico.yaml",
        "flannel": "https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml",
    }
    if plugin not in plugins:
        raise ValueError(f"Unsupported plugin: {plugin}")
    run_command(f"kubectl apply -f {plugins[plugin]}")


def get_join_command() -> str:
    """Get worker node join command"""
    return run_command("kubeadm token create --print-join-command")


def save_join_command(join_command: str, filename: str = "join_command.sh"):
    """Save join command to file"""
    with open(filename, "w") as file:
        file.write(join_command)
    os.chmod(filename, 0o600)
    logging.info(f"Join command saved to {filename}")


def join_worker_node(join_command: str):
    """Join worker node to cluster"""
    if not join_command.startswith("kubeadm join"):
        raise ValueError("Invalid join command")
    run_command(join_command)


def healthcheck():
    """Verify cluster health"""
    try:
        run_command("kubectl get nodes")
        run_command("kubectl get pods --all-namespaces")
    except CalledProcessError:
        raise K8sSetupError("Cluster health check failed")


def reset_kubernetes():
    """Reset Kubernetes setup"""
    backup_kubernetes_config()
    run_command("kubeadm reset -f")
    run_command("rm -rf ~/.kube")
    logging.info("Kubernetes reset complete")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Kubernetes Cluster Automation")
    parser.add_argument("--role", choices=["master", "worker"], required=True)
    parser.add_argument("--join-command", help="Worker node join command")
    parser.add_argument("--config", default="config.yml", help="Config file path")
    return parser.parse_args()


def main():
    """Main function for Kubernetes cluster setup"""
    try:
        args = parse_arguments()
        config = load_config(args.config)
        check_system_requirements()
        install_prerequisites()
        disable_swap()

        if args.role == "master":
            initialize_master(config["pod_network_cidr"])
            deploy_network_plugin(config["network_plugin"])
            join_command = get_join_command()
            save_join_command(join_command)
            healthcheck()
        elif args.role == "worker":
            if not args.join_command:
                raise ValueError("Worker role requires join command")
            join_worker_node(args.join_command)

        logging.info("Setup complete!")

    except Exception as e:
        logging.critical(f"Setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
