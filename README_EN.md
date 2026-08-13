# Mibone

> **mi**homo + **bone** = bare-bones mihomo, ready out of the box.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6)](https://github.com/aube00/mibone/releases)
[![LINUX DO](https://cdn3.ldstatic.com/original/4X/b/f/b/bfb681a6bdec04853c7b5e16c379f3a79fe47a9c.svg)](https://linux.do)

[中文](README.md)

## What is this?

Mibone deploys [mihomo](https://github.com/MetaCubeX/mihomo) (Clash-compatible proxy kernel) as a Windows system service. No GUI client needed — a single exe and a few commands.

**Compared to GUI clients:**

| | Mibone | Clash Verge / CFW |
|---|---|---|
| Runs as | System service (auto-start, silent) | Desktop app (window required) |
| TUN mode | SYSTEM privileges, no UAC popup | UAC prompt every launch |
| Resources | mihomo kernel only (~30MB) | Kernel + Electron/Tauri (~200MB+) |
| Node switching | [zashboard](https://github.com/Zephyruso/zashboard) web panel | Built-in GUI |
| Configuration | YAML files + CLI | GUI interface |

## Who is this for?

- Migrating from GUI clients (Clash Verge / CFW) and want something lighter
- Want your proxy to auto-start on boot and run silently — no desktop window
- Managing multiple machines and prefer CLI + config files over GUI
- Want to use the mihomo kernel without the hassle of manual service registration and config generation
- You know an AI agent could walk you through the raw mihomo setup — but you'd rather have a tool that's already built, tested, and hardened, ready to use out of the box

## Why not just use mihomo directly?

mihomo is a proxy kernel — it doesn't manage its own lifecycle. Using it directly means:

- Hand-writing a full `config.yaml` (300+ lines: proxy groups, rules, DNS, TUN)
- Manually registering a Windows service (winsw setup + XML config)
- Manually downloading GeoIP / GeoSite data files
- Manually converting subscription URLs into mihomo configuration
- Manually restarting or calling the API after every config change

Mibone automates all of this — paste your subscription URL, run `mibone init`, done.

## Features

- **One-command setup**: `mibone init` — paste your subscription URL, done
- **System service**: registered via [winsw](https://github.com/winsw/winsw), auto-starts on boot
- **TUN mode**: runs as SYSTEM, no UAC prompts, fully transparent proxy
- **Multi-subscription**: native mihomo `proxy-providers` with auto-refresh
- **Customizable**: `override.yaml` with deep merge over defaults
- **Residential proxy** (optional): chain proxy via residential SOCKS5
- **Web dashboard**: [zashboard](https://github.com/Zephyruso/zashboard) for node switching and latency testing
- **Subscription cache fallback**: if a subscription download fails, uses the last cached version — never leaves you disconnected
- **Port conflict detection**: checks for occupied ports at install time and warns early, instead of failing silently on startup
- **Zero dependencies**: single exe, no Python / Node / runtime needed

## Quick Start

### 1. Download

Download the latest release from [Releases](https://github.com/aube00/mibone/releases) and extract to any directory (e.g. `D:\mibone`).

### 2. Initialize

Open an **administrator** terminal (CMD or PowerShell), navigate to the mibone directory:

```powershell
cd D:\mibone
.\mibone.exe init
```

Follow the prompts to paste your subscription URL. `init` will:
- Save subscriptions to `subscriptions.yaml`
- Download mihomo, winsw, zashboard, and GeoX data
- Generate configuration
- Register and start the system service
- Open the zashboard dashboard

### 3. Done

The browser opens zashboard automatically:

```
http://127.0.0.1:9090/ui
```

Select your nodes and you're good to go.

> **No daily maintenance needed.** The mihomo service auto-starts on boot and refreshes nodes via `proxy-providers`.

## Commands

| Command | Description |
|---|---|
| `mibone init` | Interactive first-time setup |
| `mibone setup` | Download mihomo / winsw / zashboard / GeoX |
| `mibone setup --update` | Update components to latest versions |
| `mibone install` | Generate config + register service + start |
| `mibone status` | Show service status and dashboard URL |
| `mibone restart` | Restart service |
| `mibone update` | Re-generate config and hot-reload |
| `mibone uninstall` | Stop and remove service |
| `mibone log` | Show recent logs |

> Service commands (install / restart / uninstall) require **administrator privileges**.

## Customization

Copy the example file and edit:

```powershell
copy override.example.yaml override.yaml
```

| Field | Effect |
|---|---|
| Top-level (`mixed-port`, `allow-lan`, etc.) | Override defaults directly |
| Nested (`dns`, `tun`, etc.) | Deep merge (your values win) |
| `extra-proxy-groups` | Append proxy groups (same name = replace) |
| `prepend-rules` | Insert rules at the top (highest priority) |
| `append-rules` | Insert rules before the catch-all |
| `_chain-proxy` | Residential proxy config (optional) |

After editing, run `mibone update` to apply changes.

## FAQ

**Do I need admin rights?** — Yes, for `init`, `install`, `restart`, and `uninstall` (Windows service management). Other commands don't need admin.

**Can it coexist with Clash Verge?** — Not simultaneously. They use the same port (7890) and TUN device. Close Clash Verge before installing mibone.

**How do nodes refresh?** — Automatically via `proxy-providers` (default: hourly). Or restart the service / refresh in zashboard.

**How to uninstall completely?** — Run `mibone uninstall`, then delete the mibone directory. No registry or system files left behind.

## Development

```bash
git clone https://github.com/aube00/mibone.git
cd mibone
pip install -r requirements.txt
python -m mibone init
```

### Build

Release builds use Nuitka to compile into a single exe:

```powershell
pip install nuitka ordered-set zstandard
cd src
nuitka --onefile --standalone --assume-yes-for-downloads ^
    --output-dir=..\dist ^
    --output-filename=mibone.exe ^
    mibone
```

> Requires a C compiler: MSVC ([Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)) or MinGW.

## License

[MIT](LICENSE)
