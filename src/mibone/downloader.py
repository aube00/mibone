"""Download mihomo, winsw, zashboard, and GeoX data files."""

import json
import platform
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from mibone.utils import print_ok, print_err, print_warn, print_bi

GITHUB_API = "https://api.github.com/repos"


def _mihomo_asset_name():
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        return "mihomo-windows-amd64-"
    if arch in ("aarch64", "arm64"):
        return "mihomo-windows-arm64-"
    return "mihomo-windows-amd64-"


COMPONENTS = {
    "mihomo": {
        "repo": "MetaCubeX/mihomo",
        "asset_pattern": _mihomo_asset_name,
        "target": "bin/mihomo.exe",
    },
    "winsw": {
        "repo": "winsw/winsw",
        "asset_pattern": "WinSW-net461.exe",
        "target": "bin/mihomo-service.exe",
    },
    "zashboard": {
        "repo": "Zephyruso/zashboard",
        "asset_pattern": "dist-cdn.zip",
        "target_dir": "bin/ui",
        "is_zip": True,
    },
}

GEOX_FILES = {
    "geoip.metadb": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb",
    "geosite.dat": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat",
    "GeoLite2-ASN.mmdb": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb",
    "Country.mmdb": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb",
}


def run_setup(base_dir, update=False):
    base_dir = Path(base_dir)
    bin_dir = base_dir / "bin"
    bin_dir.mkdir(exist_ok=True)

    success = True

    for name, comp in COMPONENTS.items():
        target = base_dir / comp.get("target", "")
        target_dir = (
            base_dir / comp.get("target_dir", "") if "target_dir" in comp else None
        )

        if not update and (
            target.exists() if target.name else (target_dir and target_dir.exists())
        ):
            print_ok(f"{name} 已存在，跳过", f"{name} exists, skipping")
            continue

        print_bi(f"正在下载 {name}...", f"Downloading {name}...")
        if not _download_component(name, comp, base_dir):
            success = False

    for filename, url in GEOX_FILES.items():
        target = bin_dir / filename
        if not update and target.exists():
            print_ok(f"{filename} 已存在，跳过", f"{filename} exists, skipping")
            continue

        print_bi(f"正在下载 {filename}...", f"Downloading {filename}...")
        if _download_file(url, target):
            print_ok(f"{filename}", f"{filename}")
        else:
            print_err(f"{filename} 下载失败", f"Failed to download {filename}")
            success = False

    return success


def _download_component(name, comp, base_dir):
    try:
        repo = comp["repo"]
        release_url = f"{GITHUB_API}/{repo}/releases/latest"
        req = urllib.request.Request(release_url, headers={"User-Agent": "mibone"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            release = json.loads(resp.read().decode("utf-8"))

        pattern = comp["asset_pattern"]
        if callable(pattern):
            pattern = pattern()

        asset_url = None
        for asset in release.get("assets", []):
            asset_name = asset["name"]
            if isinstance(pattern, str) and pattern in asset_name:
                if name == "mihomo" and not asset_name.endswith(".zip"):
                    continue
                asset_url = asset["browser_download_url"]
                break

        if not asset_url:
            print_err(f"找不到 {name} 的下载文件", f"No matching asset for {name}")
            return False

        if comp.get("is_zip"):
            tmp_zip = base_dir / "bin" / f"{name}.tmp.zip"
            if not _download_file(asset_url, tmp_zip):
                return False
            target_dir = base_dir / comp["target_dir"]
            if target_dir.exists():
                shutil.rmtree(target_dir)
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(target_dir)
            tmp_zip.unlink()
        elif name == "mihomo":
            tmp_zip = base_dir / "bin" / "mihomo.tmp.zip"
            if not _download_file(asset_url, tmp_zip):
                return False
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                for member in zf.namelist():
                    if member.endswith(".exe"):
                        with (
                            zf.open(member) as src,
                            open(base_dir / comp["target"], "wb") as dst,
                        ):
                            dst.write(src.read())
                        break
            tmp_zip.unlink()
        else:
            target = base_dir / comp["target"]
            if not _download_file(asset_url, target):
                return False

        print_ok(f"{name} v{release.get('tag_name', '?')}", name)
        return True

    except Exception as e:
        print_err(f"{name} 下载出错: {e}", f"{name} download error: {e}")
        return False


def _download_file(url, target):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mibone"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(target, "wb") as f:
                shutil.copyfileobj(resp, f)
        return True
    except Exception as e:
        print_err(f"下载失败: {e}", f"Download failed: {e}")
        return False
