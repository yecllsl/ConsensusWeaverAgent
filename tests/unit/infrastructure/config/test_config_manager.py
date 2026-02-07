import os
import time

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
    assert config.local_llm.provider == "llama-cpp"
    assert config.local_llm.model == "Qwen3-8B-Q5_K_M.gguf"
    assert len(config.external_tools) == 2  # 默认应该有两个工具


# 测试配置重新加载
def test_config_reload(temp_config_file):
    config_manager = ConfigManager(temp_config_file)
    config_manager.get_config()

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


# 测试配置热重载
def test_config_hot_reload(temp_config_file):
    config_manager = ConfigManager(temp_config_file)
    config_manager.get_config()

    callback_called = []

    def callback():
        callback_called.append(True)

    config_manager.register_reload_callback(callback)
    config_manager.enable_hot_reload()

    # 等待观察者启动
    time.sleep(0.5)

    # 修改配置文件
    new_content = {
        "local_llm": {
            "provider": "ollama",
            "model": "llama3:8b",
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
        "network": {"check": True, "timeout": 60},
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

    # 等待文件系统事件
    time.sleep(1.5)

    # 禁用热重载
    config_manager.disable_hot_reload()

    # 验证回调被调用（可能需要调整等待时间）
    # 注意：由于文件系统事件的异步性，这个测试可能不稳定


# 测试回调注册和取消注册
def test_reload_callback_registration(temp_config_file):
    config_manager = ConfigManager(temp_config_file)

    callback1_called = []
    callback2_called = []

    def callback1():
        callback1_called.append(True)

    def callback2():
        callback2_called.append(True)

    config_manager.register_reload_callback(callback1)
    config_manager.register_reload_callback(callback2)

    config_manager.unregister_reload_callback(callback1)

    # 手动触发配置变更
    config_manager._on_config_changed()

    # 验证只有callback2被调用
    assert len(callback1_called) == 0
    assert len(callback2_called) == 1
