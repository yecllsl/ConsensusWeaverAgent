# ConsensusWeaverAgent

智能问答协调终端应用 - 一个能够协调多个AI工具并生成综合报告的智能系统。

## 项目概述

ConsensusWeaverAgent是一款先进的本地终端智能问答协调应用。该应用以用户提出的问题为起点，通过与运行在本地的大语言模型互动，主动引导用户澄清和完善问题的核心意图。随后，应用将智能决策执行路径，可并行调用多个需要联网的外部AI命令行工具获取多角度答案，并对这些答案在本地进行深度分析和共识度计算，最终为用户呈现一份结构清晰、洞察深刻的综合性报告。

### 最新功能

- **批量查询模式**：支持从文件批量导入问题，并发处理多个查询
- **智能工具选择器**：根据问题类型自动选择最适合的工具
- **性能监控和统计**：实时监控系统性能指标，生成性能报告
- **外部Agent调用重试机制**：提高系统容错能力
- **统一的 CI/CD 脚本**：整合 CI 和 CD 流程到单一脚本
- **历史记录管理**：查询、导出和统计分析历史会话记录
- **多格式报告生成**：支持TEXT、Markdown、HTML、JSON、PDF五种报告格式
- **智能缓存机制**：LLM响应缓存和工具结果缓存，提升性能
- **增强的测试覆盖**：80.00%代码覆盖率，确保质量稳定

## 核心功能

### 智能交互引擎
- 与本地LLM互动，引导用户澄清问题意图
- 支持多轮对话和问题重构
- 智能识别用户需求并引导完善

### 并发查询执行器
- 并行调用多个外部AI工具获取答案
- 支持自定义工具配置和优先级
- 网络超时和错误处理

### 共识分析引擎
- 对多个答案进行深度分析
- 计算相似度矩阵和共识度评分
- 识别核心观点和分歧点
- 生成综合总结和最终结论

### 报告生成器
- 生成结构化综合报告
- 支持多种输出格式（TEXT、Markdown、HTML、JSON、PDF）
- 包含详细的共识分析和可视化数据

### 历史记录管理
- 查询和筛选历史会话
- 按日期、关键词、共识度排序
- 导出历史记录为多种格式
- 统计分析和数据汇总

### 智能缓存机制
- LLM响应缓存，减少重复计算
- 工具结果缓存，提升响应速度
- 支持缓存过期和大小限制
- 缓存命中统计和性能监控

### 批量查询管理
- 从JSON文件批量导入问题
- 并发处理多个查询（可配置并发数）
- 生成结构化的批量查询报告
- 支持失败重试机制

### 智能工具选择
- 根据问题类型自动选择最适合的工具
- 工具性能评分和推荐机制
- 基于历史数据的智能推荐
- 支持自定义工具选择策略

### 性能监控
- 实时监控系统性能指标（CPU、内存、磁盘、网络）
- 性能阈值告警
- 生成性能报告
- 历史性能数据统计

## 技术栈

- **Python 3.12+**：核心编程语言
- **LangChain**：LLM集成框架
- **llama-cpp-python**：本地LLM服务
- **Click**：命令行界面
- **PyYAML**：配置管理
- **SQLite**：数据持久化
- **NLTK**：文本分析
- **scikit-learn**：相似度计算
- **pytest**：单元测试框架
- **uv**：现代Python包管理器

## 环境搭建

### 前置要求

- Windows 10/11 (64位) / macOS / Linux
- Python 3.12+
- 至少8GB RAM (推荐16GB以上)
- 至少10GB可用磁盘空间

### 安装步骤

#### 方法1：使用uv安装（推荐）

```powershell
# 1. 克隆项目代码
git clone <项目仓库地址>
cd ConsensusWeaverAgent

# 2. 安装uv包管理器
pip install uv

# 3. 创建虚拟环境并安装依赖
uv venv
uv sync --all-extras
```

#### 方法2：使用pip安装

```powershell
# 1. 克隆项目代码
git clone <项目仓库地址>
cd ConsensusWeaverAgent

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 4. 安装依赖
pip install -e .
```

#### 方法3：直接安装（生产环境）

```powershell
# 直接使用pip安装
pip install consensusweaveragent
```

### 下载必需资源

#### 1. 下载NLTK资源

```powershell
python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

#### 2. 下载GGUF模型文件

**方法1：使用模型下载脚本（推荐）**

```powershell
python scripts/download_qwen3-8b-gguf.py
```

**方法2：手动下载**

1. 访问 [ModelScope模型库](https://modelscope.cn/models/qwen/Qwen3-4B-GGUF)
2. 下载Qwen3-4B-Q5_K_M.gguf模型文件
3. 创建.models/qwen/目录
4. 将模型文件放置到该目录中

**方法3：从Hugging Face下载**

1. 访问 [Hugging Face模型库](https://huggingface.co/Qwen/Qwen3-4B-GGUF)
2. 下载Qwen3-4B-Q5_K_M.gguf模型文件
3. 创建.models/qwen/目录
4. 将模型文件放置到该目录中

## 命令行使用

### 基本命令语法

```powershell
consensusweaver [选项]
```

### 可用选项

| 选项 | 别名 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| `--config` | `-c` | PATH | 否 | `config.yaml` | 指定配置文件路径 |
| `--verbose` | `-v` | FLAG | 否 | `False` | 启用详细日志输出 |
| `--iflow` | `--i` | FLAG | 否 | `False` | 使用iflow作为主Agent |
| `--qwen` | `--q` | FLAG | 否 | `False` | 使用qwen作为主Agent |
| `--codebuddy` | `--b` | FLAG | 否 | `False` | 使用codebuddy作为主Agent |
| `--help` | `-h` | FLAG | 否 | - | 显示帮助信息 |

### 参数说明

#### --config / -c
- **类型**：文件路径（PATH）
- **描述**：指定自定义配置文件路径
- **默认值**：`config.yaml`
- **使用场景**：当需要使用不同的配置文件时
- **示例**：
  ```powershell
  consensusweaver --config my_config.yaml
  consensusweaver -c /path/to/custom_config.yaml
  ```

#### --verbose / -v
- **类型**：标志（FLAG）
- **描述**：启用详细日志输出，用于调试和问题排查
- **默认值**：`False`
- **使用场景**：开发调试、问题排查
- **示例**：
  ```powershell
  consensusweaver --verbose
  consensusweaver -v
  ```

#### --iflow / --i
- **类型**：标志（FLAG）
- **描述**：使用iflow作为主Agent进行问题处理
- **默认值**：`False`
- **依赖关系**：与`--qwen`和`--codebuddy`互斥，只能选择一个
- **使用场景**：需要使用iflow工具作为主要回答来源
- **示例**：
  ```powershell
  consensusweaver --iflow
  consensusweaver --i
  ```

#### --qwen / --q
- **类型**：标志（FLAG）
- **描述**：使用qwen作为主Agent进行问题处理
- **默认值**：`False`
- **依赖关系**：与`--iflow`和`--codebuddy`互斥，只能选择一个
- **使用场景**：需要使用qwen工具作为主要回答来源
- **示例**：
  ```powershell
  consensusweaver --qwen
  consensusweaver --q
  ```

#### --codebuddy / --b
- **类型**：标志（FLAG）
- **描述**：使用codebuddy作为主Agent进行问题处理
- **默认值**：`False`
- **依赖关系**：与`--iflow`和`--qwen`互斥，只能选择一个
- **使用场景**：需要使用codebuddy工具作为主要回答来源
- **示例**：
  ```powershell
  consensusweaver --codebuddy
  consensusweaver --b
  ```

### 参数依赖关系

以下参数之间存在互斥关系，**不能同时使用**：

- `--iflow` / `--i`
- `--qwen` / `--q`
- `--codebuddy` / `--b`

**错误示例**：
```powershell
# 错误：同时指定了多个Agent
consensusweaver --iflow --qwen
```

**正确示例**：
```powershell
# 正确：只指定一个Agent
consensusweaver --iflow
```

### 使用示例

#### 基础使用场景

**场景1：使用默认配置启动应用**

```powershell
consensusweaver
```

**场景2：使用自定义配置文件**

```powershell
# 使用项目根目录下的自定义配置
consensusweaver --config my_config.yaml

# 使用绝对路径的配置文件
consensusweaver -c /home/user/configs/production.yaml
```

**场景3：启用详细日志进行调试**

```powershell
# 启用详细日志
consensusweaver --verbose

# 结合自定义配置使用
consensusweaver -c config.yaml -v
```

#### 高级使用场景

**场景4：使用特定工具作为主Agent**

```powershell
# 使用iflow作为主Agent
consensusweaver --iflow

# 使用qwen作为主Agent
consensusweaver --qwen

# 使用codebuddy作为主Agent
consensusweaver --codebuddy
```

**场景5：组合使用多个选项**

```powershell
# 使用自定义配置 + 详细日志 + 特定Agent
consensusweaver --config production.yaml --verbose --iflow

# 简写形式
consensusweaver -c prod.yaml -v -i
```

**场景6：开发环境调试**

```powershell
# 开发调试模式
consensusweaver --config dev_config.yaml --verbose
```

### 交互流程

1. **启动应用**
   ```powershell
   consensusweaver
   ```

2. **输入问题**
   - 在命令行中输入您的问题，按回车键确认
   - 系统会自动分析问题并可能要求您澄清一些细节

3. **问题澄清（如需要）**
   - 如果问题不够明确，系统会提出澄清问题
   - 回答澄清问题以完善原始问题
   - 最多进行3轮澄清（可在配置中调整）

4. **查看执行过程**
   - 系统会显示正在调用的工具
   - 显示每个工具的执行状态和结果
   - 实时更新执行进度

5. **查看分析结果**
   - 系统会显示相似度矩阵
   - 显示共识度评分
   - 识别核心观点和分歧点
   - 生成综合总结和最终结论

6. **保存报告**
   - 系统会询问是否保存报告
   - 确认后报告将保存到reports/目录
   - 支持多种格式（TEXT、Markdown、HTML、JSON、PDF）

7. **继续使用**
   - 可以继续提问或退出应用
   - 历史记录会自动保存

## 配置管理

项目使用YAML格式的配置文件 `config.yaml`，首次运行时会自动创建默认配置。

### 配置文件结构

```yaml
app:
  history_enabled: true
  history_limit: 100
  log_file: logs/consensusweaver.log
  log_level: info
  max_clarification_rounds: 3
  max_parallel_tools: 5

external_tools:
  - name: iflow
    command: iflow.ps1
    args: -y -p
    enabled: true
    needs_internet: true
    priority: 1

local_llm:
  provider: llama-cpp
  model: Qwen3-8B-Q5_K_M.gguf
  model_path: .models/qwen/Qwen3-8B-Q5_K_M.gguf
  n_ctx: 4096
  n_threads: 6
  max_tokens: 512
  temperature: 0.3

network:
  check_before_run: true
  timeout: 120
```

### 主要配置项说明

#### app配置节

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|----------|------|
| `history_enabled` | BOOLEAN | `true` | 是否启用历史记录功能 |
| `history_limit` | INTEGER | `100` | 保存的历史记录最大数量 |
| `log_file` | STRING | `logs/consensusweaver.log` | 日志文件路径 |
| `log_level` | STRING | `info` | 日志级别（debug/info/warning/error） |
| `max_clarification_rounds` | INTEGER | `3` | 最大问题澄清轮数 |
| `max_parallel_tools` | INTEGER | `5` | 最大并行工具执行数量 |

#### external_tools配置节

| 配置项 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| `name` | STRING | 是 | 工具名称 |
| `command` | STRING | 是 | 工具命令路径 |
| `args` | STRING | 否 | 工具命令参数 |
| `enabled` | BOOLEAN | 是 | 是否启用该工具 |
| `needs_internet` | BOOLEAN | 是 | 是否需要网络连接 |
| `priority` | INTEGER | 是 | 工具优先级（数字越小优先级越高） |

#### local_llm配置节

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|----------|------|
| `provider` | STRING | `llama-cpp` | LLM服务提供商 |
| `model` | STRING | `Qwen3-4B-Q5_K_M.gguf` | 模型文件名 |
| `model_path` | STRING | `.models/qwen/Qwen3-4B-Q5_K_M.gguf` | 模型文件完整路径 |
| `n_ctx` | INTEGER | `4096` | 上下文窗口大小 |
| `n_threads` | INTEGER | `16` | 线程数 |
| `max_tokens` | INTEGER | `512` | 最大生成token数 |
| `temperature` | FLOAT | `0.3` | 温度参数（0.0-1.0） |

#### network配置节

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|----------|------|
| `check_before_run` | BOOLEAN | `true` | 运行前检查网络连接 |
| `timeout` | INTEGER | `120` | 网络请求超时时间（秒） |

### 自定义配置示例

#### 示例1：开发环境配置

```yaml
app:
  history_enabled: true
  history_limit: 50
  log_file: logs/dev.log
  log_level: debug
  max_clarification_rounds: 5
  max_parallel_tools: 3

local_llm:
  provider: llama-cpp
  model_path: .models/qwen/Qwen3-8B-Q5_K_M.gguf
  n_threads: 4
  temperature: 0.5
```

#### 示例2：生产环境配置

```yaml
app:
  history_enabled: true
  history_limit: 1000
  log_file: logs/production.log
  log_level: warning
  max_clarification_rounds: 3
  max_parallel_tools: 5

local_llm:
  provider: llama-cpp
  model_path: .models/qwen/Qwen3-8B-Q5_K_M.gguf
  n_threads: 8
  temperature: 0.3
```

## 项目结构

```
ConsensusWeaverAgent/
├── src/                          # 源代码目录
│   ├── main.py                   # 应用入口
│   ├── core/                     # 核心功能层
│   │   ├── analyzer/             # 共识分析引擎
│   │   ├── executor/             # 并发查询执行器
│   │   └── reporter/             # 报告生成器
│   │       ├── report_generator.py    # 基础报告生成器
│   │       └── multi_format_reporter.py  # 多格式报告生成器
│   ├── infrastructure/           # 基础设施层
│   │   ├── cache/               # 缓存机制
│   │   │   └── cache_manager.py      # 缓存管理器
│   │   ├── config/               # 配置管理
│   │   ├── data/                 # 数据持久化
│   │   ├── llm/                  # LLM集成服务
│   │   ├── logging/              # 日志系统
│   │   └── tools/                # 外部工具集成
│   ├── service/                  # 应用服务层
│   │   ├── history/              # 历史记录服务
│   │   │   └── history_manager.py     # 历史记录管理器
│   │   ├── interaction/          # 智能交互引擎
│   │   └── strategy/             # 执行策略管理器
│   ├── models/                   # 数据模型
│   ├── ui/                       # 用户界面层
│   └── utils/                    # 工具函数
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   │   ├── test_cache_manager.py
│   │   ├── test_history_manager.py
│   │   ├── test_multi_format_reporter.py
│   │   └── ...
│   ├── integration/              # 集成测试
│   └── test_external_tools.py
├── docs/                         # 文档目录
│   ├── design/                   # 设计文档
│   ├── requirements/              # 需求文档
│   └── external/                 # 外部文档
├── .models/                      # 模型文件目录
├── reports/                      # 报告输出目录
├── logs/                         # 日志文件目录
├── htmlcov/                      # 测试覆盖率报告
└── config.yaml                   # 配置文件
```

## 开发指南

### 代码风格

- 使用ruff进行代码格式化和检查
- 遵守PEP 8编码规范
- 所有函数必须包含类型注解
- 公共函数必须包含Google风格文档字符串

### 测试

- 使用pytest进行单元测试
- 测试文件位于tests/unit/目录
- 测试覆盖率目标：70%+
- 运行测试命令：
  ```powershell
  # 运行所有测试
  uv run pytest -n auto
  
  # 运行测试并生成覆盖率报告
  uv run pytest --cov=src --cov-report=term-missing
  
  # 生成HTML覆盖率报告
  uv run pytest --cov=src --cov-report=html
  ```

### 依赖管理

- 使用uv工具管理依赖
- 添加依赖：`uv add <package>`
- 添加开发依赖：`uv add --group dev <package>`
- 同步环境：`uv sync`

### CI/CD

- 使用GitHub Actions进行持续集成
- 本地CI脚本：`python Scripts/ci.py`

## 常见问题

### Q1: 如何更改使用的LLM模型？

A: 修改config.yaml文件中的`local`配置节：

```yaml
local_llm:
  model_path: .models/your_model/your_model.gguf
```

### Q2: 如何添加新的外部工具？

A: 在config.yaml的`external_tools`配置节中添加新的工具配置：

```yaml
external_tools:
  - name: your_tool
    command: your_tool.ps1
    args: -p
    enabled: true
    needs_internet: true
    priority: 4
```

### Q3: 如何查看历史记录？

A: 历史记录功能已集成到应用中，可以通过以下方式访问：

1. 在应用运行时，系统会自动保存历史记录
2. 历史记录保存在SQLite数据库中
3. 可以通过HistoryManager类查询和导出历史记录

### Q4: 如何生成不同格式的报告？

A: 使用MultiFormatReporter类生成不同格式的报告：

```python
from src.core.reporter.multi_format_reporter import MultiFormatReporter

reporter = MultiFormatReporter(data_manager)

# 生成Markdown格式报告
report = reporter.generate_report(session_id, "markdown")

# 生成HTML格式报告
report = reporter.generate_report(session_id, "html")

# 生成JSON格式报告
report = reporter.generate_report(session_id, "json")

# 生成PDF格式报告
report = reporter.generate_report(session_id, "pdf")
```

### Q5: 如何启用或禁用缓存？

A: 修改配置文件中的缓存设置：

```yaml
app:
  cache_enabled: true  # 启用缓存
  cache_ttl: 3600     # 缓存生存时间（秒）
  cache_max_size: 1000 # 缓存最大条目数
```

## 贡献指南

1. **分支管理**：使用feature分支进行开发，完成后合并到develop分支
2. **代码提交**：遵循conventional commits规范
3. **代码审查**：所有代码变更必须经过代码审查
4. **测试要求**：所有新功能必须添加单元测试
5. **文档更新**：更新相关文档以反映代码变更

## 性能优化

### 缓存机制

- LLM响应缓存：减少重复的LLM调用
- 工具结果缓存：避免重复的网络请求
- 缓存命中率监控：通过日志查看缓存性能

### 并发执行

- 支持并行调用多个工具
- 可配置最大并行数
- 自动管理资源使用

### 数据库优化

- 使用索引加速查询
- 优化的SQL查询语句
- 自动清理过期数据

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目GitHub Issues
- 团队内部技术群
- 项目维护人员

## 更新日志

### v0.4.0 (开发中)

**新增功能**：
- rich库美化终端：提供美观的终端界面，支持进度条、表格、语法高亮等功能
- 用户反馈学习系统：收集用户反馈，学习用户偏好，优化工具选择策略
- 配置热重载：支持在运行时重新加载配置文件，无需重启应用
- 错误处理和恢复机制：完善错误分类，实现自动恢复策略，提供友好的错误提示

**改进**：
- 测试覆盖率提升至80%以上
- 终端交互体验优化
- 配置管理灵活性提升
- 系统稳定性增强

**修复**：
- 修复了配置热重载的状态不一致问题
- 修复了错误恢复策略的边界情况

### v0.3.0

**新增功能**：
- 批量查询模式：支持从文件批量导入问题，并发处理多个查询
- 智能工具选择器：根据问题类型自动选择最适合的工具
- 性能监控和统计：实时监控系统性能指标，生成性能报告
- 外部Agent调用重试机制：提高系统容错能力
- 历史记录管理功能
- 多格式报告生成（TEXT、Markdown、HTML、JSON、PDF）
- 智能缓存机制（LLM响应缓存、工具结果缓存）
- 增强的测试覆盖率（73.70%）

**改进**：
- 工具选择算法优化
- 性能监控精度提升
- 批量查询性能优化
- 数据库查询优化
- 报告生成性能提升
- 错误处理和日志改进

**修复**：
- 修复了批量查询的并发控制问题
- 修复了性能监控的资源泄漏问题
- 修复了历史记录查询的边界情况
- 修复了缓存过期处理的bug
- 修复了PDF生成的兼容性问题

### v0.2.0

**初始版本**：
- 智能交互引擎
- 并发查询执行器
- 共识分析引擎
- 基础报告生成器
- 配置管理系统
