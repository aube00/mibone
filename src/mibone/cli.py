import argparse
import sys

from mibone import __version__
from mibone.utils import (
    get_base_dir,
    print_bi,
    print_ok,
    print_err,
    print_warn,
    DASHBOARD_PORT,
    MIXED_PORT,
    SOCKS_PORT,
)


def cmd_init(args):
    base = get_base_dir()
    subs_path = base / "subscriptions.yaml"

    print()
    print("=" * 50)
    print_bi("欢迎使用 Mibone！", "Welcome to Mibone!")
    print_bi(
        "mihomo 裸核服务，轻量、快速、可控",
        "Bare mihomo service — lightweight, fast, in control",
    )
    print("=" * 50)
    print()

    subscriptions = []
    while True:
        prompt = (
            "请粘贴订阅地址 (Paste subscription URL): "
            if not subscriptions
            else "添加另一个订阅 (Add another URL): "
        )
        url = input(prompt).strip()
        if not url:
            if not subscriptions:
                print_err(
                    "至少需要一个订阅地址", "At least one subscription URL is required"
                )
                continue
            break

        name = input(f"订阅名称 (Name) [订阅{len(subscriptions) + 1}]: ").strip()
        if not name:
            name = f"订阅{len(subscriptions) + 1}"
        subscriptions.append({"name": name, "url": url})

        more = input("是否添加更多订阅？(Add more?) [y/N]: ").strip().lower()
        if more not in ("y", "yes"):
            break

    import yaml

    subs_data = {"subscriptions": subscriptions}
    with open(subs_path, "w", encoding="utf-8") as f:
        yaml.dump(
            subs_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    print_ok(f"订阅已保存到 {subs_path.name}", f"Saved to {subs_path.name}")
    print()

    print_bi("正在下载组件...", "Downloading components...")
    from mibone.downloader import run_setup

    if not run_setup(base):
        print_err(
            "下载失败，请检查网络后重试", "Download failed, check network and retry"
        )
        return 1

    print()
    print_bi("正在生成配置并安装服务...", "Generating config and installing service...")
    from mibone.merge import generate_config

    try:
        generate_config(base)
    except (KeyError, ValueError, FileNotFoundError) as e:
        print_err(f"配置生成失败: {e}", f"Config generation failed: {e}")
        return 1
    print_ok("配置已生成", "Config generated")

    from mibone.service import install_service

    if not install_service(base):
        print_err("服务安装失败", "Service installation failed")
        print_bi("请以管理员身份重新运行", "Please re-run as administrator")
        return 1

    print()
    print("=" * 50)
    print_ok("服务已启动！", "Service started!")
    print()
    print(f"  面板地址 (Dashboard): http://127.0.0.1:{DASHBOARD_PORT}/ui")
    print(f"  代理端口 (Proxy):     HTTP {MIXED_PORT} / SOCKS5 {SOCKS_PORT}")
    print("=" * 50)
    print()

    import webbrowser

    try:
        webbrowser.open(f"http://127.0.0.1:{DASHBOARD_PORT}/ui")
    except Exception:
        pass

    return 0


def cmd_setup(args):
    base = get_base_dir()
    print_bi("正在下载组件...", "Downloading components...")
    from mibone.downloader import run_setup

    if run_setup(base, update=args.update):
        print_ok("下载完成", "Download complete")
        return 0
    print_err("下载失败", "Download failed")
    return 1


def cmd_install(args):
    base = get_base_dir()

    subs_path = base / "subscriptions.yaml"
    if not subs_path.exists():
        print_err("未找到 subscriptions.yaml", "subscriptions.yaml not found")
        print_bi("请先运行 mibone init", "Run mibone init first")
        return 1

    from mibone.merge import generate_config

    try:
        generate_config(base)
    except (KeyError, ValueError, FileNotFoundError) as e:
        print_err(f"配置生成失败: {e}", f"Config generation failed: {e}")
        return 1
    print_ok("配置已生成", "Config generated")

    from mibone.service import install_service

    if not install_service(base):
        print_err("服务安装失败，请以管理员身份运行", "Failed, run as administrator")
        return 1

    print_ok("服务已启动", "Service started")
    print(f"  面板: http://127.0.0.1:{DASHBOARD_PORT}/ui")
    return 0


def cmd_status(args):
    base = get_base_dir()
    from mibone.service import show_status

    return show_status(base)


def cmd_restart(args):
    base = get_base_dir()
    from mibone.service import restart_service

    if restart_service(base):
        print_ok("服务已重启", "Service restarted")
        return 0
    print_err("重启失败", "Restart failed")
    return 1


def cmd_update(args):
    base = get_base_dir()

    subs_path = base / "subscriptions.yaml"
    if not subs_path.exists():
        print_err("未找到 subscriptions.yaml", "subscriptions.yaml not found")
        return 1

    from mibone.merge import generate_config

    try:
        generate_config(base)
    except (KeyError, ValueError, FileNotFoundError) as e:
        print_err(f"配置生成失败: {e}", f"Config generation failed: {e}")
        return 1
    print_ok("配置已更新", "Config updated")

    from mibone.service import reload_config

    if reload_config(base):
        print_ok("mihomo 已重载", "mihomo reloaded")
    else:
        print_warn(
            "重载失败，请手动重启服务", "Reload failed, restart service manually"
        )
    return 0


def cmd_uninstall(args):
    base = get_base_dir()
    from mibone.service import uninstall_service

    if uninstall_service(base):
        print_ok("服务已移除", "Service removed")
        return 0
    print_err("移除失败", "Uninstall failed")
    return 1


def cmd_log(args):
    base = get_base_dir()
    from mibone.service import show_log

    return show_log(base, lines=args.lines)


def main():
    parser = argparse.ArgumentParser(
        prog="mibone",
        description="Mibone — mihomo 裸核服务管理 (bare mihomo service manager)",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"mibone {__version__}"
    )

    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="交互式初始化 (interactive first-time setup)")
    p_init.set_defaults(func=cmd_init)

    p_setup = sub.add_parser(
        "setup", help="下载 mihomo/winsw/zashboard/GeoX (download components)"
    )
    p_setup.add_argument(
        "--update", action="store_true", help="更新已有组件 (update existing)"
    )
    p_setup.set_defaults(func=cmd_setup)

    p_install = sub.add_parser(
        "install", help="生成配置 + 安装服务 (generate config + install service)"
    )
    p_install.set_defaults(func=cmd_install)

    p_status = sub.add_parser("status", help="查看服务状态 (show service status)")
    p_status.set_defaults(func=cmd_status)

    p_restart = sub.add_parser("restart", help="重启服务 (restart service)")
    p_restart.set_defaults(func=cmd_restart)

    p_update = sub.add_parser(
        "update", help="更新配置并重载 (re-generate config + reload)"
    )
    p_update.set_defaults(func=cmd_update)

    p_uninstall = sub.add_parser("uninstall", help="移除服务 (remove service)")
    p_uninstall.set_defaults(func=cmd_uninstall)

    p_log = sub.add_parser("log", help="查看日志 (show recent logs)")
    p_log.add_argument(
        "-n", "--lines", type=int, default=50, help="显示行数 (number of lines)"
    )
    p_log.set_defaults(func=cmd_log)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    sys.exit(args.func(args) or 0)
