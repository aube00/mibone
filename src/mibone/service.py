"""Windows service management via winsw + mihomo API."""

import json
import subprocess
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

from mibone.utils import (
    print_bi,
    print_ok,
    print_err,
    print_warn,
    DASHBOARD_PORT,
    MIXED_PORT,
    SOCKS_PORT,
)


def _winsw(base_dir, *args):
    exe = Path(base_dir) / "bin" / "mihomo-service.exe"
    if not exe.exists():
        print_err("未找到 mihomo-service.exe", "mihomo-service.exe not found")
        print_bi("请先运行 mibone setup", "Run mibone setup first")
        return None
    try:
        result = subprocess.run(
            [str(exe)] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(Path(base_dir) / "bin"),
        )
        return result
    except subprocess.TimeoutExpired:
        print_err("操作超时", "Operation timed out")
        return None
    except FileNotFoundError:
        print_err("无法执行 winsw", "Cannot execute winsw")
        return None


def _check_port(port):
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def install_service(base_dir):
    base_dir = Path(base_dir)

    if _check_port(MIXED_PORT):
        print_warn(
            f"端口 {MIXED_PORT} 已被占用，请先关闭其他代理工具 (如 Clash Verge)",
            f"Port {MIXED_PORT} in use, close other proxy tools first (e.g. Clash Verge)",
        )
        return False
    if _check_port(DASHBOARD_PORT):
        print_warn(
            f"端口 {DASHBOARD_PORT} (面板) 已被占用，zashboard 可能无法访问",
            f"Port {DASHBOARD_PORT} (dashboard) in use, zashboard may not work",
        )
    if _check_port(SOCKS_PORT):
        print_warn(
            f"端口 {SOCKS_PORT} (SOCKS5) 已被占用",
            f"Port {SOCKS_PORT} (SOCKS5) in use",
        )

    config_path = base_dir / "bin" / "config.yaml"
    if not config_path.exists():
        print_err("未找到 bin/config.yaml", "bin/config.yaml not found")
        print_bi(
            "请先运行 mibone install 或 mibone init",
            "Run mibone install or mibone init first",
        )
        return False

    result = _winsw(base_dir, "install")
    if result is None:
        return False

    if result.returncode != 0 and "already exists" not in result.stderr.lower():
        print_err(
            f"安装失败: {result.stderr.strip()}",
            f"Install failed: {result.stderr.strip()}",
        )
        return False

    result = _winsw(base_dir, "start")
    if result is None:
        return False
    if result.returncode != 0 and "already started" not in result.stderr.lower():
        print_err(
            f"启动失败: {result.stderr.strip()}",
            f"Start failed: {result.stderr.strip()}",
        )
        return False

    return True


def uninstall_service(base_dir):
    result = _winsw(base_dir, "stop")
    result = _winsw(base_dir, "uninstall")
    if result is None:
        return False
    return result.returncode == 0 or "does not exist" in result.stderr.lower()


def restart_service(base_dir):
    result = _winsw(base_dir, "restart")
    if result is None:
        return False
    return result.returncode == 0


def reload_config(base_dir):
    base_dir = Path(base_dir)
    config_path = base_dir / "bin" / "config.yaml"
    if not config_path.exists():
        return False

    from mibone.utils import load_yaml

    config = load_yaml(config_path)
    secret = config.get("secret", "")
    controller = config.get("external-controller", f"127.0.0.1:{DASHBOARD_PORT}")

    try:
        payload = json.dumps({"path": str(config_path.resolve())}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"
        req = urllib.request.Request(
            f"http://{controller}/configs",
            data=payload,
            method="PUT",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        return True
    except Exception:
        return False


def show_status(base_dir):
    result = _winsw(base_dir, "status")
    if result is None:
        return 1

    running = _check_port(DASHBOARD_PORT)

    print()
    if running:
        print_ok("mihomo 服务运行中", "mihomo service is running")
        print(f"  面板 (Dashboard): http://127.0.0.1:{DASHBOARD_PORT}/ui")
        print(f"  代理 (Proxy):     HTTP {MIXED_PORT} / SOCKS5 {SOCKS_PORT}")
    else:
        print_err("mihomo 服务未运行", "mihomo service is not running")
        print_bi("运行 mibone restart 重启服务", "Run mibone restart to start")
    print()
    return 0 if running else 1


def show_log(base_dir, lines=50):
    base_dir = Path(base_dir)
    log_path = base_dir / "bin" / "mihomo-service.out.log"
    err_path = base_dir / "bin" / "mihomo-service.err.log"

    for path, label in [(log_path, "stdout"), (err_path, "stderr")]:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            tail = deque(f, maxlen=lines)
        if tail:
            print(f"--- {label} ({path.name}) ---")
            for line in tail:
                print(line, end="")
            print()

    if not log_path.exists() and not err_path.exists():
        print_warn("未找到日志文件", "No log files found")
        print_bi("服务启动后才会生成日志", "Logs are created after service starts")
    return 0
