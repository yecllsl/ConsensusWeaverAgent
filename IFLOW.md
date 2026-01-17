# ConsensusWeaverAgent 项目上下文

## 项目概述

ConsensusWeaverAgent 是一款智能问答协调终端应用，能够协调多个AI工具并生成综合报告。该应用以本地大语言模型为核心，通过与用户交互澄清问题意图，智能决策执行路径，并发调用多个外部AI工具获取多角度答案，最终在本地进行深度分析和共识度计算，生成结构清晰的综合报告。

## 技术栈

- **Python 3.12+**：核心编程语言
- **LangChain**：LLM集成框架
- **llama-cpp-python**：本地LLM服务（GGUF格式模型）
- **Click**：命令行界面
- **PyYAML**：配置管理
- **SQLite**：数据持久化
- **NLTK**：文本分析
- **scikit-learn**：相似度计算
- **uv**：现代化Python包管理器

## 项目结构

```
ConsensusWeaverAgent/
├── src/                          # 源代码目录
│   ├── main.py                   # 应用入口
│   ├── core/                     # 核心功能层
│   │   ├── analyzer/             # 共识分析引擎
│   │   ├── executor/             # 并发查询执行器
│   │   └── reporter/             # 报告生成器
│   ├── infrastructure/           # 基础设施层
│   │   ├── config/               # 配置管理
│   │   ├── data/                 # 数据持久化
│   │   ├── llm/                  # LLM集成服务
│   │   ├── logging/              # 日志系统
│   │   └── tools/                # 外部工具集成
│   ├── service/                  # 应用服务层
│   │   ├── interaction/          # 智能交互引擎
│   │   └── strategy/             # 执行策略管理器
│   ├── models/                   # 数据模型
│   ├── ui/                       # 用户界面层
│   └── utils/                    # 工具函数
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── test_external_tools.py
├── docs/                         # 文档目录
│   ├── design/                   # 设计文档
│   │   ├── 技术选型.md
│   │   └── 架构设计.md
│   ├── dev/                      # 开发文档
│   │   └── 本地开发环境搭建.md
│   ├── maintain/                 # 维护文档
│   │   └── 待办清单.md
│   ├── external/                 # 外部文档
│   │   └── tutorials/
│   │       └── 调用外部工具教程.md
│   └── requirements/             # 需求文档
│       ├── requirements.md
│       └── 需求清单.md
├── Scripts/                      # 脚本目录
│   └── download_qwen3-8b-gguf.py # 模型下载脚本
├── .models/                      # 模型文件目录
│   ├── nltk_data/                # NLTK资源
│   └── qwen/                     # Qwen模型文件
├── pyproject.toml                # 项目配置和依赖管理
├── config.yaml                   # 应用配置文件（首次运行自动生成）
├── README.md                     # 项目说明文档
└── .gitignore                    # Git忽略规则
```

## 架构设计

应用采用分层架构设计，从底层到上层依次为：

1. **基础设施层** (Infrastructure Layer)
   - LLM集成服务
   - 外部工具集成
   - 数据持久化
   - 配置管理
   - 日志系统

2. **核心功能层** (Core Layer)
   - 并发查询执行器
   - 共识分析引擎
   - 报告生成器

3. **应用服务层** (Service Layer)
   - 智能交互引擎
   - 执行策略管理器

4. **用户界面层** (UI Layer)
   - 命令行界面 (CLI)

## 核心功能

1. **智能交互引擎**：与本地LLM互动，引导用户澄清问题意图
2. **执行策略管理器**：根据澄清后的问题判断最优执行路径（直接回答或并行查询）
3. **并发查询执行器**：并行调用多个外部AI工具获取答案
4. **共识分析引擎**：对多个答案进行深度分析和共识度计算
5. **报告生成器**：生成综合报告，包含共识分析、综合结论和分歧点

## 构建和运行

### 环境要求

- Windows 10/11 (64位)
- Python 3.12+
- 至少8GB RAM (推荐16GB以上)
- 至少10GB可用磁盘空间

### 安装步骤

1. **克隆项目代码**
   ```powershell
   git clone <项目仓库地址>
   cd ConsensusWeaverAgent
   ```

2. **安装uv包管理器**
   ```powershell
   pip install uv
   ```

3. **创建虚拟环境并安装依赖**
   ```powershell
   uv venv && uv sync --all-extras
   ```

4. **激活虚拟环境**
   ```powershell
   .venv\Scripts\activate
   ```

5. **下载NLTK资源**
   ```powershell
   python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

6. **下载GGUF模型文件**
   ```powershell
   python Scripts/download_qwen3-8b-gguf.py
   ```

### 运行应用

```powershell
# 基本运行
python -m src.main

# 指定配置文件
python -m src.main --config my_config.yaml

# 启用详细日志
python -m src.main --verbose
```

## 开发规范

### 代码格式化和Lint

使用 ruff 统一处理代码格式化和lint检查：

```powershell
uv run ruff check .
uv run ruff format .
```

**重要**：使用 `uv run` 确保使用虚拟环境中的 ruff 版本，保证环境一致性。

### 类型检查

使用 mypy 进行严格的类型检查：

```powershell
uv run mypy --strict .
```

### 测试

```powershell
# 运行单元测试
uv run pytest tests/unit/

# 运行集成测试
uv run pytest tests/integration/

# 运行所有测试
uv run pytest
```

**重要**：使用 `uv run` 确保使用虚拟环境中的 pytest 版本。

### 代码风格

- 所有函数/方法必须包含完整类型注解
- 复杂结构使用 `TypedDict` 或 `@dataclass`
- 公共模块/类/函数必须包含Google风格docstring
- 使用ruff自动格式化，line-length为88字符

### 依赖管理

```powershell
# 添加依赖
uv add <package>
uv add --group dev <package>  # 添加开发依赖

# 更新依赖
uv update

# 同步环境
uv sync
```

## 配置管理

项目使用YAML格式的配置文件 `config.yaml`，首次运行时会自动创建默认配置。

### 主要配置项

- **local_llm**：本地LLM服务配置（模型路径、参数等）
- **external_tools**：外部AI工具配置（命令、参数、优先级等）
- **network**：网络相关配置（超时、检查等）
- **app**：应用行为配置（日志级别、最大澄清轮数等）

### 配置文件示例

```yaml
local_llm:
  provider: "llama-cpp"
  model: "Qwen3-8B-Q5_K_M.gguf"
  model_path: ".models/qwen/Qwen3-8B-Q5_K_M.gguf"
  n_ctx: 4096
  n_threads: 4
  temperature: 0.3

external_tools:
  - name: "iflow"
    command: "iflow.ps1"
    args: "-y -p"
    needs_internet: true
    priority: 1
    enabled: true

network:
  check_before_run: true
  timeout: 60

app:
  max_clarification_rounds: 3
  max_parallel_tools: 5
  log_level: "info"
  log_file: "consensusweaver.log"
  history_enabled: true
  history_limit: 100
```

## 关键特性

### 本地优先

- 核心功能采用本地处理，保障隐私和响应速度
- 本地LLM直接加载GGUF模型文件，无需联网
- 仅外部工具调用需要网络连接

### 模块化设计

- 清晰的模块划分，低耦合高内聚
- 支持未来功能扩展和性能升级
- 易于维护和测试

### 并发友好

- 支持高效的并发任务处理
- 最大并发工具数可配置（默认5个）
- 使用 asyncio 实现异步处理

### 容错设计

- 具备错误处理和恢复机制
- 单个工具失败不影响其他工具执行
- 详细的错误日志和友好的错误提示

## 外部工具集成

应用通过子进程调用外部AI命令行工具，支持的工具包括：

- **iflow**：优先级1
- **codebuddy**：优先级2
- **qwen**：优先级3

工具配置在 `config.yaml` 的 `external_tools` 部分，可以轻松添加或禁用工具。

## 数据流

1. 用户输入问题
2. 智能交互引擎分析问题并引导澄清
3. 执行策略管理器判断执行路径
4. 如果是简单问题，本地LLM直接回答
5. 如果是复杂问题，并发查询执行器调用外部工具
6. 共识分析引擎分析多个答案的共识度
7. 报告生成器生成综合报告
8. 用户查看并可选择保存报告

## 文档资源

- **需求文档**：`docs/requirements/requirements.md`
- **技术选型**：`docs/design/技术选型.md`
- **架构设计**：`docs/design/架构设计.md`
- **本地开发环境搭建**：`docs/dev/本地开发环境搭建.md`
- **调用外部工具教程**：`docs/external/tutorials/调用外部工具教程.md`

## 常见问题

### 模型加载失败

确认模型文件已正确下载到 `.models/qwen/` 目录，并检查 `config.yaml` 中的 `model_path` 配置。

### 依赖安装问题

使用 `uv sync --all-extras` 重新同步依赖，确保虚拟环境已激活。

### 外部工具调用失败

确认外部工具已正确安装并配置，检查网络连接是否正常。

### 内存不足

尝试使用更小的模型文件（如Q4_K_M版本），减少 `config.yaml` 中的 `n_ctx` 值。

## 贡献指南

1. 使用 feature 分支进行开发
2. 遵循 conventional commits 规范
3. 确保所有代码通过 ruff 检查和 mypy 类型检查
4. 为新功能添加单元测试
5. 所有测试通过后提交合并请求

## 许可证

MIT License