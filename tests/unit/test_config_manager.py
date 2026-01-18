import os

import pytest
import yaml

from src.infrastructure.config.config_manager import (
    AppConfig,
    Config,
    ConfigManager,
    LocalLLMConfig,
    NetworkConfig,
)


# 创建临时配置文件
@pytest.fixture
def temp_config_file(tmp_path):
    config_content = {
        "local_llm": {
            "provider": "ollama",
            "model": "qwen3:8b",
            "base_url": "http://localhost:11434",
            "timeout": 30,
        },
        "external_tools": [
            {
                "name": "iflow",
                "command": "iflow",
                "args": "ask --streaming=false",
                "needs_internet": True,
                "priority": 1,
                "enabled": True,
            }
        ],
        "network": {"check_before_run": True, "timeout": 60},
        "app": {
            "max_clarification_rounds": 3,
            "max_parallel_tools": 5,
            "log_level": "info",
            "log_file": "consensusweaver.log",
            "history_enabled": True,
            "history_limit": 100,
        },
    }

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_content, f, default_flow_style=False, allow_unicode=True)

    return str(config_path)


# 测试配置加载
def test_config_load(temp_config_file):
    config_manager = ConfigManager(temp_config_file)
    config = config_manager.get_config()

    # 验证配置类型
    assert isinstance(config, Config)
    assert isinstance(config.local_llm, LocalLLMConfig)
    assert isinstance(config.external_tools, list)
    assert isinstance(config.network, NetworkConfig)
    assert isinstance(config.app, AppConfig)

    # 验证配置值
    assert config.local_llm.provider == "ollama"
    assert config.local_llm.model == "qwen3:8b"
    assert len(config.external_tools) == 1
    assert config.external_tools[0].name == "iflow"
    assert config.network.check_before_run is True
    assert config.app.max_clarification_rounds == 3


# 测试默认配置创建
def test_default_config_creation(tmp_path):
    # 使用不存在的配置文件路径
    config_path = tmp_path / "non_existent_config.yaml"
    config_manager = ConfigManager(str(config_path))

    # 验证配置文件被创建
    assert os.path.exists(config_path)

    # 验证默认配置值
    config = config_manager.get_config()
    assert config.local_llm.provider == "ollama"
    assert config.local_llm.model == "qwen3:8b"
    assert len(config.external_tools) == 2  # 默认应该有两个工具


# 测试配置重新加载
def test_config_reload(temp_config_file):
    config_manager = ConfigManager(temp_config_file)
    config = config_manager.get_config()

    # 修改配置文件
    new_content = {
        "local_llm": {
            "provider": "ollama",
            "model": "llama3:70b",  # 修改模型
            "base_url": "http://localhost:11434",
            "timeout": 30,
        },
        "external_tools": [
            {
                "name": "iflow",
                "command": "iflow",
                "args": "ask --streaming=false",
                "needs_internet": True,
                "priority": 1,
                "enabled": True,
            }
        ],
        "network": {"check_before_run": True, "timeout": 60},
        "app": {
            "max_clarification_rounds": 3,
            "max_parallel_tools": 5,
            "log_level": "info",
            "log_file": "consensusweaver.log",
            "history_enabled": True,
            "history_limit": 100,
        },
    }

    with open(temp_config_file, "w", encoding="utf-8") as f:
        yaml.dump(new_content, f, default_flow_style=False, allow_unicode=True)

    # 重新加载配置
    config_manager.reload_config()
    new_config = config_manager.get_config()

    # 验证配置已更新
    assert new_config.local_llm.model == "llama3:70b"
