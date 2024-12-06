import os
import sys
import yaml
import logging
import argparse
import shutil
import subprocess
import psutil
import ipaddress
import json
import re
import socket
import platform
from pathlib import Path
from datetime import datetime
from subprocess import run, CalledProcessError
from typing import Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("k8s_setup.log")],
)


class K8sSetupError(Exception):
    pass


class SystemInfo:
    def __init__(self):
        self.distro = self.detect_distro()
        self.arch = platform.machine()
        self.cpu_count = psutil.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        self.kernel_version = platform.release()
        self.hostname = socket.gethostname()
        self.ip_address = self.get_ip_address()

    @staticmethod
    def detect_distro() -> Dict[str, str]:
        """Detect detailed Linux distribution info"""
        os_info = {}
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.rstrip().split("=", 1)
                        os_info[key] = value.strip('"')
            return os_info
        except Exception as e:
            raise K8sSetupError(f"Unable to detect Linux distribution: {e}")

    @staticmethod
    def get_ip_address() -> str:
        """Get primary IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 1))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()


class PackageManager:
    def __init__(self, distro_id: str):
        self.distro_id = distro_id.lower()
        self.commands = self._get_commands()
        self.container_runtime = "containerd"

    def _get_commands(self) -> Dict[str, Dict[str, str]]:
        return {
            "ubuntu": {
                "update": "apt-get update",
                "install": "apt-get install -y",
                "remove": "apt-get remove -y",
                "clean": "apt-get clean",
            },
            "debian": {
                "update": "apt-get update",
                "install": "apt-get install -y",
                "remove": "apt-get remove -y",
                "clean": "apt-get clean",
            },
            "fedora": {
                "update": "dnf check-update",
                "install": "dnf install -y",
                "remove": "dnf remove -y",
                "clean": "dnf clean all",
            },
            "centos": {
                "update": "yum check-update",
                "install": "yum install -y",
                "remove": "yum remove -y",
                "clean": "yum clean all",
            },
            "rhel": {
                "update": "yum check-update",
                "install": "yum install -y",
                "remove": "yum remove -y",
                "clean": "yum clean all",
            },
            "suse": {
                "update": "zypper refresh",
                "install": "zypper install -y",
                "remove": "zypper remove -y",
                "clean": "zypper clean",
            },
            "arch": {
                "update": "pacman -Sy",
                "install": "pacman -S --noconfirm",
                "remove": "pacman -R --noconfirm",
                "clean": "pacman -Sc --noconfirm",
            },
        }

    def setup_kubernetes_repo(self):
        """Setup Kubernetes repository based on distribution"""
        commands = {
            "ubuntu": [
                f"{self.commands[self.distro_id]['install']} apt-transport-https ca-certificates curl gpg",
                "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg",
                'echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" > /etc/apt/sources.list.d/kubernetes.list',
            ],
            "debian": [
                f"{self.commands[self.distro_id]['install']} apt-transport-https ca-certificates curl gpg",
                "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg",
                'echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" > /etc/apt/sources.list.d/kubernetes.list',
            ],
            "fedora": [
                "cat <<EOF > /etc/yum.repos.d/kubernetes.repo\n"
                "[kubernetes]\n"
                "name=Kubernetes\n"
                "baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-$basearch\n"
                "enabled=1\n"
                "gpgcheck=1\n"
                "repo_gpgcheck=1\n"
                "gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg\n"
                "EOF"
            ],
        }

        commands["rhel"] = commands["fedora"]
        commands["centos"] = commands["fedora"]

        if self.distro_id in commands:
            for cmd in commands[self.distro_id]:
                run_command(cmd)
            run_command(self.commands[self.distro_id]["update"])


class ContainerRuntime:
    def __init__(self, pkg_mgr: PackageManager):
        self.pkg_mgr = pkg_mgr

    def install_containerd(self):
        """Install and configure containerd"""
        # Install containerd
        if self.pkg_mgr.distro_id in ["ubuntu", "debian"]:
            run_command(
                f"{self.pkg_mgr.commands[self.pkg_mgr.distro_id]['install']} containerd.io"
            )

        # Configure containerd to use SystemdCgroup
        os.makedirs("/etc/containerd", exist_ok=True)
        run_command("containerd config default > /etc/containerd/config.toml")
        with open("/etc/containerd/config.toml", "r") as f:
            config = f.read()

        config = re.sub(
            r'(\[plugins\."io\.containerd\.grpc\.v1\.cri"\.containerd\.runtimes\.runc\.options\].*\n\s*)SystemdCgroup = false',
            r"\1SystemdCgroup = true",
            config,
            flags=re.DOTALL,
        )

        with open("/etc/containerd/config.toml", "w") as f:
            f.write(config)

        run_command("systemctl restart containerd")
        run_command("systemctl enable containerd")


class K8sCluster:
    def __init__(self, config: Dict):
        self.config = config
        self.system_info = SystemInfo()
        self.pkg_mgr = PackageManager(self.system_info.distro["ID"])
        self.container_runtime = ContainerRuntime(self.pkg_mgr)

    def check_prerequisites(self):
        """Check system prerequisites"""
        min_requirements = {
            "memory_gb": 2,
            "cpu_cores": 2,
            "ports": [6443, 2379, 2380, 10250, 10257, 10259],
        }

        if self.system_info.memory_gb < min_requirements["memory_gb"]:
            raise K8sSetupError(
                f"Insufficient memory: {self.system_info.memory_gb:.1f}GB < {min_requirements['memory_gb']}GB"
            )

        if self.system_info.cpu_count < min_requirements["cpu_cores"]:
            raise K8sSetupError(
                f"Insufficient CPU cores: {self.system_info.cpu_count} < {min_requirements['cpu_cores']}"
            )

        # Check port availability
        for port in min_requirements["ports"]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    raise K8sSetupError(f"Port {port} is already in use")

    def configure_system(self):
        """Configure system settings"""
        # Disable swap
        run_command("swapoff -a")
        run_command("sed -i '/ swap / s/^/#/' /etc/fstab")

        # Load required modules
        modules = ["overlay", "br_netfilter"]
        module_config = "/etc/modules-load.d/k8s.conf"
        with open(module_config, "w") as f:
            f.write("\n".join(modules))

        for module in modules:
            run_command(f"modprobe {module}")

        # Configure sysctl parameters
        sysctl_config = {
            "net.bridge.bridge-nf-call-iptables": 1,
            "net.bridge.bridge-nf-call-ip6tables": 1,
            "net.ipv4.ip_forward": 1,
            "net.ipv4.conf.all.forwarding": 1,
            "net.ipv6.conf.all.forwarding": 1,
        }

        with open("/etc/sysctl.d/k8s.conf", "w") as f:
            for key, value in sysctl_config.items():
                f.write(f"{key} = {value}\n")

        run_command("sysctl --system")

    def initialize_master(self) -> str:
        """Initialize Kubernetes control plane"""
        try:
            ipaddress.ip_network(self.config["pod_network_cidr"])
        except ValueError:
            raise K8sSetupError(
                f"Invalid pod network CIDR: {self.config['pod_network_cidr']}"
            )

        init_config = {
            "apiVersion": "kubeadm.k8s.io/v1beta3",
            "kind": "ClusterConfiguration",
            "networking": {
                "podSubnet": self.config["pod_network_cidr"],
                "serviceSubnet": self.config.get("service_cidr", "10.96.0.0/12"),
            },
            "controllerManager": {"extraArgs": {"bind-address": "0.0.0.0"}},
            "scheduler": {"extraArgs": {"bind-address": "0.0.0.0"}},
        }

        if self.config.get("kubernetes_version"):
            init_config["kubernetesVersion"] = self.config["kubernetes_version"]

        # Write kubeadm config
        with open("kubeadm-config.yaml", "w") as f:
            yaml.dump(init_config, f)

        output = run_command("kubeadm init --config kubeadm-config.yaml")

        # Configure kubectl
        os.makedirs(os.path.expanduser("~/.kube"), exist_ok=True)
        shutil.copy("/etc/kubernetes/admin.conf", os.path.expanduser("~/.kube/config"))
        os.chmod(os.path.expanduser("~/.kube/config"), 0o600)

        # Deploy network plugin
        self.deploy_network_plugin()

        return output

    def deploy_network_plugin(self):
        """Deploy CNI network plugin"""
        plugins = {
            "calico": {
                "url": "https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml",
                "config": {},
            },
            "cilium": {
                "url": "https://raw.githubusercontent.com/cilium/cilium/v1.14/install/kubernetes/quick-install.yaml",
                "config": {},
            },
            "flannel": {
                "url": "https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml",
                "config": {},
            },
        }

        plugin = self.config["network_plugin"].lower()
        if plugin not in plugins:
            raise K8sSetupError(f"Unsupported network plugin: {plugin}")

        # Download and apply network plugin manifest
        manifest = run_command(f"curl -fsSL {plugins[plugin]['url']}")

        # Apply any plugin-specific configurations
        if plugins[plugin]["config"]:
            manifest_dict = yaml.safe_load(manifest)
            # Apply configurations here
            manifest = yaml.dump(manifest_dict)

        with open(f"{plugin}-manifest.yaml", "w") as f:
            f.write(manifest)

        run_command(f"kubectl apply -f {plugin}-manifest.yaml")

    def setup_monitoring(self):
        """Deploy monitoring stack (Prometheus + Grafana)"""
        run_command(
            "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts"
        )
        run_command("helm repo update")
        run_command(
            "helm install prometheus prometheus-community/kube-prometheus-stack "
            "--namespace monitoring --create-namespace"
        )

    def setup_logging(self):
        """Deploy logging stack (EFK)"""
        run_command("kubectl create namespace logging")
        # Deploy Elasticsearch
        run_command(
            "helm install elasticsearch elastic/elasticsearch "
            "--namespace logging "
            "--set replicas=1,resources.requests.cpu=100m,resources.requests.memory=512Mi"
        )
        # Deploy Fluent Bit
        run_command("helm install fluent-bit fluent/fluent-bit " "--namespace logging")
        # Deploy Kibana
        run_command("helm install kibana elastic/kibana " "--namespace logging")


def run_command(
    cmd: str,
    shell: bool = True,
    check: bool = True,
    suppress_output: bool = False,
    retries: int = 3,
    timeout: int = 300,
) -> str:
    """Execute shell command with retries and timeout"""
    for attempt in range(retries):
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            if not suppress_output:
                logging.info(result.stdout)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logging.error(f"Command timed out after {timeout} seconds")
            if attempt == retries - 1:
                raise K8sSetupError("Command repeatedly timed out")
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {e.stderr}")
            if attempt == retries - 1:
                raise K8sSetupError(f"Command failed after {retries} attempts")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            if attempt == retries - 1:
                raise K8sSetupError(f"Unexpected error after {retries} attempts")


def parse_args():
    parser = argparse.ArgumentParser(description="Kubernetes Cluster Setup")
    parser.add_argument(
        "--role",
        choices=["master", "worker"],
        required=True,
        help="Node role (master/worker)",
    )
    parser.add_argument(
        "--config", default="config.yml", help="Path to configuration file"
    )
    parser.add_argument("--join-command", help="Worker node join command")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


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


def main():
    try:
        args = parse_args()
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        if os.geteuid() != 0:
            raise K8sSetupError("Script must be run as root")

        config = load_config(args.config)
        cluster = K8sCluster(config)

        logging.info("Checking system prerequisites...")
        cluster.check_prerequisites()

        logging.info("Configuring system...")
        cluster.configure_system()

        logging.info("Installing container runtime...")
        cluster.container_runtime.install_containerd()

        if args.role == "master":
            logging.info("Initializing master node...")
            output = cluster.initialize_master()

            if config.get("enable_monitoring", False):
                logging.info("Setting up monitoring stack...")
                cluster.setup_monitoring()

            if config.get("enable_logging", False):
                logging.info("Setting up logging stack...")
                cluster.setup_logging()

            join_cmd = re.search(
                r"kubeadm join .+\n\s+--discovery-token-ca-cert-hash .+",
                output,
                re.MULTILINE,
            )
            if join_cmd:
                with open("join-command.sh", "w") as f:
                    f.write(join_cmd.group())
                os.chmod("join-command.sh", 0o600)
                logging.info("Join command saved to join-command.sh")

        elif args.role == "worker":
            if not args.join_command:
                raise K8sSetupError("Worker role requires --join-command")
            logging.info("Joining worker node to cluster...")
            run_command(args.join_command)

        logging.info("Setup completed successfully!")

    except K8sSetupError as e:
        logging.error(f"Setup failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
