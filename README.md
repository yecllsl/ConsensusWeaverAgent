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

## 在 Trae 中使用

本项目既可以通过 **MCP Server** 被任意 Agent 调用，也提供了 **ConsensusWeaver Skill** 供 TRAE 直接触发，实现“用户提问 → 并行询问多个 AI → TRAE 合成共识答案”的完整工作流。

### 1. 启动 MCP Server

```powershell
python mcp_server.py
```

MCP Server 启动后会暴露 `ask_ai`、`list_platforms`、`check_login`、`capture_screenshot` 四个工具。

### 2. 在 Trae 中注册 MCP Server

在 Trae 的 MCP 配置中添加 ConsensusWeaver，例如：

```json
{
  "mcpServers": {
    "ConsensusWeaver": {
      "command": "python",
      "args": [
        "%项目所在目录%/ConsensusWeaverAgent/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

路径请替换为你本地克隆后的实际位置。

### 3. 安装 ConsensusWeaver Skill

将本仓库中的 Skill 文件：

```
.trae/skills/consensusweaver/SKILL.md
```

复制到 Trae 的 skills 目录下（如 `.trae/skills/consensusweaver/SKILL.md`），使 TRAE 能够识别并触发该 skill。

### 4. 使用工作流

当用户在 Trae 中提出需要多角度参考的问题时：

1. TRAE 自动触发 `ConsensusWeaver` skill。
2. Skill 调用 MCP 的 `ask_ai`，默认同时向 5 个平台提问，最少 3 个成功即进入汇总。
3. TRAE 读取 `results` 中 `status` 为 `success` 的答案。
4. TRAE 提炼共识、保留互补观点、标注分歧，并说明失败平台原因。

典型触发问题：

- “如何学习 Python？请给出不同角度的建议。”
- “比较 Vue 和 React 的适用场景。”
- “用 ConsensusWeaver 问一下：未来火星移民最先要解决哪些问题？”

## 目录结构

```
.
├── adapters/           # 平台适配器
├── core/               # 浏览器池、平台管理器、配置
├── tests/              # 单元/集成/E2E 测试
├── scripts/            # 调试与测试脚本
├── .trae/skills/       # Trae Skill 定义
├── data/               # 用户数据、截图、日志、测试报告
├── mcp_server.py       # MCP 入口
├── config.yaml         # 配置文件
└── requirements.txt    # Python 依赖
```

## 许可

MIT
