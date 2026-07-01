"""配置模块单元测试"""
import os
import tempfile
import pytest
from pathlib import Path


def test_load_config_from_yaml():
    """测试从 YAML 文件加载配置"""
    yaml_content = """
browser:
  headless: true
  viewport_width: 1280
  viewport_height: 800
  slow_mo: 0
  user_data_base_dir: "./data/user_data"
platforms:
  doubao:
    enabled: true
    name: "豆包"
    base_url: "https://www.doubao.com"
defaults:
  timeout: 120
  min_success: 3
  max_concurrent: 5
paths:
  screenshot_dir: "./data/screenshots"
  log_dir: "./data/logs"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        config_path = f.name

    try:
        from core.config import Config
        config = Config.load(config_path)
        assert config.browser.headless is True
        assert config.browser.viewport_width == 1280
        assert config.platforms["doubao"].name == "豆包"
        assert config.platforms["doubao"].enabled is True
        assert config.platforms["doubao"].base_url == "https://www.doubao.com"
        assert config.defaults.timeout == 120
        assert config.defaults.min_success == 3
        assert config.defaults.max_concurrent == 5
        assert config.paths.screenshot_dir == "./data/screenshots"
    finally:
        os.unlink(config_path)


def test_load_config_missing_file():
    """测试加载不存在的配置文件时抛出异常"""
    from core.config import Config
    with pytest.raises(FileNotFoundError):
        Config.load("nonexistent_config.yaml")


def test_get_enabled_platforms():
    """测试获取已启用的平台列表"""
    yaml_content = """
browser:
  headless: true
  viewport_width: 1280
  viewport_height: 800
  slow_mo: 0
  user_data_base_dir: "./data/user_data"
platforms:
  doubao:
    enabled: true
    name: "豆包"
    base_url: "https://www.doubao.com"
  chatglm:
    enabled: false
    name: "智谱清言"
    base_url: "https://chatglm.cn"
defaults:
  timeout: 120
  min_success: 3
  max_concurrent: 5
paths:
  screenshot_dir: "./data/screenshots"
  log_dir: "./data/logs"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        config_path = f.name

    try:
        from core.config import Config
        config = Config.load(config_path)
        enabled = config.get_enabled_platforms()
        assert "doubao" in enabled
        assert "chatglm" not in enabled
    finally:
        os.unlink(config_path)
