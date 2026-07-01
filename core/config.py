"""配置加载与管理模块"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800
    slow_mo: int = 0
    user_data_base_dir: str = "./data/user_data"


@dataclass
class PlatformConfig:
    """单个平台配置"""
    enabled: bool = True
    name: str = ""
    base_url: str = ""


@dataclass
class DefaultsConfig:
    """默认参数配置"""
    timeout: int = 120
    min_success: int = 3
    max_concurrent: int = 5


@dataclass
class PathsConfig:
    """路径配置"""
    screenshot_dir: str = "./data/screenshots"
    log_dir: str = "./data/logs"


@dataclass
class Config:
    """全局配置"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    platforms: Dict[str, PlatformConfig] = field(default_factory=dict)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)

    @classmethod
    def load(cls, config_path: str) -> "Config":
        """从 YAML 文件加载配置"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        browser = BrowserConfig(**data.get("browser", {}))

        platforms = {}
        for pid, pdata in data.get("platforms", {}).items():
            platforms[pid] = PlatformConfig(**pdata)

        defaults = DefaultsConfig(**data.get("defaults", {}))
        paths = PathsConfig(**data.get("paths", {}))

        return cls(
            browser=browser,
            platforms=platforms,
            defaults=defaults,
            paths=paths,
        )

    def get_enabled_platforms(self) -> List[str]:
        """获取所有已启用平台的 ID 列表"""
        return [pid for pid, p in self.platforms.items() if p.enabled]
