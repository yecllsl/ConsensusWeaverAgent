# ConsensusWeaverAgent

ConsensusWeaverAgent 是一个基于 MCP 协议的多 AI 平台答案聚合服务。它通过 Playwright 浏览器自动化，并行向 5 个中文 AI WebApp 提问，收集所有可用答案后由 TRAE 进行汇总、分析与共识提炼。

支持的 AI 平台：豆包、智谱清言、DeepSeek、千问、元宝。

## 核心功能

- **并行提问**：使用 `asyncio.gather` 同时向多个平台提问。
- **答案收集**：每个平台返回原始答案、元数据、截图和 HTML 片段。
- **登录状态管理**：每个平台使用独立的持久化用户数据目录，保持登录状态。
- **MCP 工具暴露**：提供 `ask_ai`、`list_platforms`、`check_login`、`capture_screenshot` 四个工具。
- **共识合成**：TRAE 读取成功平台的答案，提炼共识、标注分歧、补充独立观点。

## 架构

```
mcp_server.py  →  PlatformManager  →  BrowserPool
                                    →  DoubaoAdapter
                                    →  ChatGLMAdapter
                                    →  DeepSeekAdapter
                                    →  QianwenAdapter
                                    →  YuanbaoAdapter
```

- `adapters/`：各平台适配器，封装导航、登录检查、提问、等待、截图、开新对话逻辑。
- `core/`：配置加载、浏览器池、平台管理器。
- `mcp_server.py`：FastMCP 入口，暴露工具。

## 安装

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

运行时需要在项目根目录放置 `config.yaml`。

## 运行

```powershell
python mcp_server.py
```

## 测试

```powershell
# 全部测试
python -m pytest

# 仅单元测试（不启动浏览器）
python -m pytest -m "not slow and not integration and not e2e"

# 单个文件
python -m pytest tests/unit/test_config.py -v
```

## MCP 工具

| 工具 | 说明 |
| --- | --- |
| `ask_ai` | 并行提问，返回各平台结果与汇总 |
| `list_platforms` | 列出支持的 AI 平台及状态 |
| `check_login` | 检查/等待平台登录状态 |
| `capture_screenshot` | 对指定平台当前页面截图 |

## 配置

`config.yaml` 示例：

```yaml
browser:
  headless: false
  viewport_width: 1280
  viewport_height: 800

platforms:
  doubao:    { enabled: true, name: "豆包",    base_url: "https://www.doubao.com" }
  chatglm:   { enabled: true, name: "智谱清言", base_url: "https://chatglm.cn" }
  deepseek:  { enabled: true, name: "DeepSeek", base_url: "https://chat.deepseek.com" }
  qianwen:   { enabled: true, name: "千问",    base_url: "https://qianwen.com/chat" }
  yuanbao:   { enabled: true, name: "元宝",    base_url: "https://yuanbao.tencent.com/chat" }

defaults:
  timeout: 120
  min_success: 3
  max_concurrent: 5
```

## 目录结构

```
.
├── adapters/           # 平台适配器
├── core/               # 浏览器池、平台管理器、配置
├── tests/              # 单元/集成/E2E 测试
├── scripts/            # 调试与测试脚本
├── data/               # 用户数据、截图、日志、测试报告
├── mcp_server.py       # MCP 入口
├── config.yaml         # 配置文件
└── requirements.txt    # Python 依赖
```

## 许可

MIT
