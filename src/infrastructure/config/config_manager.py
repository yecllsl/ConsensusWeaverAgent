import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, cast

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer  # type: ignore

logger = logging.getLogger(__name__)


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
class RetryConfig:
    enabled: bool = True
    auto_retry: bool = True
    max_retries: int = 3
    retry_delay: int = 2
    retry_on_timeout: bool = True
    retry_on_error: bool = True
    exponential_backoff: bool = False


@dataclass
class Config:
    local_llm: LocalLLMConfig
    external_tools: list[ExternalToolConfig]
    network: NetworkConfig
    app: AppConfig
    retry: RetryConfig


class ConfigFileHandler(FileSystemEventHandler):  # type: ignore[misc]
    """配置文件变更处理器"""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback

    def on_modified(self, event: Any) -> None:
        """文件修改事件"""
        if event.is_directory:
            return

        if event.src_path.endswith("config.yaml"):
            self.callback()


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Optional[Config] = None
        self._reload_callbacks: List[Callable[[], None]] = []
        self._observer: Optional[Any] = None
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        config_dict = self._load_config_dict()
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

        # 解析重试配置
        retry_config = RetryConfig(**config_dict.get("retry", {}))

        return Config(
            local_llm=llm_config,
            external_tools=tools_config,
            network=network_config,
            app=app_config,
            retry=retry_config,
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
            "retry": {
                "enabled": True,
                "auto_retry": True,
                "max_retries": 3,
                "retry_delay": 2,
                "retry_on_timeout": True,
                "retry_on_error": True,
                "exponential_backoff": False,
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

    def enable_hot_reload(self) -> None:
        """启用配置热重载"""
        if self._observer is not None:
            return

        self._observer = Observer()
        handler = ConfigFileHandler(self._on_config_changed)
        self._observer.schedule(
            handler, os.path.dirname(self.config_path), recursive=False
        )
        self._observer.start()

    def disable_hot_reload(self) -> None:
        """禁用配置热重载"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def _on_config_changed(self) -> None:
        """配置文件变更回调"""
        try:
            new_config = self._parse_config(self._load_config_dict())
            self.config = new_config

            for callback in self._reload_callbacks:
                callback()

        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")

    def _load_config_dict(self) -> Dict[str, Any]:
        """加载配置字典"""
        if not os.path.exists(self.config_path):
            self._create_default_config()

        with open(self.config_path, "r", encoding="utf-8") as f:
            return cast(Dict[str, Any], yaml.safe_load(f))

    def register_reload_callback(self, callback: Callable[[], None]) -> None:
        """注册配置重载回调"""
        self._reload_callbacks.append(callback)

    def unregister_reload_callback(self, callback: Callable[[], None]) -> None:
        """取消注册配置重载回调"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
