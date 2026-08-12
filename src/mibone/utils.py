import sys
from pathlib import Path

import yaml


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path.cwd()


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def print_bi(zh, en):
    print(f"{zh} ({en})")


def print_ok(zh, en):
    print(f"  ✓ {zh} ({en})")


def print_err(zh, en):
    print(f"  ✗ {zh} ({en})", file=sys.stderr)


def print_warn(zh, en):
    print(f"  ! {zh} ({en})")


DASHBOARD_PORT = 9090
MIXED_PORT = 7890
SOCKS_PORT = 7891
