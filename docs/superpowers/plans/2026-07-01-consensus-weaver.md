# ConsensusWeaver Agent 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 MCP Server，通过 Playwright 浏览器自动化并行向 5 个 AI WebApp 提问，收集答案返回给 LLM 融合。

**Architecture:** 平台适配器架构 — MCP Server 暴露统一工具接口，PlatformManager 负责并发调度，每个 AI 平台一个独立适配器模块，BrowserPool 管理浏览器实例生命周期。

**Tech Stack:** Python 3.11+, FastMCP, Playwright (async), PyYAML, pytest, asyncio

---

## 文件结构总览

| 文件 | 职责 |
|------|------|
| `requirements.txt` | Python 依赖声明 |
| `.gitignore` | Git 忽略规则 |
| `config.yaml` | 运行配置（浏览器、平台、路径、默认参数） |
| `conftest.py` | pytest 根级 fixture（事件循环、配置） |
| `pytest.ini` | pytest 配置 |
| `core/config.py` | 配置加载与校验 |
| `core/browser_pool.py` | 浏览器实例池，管理 Playwright 生命周期和 user data dir |
| `core/platform_manager.py` | 平台注册、并发调度、结果汇总 |
| `adapters/base_adapter.py` | 适配器基类，定义统一接口和 AdapterResult 数据类 |
| `adapters/doubao_adapter.py` | 豆包平台适配器 |
| `adapters/chatglm_adapter.py` | 智谱清言适配器 |
| `adapters/deepseek_adapter.py` | DeepSeek 适配器 |
| `adapters/qianwen_adapter.py` | 千问适配器 |
| `adapters/yuanbao_adapter.py` | 元宝适配器 |
| `utils/logger.py` | 日志工具 |
| `utils/screenshot.py` | 截图工具 |
| `mcp_server.py` | MCP Server 入口，定义 4 个工具 |
| `tests/conftest.py` | 测试级 fixture |
| `tests/unit/test_config.py` | 配置模块单元测试 |
| `tests/unit/test_browser_pool.py` | 浏览器池单元测试 |
| `tests/unit/test_platform_manager.py` | 平台管理器单元测试 |
| `tests/unit/test_base_adapter.py` | 适配器基类单元测试 |
| `tests/integration/test_browser_pool.py` | 浏览器池集成测试 |
| `tests/integration/test_platform_manager.py` | 平台管理器集成测试 |
| `tests/e2e/test_mcp_tools.py` | MCP 工具 E2E 测试 |

---

## Task 1: 项目骨架与依赖

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `config.yaml`
- Create: `pytest.ini`
- Create: `core/__init__.py`
- Create: `adapters/__init__.py`
- Create: `utils/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/e2e/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastmcp>=0.1.0
playwright>=1.40.0
pyyaml>=6.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.egg

# 虚拟环境
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 运行数据
data/user_data/
data/screenshots/
data/logs/

# 测试
.pytest_cache/
test_results/
allure_report/

# 临时文件
*.tmp
*.bak
```

- [ ] **Step 3: 创建 config.yaml**

```yaml
# 浏览器配置
browser:
  headless: true
  viewport_width: 1280
  viewport_height: 800
  slow_mo: 0
  user_data_base_dir: "./data/user_data"

# 平台配置
platforms:
  doubao:
    enabled: true
    name: "豆包"
    base_url: "https://www.doubao.com"
  chatglm:
    enabled: true
    name: "智谱清言"
    base_url: "https://chatglm.cn"
  deepseek:
    enabled: true
    name: "DeepSeek"
    base_url: "https://chat.deepseek.com"
  qianwen:
    enabled: true
    name: "千问"
    base_url: "https://qianwen.com/chat"
  yuanbao:
    enabled: true
    name: "元宝"
    base_url: "https://yuanbao.tencent.com/chat"

# 默认参数
defaults:
  timeout: 120
  min_success: 3
  max_concurrent: 5

# 路径配置
paths:
  screenshot_dir: "./data/screenshots"
  log_dir: "./data/logs"
```

- [ ] **Step 4: 创建 pytest.ini**

```ini
[pytest]
asyncio_mode = auto
markers =
    slow: 标记慢测试（真实浏览器调用）
    integration: 集成测试
    e2e: 端到端测试
testpaths = tests
```

- [ ] **Step 5: 创建所有 __init__.py**

创建以下空文件（内容为空即可）：
- `core/__init__.py`
- `adapters/__init__.py`
- `utils/__init__.py`
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`

- [ ] **Step 6: 创建数据目录**

```bash
mkdir -p data/user_data/doubao data/user_data/chatglm data/user_data/deepseek data/user_data/qianwen data/user_data/yuanbao data/screenshots data/logs
```

- [ ] **Step 7: 安装依赖并验证**

Run:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```
Expected: 安装成功，无报错

- [ ] **Step 8: 初始化 git 并提交**

```bash
git init
git add .
git commit -m "chore: 项目骨架与依赖初始化"
```

---

## Task 2: 配置模块 (core/config.py)

**Files:**
- Create: `core/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: 编写配置模块的失败测试**

```python
# tests/unit/test_config.py
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.config'`

- [ ] **Step 3: 实现配置模块**

```python
# core/config.py
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
        """从 YAML 文件加载配置

        Args:
            config_path: YAML 配置文件路径

        Returns:
            Config 实例

        Raises:
            FileNotFoundError: 配置文件不存在
        """
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add core/config.py tests/unit/test_config.py
git commit -m "feat: 配置模块 - YAML 加载与校验"
```

---

## Task 3: 日志工具 (utils/logger.py)

**Files:**
- Create: `utils/logger.py`
- Create: `tests/unit/test_logger.py`

- [ ] **Step 1: 编写日志工具的失败测试**

```python
# tests/unit/test_logger.py
"""日志工具单元测试"""
import logging
from utils.logger import get_logger


def test_get_logger_returns_logger():
    """测试 get_logger 返回 Logger 实例"""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)


def test_get_logger_same_name_returns_same_instance():
    """测试相同名称返回同一个 Logger 实例"""
    logger1 = get_logger("test_module")
    logger2 = get_logger("test_module")
    assert logger1 is logger2


def test_logger_has_handler():
    """测试 logger 至少有一个 handler"""
    logger = get_logger("test_handler_check")
    assert len(logger.handlers) >= 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_logger.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.logger'`

- [ ] **Step 3: 实现日志工具**

```python
# utils/logger.py
"""日志工具模块"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def get_logger(name: str, log_dir: str = None) -> logging.Logger:
    """获取命名日志器

    Args:
        name: 日志器名称，通常用模块名
        log_dir: 日志文件保存目录，为 None 时仅输出到控制台

    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler（可选）
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            log_path / f"{today}.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_logger.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add utils/logger.py tests/unit/test_logger.py
git commit -m "feat: 日志工具模块"
```

---

## Task 4: 适配器基类 (adapters/base_adapter.py)

**Files:**
- Create: `adapters/base_adapter.py`
- Create: `tests/unit/test_base_adapter.py`

- [ ] **Step 1: 编写适配器基类的失败测试**

```python
# tests/unit/test_base_adapter.py
"""适配器基类单元测试"""
import pytest
from adapters.base_adapter import BaseAdapter, AdapterResult


def test_adapter_result_success():
    """测试 AdapterResult 成功状态"""
    result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="测试答案",
        duration_ms=1000,
        screenshot_path="/tmp/test.png",
        error=None,
    )
    assert result.platform == "doubao"
    assert result.status == "success"
    assert result.answer == "测试答案"
    assert result.is_success is True


def test_adapter_result_failure():
    """测试 AdapterResult 失败状态"""
    result = AdapterResult(
        platform="chatglm",
        platform_name="智谱清言",
        status="failed",
        answer=None,
        duration_ms=120000,
        screenshot_path="/tmp/test.png",
        error="超时",
    )
    assert result.status == "failed"
    assert result.is_success is False
    assert result.error == "超时"


def test_adapter_result_to_dict():
    """测试 AdapterResult 转 dict"""
    result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="答案",
        duration_ms=500,
        screenshot_path="/tmp/s.png",
        error=None,
    )
    d = result.to_dict()
    assert d["platform"] == "doubao"
    assert d["platform_name"] == "豆包"
    assert d["status"] == "success"
    assert d["answer"] == "答案"
    assert d["duration_ms"] == 500
    assert d["screenshot_path"] == "/tmp/s.png"
    assert d["error"] is None


def test_base_adapter_is_abstract():
    """测试 BaseAdapter 不能直接实例化"""
    with pytest.raises(TypeError):
        BaseAdapter(
            platform_id="test",
            platform_name="测试",
            base_url="https://example.com",
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_base_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.base_adapter'`

- [ ] **Step 3: 实现适配器基类**

```python
# adapters/base_adapter.py
"""平台适配器基类，定义统一接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import get_logger


@dataclass
class AdapterResult:
    """适配器执行结果"""
    platform: str
    platform_name: str
    status: str  # "success" 或 "failed"
    answer: Optional[str]
    duration_ms: int
    screenshot_path: Optional[str]
    error: Optional[str]

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == "success"

    def to_dict(self) -> dict:
        """转为字典"""
        return asdict(self)


class BaseAdapter(ABC):
    """平台适配器基类

    所有 AI 平台适配器继承此类，实现统一的接口。
    每个适配器负责一个平台的浏览器自动化操作。
    """

    def __init__(self, platform_id: str, platform_name: str, base_url: str):
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.base_url = base_url
        self.logger = get_logger(f"adapter.{platform_id}")

    @abstractmethod
    async def navigate_to_chat(self) -> None:
        """导航到聊天页面"""
        pass

    @abstractmethod
    async def check_login_status(self) -> bool:
        """检查是否已登录，返回 True/False"""
        pass

    @abstractmethod
    async def send_question(self, question: str) -> None:
        """在输入框中输入问题并发送"""
        pass

    @abstractmethod
    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待回答完成，返回答案文本"""
        pass

    @abstractmethod
    async def capture_screenshot(self, save_path: str) -> str:
        """截取当前页面，返回保存路径"""
        pass

    @abstractmethod
    async def new_chat(self) -> None:
        """开启新对话"""
        pass

    async def ask(self, question: str, timeout: int = 120) -> AdapterResult:
        """完整提问流程封装

        依次执行：导航 → 登录检查 → 新对话 → 发送 → 等待 → 提取 → 截图

        Args:
            question: 问题文本
            timeout: 超时秒数

        Returns:
            AdapterResult 执行结果
        """
        start_time = datetime.now()
        screenshot_path = None
        error_msg = None
        answer = None

        try:
            # 1. 导航到聊天页
            await self.navigate_to_chat()

            # 2. 检查登录状态
            is_logged_in = await self.check_login_status()
            if not is_logged_in:
                raise RuntimeError(f"未登录: 请先调用 check_login 登录 {self.platform_name}")

            # 3. 开启新对话
            await self.new_chat()

            # 4. 输入并发送问题
            await self.send_question(question)

            # 5. 等待回答完成并提取答案
            answer = await self.wait_for_answer(timeout)

            # 6. 截图保存
            screenshot_path = await self._save_screenshot()

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"{self.platform_name} 提问失败: {error_msg}")
            # 失败时也尝试截图
            try:
                screenshot_path = await self._save_screenshot()
            except Exception:
                pass

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        status = "success" if error_msg is None else "failed"

        return AdapterResult(
            platform=self.platform_id,
            platform_name=self.platform_name,
            status=status,
            answer=answer,
            duration_ms=duration_ms,
            screenshot_path=screenshot_path,
            error=error_msg,
        )

    async def _save_screenshot(self) -> Optional[str]:
        """保存截图，子类可覆盖以指定保存路径"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"./data/screenshots/{self.platform_id}_{timestamp}.png"
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            return await self.capture_screenshot(save_path)
        except Exception:
            return None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_base_adapter.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/base_adapter.py tests/unit/test_base_adapter.py
git commit -m "feat: 适配器基类与 AdapterResult 数据结构"
```

---

## Task 5: 浏览器实例池 (core/browser_pool.py)

**Files:**
- Create: `core/browser_pool.py`
- Create: `tests/unit/test_browser_pool.py`

- [ ] **Step 1: 编写浏览器池的失败测试**

```python
# tests/unit/test_browser_pool.py
"""浏览器池单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.browser_pool import BrowserPool
from core.config import BrowserConfig


@pytest.fixture
def browser_config():
    """浏览器配置 fixture"""
    return BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        slow_mo=0,
        user_data_base_dir="./data/user_data",
    )


def test_browser_pool_init(browser_config):
    """测试浏览器池初始化"""
    pool = BrowserPool(browser_config)
    assert pool.config == browser_config
    assert pool._playwright is None
    assert pool._contexts == {}


def test_browser_pool_user_data_path(browser_config):
    """测试用户数据目录路径生成"""
    pool = BrowserPool(browser_config)
    path = pool._get_user_data_path("doubao")
    assert "doubao" in path
    assert "user_data" in path
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_browser_pool.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.browser_pool'`

- [ ] **Step 3: 实现浏览器池**

```python
# core/browser_pool.py
"""浏览器实例池，管理 Playwright 生命周期和用户数据目录"""
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from core.config import BrowserConfig
from utils.logger import get_logger


class BrowserPool:
    """浏览器实例池

    管理多个浏览器上下文，每个平台使用独立的用户数据目录
    以持久化登录态（cookies、localStorage）。
    """

    def __init__(self, config: BrowserConfig):
        self.config = config
        self._playwright = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self.logger = get_logger("browser_pool")

    def _get_user_data_path(self, platform_id: str) -> str:
        """获取指定平台的用户数据目录路径"""
        return str(Path(self.config.user_data_base_dir) / platform_id)

    async def start(self) -> None:
        """启动 Playwright 运行时"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self.logger.info("Playwright 运行时已启动")

    async def stop(self) -> None:
        """关闭所有浏览器上下文和 Playwright 运行时"""
        # 关闭所有页面
        for platform_id, page in self._pages.items():
            try:
                await page.close()
            except Exception as e:
                self.logger.warning(f"关闭页面 {platform_id} 失败: {e}")
        self._pages.clear()

        # 关闭所有上下文
        for platform_id, context in self._contexts.items():
            try:
                await context.close()
            except Exception as e:
                self.logger.warning(f"关闭上下文 {platform_id} 失败: {e}")
        self._contexts.clear()

        # 停止 Playwright
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            self.logger.info("Playwright 运行时已停止")

    async def get_context(self, platform_id: str, headless: Optional[bool] = None) -> BrowserContext:
        """获取或创建指定平台的浏览器上下文

        每个平台使用独立的用户数据目录，持久化登录态。

        Args:
            platform_id: 平台 ID
            headless: 是否无头模式，为 None 时使用配置默认值

        Returns:
            BrowserContext 实例
        """
        if platform_id in self._contexts:
            return self._contexts[platform_id]

        if self._playwright is None:
            await self.start()

        user_data_path = self._get_user_data_path(platform_id)
        Path(user_data_path).mkdir(parents=True, exist_ok=True)

        is_headless = headless if headless is not None else self.config.headless

        # 使用持久化上下文，保存登录态
        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=is_headless,
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            slow_mo=self.config.slow_mo,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._contexts[platform_id] = context
        self.logger.info(f"为平台 {platform_id} 创建浏览器上下文")
        return context

    async def get_page(self, platform_id: str, headless: Optional[bool] = None) -> Page:
        """获取或创建指定平台的页面

        复用已有页面，避免重复创建。

        Args:
            platform_id: 平台 ID
            headless: 是否无头模式

        Returns:
            Page 实例
        """
        if platform_id in self._pages:
            # 检查页面是否仍然有效
            try:
                _ = self._pages[platform_id].url
                return self._pages[platform_id]
            except Exception:
                del self._pages[platform_id]

        context = await self.get_context(platform_id, headless)

        # 复用已有页面或新建
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()

        self._pages[platform_id] = page
        return page

    async def close_context(self, platform_id: str) -> None:
        """关闭指定平台的浏览器上下文"""
        if platform_id in self._pages:
            try:
                await self._pages[platform_id].close()
            except Exception:
                pass
            del self._pages[platform_id]

        if platform_id in self._contexts:
            try:
                await self._contexts[platform_id].close()
            except Exception:
                pass
            del self._contexts[platform_id]
            self.logger.info(f"已关闭平台 {platform_id} 的浏览器上下文")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_browser_pool.py -v`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add core/browser_pool.py tests/unit/test_browser_pool.py
git commit -m "feat: 浏览器实例池 - 持久化上下文管理"
```

---

## Task 6: 豆包适配器 (adapters/doubao_adapter.py)

**Files:**
- Create: `adapters/doubao_adapter.py`
- Create: `tests/unit/test_doubao_adapter.py`

- [ ] **Step 1: 编写豆包适配器的失败测试**

```python
# tests/unit/test_doubao_adapter.py
"""豆包适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from adapters.doubao_adapter import DoubaoAdapter
from adapters.base_adapter import AdapterResult


@pytest.fixture
def mock_page():
    """模拟 Page 对象"""
    page = AsyncMock()
    page.url = "https://www.doubao.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    """豆包适配器 fixture"""
    return DoubaoAdapter(page=mock_page)


def test_doubao_adapter_attributes(adapter):
    """测试豆包适配器属性"""
    assert adapter.platform_id == "doubao"
    assert adapter.platform_name == "豆包"
    assert adapter.base_url == "https://www.doubao.com"


@pytest.mark.asyncio
async def test_doubao_navigate_to_chat(adapter, mock_page):
    """测试导航到聊天页"""
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())

    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once_with("https://www.doubao.com/chat")


@pytest.mark.asyncio
async def test_doubao_check_login_status_logged_in(adapter, mock_page):
    """测试已登录状态检测"""
    mock_page.url = "https://www.doubao.com/chat/123"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())

    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_doubao_check_login_status_not_logged_in(adapter, mock_page):
    """测试未登录状态检测"""
    mock_page.url = "https://www.doubao.com"
    mock_page.query_selector = AsyncMock(return_value=None)

    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_doubao_send_question(adapter, mock_page):
    """测试发送问题"""
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()

    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_doubao_capture_screenshot(adapter, mock_page):
    """测试截图"""
    mock_page.screenshot = AsyncMock(return_value=None)

    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
    mock_page.screenshot.assert_called_once()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_doubao_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.doubao_adapter'`

- [ ] **Step 3: 实现豆包适配器**

```python
# adapters/doubao_adapter.py
"""豆包平台适配器"""
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter
from utils.logger import get_logger


class DoubaoAdapter(BaseAdapter):
    """豆包 (doubao.com) 适配器"""

    def __init__(self, page: Page):
        super().__init__(
            platform_id="doubao",
            platform_name="豆包",
            base_url="https://www.doubao.com",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到豆包聊天页面"""
        await self.page.goto("https://www.doubao.com/chat", wait_until="domcontentloaded")
        # 等待页面主要内容加载
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到豆包聊天页")

    async def check_login_status(self) -> bool:
        """检查豆包登录状态

        通过 URL 和 DOM 元素双重判断：
        1. URL 是否停留在聊天页（未登录会跳转到首页/登录页）
        2. 是否存在聊天输入框
        """
        checks_passed = 0

        # 检查 1: URL 是否包含 /chat 路径
        if "/chat" in self.page.url:
            checks_passed += 1

        # 检查 2: 是否存在聊天输入框
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1

        self.logger.debug(f"豆包登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在豆包输入框中输入问题并发送"""
        # 等待输入框可用
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)

        # 按回车发送
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待豆包回答完成并提取答案文本

        策略：
        1. 等待发送按钮从禁用恢复为可用（表示回答完成）
        2. 定位最后一条 AI 回答气泡
        3. 提取 innerText
        """
        import asyncio

        # 等待回答生成完成：检测输入框是否重新可用
        # 豆包在生成回答时输入框会被禁用，完成后恢复
        elapsed = 0
        poll_interval = 1  # 每秒检测一次
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # 检查输入框是否可用（回答完成的标志）
            textarea = await self.page.query_selector("textarea")
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    # 输入框可用，可能回答已完成
                    # 额外等待 2 秒确保内容稳定
                    await asyncio.sleep(2)
                    break

        # 提取最后一条 AI 回答
        # 豆包的回答气泡通常在消息列表的最后一个
        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到豆包的回答内容")

        self.logger.info(f"豆包回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本

        尝试多种选择器定位回答气泡，适配豆包页面结构变更。
        """
        # 尝试的选择器列表（按优先级排列）
        selectors = [
            # AI 回答消息容器的常见选择器
            "[data-testid='receive_message']",
            ".message-assistant",
            ".chat-message-ai",
            # 通用消息容器（取最后一个）
            "[class*='message-content']",
            "[class*='answer-content']",
            "[class*='markdown']",
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                last_element = elements[-1]
                text = await last_element.inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()

        # 兜底方案：获取整个对话区域的文本
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) {
                return messages[messages.length - 1].innerText;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取豆包当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的豆包对话

        优先方案：点击"新对话"按钮
        备选方案：刷新页面
        """
        try:
            # 尝试点击新对话按钮
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('新建聊天')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass

        # 备选方案：刷新页面
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_doubao_adapter.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/doubao_adapter.py tests/unit/test_doubao_adapter.py
git commit -m "feat: 豆包平台适配器"
```

---

## Task 7: 智谱清言适配器 (adapters/chatglm_adapter.py)

**Files:**
- Create: `adapters/chatglm_adapter.py`
- Create: `tests/unit/test_chatglm_adapter.py`

- [ ] **Step 1: 编写智谱清言适配器的失败测试**

```python
# tests/unit/test_chatglm_adapter.py
"""智谱清言适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.chatglm_adapter import ChatGLMAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://chatglm.cn/main/alltoolsdetail"
    return page


@pytest.fixture
def adapter(mock_page):
    return ChatGLMAdapter(page=mock_page)


def test_chatglm_adapter_attributes(adapter):
    assert adapter.platform_id == "chatglm"
    assert adapter.platform_name == "智谱清言"
    assert adapter.base_url == "https://chatglm.cn"


@pytest.mark.asyncio
async def test_chatglm_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_chatglm_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://chatglm.cn/main/alltoolsdetail"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_chatglm_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://chatglm.cn/login"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_chatglm_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_chatglm_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_chatglm_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.chatglm_adapter'`

- [ ] **Step 3: 实现智谱清言适配器**

```python
# adapters/chatglm_adapter.py
"""智谱清言平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class ChatGLMAdapter(BaseAdapter):
    """智谱清言 (chatglm.cn) 适配器"""

    def __init__(self, page: Page):
        super().__init__(
            platform_id="chatglm",
            platform_name="智谱清言",
            base_url="https://chatglm.cn",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到智谱清言聊天页面"""
        await self.page.goto("https://chatglm.cn/main/alltoolsdetail", wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到智谱清言聊天页")

    async def check_login_status(self) -> bool:
        """检查智谱清言登录状态

        通过 URL 和 DOM 元素双重判断：
        1. URL 是否包含 main/alltoolsdetail（未登录会跳转到登录页）
        2. 是否存在聊天输入框
        """
        checks_passed = 0

        # 检查 1: URL 是否在聊天页
        if "main" in self.page.url and "login" not in self.page.url:
            checks_passed += 1

        # 检查 2: 是否存在输入框
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1

        self.logger.debug(f"智谱清言登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在智谱清言输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待智谱清言回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # 检测回答是否完成：发送按钮恢复可用
            textarea = await self.page.query_selector("textarea")
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    await asyncio.sleep(2)
                    break

        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到智谱清言的回答内容")

        self.logger.info(f"智谱清言回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本"""
        selectors = [
            "[class*='answer']",
            "[class*='ai-message']",
            "[class*='markdown-body']",
            "[class*='message-content']",
            "[class*='content-area']",
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                last_element = elements[-1]
                text = await last_element.inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()

        # 兜底方案
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) {
                return messages[messages.length - 1].innerText;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取智谱清言当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的智谱清言对话"""
        try:
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('新建')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass

        # 备选：刷新页面
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_chatglm_adapter.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/chatglm_adapter.py tests/unit/test_chatglm_adapter.py
git commit -m "feat: 智谱清言平台适配器"
```

---

## Task 8: DeepSeek 适配器 (adapters/deepseek_adapter.py)

**Files:**
- Create: `adapters/deepseek_adapter.py`
- Create: `tests/unit/test_deepseek_adapter.py`

- [ ] **Step 1: 编写 DeepSeek 适配器的失败测试**

```python
# tests/unit/test_deepseek_adapter.py
"""DeepSeek 适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.deepseek_adapter import DeepSeekAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://chat.deepseek.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return DeepSeekAdapter(page=mock_page)


def test_deepseek_adapter_attributes(adapter):
    assert adapter.platform_id == "deepseek"
    assert adapter.platform_name == "DeepSeek"
    assert adapter.base_url == "https://chat.deepseek.com"


@pytest.mark.asyncio
async def test_deepseek_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_deepseek_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://chat.deepseek.com/chat/123"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_deepseek_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://chat.deepseek.com/sign_in"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_deepseek_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_deepseek_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_deepseek_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.deepseek_adapter'`

- [ ] **Step 3: 实现 DeepSeek 适配器**

```python
# adapters/deepseek_adapter.py
"""DeepSeek 平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    """DeepSeek (chat.deepseek.com) 适配器

    注意：DeepSeek 有「深度思考」功能，回答时会有思考过程。
    本适配器只提取最终答案，不包含思考过程。
    """

    def __init__(self, page: Page):
        super().__init__(
            platform_id="deepseek",
            platform_name="DeepSeek",
            base_url="https://chat.deepseek.com",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到 DeepSeek 聊天页面"""
        await self.page.goto("https://chat.deepseek.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到 DeepSeek 聊天页")

    async def check_login_status(self) -> bool:
        """检查 DeepSeek 登录状态

        通过 URL 和 DOM 元素双重判断：
        1. URL 是否在聊天页（未登录会跳转到 sign_in）
        2. 是否存在聊天输入框
        """
        checks_passed = 0

        # 检查 1: URL 是否在聊天页（不含 sign_in）
        if "chat" in self.page.url and "sign_in" not in self.page.url:
            checks_passed += 1

        # 检查 2: 是否存在输入框
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1

        self.logger.debug(f"DeepSeek 登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在 DeepSeek 输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待 DeepSeek 回答完成并提取答案

        DeepSeek 的特殊处理：
        - 可能有「思考过程」展开/收起，需跳过
        - 只提取最终答案部分
        """
        elapsed = 0
        poll_interval = 1
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # 检测回答是否完成：检查停止生成按钮是否消失
            stop_btn = await self.page.query_selector("[class*='stop'], [aria-label='Stop']")
            if not stop_btn:
                # 停止按钮消失，回答可能已完成
                await asyncio.sleep(2)
                break

        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到 DeepSeek 的回答内容")

        self.logger.info(f"DeepSeek 回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本

        DeepSeek 的回答结构：
        - 可能包含「思考过程」区块（class 中含 think）
        - 最终答案在单独的消息区块中
        优先提取非思考过程的内容。
        """
        # 尝试定位回答内容（跳过思考过程）
        selectors = [
            # 最终回答内容（排除思考过程）
            "div[class*='markdown']:not([class*='think'])",
            "[class*='answer-content']",
            "[class*='message-content']",
            "[class*='ai-message']",
            "[class*='response']",
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                last_element = elements[-1]
                text = await last_element.inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()

        # 兜底方案
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) {
                return messages[messages.length - 1].innerText;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取 DeepSeek 当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的 DeepSeek 对话"""
        try:
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('New Chat')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass

        # 备选：刷新页面
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_deepseek_adapter.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/deepseek_adapter.py tests/unit/test_deepseek_adapter.py
git commit -m "feat: DeepSeek 平台适配器"
```

---

## Task 9: 千问适配器 (adapters/qianwen_adapter.py)

**Files:**
- Create: `adapters/qianwen_adapter.py`
- Create: `tests/unit/test_qianwen_adapter.py`

- [ ] **Step 1: 编写千问适配器的失败测试**

```python
# tests/unit/test_qianwen_adapter.py
"""千问适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.qianwen_adapter import QianwenAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://qianwen.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return QianwenAdapter(page=mock_page)


def test_qianwen_adapter_attributes(adapter):
    assert adapter.platform_id == "qianwen"
    assert adapter.platform_name == "千问"
    assert adapter.base_url == "https://qianwen.com/chat"


@pytest.mark.asyncio
async def test_qianwen_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_qianwen_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://qianwen.com/chat"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_qianwen_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://qianwen.com/login"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_qianwen_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_qianwen_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_qianwen_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.qianwen_adapter'`

- [ ] **Step 3: 实现千问适配器**

```python
# adapters/qianwen_adapter.py
"""千问平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class QianwenAdapter(BaseAdapter):
    """千问 (qianwen.com) 适配器"""

    def __init__(self, page: Page):
        super().__init__(
            platform_id="qianwen",
            platform_name="千问",
            base_url="https://qianwen.com/chat",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到千问聊天页面"""
        await self.page.goto("https://qianwen.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到千问聊天页")

    async def check_login_status(self) -> bool:
        """检查千问登录状态

        通过 URL 和 DOM 元素双重判断：
        1. URL 是否在聊天页（未登录会跳转到登录页）
        2. 是否存在聊天输入框
        """
        checks_passed = 0

        # 检查 1: URL 是否在聊天页
        if "chat" in self.page.url and "login" not in self.page.url:
            checks_passed += 1

        # 检查 2: 是否存在输入框
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1

        self.logger.debug(f"千问登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在千问输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待千问回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # 检测回答是否完成：发送按钮恢复可用
            textarea = await self.page.query_selector("textarea")
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    await asyncio.sleep(2)
                    break

        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到千问的回答内容")

        self.logger.info(f"千问回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本"""
        selectors = [
            "[class*='answer']",
            "[class*='ai-message']",
            "[class*='markdown-body']",
            "[class*='message-content']",
            "[class*='response']",
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                last_element = elements[-1]
                text = await last_element.inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()

        # 兜底方案
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) {
                return messages[messages.length - 1].innerText;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取千问当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的千问对话"""
        try:
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('新建')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass

        # 备选：刷新页面
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_qianwen_adapter.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/qianwen_adapter.py tests/unit/test_qianwen_adapter.py
git commit -m "feat: 千问平台适配器"
```

---

## Task 10: 元宝适配器 (adapters/yuanbao_adapter.py)

**Files:**
- Create: `adapters/yuanbao_adapter.py`
- Create: `tests/unit/test_yuanbao_adapter.py`

- [ ] **Step 1: 编写元宝适配器的失败测试**

```python
# tests/unit/test_yuanbao_adapter.py
"""元宝适配器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from adapters.yuanbao_adapter import YuanbaoAdapter


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://yuanbao.tencent.com/chat"
    return page


@pytest.fixture
def adapter(mock_page):
    return YuanbaoAdapter(page=mock_page)


def test_yuanbao_adapter_attributes(adapter):
    assert adapter.platform_id == "yuanbao"
    assert adapter.platform_name == "元宝"
    assert adapter.base_url == "https://yuanbao.tencent.com/chat"


@pytest.mark.asyncio
async def test_yuanbao_navigate_to_chat(adapter, mock_page):
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    await adapter.navigate_to_chat()
    mock_page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_yuanbao_check_login_status_logged_in(adapter, mock_page):
    mock_page.url = "https://yuanbao.tencent.com/chat/123"
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    result = await adapter.check_login_status()
    assert result is True


@pytest.mark.asyncio
async def test_yuanbao_check_login_status_not_logged_in(adapter, mock_page):
    mock_page.url = "https://yuanbao.tencent.com/login"
    mock_page.query_selector = AsyncMock(return_value=None)
    result = await adapter.check_login_status()
    assert result is False


@pytest.mark.asyncio
async def test_yuanbao_send_question(adapter, mock_page):
    mock_page.wait_for_selector = AsyncMock(return_value=AsyncMock())
    mock_page.fill = AsyncMock()
    mock_page.keyboard = AsyncMock()
    await adapter.send_question("测试问题")
    mock_page.wait_for_selector.assert_called()


@pytest.mark.asyncio
async def test_yuanbao_capture_screenshot(adapter, mock_page):
    mock_page.screenshot = AsyncMock(return_value=None)
    result = await adapter.capture_screenshot("/tmp/test.png")
    assert result == "/tmp/test.png"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_yuanbao_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.yuanbao_adapter'`

- [ ] **Step 3: 实现元宝适配器**

```python
# adapters/yuanbao_adapter.py
"""元宝平台适配器"""
import asyncio
from typing import Optional

from playwright.async_api import Page

from adapters.base_adapter import BaseAdapter


class YuanbaoAdapter(BaseAdapter):
    """元宝 (yuanbao.tencent.com) 适配器

    注意：腾讯系产品可能有额外验证（如二维码登录确认），
    登录态检查需更严格。
    """

    def __init__(self, page: Page):
        super().__init__(
            platform_id="yuanbao",
            platform_name="元宝",
            base_url="https://yuanbao.tencent.com/chat",
        )
        self.page = page

    async def navigate_to_chat(self) -> None:
        """导航到元宝聊天页面"""
        await self.page.goto("https://yuanbao.tencent.com/chat", wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=30000)
        self.logger.info("已导航到元宝聊天页")

    async def check_login_status(self) -> bool:
        """检查元宝登录状态

        通过 URL 和 DOM 元素双重判断：
        1. URL 是否在聊天页（未登录会跳转到登录页）
        2. 是否存在聊天输入框
        """
        checks_passed = 0

        # 检查 1: URL 是否在聊天页
        if "chat" in self.page.url and "login" not in self.page.url:
            checks_passed += 1

        # 检查 2: 是否存在输入框
        textarea = await self.page.query_selector("textarea")
        if textarea:
            checks_passed += 1

        self.logger.debug(f"元宝登录检测: {checks_passed}/2 项通过")
        return checks_passed >= 2

    async def send_question(self, question: str) -> None:
        """在元宝输入框中输入问题并发送"""
        textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        await textarea.click()
        await self.page.fill("textarea", question)
        await self.page.keyboard.press("Enter")
        self.logger.info(f"已发送问题: {question[:50]}...")

    async def wait_for_answer(self, timeout: int = 120) -> str:
        """等待元宝回答完成并提取答案"""
        elapsed = 0
        poll_interval = 1
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            # 检测回答是否完成：发送按钮恢复可用
            textarea = await self.page.query_selector("textarea")
            if textarea:
                is_disabled = await textarea.get_attribute("disabled")
                if is_disabled is None:
                    await asyncio.sleep(2)
                    break

        answer = await self._extract_last_answer()
        if not answer:
            raise RuntimeError("未能提取到元宝的回答内容")

        self.logger.info(f"元宝回答已提取，长度: {len(answer)} 字符")
        return answer

    async def _extract_last_answer(self) -> Optional[str]:
        """提取最后一条 AI 回答文本"""
        selectors = [
            "[class*='answer']",
            "[class*='ai-message']",
            "[class*='markdown-body']",
            "[class*='message-content']",
            "[class*='response']",
            "[class*='chat-content']",
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                last_element = elements[-1]
                text = await last_element.inner_text()
                if text and len(text.strip()) > 0:
                    return text.strip()

        # 兜底方案
        all_text = await self.page.evaluate("""() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="chat"]');
            if (messages.length > 0) {
                return messages[messages.length - 1].innerText;
            }
            return '';
        }""")
        return all_text.strip() if all_text else None

    async def capture_screenshot(self, save_path: str) -> str:
        """截取元宝当前页面"""
        await self.page.screenshot(path=save_path, full_page=False)
        return save_path

    async def new_chat(self) -> None:
        """开启新的元宝对话"""
        try:
            new_chat_selectors = [
                "button:has-text('新对话')",
                "button:has-text('新建')",
                "[class*='new-chat']",
                "[class*='new-conversation']",
            ]
            for selector in new_chat_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    self.logger.info("已通过按钮开启新对话")
                    return
        except Exception:
            pass

        # 备选：刷新页面
        await self.page.reload(wait_until="domcontentloaded")
        await self.page.wait_for_selector("textarea", timeout=15000)
        self.logger.info("已通过刷新页面开启新对话")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_yuanbao_adapter.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add adapters/yuanbao_adapter.py tests/unit/test_yuanbao_adapter.py
git commit -m "feat: 元宝平台适配器"
```

---

## Task 11: 平台管理器 (core/platform_manager.py)

**Files:**
- Create: `core/platform_manager.py`
- Create: `tests/unit/test_platform_manager.py`

- [ ] **Step 1: 编写平台管理器的失败测试**

```python
# tests/unit/test_platform_manager.py
"""平台管理器单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.platform_manager import PlatformManager
from core.config import Config, BrowserConfig, PlatformConfig, DefaultsConfig, PathsConfig
from adapters.base_adapter import AdapterResult


@pytest.fixture
def test_config():
    """测试配置"""
    return Config(
        browser=BrowserConfig(headless=True, viewport_width=1280, viewport_height=800, slow_mo=0, user_data_base_dir="./data/user_data"),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
        },
        defaults=DefaultsConfig(timeout=120, min_success=3, max_concurrent=5),
        paths=PathsConfig(screenshot_dir="./data/screenshots", log_dir="./data/logs"),
    )


def test_platform_manager_init(test_config):
    """测试平台管理器初始化"""
    mgr = PlatformManager(test_config)
    assert mgr.config == test_config
    assert len(mgr._adapter_registry) == 5  # 注册了 5 个适配器类


def test_platform_manager_get_enabled_platforms(test_config):
    """测试获取已启用平台"""
    mgr = PlatformManager(test_config)
    enabled = mgr.get_enabled_platforms()
    assert "doubao" in enabled
    assert "chatglm" in enabled


@pytest.mark.asyncio
async def test_platform_manager_ask_single_platform(test_config):
    """测试单平台提问（使用 mock）"""
    mgr = PlatformManager(test_config)

    # Mock 适配器实例
    mock_result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="测试答案",
        duration_ms=1000,
        screenshot_path=None,
        error=None,
    )

    mock_adapter = AsyncMock()
    mock_adapter.ask = AsyncMock(return_value=mock_result)
    mock_adapter.platform_id = "doubao"
    mock_adapter.platform_name = "豆包"

    # Mock _create_adapter 方法
    mgr._create_adapter = AsyncMock(return_value=mock_adapter)
    mgr._browser_pool = AsyncMock()
    mgr._browser_pool.get_page = AsyncMock(return_value=AsyncMock())

    result = await mgr.ask_question("测试问题", ["doubao"], timeout=10, min_success=1)

    assert result["success"] is True
    assert result["success_count"] == 1
    assert result["total_count"] == 1
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_platform_manager_min_success_logic(test_config):
    """测试 min_success 逻辑"""
    mgr = PlatformManager(test_config)

    # 两个平台都失败
    mock_result_fail = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="failed",
        answer=None,
        duration_ms=5000,
        screenshot_path=None,
        error="超时",
    )

    mock_adapter = AsyncMock()
    mock_adapter.ask = AsyncMock(return_value=mock_result_fail)

    mgr._create_adapter = AsyncMock(return_value=mock_adapter)
    mgr._browser_pool = AsyncMock()
    mgr._browser_pool.get_page = AsyncMock(return_value=AsyncMock())

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is False  # 0 成功 < 1 最小要求
    assert result["success_count"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/unit/test_platform_manager.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.platform_manager'`

- [ ] **Step 3: 实现平台管理器**

```python
# core/platform_manager.py
"""平台管理器 - 平台注册、并发调度、结果汇总"""
import asyncio
from typing import Dict, List, Optional, Type

from adapters.base_adapter import BaseAdapter, AdapterResult
from adapters.doubao_adapter import DoubaoAdapter
from adapters.chatglm_adapter import ChatGLMAdapter
from adapters.deepseek_adapter import DeepSeekAdapter
from adapters.qianwen_adapter import QianwenAdapter
from adapters.yuanbao_adapter import YuanbaoAdapter
from core.browser_pool import BrowserPool
from core.config import Config
from utils.logger import get_logger


class PlatformManager:
    """平台管理器

    负责平台适配器的注册与发现、并发调度各平台提问、汇总结果。
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("platform_manager")
        self._browser_pool = BrowserPool(config.browser)

        # 适配器注册表：platform_id -> AdapterClass
        self._adapter_registry: Dict[str, Type[BaseAdapter]] = {
            "doubao": DoubaoAdapter,
            "chatglm": ChatGLMAdapter,
            "deepseek": DeepSeekAdapter,
            "qianwen": QianwenAdapter,
            "yuanbao": YuanbaoAdapter,
        }

    def get_enabled_platforms(self) -> List[str]:
        """获取所有已启用且已注册的平台 ID 列表"""
        enabled_in_config = self.config.get_enabled_platforms()
        return [p for p in enabled_in_config if p in self._adapter_registry]

    async def _create_adapter(self, platform_id: str) -> BaseAdapter:
        """为指定平台创建适配器实例

        Args:
            platform_id: 平台 ID

        Returns:
            适配器实例
        """
        adapter_class = self._adapter_registry[platform_id]
        page = await self._browser_pool.get_page(platform_id)
        return adapter_class(page=page)

    async def ask_question(
        self,
        question: str,
        platforms: Optional[List[str]] = None,
        timeout: int = 120,
        min_success: int = 3,
    ) -> dict:
        """并行向多个平台提问并汇总结果

        Args:
            question: 问题内容
            platforms: 指定平台列表，为 None 时使用所有已启用平台
            timeout: 单平台超时秒数
            min_success: 最少成功数

        Returns:
            汇总结果字典，包含 success, total_count, success_count, question, results
        """
        # 确定目标平台
        if platforms is None:
            target_platforms = self.get_enabled_platforms()
        else:
            # 过滤掉未注册的平台
            target_platforms = [p for p in platforms if p in self._adapter_registry]
            if len(target_platforms) < len(platforms):
                invalid = set(platforms) - set(target_platforms)
                self.logger.warning(f"忽略未注册的平台: {invalid}")

        self.logger.info(f"开始并行提问，目标平台: {target_platforms}")

        # 并行执行各平台提问
        tasks = []
        for platform_id in target_platforms:
            task = self._ask_single_platform(platform_id, question, timeout)
            tasks.append(task)

        results: List[AdapterResult] = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results: List[AdapterResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                platform_id = target_platforms[i]
                platform_name = self.config.platforms.get(platform_id)
                platform_name = platform_name.name if platform_name else platform_id
                processed_results.append(AdapterResult(
                    platform=platform_id,
                    platform_name=platform_name,
                    status="failed",
                    answer=None,
                    duration_ms=0,
                    screenshot_path=None,
                    error=f"未捕获异常: {str(result)}",
                ))
            else:
                processed_results.append(result)

        # 统计成功数
        success_count = sum(1 for r in processed_results if r.is_success)
        total_count = len(processed_results)
        is_success = success_count >= min_success

        self.logger.info(
            f"提问完成: {success_count}/{total_count} 成功, "
            f"最小要求 {min_success}, 整体{'成功' if is_success else '失败'}"
        )

        return {
            "success": is_success,
            "total_count": total_count,
            "success_count": success_count,
            "question": question,
            "results": [r.to_dict() for r in processed_results],
        }

    async def _ask_single_platform(
        self, platform_id: str, question: str, timeout: int
    ) -> AdapterResult:
        """向单个平台提问

        Args:
            platform_id: 平台 ID
            question: 问题内容
            timeout: 超时秒数

        Returns:
            AdapterResult 执行结果
        """
        try:
            adapter = await self._create_adapter(platform_id)
            return await adapter.ask(question, timeout)
        except Exception as e:
            platform_name = self.config.platforms.get(platform_id)
            platform_name = platform_name.name if platform_name else platform_id
            self.logger.error(f"平台 {platform_name} 执行异常: {e}")
            return AdapterResult(
                platform=platform_id,
                platform_name=platform_name,
                status="failed",
                answer=None,
                duration_ms=0,
                screenshot_path=None,
                error=str(e),
            )

    async def check_login(self, platform_id: str, headless: bool = False) -> dict:
        """检查指定平台的登录状态"""
        adapter = await self._create_adapter(platform_id)
        is_logged_in = await adapter.check_login_status()
        platform_name = self.config.platforms.get(platform_id)
        platform_name = platform_name.name if platform_name else platform_id

        return {
            "platform": platform_id,
            "is_logged_in": is_logged_in,
            "message": "登录状态正常" if is_logged_in else f"未登录，请先登录 {platform_name}",
        }

    async def capture_screenshot(self, platform_id: str) -> dict:
        """对指定平台截图"""
        from datetime import datetime
        adapter = await self._create_adapter(platform_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"{self.config.paths.screenshot_dir}/debug_{platform_id}_{timestamp}.png"

        from pathlib import Path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        actual_path = await adapter.capture_screenshot(save_path)
        page_url = adapter.page.url

        return {
            "platform": platform_id,
            "screenshot_path": actual_path,
            "page_url": page_url,
        }

    async def list_platforms(self) -> dict:
        """列出所有平台及其状态"""
        platforms_info = []
        for pid, adapter_class in self._adapter_registry.items():
            pconfig = self.config.platforms.get(pid)
            platforms_info.append({
                "id": pid,
                "name": pconfig.name if pconfig else pid,
                "url": pconfig.base_url if pconfig else "",
                "enabled": pconfig.enabled if pconfig else False,
                "login_status": "unknown",  # 不主动检查，避免打开浏览器
            })

        return {"platforms": platforms_info}

    async def cleanup(self) -> None:
        """清理资源"""
        await self._browser_pool.stop()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/unit/test_platform_manager.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add core/platform_manager.py tests/unit/test_platform_manager.py
git commit -m "feat: 平台管理器 - 并发调度与结果汇总"
```

---

## Task 12: MCP Server (mcp_server.py)

**Files:**
- Create: `mcp_server.py`

- [ ] **Step 1: 实现 MCP Server**

```python
# mcp_server.py
"""ConsensusWeaver MCP Server 入口

通过 MCP 协议暴露 4 个工具：
- ask_ai: 并行向多个 AI WebApp 提问
- list_platforms: 列出支持的 AI 平台
- check_login: 检查/准备登录状态
- capture_screenshot: 截图调试
"""
from typing import List, Optional

from fastmcp import FastMCP

from core.config import Config
from core.platform_manager import PlatformManager
from utils.logger import get_logger

# 初始化 MCP Server
mcp = FastMCP("ConsensusWeaver")

# 加载配置
config = Config.load("config.yaml")
logger = get_logger("mcp_server", config.paths.log_dir)

# 全局平台管理器实例
_manager: Optional[PlatformManager] = None


def get_manager() -> PlatformManager:
    """获取或创建平台管理器单例"""
    global _manager
    if _manager is None:
        _manager = PlatformManager(config)
    return _manager


@mcp.tool()
async def ask_ai(
    question: str,
    platforms: Optional[List[str]] = None,
    timeout: int = 120,
    min_success: int = 3,
) -> dict:
    """向多个 AI WebApp 并行提问，收集答案

    Args:
        question: 要提问的问题内容
        platforms: 指定提问哪些平台（如 ["doubao", "deepseek"]），不传则全部
        timeout: 单个平台的超时时间（秒），默认 120
        min_success: 最少成功数量，低于此数则整体失败，默认 3

    Returns:
        包含各平台答案的汇总结果
    """
    logger.info(f"ask_ai 调用: question={question[:50]}..., platforms={platforms}")

    # 参数校验
    if not question or not question.strip():
        return {"success": False, "error": "问题内容不能为空"}

    if timeout < 1 or timeout > 600:
        return {"success": False, "error": "超时时间应在 1-600 秒之间"}

    if min_success < 1:
        return {"success": False, "error": "最小成功数应大于 0"}

    manager = get_manager()
    result = await manager.ask_question(
        question=question,
        platforms=platforms,
        timeout=timeout,
        min_success=min_success,
    )
    return result


@mcp.tool()
async def list_platforms() -> dict:
    """列出当前所有支持的 AI 平台及其可用状态

    Returns:
        包含平台列表的字典
    """
    logger.info("list_platforms 调用")
    manager = get_manager()
    return await manager.list_platforms()


@mcp.tool()
async def check_login(
    platform: str,
    headless: bool = False,
    wait_login_seconds: int = 0,
) -> dict:
    """检查指定平台的登录状态

    Args:
        platform: 平台 ID（如 "doubao"）
        headless: 是否无头模式，默认 False（便于手动登录）
        wait_login_seconds: 等待手动登录的秒数，>0 时打开浏览器等待，默认 0

    Returns:
        包含登录状态信息的字典
    """
    logger.info(f"check_login 调用: platform={platform}, wait={wait_login_seconds}")

    if not platform or not platform.strip():
        return {"platform": "", "is_logged_in": False, "message": "平台 ID 不能为空"}

    manager = get_manager()

    # 如果需要等待手动登录
    if wait_login_seconds > 0:
        import asyncio
        # 先创建适配器（打开浏览器）
        adapter = await manager._create_adapter(platform)
        await adapter.navigate_to_chat()
        logger.info(f"浏览器已打开，等待 {wait_login_seconds} 秒供用户登录...")
        await asyncio.sleep(wait_login_seconds)

    result = await manager.check_login(platform, headless=headless)
    return result


@mcp.tool()
async def capture_screenshot(platform: str) -> dict:
    """对指定平台的当前页面截图，用于调试

    Args:
        platform: 平台 ID（如 "doubao"）

    Returns:
        包含截图路径和当前页面 URL 的字典
    """
    logger.info(f"capture_screenshot 调用: platform={platform}")

    if not platform or not platform.strip():
        return {"platform": "", "screenshot_path": "", "page_url": "", "error": "平台 ID 不能为空"}

    manager = get_manager()
    return await manager.capture_screenshot(platform)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: 验证模块可导入**

Run: `python -c "import mcp_server; print('MCP Server 模块导入成功')"`
Expected: 输出 "MCP Server 模块导入成功"

- [ ] **Step 3: 提交**

```bash
git add mcp_server.py
git commit -m "feat: MCP Server - 4 个工具接口"
```

---

## Task 13: 测试 conftest (tests/conftest.py)

**Files:**
- Create: `conftest.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建根级 conftest.py**

```python
# conftest.py
"""根级 pytest 配置，提供项目路径到 sys.path"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使测试可以导入项目模块
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

- [ ] **Step 2: 创建测试级 conftest.py**

```python
# tests/conftest.py
"""测试级 pytest 配置与 fixtures"""
import pytest
import tempfile
import os
from pathlib import Path

from core.config import Config, BrowserConfig, PlatformConfig, DefaultsConfig, PathsConfig


@pytest.fixture
def test_config():
    """测试用配置 fixture

    使用独立的数据目录，不污染生产数据。
    """
    # 创建临时目录
    tmp_dir = tempfile.mkdtemp(prefix="consensus_test_")
    user_data_dir = os.path.join(tmp_dir, "user_data")
    screenshot_dir = os.path.join(tmp_dir, "screenshots")
    log_dir = os.path.join(tmp_dir, "logs")

    for d in [user_data_dir, screenshot_dir, log_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    config = Config(
        browser=BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            slow_mo=0,
            user_data_base_dir=user_data_dir,
        ),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
            "deepseek": PlatformConfig(enabled=True, name="DeepSeek", base_url="https://chat.deepseek.com"),
            "qianwen": PlatformConfig(enabled=True, name="千问", base_url="https://qianwen.com/chat"),
            "yuanbao": PlatformConfig(enabled=True, name="元宝", base_url="https://yuanbao.tencent.com/chat"),
        },
        defaults=DefaultsConfig(timeout=10, min_success=3, max_concurrent=5),
        paths=PathsConfig(screenshot_dir=screenshot_dir, log_dir=log_dir),
    )
    yield config

    # 清理临时目录
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def test_config_partial():
    """部分平台的测试配置（仅 2 个平台）"""
    tmp_dir = tempfile.mkdtemp(prefix="consensus_test_")
    config = Config(
        browser=BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            slow_mo=0,
            user_data_base_dir=os.path.join(tmp_dir, "user_data"),
        ),
        platforms={
            "doubao": PlatformConfig(enabled=True, name="豆包", base_url="https://www.doubao.com"),
            "chatglm": PlatformConfig(enabled=True, name="智谱清言", base_url="https://chatglm.cn"),
        },
        defaults=DefaultsConfig(timeout=10, min_success=1, max_concurrent=2),
        paths=PathsConfig(
            screenshot_dir=os.path.join(tmp_dir, "screenshots"),
            log_dir=os.path.join(tmp_dir, "logs"),
        ),
    )
    yield config

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
```

- [ ] **Step 3: 验证 fixture 可用**

Run: `python -m pytest tests/unit/test_config.py -v --tb=short`
Expected: 3 passed

- [ ] **Step 4: 提交**

```bash
git add conftest.py tests/conftest.py
git commit -m "test: pytest 配置与公共 fixtures"
```

---

## Task 14: 集成测试 - 浏览器池 (tests/integration/test_browser_pool.py)

**Files:**
- Create: `tests/integration/test_browser_pool.py`

- [ ] **Step 1: 编写浏览器池集成测试**

```python
# tests/integration/test_browser_pool.py
"""浏览器池集成测试 - 使用真实 Playwright 浏览器"""
import pytest
from pathlib import Path

from core.browser_pool import BrowserPool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_start_stop(test_config):
    """测试浏览器池启动和停止"""
    pool = BrowserPool(test_config.browser)
    await pool.start()
    assert pool._playwright is not None

    await pool.stop()
    assert pool._playwright is None
    assert len(pool._contexts) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_get_context(test_config):
    """测试获取浏览器上下文"""
    pool = BrowserPool(test_config.browser)
    try:
        context = await pool.get_context("doubao", headless=True)
        assert context is not None
        assert "doubao" in pool._contexts

        # 再次获取应返回同一上下文
        context2 = await pool.get_context("doubao")
        assert context2 is context
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_get_page(test_config):
    """测试获取页面"""
    pool = BrowserPool(test_config.browser)
    try:
        page = await pool.get_page("doubao", headless=True)
        assert page is not None

        # 再次获取应返回同一页面
        page2 = await pool.get_page("doubao")
        assert page2 is page
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_user_data_dir_created(test_config):
    """测试用户数据目录被创建"""
    pool = BrowserPool(test_config.browser)
    try:
        await pool.get_context("doubao", headless=True)
        user_data_path = Path(test_config.browser.user_data_base_dir) / "doubao"
        assert user_data_path.exists()
    finally:
        await pool.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_browser_pool_close_context(test_config):
    """测试关闭指定平台的上下文"""
    pool = BrowserPool(test_config.browser)
    try:
        await pool.get_context("doubao", headless=True)
        assert "doubao" in pool._contexts

        await pool.close_context("doubao")
        assert "doubao" not in pool._contexts
    finally:
        await pool.stop()
```

- [ ] **Step 2: 运行集成测试**

Run: `python -m pytest tests/integration/test_browser_pool.py -v -m integration`
Expected: 5 passed（会启动真实浏览器，稍慢）

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_browser_pool.py
git commit -m "test: 浏览器池集成测试"
```

---

## Task 15: 集成测试 - 平台管理器 (tests/integration/test_platform_manager.py)

**Files:**
- Create: `tests/integration/test_platform_manager.py`

- [ ] **Step 1: 编写平台管理器集成测试**

```python
# tests/integration/test_platform_manager.py
"""平台管理器集成测试 - 使用 mock 适配器验证调度逻辑"""
import pytest
from unittest.mock import AsyncMock, patch

from core.platform_manager import PlatformManager
from adapters.base_adapter import AdapterResult


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_list_platforms(test_config):
    """测试列出平台"""
    mgr = PlatformManager(test_config)
    result = await mgr.list_platforms()

    assert "platforms" in result
    assert len(result["platforms"]) == 5
    ids = [p["id"] for p in result["platforms"]]
    assert "doubao" in ids
    assert "chatglm" in ids
    assert "deepseek" in ids
    assert "qianwen" in ids
    assert "yuanbao" in ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_ask_with_mock_adapters(test_config_partial):
    """测试并行提问（mock 适配器）"""
    mgr = PlatformManager(test_config_partial)

    # 创建 mock 适配器
    mock_result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="豆包的回答",
        duration_ms=1000,
        screenshot_path=None,
        error=None,
    )
    mock_result2 = AdapterResult(
        platform="chatglm",
        platform_name="智谱清言",
        status="success",
        answer="智谱清言的回答",
        duration_ms=2000,
        screenshot_path=None,
        error=None,
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=mock_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=mock_result2)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is True
    assert result["success_count"] == 2
    assert result["total_count"] == 2
    assert len(result["results"]) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_partial_failure(test_config_partial):
    """测试部分平台失败的场景"""
    mgr = PlatformManager(test_config_partial)

    success_result = AdapterResult(
        platform="doubao", platform_name="豆包",
        status="success", answer="回答", duration_ms=1000,
        screenshot_path=None, error=None,
    )
    fail_result = AdapterResult(
        platform="chatglm", platform_name="智谱清言",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="超时",
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=success_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=fail_result)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=2)

    assert result["success"] is False  # 1 成功 < 2 要求
    assert result["success_count"] == 1
    assert result["results"][0]["status"] == "success"
    assert result["results"][1]["status"] == "failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_all_failed(test_config_partial):
    """测试全部平台失败"""
    mgr = PlatformManager(test_config_partial)

    fail_result = AdapterResult(
        platform="doubao", platform_name="豆包",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="连接失败",
    )
    fail_result2 = AdapterResult(
        platform="chatglm", platform_name="智谱清言",
        status="failed", answer=None, duration_ms=5000,
        screenshot_path=None, error="连接失败",
    )

    mock_adapter1 = AsyncMock()
    mock_adapter1.ask = AsyncMock(return_value=fail_result)
    mock_adapter2 = AsyncMock()
    mock_adapter2.ask = AsyncMock(return_value=fail_result2)

    mgr._create_adapter = AsyncMock(side_effect=[mock_adapter1, mock_adapter2])

    result = await mgr.ask_question("测试问题", ["doubao", "chatglm"], timeout=10, min_success=1)

    assert result["success"] is False
    assert result["success_count"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_manager_invalid_platform_filtered(test_config):
    """测试不存在的平台被过滤"""
    mgr = PlatformManager(test_config)

    result = await mgr.ask_question(
        "测试问题",
        ["doubao", "nonexistent"],
        timeout=5,
        min_success=1,
    )

    # nonexistent 被过滤，只有 doubao 参与执行
    # 但因为没有真实浏览器，doubao 也会失败
    assert result["total_count"] == 1  # 只有 doubao
```

- [ ] **Step 2: 运行集成测试**

Run: `python -m pytest tests/integration/test_platform_manager.py -v -m integration`
Expected: 5 passed

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_platform_manager.py
git commit -m "test: 平台管理器集成测试"
```

---

## Task 16: E2E 测试 (tests/e2e/test_mcp_tools.py)

**Files:**
- Create: `tests/e2e/test_mcp_tools.py`

- [ ] **Step 1: 编写 E2E 测试**

```python
# tests/e2e/test_mcp_tools.py
"""MCP 工具 E2E 测试 - 完整调用链验证"""
import pytest
from unittest.mock import AsyncMock, patch

from adapters.base_adapter import AdapterResult


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_platforms_tool():
    """测试 list_platforms 工具完整调用"""
    from mcp_server import list_platforms

    result = await list_platforms.fn()

    assert "platforms" in result
    assert len(result["platforms"]) == 5
    for p in result["platforms"]:
        assert "id" in p
        assert "name" in p
        assert "url" in p
        assert "enabled" in p


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_empty_question():
    """测试 ask_ai 空问题参数校验"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="", platforms=["doubao"])
    assert result["success"] is False
    assert "空" in result["error"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_invalid_timeout():
    """测试 ask_ai 非法超时参数"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="测试", timeout=0)
    assert result["success"] is False
    assert "超时" in result["error"]

    result2 = await ask_ai.fn(question="测试", timeout=999)
    assert result2["success"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_invalid_min_success():
    """测试 ask_ai 非法 min_success 参数"""
    from mcp_server import ask_ai

    result = await ask_ai.fn(question="测试", min_success=0)
    assert result["success"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_with_mock_manager():
    """测试 ask_ai 工具调用（mock 平台管理器）"""
    from mcp_server import ask_ai, get_manager

    mock_manager = AsyncMock()
    mock_manager.ask_question = AsyncMock(return_value={
        "success": True,
        "total_count": 1,
        "success_count": 1,
        "question": "测试问题",
        "results": [
            {
                "platform": "doubao",
                "platform_name": "豆包",
                "status": "success",
                "answer": "回答",
                "duration_ms": 1000,
                "screenshot_path": None,
                "error": None,
            }
        ],
    })

    with patch("mcp_server.get_manager", return_value=mock_manager):
        result = await ask_ai.fn(question="测试问题", platforms=["doubao"])

    assert result["success"] is True
    assert result["success_count"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["platform"] == "doubao"
    assert result["results"][0]["answer"] == "回答"

    # 验证返回结构字段完整性
    for r in result["results"]:
        assert "platform" in r
        assert "platform_name" in r
        assert "status" in r
        assert "answer" in r
        assert "duration_ms" in r
        assert "screenshot_path" in r
        assert "error" in r


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_check_login_empty_platform():
    """测试 check_login 空平台参数校验"""
    from mcp_server import check_login

    result = await check_login.fn(platform="")
    assert result["is_logged_in"] is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_capture_screenshot_empty_platform():
    """测试 capture_screenshot 空平台参数校验"""
    from mcp_server import capture_screenshot

    result = await capture_screenshot.fn(platform="")
    assert "error" in result


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ask_ai_return_structure_completeness():
    """测试 ask_ai 返回结构完整性"""
    from mcp_server import ask_ai, get_manager

    mock_manager = AsyncMock()
    mock_manager.ask_question = AsyncMock(return_value={
        "success": False,
        "total_count": 2,
        "success_count": 1,
        "question": "测试",
        "results": [
            {
                "platform": "doubao",
                "platform_name": "豆包",
                "status": "success",
                "answer": "答案1",
                "duration_ms": 1000,
                "screenshot_path": "/tmp/s1.png",
                "error": None,
            },
            {
                "platform": "chatglm",
                "platform_name": "智谱清言",
                "status": "failed",
                "answer": None,
                "duration_ms": 120000,
                "screenshot_path": "/tmp/s2.png",
                "error": "超时",
            },
        ],
    })

    with patch("mcp_server.get_manager", return_value=mock_manager):
        result = await ask_ai.fn(question="测试", platforms=["doubao", "chatglm"])

    # 验证顶层字段
    assert "success" in result
    assert "total_count" in result
    assert "success_count" in result
    assert "question" in result
    assert "results" in result

    # 验证每个结果的字段
    for r in result["results"]:
        assert isinstance(r["platform"], str)
        assert isinstance(r["platform_name"], str)
        assert isinstance(r["status"], str)
        assert r["status"] in ("success", "failed")
        assert isinstance(r["duration_ms"], int)
```

- [ ] **Step 2: 运行 E2E 测试**

Run: `python -m pytest tests/e2e/test_mcp_tools.py -v -m e2e`
Expected: 8 passed

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_mcp_tools.py
git commit -m "test: MCP 工具 E2E 测试"
```

---

## Task 17: 全量测试与最终提交

**Files:**
- Modify: `README.md`（可选，用户未要求则跳过）

- [ ] **Step 1: 运行所有单元测试**

Run: `python -m pytest tests/unit/ -v`
Expected: 全部 passed

- [ ] **Step 2: 运行所有集成测试**

Run: `python -m pytest tests/integration/ -v -m integration`
Expected: 全部 passed

- [ ] **Step 3: 运行所有 E2E 测试**

Run: `python -m pytest tests/e2e/ -v -m e2e`
Expected: 全部 passed

- [ ] **Step 4: 运行全量测试**

Run: `python -m pytest -v`
Expected: 全部 passed

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "test: 全量测试通过"
```

---

## 实施完成后的手动验证步骤

完成以上所有 Task 后，进行手动验证：

1. **配置 TRAE MCP**：将 `mcp_server.py` 配置为 TRAE 的 local MCP Server
2. **首次登录**：对每个平台调用 `check_login(platform="doubao", wait_login_seconds=120)`，手动登录
3. **单平台测试**：调用 `ask_ai(question="你好", platforms=["doubao"])` 验证单平台
4. **全平台测试**：调用 `ask_ai(question="什么是人工智能")` 验证 5 平台并行
5. **查看结果**：检查返回结构是否完整，截图是否正常保存
6. **智能融合**：在 TRAE 中让 LLM 分析返回的多平台答案，生成融合答案
