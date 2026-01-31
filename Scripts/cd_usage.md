# CI/CD脚本使用说明

## 概述

`cicd.py` 是 ConsensusWeaverAgent 项目的统一持续集成和持续部署脚本，自动化版本管理、代码检查、测试、构建和发布流程。

## 功能特性

- **CI（持续集成）**：环境准备、依赖安装、代码检查、测试执行、安全检查
- **CD（持续部署）**：版本管理、代码检查、测试、构建、发布、Git标签管理
- **统一配置**：单一配置文件管理所有CI/CD参数
- **跨平台支持**：支持 Windows、Linux、macOS
- **灵活执行模式**：支持仅CI、仅CD或完整CI/CD流程

## 执行模式

| 模式 | 描述 |
|------|------|
| `ci` | 仅执行CI流程（代码检查和测试） |
| `cd` | 仅执行CD流程（版本管理、构建和发布） |
| `all` | 执行完整的CI/CD流程（默认） |

## 基本用法

### 查看帮助信息

```powershell
python Scripts/cicd.py --help
```

### 仅执行CI流程

```powershell
# 执行完整的CI流程（环境准备、代码检查、测试、安全检查）
python Scripts/cicd.py --mode ci

# 跳过特定步骤
python Scripts/cicd.py --mode ci --skip-format --skip-security
```

### 仅执行CD流程

```powershell
# 执行完整的CD流程（代码检查、测试、构建、发布）
python Scripts/cicd.py --mode cd

# 更新版本并发布
python Scripts/cicd.py --mode cd --version-bump patch --create-git-tag --push-git-tag --publish
```

### 执行完整CI/CD流程

```powershell
# 默认模式（all），执行完整的CI/CD流程
python Scripts/cicd.py

# 更新补丁版本并执行完整部署
python Scripts/cicd.py --version-bump patch --create-git-tag --push-git-tag --publish

# 更新次版本并执行完整部署
python Scripts/cicd.py --version-bump minor --create-git-tag --push-git-tag --publish

# 更新主版本并执行完整部署
python Scripts/cicd.py --version-bump major --create-git-tag --push-git-tag --publish
```

### 试运行模式

```powershell
# 试运行部署流程，不执行实际操作
python Scripts/cicd.com --version-bump patch --dry-run --create-git-tag --push-git-tag
```

### 发布到TestPyPI

```powershell
# 发布到测试PyPI环境
python Scripts/cicd.py --mode cd --version-bump patch --use-test-pypi --create-git-tag --push-git-tag --publish
```

## 命令行选项

### 通用选项

| 选项 | 描述 | 默认值 |
|------|------|----------|
| `--mode` | 执行模式（ci/cd/all） | all |
| `--config` | 指定配置文件路径 | - |
| `--python-version` | 指定Python版本 | 3.12 |
| `--uv-version` | 指定uv版本 | 0.9.0 |
| `--project-dir` | 指定项目目录 | 当前目录 |
| `--log-level` | 日志级别（debug/info/warning/error/critical） | info |

### CI选项

| 选项 | 描述 |
|------|------|
| `--skip-env-prep` | 跳过环境准备 |
| `--skip-deps` | 跳过依赖安装 |
| `--skip-format` | 跳过代码格式检查和格式化 |
| `--skip-mypy` | 跳过类型检查 |
| `--skip-tests` | 跳过测试执行 |
| `--skip-security` | 跳过安全检查 |

### CD选项

| 选项 | 描述 |
|------|------|
| `--skip-checks` | 跳过代码检查（CD） |
| `--skip-build` | 跳过包构建 |
| `--skip-publish` | 跳过包发布（默认跳过） |
| `--skip-git` | 跳过Git操作 |
| `--version-bump` | 更新版本号（major/minor/patch） |
| `--create-git-tag` | 创建Git标签 |
| `--push-git-tag` | 推送Git标签到远程仓库 |
| `--publish` | 启用包发布到PyPI |
| `--use-test-pypi` | 发布到TestPyPI而非PyPI |
| `--dry-run` | 试运行模式，不执行实际操作 |

## 配置选项

脚本支持通过配置文件自定义以下参数：

| 配置项 | 描述 | 默认值 |
|--------|------|----------|
| `PYTHON_VERSION` | Python版本要求 | 3.12 |
. | `UV_VERSION` | uv依赖管理工具版本 | 0.9.0 |
` | `UV_INDEX_URL` | PyPI镜像源 | https://pypi.org/simple |
| `RUFF_OUTPUT_FORMAT` | ruff输出格式 | github |
| `MYPY_STRICT` | mypy严格模式 | false |
| `PYTEST_VERBOSE` | pytest详细输出 | true |
| `PYTEST_TB_STYLE` | pytest回溯样式 | short |
| `COVERAGE_ENABLED` | 启用测试覆盖率 | true |
| `COVERAGE_THRESHOLD` | 覆盖率阈值（%） | 70 |
| `PYPI_INDEX_URL` | PyPI上传地址 | https://upload.pypi.org/legacy/ |
| `TEST_PYPI_INDEX_URL` | TestPyPI上传地址 | https://test.pypi.org/legacy/ |

## CI流程

CI脚本按以下顺序执行各个阶段：

1. **环境准备**
   - 检查Python版本
   - 检查uv依赖管理工具
   - 安装uv（如需要）

2. **依赖安装**
   - 安装项目依赖
   - 安装开发依赖

3. **代码格式检查**
   - 使用ruff检查代码格式
   - 检查代码风格和潜在问题

4. **代码格式化**
   - 使用ruff格式化代码
   - 确保代码格式一致

5. **类型检查**
   - 使用mypy进行类型检查
   - 支持strict模式（可选）

6. **测试执行**
   - 使用pytest运行测试套件
   - 生成测试报告（JUnit XML）
   - 生成覆盖率报告（XML和HTML）
   - 检查覆盖率是否达到阈值

7. **测试报告生成**
   - 确认测试报告已生成

8. **安全检查**
   - 使用bandit进行安全扫描
   - 生成安全报告（JSON）

## CD流程

CD脚本按以下顺序执行各个阶段：

1. **环境检查**
   - 检查Python版本
   - 检查uv依赖管理工具
   - 检查Git版本控制（可选）

2. **代码检查**
   - 使用ruff检查代码格式
   - 使用mypy进行类型检查

3. **测试执行**
   - 使用pytest运行测试套件
   - 并行测试加速执行

4. **包构建**
   - 清理旧的构建文件
   - 使用setuptools构建发布包
   - 生成wheel和源码包

5. **Git标签管理**
   - 检查Git仓库状态
   - 创建版本标签
   - 推送标签到远程仓库

6. **包发布**
   - 使用twine上传包到PyPI
   - 支持TestPyPI测试环境

## 使用场景

### 场景1：日常补丁发布

```powershell
# 修复bug后发布补丁版本
python Scripts/cicd.py --version-bump patch --create-git-tag --push-git-tag --publish
```

### 场景2：新功能发布

```powershell
# 添加新功能后发布次版本
python Scripts/cicd.py --version-bump minor --create-git-tag --push-git-tag --publish
```

### 场景3：重大更新发布

```powershell
# 重大变更后发布主版本
python Scripts/cicd.py --version-bump major --create-git-tag --push-git-tag --publish
```

### 场景4：测试发布流程

```powershell
# 在TestPyPI测试发布流程
python Scripts/cicd.py --version-bump patch --use-test-pypi --dry-run
```

### 场景5：仅构建包

```powershell
# 只构建包，不发布
python Scripts/cicd.py --skip-publish
```

### 场景6：本地开发测试

```powershell
# 仅运行CI流程，不执行发布
python Scripts/cicd.py --mode ci
```

### 场景7：快速CI检查

```powershell
# 跳过耗时步骤，快速检查代码
python Scripts/cicd.py --mode ci --skip-tests --skip-security
```

## 环境要求

- Python 3.12+
- uv依赖管理工具
- Git（可选，用于标签管理）
- PyPI账号（用于发布）
- twine（自动安装）
- pytest-cov（用于覆盖率报告）

## 注意事项

1. **PyPI认证**: 首次发布前需要配置PyPI认证信息
   ```powershell
   # 配置PyPI token
   python -m keyring set https://upload.pypi.org/legacy/ username __token__
   python -m keyring set https://upload.pypi.org/legacy/ password <your-token>
   ```

2. **版本号格式**: 版本号遵循语义化版本规范（Semantic Versioning）
   - major: 不兼容的API更改
   - minor: 向后兼容的功能新增
   - patch: 向后兼容的错误修复

3. **Git工作区**: 创建标签前建议确保Git工作区干净，无未提交的更改

4. **TestPyPI**: 建议先在TestPyPI测试发布流程，确认无误后再发布到正式PyPI

5. **覆盖率阈值**: 默认设置为70%，可通过配置文件调整

6. **mypy严格模式**: 默认关闭，可通过 `--mypy-strict` 启用

## 日志文件

CI/CD脚本运行日志保存在 `logs/cicd.log`，包含详细的执行信息和错误记录。

## 错误处理

脚本在以下情况会停止执行：

- 环境检查失败
- 代码检查失败
- 测试执行失败
- 覆盖率未达到阈值
- 包构建失败
- 包发布失败

使用 `--log-level debug` 可以获取更详细的日志信息用于问题排查。

## 与GitHub Actions的同步

CI/CD脚本与GitHub Actions工作流（`.github/workflows/ci-cd.yml`）保持行为一致：

| 功能 | GitHub Actions | 本地脚本 |
|------|---------------|----------|
| Python版本 | 3.12 | 3.12 |
| UV版本 | 0.9.0 | 0.9.0 |
| ruff检查 | `--output-format=github` | `--output-format=github` |
| ruff格式化 | `ruff format .` | `ruff format .` |
| mypy检查 | `mypy src/` | `mypy src/` |
| pytest测试 | `-v --tb=short -n auto` | `-v --tb=short -n auto` |
| 覆盖率测试 | `--cov=src --cov-report=xml --cov-report=html --cov-fail-under=80` | `--cov=src --cov-report=xml --cov-report=html --cov-fail-under=70` |

## 输出文件

脚本运行后会生成以下文件：

| 文件/目录 | 描述 |
|-----------|------|
| `logs/cicd.log` | CI/CD执行日志 |
| `reports/test-results/test-results.xml` | JUnit格式测试报告 |
| `coverage.xml` | 覆盖率XML报告 |
| `htmlcov/` | 覆盖率HTML报告目录 |
| `security-report.json` | 安全扫描报告 |
| `dist/` | 构建产物目录 |
