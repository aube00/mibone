"""Tests for config generation engine (merge.py)."""

import yaml
from conftest import load_output
from mibone.merge import generate_config


class TestBasicGeneration:
    def test_generates_output_file(self, tmp_project):
        generate_config(tmp_project)
        assert (tmp_project / "bin" / "config.yaml").exists()

    def test_output_is_valid_yaml(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        assert isinstance(config, dict)


class TestProviderInjection:
    def test_creates_proxy_providers(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        assert "proxy-providers" in config
        assert len(config["proxy-providers"]) == 2

    def test_provider_has_correct_structure(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        provider = config["proxy-providers"]["main"]
        assert provider["type"] == "http"
        assert provider["url"] == "https://example.com/sub1"
        assert "health-check" in provider
        assert provider["health-check"]["enable"] is True

    def test_provider_path_uses_name(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        assert config["proxy-providers"]["main"]["path"] == "./providers/main.yaml"
        assert config["proxy-providers"]["backup"]["path"] == "./providers/backup.yaml"


class TestProviderRefExpansion:
    def test_expands_providers_marker_in_groups(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        for group in config["proxy-groups"]:
            if "use" in group:
                assert "__PROVIDERS__" not in str(group["use"]), (
                    f"Unexpanded marker in {group['name']}"
                )

    def test_expanded_refs_contain_all_providers(self, tmp_project):
        generate_config(tmp_project)
        config = load_output(tmp_project)
        auto_select = next(
            g for g in config["proxy-groups"] if g["name"] == "⚡ 自动选择"
        )
        assert "main" in auto_select["use"]
        assert "backup" in auto_select["use"]


class TestOverrideExtraGroups:
    def test_adds_new_group(self, tmp_project):
        override = {
            "extra-proxy-groups": [
                {
                    "name": "🎬 Netflix",
                    "type": "select",
                    "proxies": ["🚀 节点选择"],
                    "use": "__PROVIDERS__",
                }
            ]
        }
        with open(tmp_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(tmp_project)
        config = load_output(tmp_project)
        names = [g["name"] for g in config["proxy-groups"]]
        assert "🎬 Netflix" in names

    def test_extra_group_expands_providers(self, tmp_project):
        override = {
            "extra-proxy-groups": [
                {
                    "name": "🎬 Netflix",
                    "type": "select",
                    "proxies": ["🚀 节点选择"],
                    "use": "__PROVIDERS__",
                }
            ]
        }
        with open(tmp_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(tmp_project)
        config = load_output(tmp_project)
        netflix = next(g for g in config["proxy-groups"] if g["name"] == "🎬 Netflix")
        assert netflix["use"] == ["main", "backup"]

    def test_replaces_existing_group_by_name(self, single_sub_project):
        override = {
            "extra-proxy-groups": [
                {
                    "name": "🤖 AI 服务",
                    "type": "select",
                    "proxies": ["DIRECT", "🚀 节点选择"],
                }
            ]
        }
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        ai_group = next(g for g in config["proxy-groups"] if g["name"] == "🤖 AI 服务")
        assert ai_group["proxies"] == ["DIRECT", "🚀 节点选择"]


class TestOverrideRules:
    def test_prepend_rules_go_first(self, single_sub_project):
        override = {"prepend-rules": ["DOMAIN-SUFFIX,netflix.com,🎬 Netflix"]}
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        assert config["rules"][0] == "DOMAIN-SUFFIX,netflix.com,🎬 Netflix"

    def test_append_rules_before_match(self, single_sub_project):
        override = {"append-rules": ["DOMAIN-SUFFIX,custom.com,DIRECT"]}
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        match_idx = next(
            i for i, r in enumerate(config["rules"]) if r.startswith("MATCH,")
        )
        assert config["rules"][match_idx - 1] == "DOMAIN-SUFFIX,custom.com,DIRECT"


class TestOverrideDeepMerge:
    def test_overrides_scalar_value(self, single_sub_project):
        override = {"log-level": "info"}
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        assert config["log-level"] == "info"

    def test_deep_merges_nested_dict(self, single_sub_project):
        override = {"tun": {"mtu": 9000}}
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        assert config["tun"]["mtu"] == 9000
        assert config["tun"]["enable"] is True  # original value preserved


class TestChainProxy:
    def test_adds_chain_proxy_groups(self, single_sub_project):
        override = {
            "_chain-proxy": {
                "name": "🏠 住宅1",
                "type": "socks5",
                "server": "1.2.3.4",
                "port": 1080,
                "username": "user",
                "password": "pass",
            }
        }
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        group_names = [g["name"] for g in config["proxy-groups"]]
        assert "🏠 住宅代理" in group_names
        assert "🔗 住宅中转" in group_names
        assert "🔄 智能备用" in group_names


class TestMetaKeys:
    def test_strips_underscore_prefixed_keys(self, single_sub_project):
        override = {"_chain-proxy": {"server": "1.2.3.4", "port": 1080}}
        with open(single_sub_project / "override.yaml", "w", encoding="utf-8") as f:
            yaml.dump(override, f, allow_unicode=True)

        generate_config(single_sub_project)
        config = load_output(single_sub_project)
        for key in config:
            assert not key.startswith("_"), f"Meta key '{key}' leaked to output"


class TestErrorCases:
    def test_missing_subscriptions_file(self, tmp_path):
        (tmp_path / "config.template.yaml").write_text("mode: rule", encoding="utf-8")
        with __import__("pytest").raises(FileNotFoundError):
            generate_config(tmp_path)

    def test_empty_subscriptions_list(self, tmp_path):
        (tmp_path / "config.template.yaml").write_text("mode: rule", encoding="utf-8")
        subs = {"subscriptions": []}
        with open(tmp_path / "subscriptions.yaml", "w", encoding="utf-8") as f:
            yaml.dump(subs, f, allow_unicode=True)

        with __import__("pytest").raises(ValueError, match="No subscriptions"):
            generate_config(tmp_path)
