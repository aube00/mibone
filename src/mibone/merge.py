"""Config generation: template + subscriptions + override → bin/config.yaml"""

import re
from pathlib import Path

from mibone.utils import load_yaml, save_yaml, print_ok, print_warn, print_err

PROVIDERS_MARKER = "__PROVIDERS__"


def generate_config(base_dir):
    base_dir = Path(base_dir)

    template_path = base_dir / "config.template.yaml"
    subs_path = base_dir / "subscriptions.yaml"
    override_path = base_dir / "override.yaml"
    output_path = base_dir / "bin" / "config.yaml"

    if not template_path.exists():
        raise FileNotFoundError(f"config.template.yaml not found in {base_dir}")
    if not subs_path.exists():
        raise FileNotFoundError(f"subscriptions.yaml not found in {base_dir}")

    config = load_yaml(template_path)
    subs_data = load_yaml(subs_path)
    subscriptions = subs_data.get("subscriptions", [])

    if not subscriptions:
        raise ValueError("No subscriptions defined in subscriptions.yaml")

    provider_names = _inject_providers(config, subscriptions)
    _expand_provider_refs(config, provider_names)

    if override_path.exists():
        override = load_yaml(override_path)
        _apply_override(config, override, provider_names)

    _strip_meta_keys(config)

    save_yaml(config, output_path)
    print_ok(f"配置已写入 {output_path}", f"Config written to {output_path}")


def _inject_providers(config, subscriptions):
    providers = {}
    for i, sub in enumerate(subscriptions):
        if not isinstance(sub, dict):
            raise ValueError(
                f"订阅 #{i + 1} 格式错误，应为字典 (Subscription #{i + 1} is not a dict)"
                " — 请参考 subscriptions.example.yaml"
            )
        if "name" not in sub or not sub["name"]:
            raise ValueError(
                f"订阅 #{i + 1} 缺少 name 字段 (Subscription #{i + 1} missing 'name')"
                " — 请参考 subscriptions.example.yaml"
            )
        if "url" not in sub or not sub["url"]:
            raise ValueError(
                f"订阅 #{i + 1} 缺少 url 字段 (Subscription #{i + 1} missing 'url')"
                " — 请参考 subscriptions.example.yaml"
            )
        name = sub["name"]
        if re.search(r"[/\\]", name) or ".." in name:
            raise ValueError(
                f"订阅 #{i + 1} 的 name 含非法字符 (name contains unsafe characters: '{name}')"
                " — name 不能包含 / \\ .."
            )
        if name in providers:
            raise ValueError(
                f"订阅 #{i + 1} 的 name '{name}' 重复 (duplicate subscription name)"
                " — 每个订阅需要唯一的 name"
            )
        entry = {
            "type": "http",
            "url": sub["url"],
            "interval": sub.get("interval", 3600),
            "path": f"./providers/{name}.yaml",
            "health-check": {
                "enable": True,
                "url": "https://www.gstatic.com/generate_204",
                "interval": 300,
            },
            "override": {
                "additional-prefix": f"[{name}] ",
            },
        }
        header = {}
        if "user-agent" in sub:
            header["User-Agent"] = [sub["user-agent"]]
        if header:
            entry["header"] = header
        if sub.get("exclude-filter"):
            entry["exclude-filter"] = sub["exclude-filter"]
        providers[name] = entry

    config["proxy-providers"] = providers
    return list(providers.keys())


def _expand_provider_refs(config, provider_names):
    for group in config.get("proxy-groups", []):
        use = group.get("use")
        if use == PROVIDERS_MARKER or use == [PROVIDERS_MARKER]:
            group["use"] = list(provider_names)
        elif isinstance(use, list):
            expanded = []
            for item in use:
                if item == PROVIDERS_MARKER:
                    expanded.extend(provider_names)
                else:
                    expanded.append(item)
            group["use"] = expanded


def _apply_override(config, override, provider_names):
    extra_groups = override.pop("extra-proxy-groups", None)
    if extra_groups:
        existing = {g["name"]: i for i, g in enumerate(config.get("proxy-groups", []))}
        for group in extra_groups:
            _expand_single_group_providers(group, provider_names)
            if group["name"] in existing:
                config["proxy-groups"][existing[group["name"]]] = group
            else:
                insert_pos = len(config["proxy-groups"]) - 1
                config["proxy-groups"].insert(insert_pos, group)

    prepend = override.pop("prepend-rules", None)
    if prepend:
        config["rules"] = prepend + config.get("rules", [])

    append = override.pop("append-rules", None)
    if append:
        rules = config.get("rules", [])
        match_idx = None
        for i, r in enumerate(rules):
            if r.startswith("MATCH,"):
                match_idx = i
                break
        if match_idx is not None:
            for j, rule in enumerate(append):
                rules.insert(match_idx + j, rule)
        else:
            rules.extend(append)
        config["rules"] = rules

    chain = override.pop("_chain-proxy", None)
    if chain:
        _apply_chain_proxy(config, chain, provider_names)

    _deep_merge(config, override)


def _apply_chain_proxy(config, chain_cfg, provider_names):
    proxies = config.setdefault("proxies", [])

    chain_proxies = chain_cfg if isinstance(chain_cfg, list) else [chain_cfg]
    residential_names = []

    for i, cp in enumerate(chain_proxies):
        if not isinstance(cp, dict):
            raise ValueError(
                f"住宅代理 #{i + 1} 格式错误 (Chain proxy #{i + 1} is not a dict)"
                " — 请参考 override.example.yaml"
            )
        if "server" not in cp or not cp["server"]:
            raise ValueError(
                f"住宅代理 #{i + 1} 缺少 server 字段 (Chain proxy #{i + 1} missing 'server')"
                " — 请参考 override.example.yaml"
            )
        if "port" not in cp:
            raise ValueError(
                f"住宅代理 #{i + 1} 缺少 port 字段 (Chain proxy #{i + 1} missing 'port')"
                " — 请参考 override.example.yaml"
            )
        name = cp.get("name", f"🏠 住宅{i + 1}")
        proxy = {
            "name": name,
            "type": cp.get("type", "socks5"),
            "server": cp["server"],
            "port": cp["port"],
            "udp": True,
            "skip-cert-verify": True,
            "dialer-proxy": "🔗 住宅中转",
        }
        if "username" in cp:
            proxy["username"] = cp["username"]
        if "password" in cp:
            proxy["password"] = cp["password"]
        proxies.append(proxy)
        residential_names.append(name)

    groups = config.get("proxy-groups", [])

    groups.insert(
        -1,
        {
            "name": "🏠 住宅代理",
            "type": "select",
            "proxies": residential_names,
        },
    )
    groups.insert(
        -1,
        {
            "name": "🔗 住宅中转",
            "type": "select",
            "proxies": ["⚡ 自动选择"],
            "use": list(provider_names),
        },
    )
    groups.insert(
        -1,
        {
            "name": "🔄 智能备用",
            "type": "fallback",
            "url": "https://www.gstatic.com/generate_204",
            "interval": 120,
            "timeout": 3000,
            "lazy": False,
            "max-failed-times": 2,
            "proxies": ["🏠 住宅代理", "⚡ 美国自动"],
        },
    )

    ai_found = False
    for group in groups:
        if group["name"] == "🤖 AI 服务":
            group["proxies"] = [
                "🔄 智能备用",
                "🏠 住宅代理",
                "⚡ 美国自动",
                "🚀 节点选择",
            ]
            ai_found = True
            break
    if not ai_found:
        print_warn(
            "未找到 '🤖 AI 服务' 策略组，住宅代理需手动配置路由",
            "'🤖 AI 服务' group not found, configure residential routing manually",
        )


def _expand_single_group_providers(group, provider_names):
    use = group.get("use")
    if use == PROVIDERS_MARKER or use == [PROVIDERS_MARKER]:
        group["use"] = list(provider_names)
    elif isinstance(use, list) and PROVIDERS_MARKER in use:
        expanded = []
        for item in use:
            if item == PROVIDERS_MARKER:
                expanded.extend(provider_names)
            else:
                expanded.append(item)
        group["use"] = expanded


def _deep_merge(base, override):
    for key, value in override.items():
        if key.startswith("_"):
            continue
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _strip_meta_keys(config):
    keys_to_remove = [k for k in config if k.startswith("_")]
    for k in keys_to_remove:
        del config[k]
