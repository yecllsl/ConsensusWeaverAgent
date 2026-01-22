import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

import yaml


@dataclass
class LocalLLMConfig:
    provider: str
    model: str
    # llama-cpp specific parameters
    model_path: Optional[str] = None
    n_ctx: int = 4096
    n_threads: int = 6
    n_threads_batch: int = 6
    n_batch: int = 512
    max_tokens: int = 512
    top_p: float = 0.9
    top_k: int = 50
    repeat_penalty: float = 1.1
    last_n_tokens_size: int = 64
    use_mlock: bool = True
    use_mmap: bool = True
    n_gpu_layers: int = 0
    rope_freq_base: int = 10000
    rope_freq_scale: float = 1.0
    temperature: float = 0.3
    # ollama specific parameters
    base_url: Optional[str] = None
    timeout: int = 30


@dataclass
class ExternalToolConfig:
    name: str
    command: str
    args: str
    needs_internet: bool
    priority: int
    enabled: bool = True


@dataclass
class NetworkConfig:
    check_before_run: bool
    timeout: int


@dataclass
class AppConfig:
    max_clarification_rounds: int
    max_parallel_tools: int
    log_level: str
    log_file: str
    history_enabled: bool
    history_limit: int


@dataclass
class Config:
    local_llm: LocalLLMConfig
    external_tools: list[ExternalToolConfig]
    network: NetworkConfig
    app: AppConfig


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            self._create_default_config()

        with open(self.config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        self.config = self._parse_config(config_dict)

    def _parse_config(self, config_dict: Dict[str, Any]) -> Config:
        """解析配置字典为Config对象"""
        # 解析本地LLM配置
        llm_config = LocalLLMConfig(**config_dict["local_llm"])

        # 解析外部工具配置
        tools_config = [
            ExternalToolConfig(**tool) for tool in config_dict["external_tools"]
        ]

        # 解析网络配置
        network_config = NetworkConfig(**config_dict["network"])

        # 解析应用配置
        app_config = AppConfig(**config_dict["app"])

        return Config(
            local_llm=llm_config,
            external_tools=tools_config,
            network=network_config,
            app=app_config,
        )

    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = {
            "local_llm": {
                "provider": "llama-cpp",
                "model": "Qwen3-8B-Q5_K_M.gguf",
                "model_path": ".models/qwen/Qwen3-8B-Q5_K_M.gguf",
                "n_ctx": 4096,
                "n_threads": 6,
                "n_threads_batch": 6,
                "n_batch": 512,
                "temperature": 0.3,
            },
            "external_tools": [
                {
                    "name": "iflow",
                    "command": "iflow",
                    "args": "ask --streaming=false",
                    "needs_internet": True,
                    "priority": 1,
                    "enabled": True,
                },
                {
                    "name": "codebuddy",
                    "command": "codebuddy",
                    "args": "ask --format plain",
                    "needs_internet": True,
                    "priority": 2,
                    "enabled": True,
                },
            ],
            "network": {"check_before_run": True, "timeout": 120},
            "app": {
                "max_clarification_rounds": 3,
                "max_parallel_tools": 5,
                "log_level": "info",
                "log_file": "logs/consensusweaver.log",
                "history_enabled": True,
                "history_limit": 100,
            },
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

    def get_config(self) -> Config:
        """获取配置对象"""
        if self.config is None:
            self.load_config()
        # 类型断言：load_config会确保self.config被设置为Config对象
        return cast(Config, self.config)

    def reload_config(self) -> None:
        """重新加载配置文件"""
        self.load_config()
