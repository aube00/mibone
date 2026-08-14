# Mibone

> **mi**homo + **bone** = 开箱即用的裸核 mihomo。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6)](https://github.com/aube00/mibone/releases)

[English](README_EN.md)

---

## 这是什么？

Mibone 把 [mihomo](https://github.com/MetaCubeX/mihomo)（Clash 内核）部署为 Windows 系统服务。不需要 Clash Verge、CFW 等 GUI 客户端——一个 exe + 几条命令就搞定。

**和 GUI 客户端的区别：**

| | Mibone | Clash Verge / CFW |
|---|---|---|
| 运行方式 | 系统服务（开机自启，后台静默） | 桌面应用（需要保持窗口） |
| TUN 模式 | SYSTEM 权限，无需 UAC 弹窗 | 每次启动弹 UAC |
| 资源占用 | 仅 mihomo 内核 (~30MB) | 内核 + Electron/Tauri (~200MB+) |
| 节点管理 | [zashboard](https://github.com/Zephyruso/zashboard) Web 面板 | 内置 GUI |
| 配置方式 | YAML 文件 + CLI | GUI 界面 |

## 适合谁

- 从 Clash Verge / CFW 等 GUI 客户端迁移，想要更轻量的方案
- 希望代理开机自启、后台静默运行，不需要桌面窗口
- 有多台机器需要部署，偏好 CLI + 配置文件的管理方式
- 想用 mihomo 内核但不想折腾手动配置服务注册、配置生成等环节
- 知道 AI agent 能帮你一步步搞定裸核部署，但更想要一个已经做完、测过、加固过的现成工具——拿来就用

## 为什么不直接用裸核 mihomo？

mihomo 本身是代理内核，不管理自己的生命周期。直接用裸核你需要：

- 手写完整的 `config.yaml`（300+ 行，含策略组、规则、DNS、TUN）
- 手动注册 Windows 服务（winsw 配置 + XML 编写）
- 手动下载 GeoIP / GeoSite 数据文件
- 手动处理订阅地址 → mihomo 配置的转换
- 每次改配置手动重启或调 API

Mibone 把这些全自动化了——粘贴订阅地址，`mibone init` 一条命令搞定。

## 功能

- **一键部署**：`mibone init` 交互式引导，粘贴订阅地址即可
- **系统服务**：通过 [winsw](https://github.com/winsw/winsw) 注册为 Windows 服务，开机自启
- **TUN 模式**：SYSTEM 权限运行，无 UAC 弹窗，全局透明代理
- **多订阅支持**：mihomo 原生 `proxy-providers`，自动刷新节点
- **自由定制**：`override.yaml` 深度合并覆盖默认配置
- **住宅代理**（可选）：链式代理，机场节点中转 → 住宅 IP 出口
- **Web 面板**：[zashboard](https://github.com/Zephyruso/zashboard)，节点切换 + 延迟测试
- **订阅缓存容灾**：订阅下载失败时自动使用上次缓存，不会让你断网
- **端口冲突检测**：安装时自动检测端口占用，提前告警而不是启动后报错
- **零依赖**：单个 exe，不需要安装 Python / Node / 任何运行时

## 快速开始

### 1. 下载

从 [Releases](https://github.com/aube00/mibone/releases) 下载最新版本，解压到任意目录（如 `D:\mibone`）。

解压后的目录结构：
```
mibone/
├── mibone.exe
├── config.template.yaml
├── override.example.yaml
├── subscriptions.example.yaml
├── bin/
│   └── mihomo-service.xml
└── README.md
```

### 2. 初始化

**以管理员身份**打开终端（CMD 或 PowerShell），进入 mibone 目录：

```powershell
cd D:\mibone
.\mibone.exe init
```

按提示粘贴订阅地址。`init` 会自动完成以下步骤：
- 保存订阅到 `subscriptions.yaml`
- 下载 mihomo、winsw、zashboard、GeoX 数据
- 生成配置文件
- 注册并启动系统服务
- 打开 zashboard 面板

### 3. 完成

浏览器自动打开 zashboard 面板：

```
http://127.0.0.1:9090/ui
```

选择节点，开始使用。

> **日常使用不需要任何操作。** mihomo 服务开机自启，节点通过 `proxy-providers` 自动刷新。

## 命令一览

| 命令 | 说明 |
|---|---|
| `mibone init` | 交互式初始化（首次使用） |
| `mibone setup` | 下载 mihomo / winsw / zashboard / GeoX |
| `mibone setup --update` | 更新已下载的组件到最新版 |
| `mibone install` | 生成配置 + 注册服务 + 启动 |
| `mibone status` | 查看服务状态和面板地址 |
| `mibone restart` | 重启服务 |
| `mibone update` | 重新生成配置并热重载 |
| `mibone uninstall` | 停止并移除服务 |
| `mibone log` | 查看最近日志 |
| `mibone log -n 100` | 查看最近 100 行日志 |

> 所有服务操作（install / restart / uninstall）需要**管理员权限**。

## 自定义配置

基础使用不需要任何自定义。以下是进阶用法。

### 修改默认设置

复制示例文件：
```powershell
copy override.example.yaml override.yaml
```

编辑 `override.yaml`。支持的自定义方式：

| 字段 | 效果 |
|---|---|
| 顶层字段 (`mixed-port`, `allow-lan` 等) | 直接覆盖默认值 |
| 嵌套字段 (`dns`, `tun` 等) | 深度合并（你的值 > 默认值） |
| `extra-proxy-groups` | 追加策略组（同名则替换） |
| `prepend-rules` | 插入到规则最前面（最高优先级） |
| `append-rules` | 插入到兜底规则前面 |
| `_chain-proxy` | 住宅代理配置（见下文） |

修改后运行：
```powershell
.\mibone.exe update
```

### 示例：允许局域网访问

```yaml
allow-lan: true
```

### 示例：添加策略组和规则

```yaml
extra-proxy-groups:
  - name: "🎬 Netflix"
    type: select
    proxies: ["🚀 节点选择", "⚡ 自动选择"]

append-rules:
  - "DOMAIN-SUFFIX,netflix.com,🎬 Netflix"
  - "DOMAIN-SUFFIX,nflxvideo.net,🎬 Netflix"
```

### 住宅代理（可选）

如果你购买了静态住宅 IP，可以通过链式代理让 AI 服务使用住宅 IP 出口：

```
你的流量 → 机场节点(中转) → 住宅 IP(出口)
```

在 `override.yaml` 中配置：

```yaml
_chain-proxy:
  - name: "🏠 住宅1"
    server: 1.2.3.4        # 住宅代理地址
    port: 1080
    username: your_user
    password: your_pass
```

配置后自动生成住宅代理策略组，AI 服务组优先走住宅 IP。不配置则不生成，不影响其他功能。

## 多订阅

直接编辑 `subscriptions.yaml`（或重新运行 `mibone init`）：

```yaml
subscriptions:
  - name: "主力机场"
    url: "https://airport1.com/sub?token=xxx"
  - name: "备用机场"
    url: "https://airport2.com/sub?token=xxx"
    user-agent: "ClashForWindows"  # 某些机场需要特定 UA
```

修改后运行 `mibone update` 更新配置。

## 常见问题

### 需要管理员权限吗？

`mibone init`、`mibone install`、`mibone restart`、`mibone uninstall` 需要管理员权限（注册/管理 Windows 服务）。其他命令不需要。

### 和 Clash Verge 能共存吗？

不能同时运行。两者使用相同的端口（7890）和 TUN 设备。安装 mibone 前请先关闭 Clash Verge。

### 订阅节点怎么更新？

自动更新：mihomo 的 `proxy-providers` 默认每小时刷新一次。

手动更新：重启服务 `mibone restart`，或在 zashboard 面板里点击刷新。

### 配置文件在哪？

| 文件 | 说明 |
|---|---|
| `subscriptions.yaml` | 订阅地址（你创建的） |
| `override.yaml` | 自定义配置（你创建的，可选） |
| `config.template.yaml` | 默认配置模板（随 mibone 提供） |
| `bin/config.yaml` | 最终生成的 mihomo 配置（自动生成，不要手动编辑） |

### 怎么完全卸载？

```powershell
.\mibone.exe uninstall
```

然后删除 mibone 目录即可。不会残留注册表或系统文件。

## 开发

```bash
git clone https://github.com/aube00/mibone.git
cd mibone
pip install -r requirements.txt
python -m mibone init
```

### 构建

Release 版本使用 Nuitka 编译为单个 exe：

```powershell
pip install nuitka ordered-set zstandard
cd src
nuitka --onefile --standalone --assume-yes-for-downloads ^
    --output-dir=..\dist ^
    --output-filename=mibone.exe ^
    mibone
```

> 需要 C 编译器：MSVC（[Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)）或 MinGW 均可。

## License

[MIT](LICENSE)
