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

## 开发工作流

### 代码规范

- **代码格式化**：使用ruff统一处理代码格式化和lint检查
  ```powershell
  uv run ruff check .
  uv run ruff format .
  ```

- **类型检查**：使用mypy进行严格的类型检查
  ```powershell
  uv run mypy --strict .
  ```

### 测试流程

- **运行单元测试**
  ```powershell
  uv run pytest tests/unit/
  ```

- **运行集成测试**
  ```powershell
  uv run pytest tests/integration/
  ```

- **运行所有测试**
  ```powershell
  uv run pytest
  ```

### 依赖管理

- **添加依赖**
  ```powershell
  uv add <package>
  uv add --group dev <package>  # 添加开发依赖
  ```

- **更新依赖**
  ```powershell
  uv update
  ```

- **同步环境**
  ```powershell
  uv sync
  ```

## 运行应用

```powershell
# 运行应用
python -m src.main

# 指定配置文件
python -m src.main --config my_config.yaml

# 启用详细日志
python -m src.main --verbose
```

## 项目结构

```
src/
├── core/                   # 核心功能层
│   ├── analyzer/          # 共识分析引擎
│   ├── executor/          # 并发查询执行器
│   └── reporter/          # 报告生成器
├── infrastructure/        # 基础设施层
│   ├── config/            # 配置管理
│   ├── data/              # 数据持久化
│   ├── logging/           # 日志系统
│   ├── llm/               # LLM集成服务
│   └── tools/             # 外部工具集成
├── service/               # 应用服务层
│   ├── interaction/       # 智能交互引擎
│   └── strategy/          # 执行策略管理器
├── models/                # 数据模型
├── utils/                 # 工具函数
├── ui/                    # 用户界面层
└── main.py                # 应用入口
```

## 配置说明

项目使用YAML格式的配置文件 `config.yaml`，首次运行时会自动创建默认配置。配置文件包含以下主要部分：

- **local_llm**：本地LLM服务配置
- **external_tools**：外部AI工具配置
- **network**：网络相关配置
- **app**：应用行为配置

详细配置说明请参考 `docs/design/配置设计.md`。

## 文档

- **需求文档**：`docs/requirements/requirements.md`
- **技术选型**：`docs/design/技术选型.md`
- **架构设计**：`docs/design/架构设计.md`
- **本地开发环境搭建**：`docs/dev/本地开发环境搭建.md`

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
