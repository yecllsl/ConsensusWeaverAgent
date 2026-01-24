# ConsensusWeaverAgent

智能问答协调终端应用 - 一个能够协调多个AI工具并生成综合报告的智能系统。

## 项目概述

ConsensusWeaverAgent是一款先进的本地终端智能问答协调应用。该应用以用户提出的问题为起点，通过与运行在本地的大语言模型互动，主动引导用户澄清和完善问题的核心意图。随后，应用将智能决策执行路径，可并行调用多个需要联网的外部AI命令行工具获取多角度答案，并对这些答案在本地进行深度分析和共识度计算，最终为用户呈现一份结构清晰、洞察深刻的综合性报告。

## 核心功能

- **智能交互引擎**：与本地LLM互动，引导用户澄清问题意图
- **并发查询执行器**：并行调用多个外部AI工具获取答案
- **共识分析引擎**：对多个答案进行深度分析和共识度计算
- **报告生成器**：生成综合报告，包含共识分析、综合结论和分歧点

## 技术栈

- **Python 3.12+**：核心编程语言
- **LangChain**：LLM集成框架
- **llama-cpp-python**：本地LLM服务
- **Click**：命令行界面
- **PyYAML**：配置管理
- **SQLite**：数据持久化
- **NLTK**：文本分析
- **scikit-learn**：相似度计算

## 环境搭建

### 前置要求

- Windows 10/11 (64位) / macOS / Linux
- Python 3.12+
- 至少8GB RAM (推荐16GB以上)
- 至少10GB可用磁盘空间

### 安装步骤

1. **克隆项目代码**
   ```powershell
   git clone <项目仓库地址>
   cd ConsensusWeaverAgent
   ```

2. **使用pip安装**
   ```powershell
   # 安装依赖管理工具uv
   pip install uv
   
   # 创建虚拟环境并安装依赖
   uv venv && uv sync --all-extras
   
   # 或使用pip直接安装
   pip install -e .
   ```

3. **直接安装（推荐）**
   ```powershell
   # 直接使用pip安装
   pip install consensusweaveragent
   ```

## 命令行使用

### 基本命令

```powershell
# 启动应用
consensusweaver

# 查看帮助
consensusweaver --help
```

### 可用选项

| 选项 | 别名 | 描述 |
|------|------|------|
| `-c, --config` | | 指定配置文件路径（默认：config.yaml） |
| `-v, --verbose` | | 启用详细日志 |
| `--i, --iflow` | | 使用iflow作为主Agent |
| `--q, --qwen` | | 使用qwen作为主Agent |
| `--b, --codebuddy` | | 使用codebuddy作为主Agent |
| `--help` | | 显示帮助信息 |

### 使用示例

```powershell
# 使用默认配置启动应用
consensusweaver

# 使用自定义配置文件
consensusweaver --config my_config.yaml

# 启用详细日志
consensusweaver -v

# 使用iflow作为主Agent
consensusweaver --iflow

# 使用qwen作为主Agent
consensusweaver --qwen

# 使用codebuddy作为主Agent
consensusweaver --codebuddy
```

## 开发环境搭建

如果您需要进行开发，可以按照以下步骤搭建开发环境：

1. **安装uv包管理器**
   ```powershell
   pip install uv
   ```

2. **创建虚拟环境并安装依赖**
   ```powershell
   uv venv && uv sync --all-extras
   ```

3. **激活虚拟环境**
   ```powershell
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

4. **下载NLTK资源**
   ```powershell
   python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

5. **下载GGUF模型文件**
   - **方法1：使用模型下载脚本**
     ```powershell
     python scripts/download_qwen3-8b-gguf.py
     ```
     该脚本将从ModelScope下载Qwen3-8B-Q5_K_M.gguf模型文件到.models/qwen/目录

   - **方法2：手动下载**
     1. 访问 [ModelScope模型库](https://modelscope.cn/models/qwen/Qwen3-8B-GGUF)
     2. 下载Qwen3-8B-Q5_K_M.gguf模型文件
     3. 创建.models/qwen/目录
     4. 将模型文件放置到该目录中

   - **方法3：从Hugging Face下载**
     1. 访问 [Hugging Face模型库](https://huggingface.co/Qwen/Qwen3-8B-GGUF)
     2. 下载Qwen3-8B-Q5_K_M.gguf模型文件
     3. 创建.models/qwen/目录
     4. 将模型文件放置到该目录中

## 使用说明

1. **启动应用**
   ```powershell
   consensusweaver
   ```

2. **输入问题**
   - 在命令行中输入您的问题，按回车键确认
   - 系统会自动分析问题并可能要求您澄清一些细节

3. **查看结果**
   - 系统会并行调用多个外部AI工具获取答案
   - 对答案进行分析和共识计算
   - 生成并显示最终报告

4. **保存报告**
   - 系统会询问是否保存报告
   - 确认后报告将保存到reports/目录

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
├── .models/                      # 模型文件目录
├── reports/                      # 报告输出目录
├── logs/                         # 日志文件目录
└── config.yaml                   # 配置文件
```

## 配置管理

项目使用YAML格式的配置文件 `config.yaml`，首次运行时会自动创建默认配置。

### 主要配置项

- **local_llm**：本地LLM服务配置（模型路径、参数等）
- **external_tools**：外部AI工具配置（命令、参数、优先级等）
- **network**：网络相关配置（超时、检查等）
- **app**：应用行为配置（日志级别、最大澄清轮数等）

## 开发指南

### 代码风格

- 使用ruff进行代码格式化和检查
- 遵守PEP 8编码规范
- 所有函数必须包含类型注解
- 公共函数必须包含文档字符串

### 测试

- 使用pytest进行单元测试
- 测试文件位于tests/目录
- 运行测试命令：`uv run pytest -n auto`

### CI/CD

- 使用GitHub Actions进行持续集成
- 本地CI脚本：`python Scripts/ci.py`

## 贡献指南

1. **分支管理**：使用feature分支进行开发，完成后合并到main分支
2. **代码提交**：遵循conventional commits规范
3. **代码审查**：所有代码变更必须经过代码审查
4. **测试要求**：所有新功能必须添加单元测试

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目GitHub Issues
- 团队内部技术群
- 项目维护人员
