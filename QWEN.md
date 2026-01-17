# ConsensusWeaverAgent 项目上下文

## 项目概述

ConsensusWeaverAgent 是一款先进的本地终端智能问答协调应用。该应用以用户提出的问题为起点，通过与运行在本地的大语言模型互动，主动引导用户澄清和完善问题的核心意图。随后，应用将智能决策执行路径，可并行调用多个需要联网的外部AI命令行工具获取多角度答案，并对这些答案在本地进行深度分析和共识度计算，最终为用户呈现一份结构清晰、洞察深刻的综合性报告。

### 核心功能
- **智能交互引擎**：与本地LLM互动，引导用户澄清问题意图
- **并发查询执行器**：并行调用多个外部AI工具获取答案
- **共识分析引擎**：对多个答案进行深度分析和共识度计算
- **报告生成器**：生成综合报告，包含共识分析、综合结论和分歧点

### 技术栈
- **Python 3.12+**：核心编程语言
- **LangChain**：LLM集成框架
- **llama-cpp-python**：本地LLM服务
- **Click**：命令行界面
- **PyYAML**：配置管理
- **SQLite**：数据持久化
- **NLTK**：文本分析
- **scikit-learn**：相似度计算

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

## 主要模块详解

### 1. 交互引擎 (Interaction Engine)
- **位置**: `src/service/interaction/interaction_engine.py`
- **功能**: 管理用户交互流程，包括问题分析、澄清对话、问题重构等
- **关键类**: `InteractionEngine`, `InteractionState`
- **流程**:
  1. 接收用户原始问题
  2. 分析问题的完整性、清晰度和潜在歧义
  3. 与用户进行澄清对话（最多3轮）
  4. 重构问题以获得最佳表述

### 2. 执行策略管理器 (Execution Strategy Manager)
- **位置**: `src/service/strategy/execution_strategy.py`
- **功能**: 决定如何处理用户问题（直接回答或并行查询）
- **关键类**: `ExecutionStrategyManager`, `ExecutionPlan`
- **策略**:
  - 简单问题：直接使用本地LLM回答
  - 复杂问题：并行调用多个外部AI工具

### 3. 查询执行器 (Query Executor)
- **位置**: `src/core/executor/query_executor.py`
- **功能**: 执行并行查询，管理外部工具调用
- **关键类**: `QueryExecutor`, `QueryExecutionResult`
- **特点**: 异步执行，支持并发调用多个工具

### 4. 工具管理器 (Tool Manager)
- **位置**: `src/infrastructure/tools/tool_manager.py`
- **功能**: 管理外部AI工具的执行
- **关键类**: `ToolManager`, `ToolResult`
- **支持**: PowerShell脚本、可执行文件等

### 5. 共识分析器 (Consensus Analyzer)
- **位置**: `src/core/analyzer/consensus_analyzer.py`
- **功能**: 分析多个工具返回结果的一致性和差异
- **关键类**: `ConsensusAnalyzer`, `ConsensusAnalysisResult`
- **算法**: TF-IDF向量化 + 余弦相似度计算

### 6. 报告生成器 (Report Generator)
- **位置**: `src/core/reporter/report_generator.py`
- **功能**: 生成综合分析报告
- **关键类**: `ReportGenerator`, `Report`
- **输出**: 包含基本信息、工具结果、共识分析、综合总结和最终结论

### 7. 配置管理器 (Config Manager)
- **位置**: `src/infrastructure/config/config_manager.py`
- **功能**: 管理应用配置
- **关键类**: `ConfigManager`, `Config`
- **配置项**: 本地LLM、外部工具、网络、应用设置

### 8. 数据管理器 (Data Manager)
- **位置**: `src/infrastructure/data/data_manager.py`
- **功能**: SQLite数据库管理
- **关键类**: `DataManager`, `SessionRecord`, `ToolResultRecord`, `AnalysisResultRecord`
- **存储**: 会话信息、工具结果、分析结果

### 9. LLM服务 (LLM Service)
- **位置**: `src/infrastructure/llm/llm_service.py`
- **功能**: 本地大语言模型集成
- **关键类**: `LLMService`
- **技术**: llama-cpp-python, LangChain

## 构建和运行

### 环境要求
- Windows 10/11 (64位)
- Python 3.12+
- 至少8GB RAM (推荐16GB以上)
- 至少10GB可用磁盘空间

### 安装步骤
```powershell
# 安装依赖
uv venv && uv sync --all-extras
.venv\Scripts\activate

# 下载NLTK资源
python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# 下载模型文件
python scripts/download_qwen3-8b-gguf.py
```

### 运行应用
```powershell
# 运行应用
python -m src.main

# 指定配置文件
python -m src.main --config my_config.yaml

# 启用详细日志
python -m src.main --verbose
```

## 开发约定

### 代码规范
- 使用Ruff进行代码格式化和lint检查
- 使用MyPy进行类型检查
- 遵循PEP 8编码规范

### 测试
- 单元测试：`uv run pytest tests/unit/`
- 集成测试：`uv run pytest tests/integration/`
- 所有新功能必须添加单元测试

### 依赖管理
- 使用uv包管理器
- 运行时依赖在`[project.dependencies]`中定义
- 开发依赖在`[project.optional-dependencies.dev]`中定义

## 关键数据流

1. **用户输入** → 交互引擎 → 问题分析 → 澄清对话 → 问题重构
2. **重构问题** → 执行策略管理器 → 执行计划 → 查询执行器 → 外部工具调用
3. **工具结果** → 共识分析器 → 相似度计算 → 共识度评分 → 核心观点提取
4. **分析结果** → 报告生成器 → 综合报告 → 用户展示

## 配置文件

应用使用YAML格式的配置文件 `config.yaml`，包含：
- **local_llm**: 本地LLM服务配置
- **external_tools**: 外部AI工具配置
- **network**: 网络相关配置
- **app**: 应用行为配置

## 数据模型

- **SessionRecord**: 会话记录
- **ToolResultRecord**: 工具执行结果记录
- **AnalysisResultRecord**: 分析结果记录
- **InteractionState**: 交互状态
- **ExecutionPlan**: 执行计划
- **QueryExecutionResult**: 查询执行结果
- **ConsensusAnalysisResult**: 共识分析结果
- **Report**: 最终报告

## 错误处理

- 所有模块都有适当的异常处理机制
- 使用日志记录错误信息
- 对于NLTK资源缺失的情况，提供了备用实现
- 支持回退策略（如LLM分析失败时使用简单文本分析）

## 扩展性

- 模块化设计，易于扩展新功能
- 支持添加新的外部AI工具
- 配置驱动，易于修改行为
- 数据库设计支持历史记录和分析