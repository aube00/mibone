import shutil
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal mibone project directory with template and subscriptions."""
    src = Path(__file__).parent.parent
    shutil.copy(src / "config.template.yaml", tmp_path / "config.template.yaml")
    (tmp_path / "bin").mkdir()

    subs = {
        "subscriptions": [
            {"name": "main", "url": "https://example.com/sub1"},
            {"name": "backup", "url": "https://example.com/sub2"},
        ]
    }
    with open(tmp_path / "subscriptions.yaml", "w", encoding="utf-8") as f:
        yaml.dump(subs, f, allow_unicode=True)

    return tmp_path


@pytest.fixture
def single_sub_project(tmp_path):
    """Project with a single subscription."""
    src = Path(__file__).parent.parent
    shutil.copy(src / "config.template.yaml", tmp_path / "config.template.yaml")
    (tmp_path / "bin").mkdir()

    subs = {"subscriptions": [{"name": "only", "url": "https://example.com/sub"}]}
    with open(tmp_path / "subscriptions.yaml", "w", encoding="utf-8") as f:
        yaml.dump(subs, f, allow_unicode=True)

    return tmp_path


def load_output(tmp_path):
    """Load the generated config.yaml."""
    with open(tmp_path / "bin" / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
