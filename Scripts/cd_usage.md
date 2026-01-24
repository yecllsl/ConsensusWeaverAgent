# CD脚本使用说明

## 概述

`cd.py` 是 ConsensusWeaverAgent 项目的持续部署脚本，自动化版本管理、代码检查、测试、构建和发布流程。

## 功能特性

- **版本管理**: 自动更新版本号（major/minor/patch）
- **代码检查**: 集成 ruff 和 mypy 进行代码质量检查
- **测试执行**: 自动运行 pytest 测试套件
- **包构建**: 使用 setuptools 构建发布包
- **Git标签管理**: 自动创建和推送版本标签
- **PyPI发布**: 支持发布到 PyPI 和 TestPyPI
- **试运行模式**: 支持干运行，不执行实际操作

## 基本用法

### 查看帮助信息

```powershell
python Scripts/cd.py --help
```

### 完整部署流程（推荐）

```powershell
# 更新补丁版本（0.2.0 -> 0.2.1）并执行完整部署
python Scripts/cd.py --version-bump patch --create-git-tag --push-git-tag

# 更新次版本（0.2.0 -> 0.3.0）并执行完整部署
python Scripts/cd.py --version-bump minor --create-git-tag --push-git-tag

# 更新主版本（0.2.0 -> 1.0.0）并执行完整部署
python Scripts/cd.py --version-bump major --create-git-tag --push-git-tag
```

### 试运行模式

```powershell
# 试运行部署流程，不执行实际操作
python Scripts/cd.py --version-bump patch --dry-run --create-git-tag --push-git-tag
```

### 发布到TestPyPI

```powershell
# 发布到测试PyPI环境
python Scripts/cd.py --version-bump patch --use-test-pypi --create-git-tag --push-git-tag
```

## 命令行选项

| 选项 | 描述 |
|------|------|
| `--config` | 指定配置文件路径 |
| `--python-version` | 指定Python版本（默认：3.12） |
| `--uv-version` | 指定uv版本（默认：0.9.0） |
| `--project-dir` | 指定项目目录 |
| `--skip-checks` | 跳过代码检查 |
| `--skip-tests` | 跳过测试执行 |
| `--skip-build` | 跳过包构建 |
| `--skip-publish` | 跳过包发布 |
| `--skip-git` | 跳过Git操作 |
| `--version-bump` | 更新版本号（major/minor/patch） |
| `--use-test-pypi` | 发布到TestPyPI而非PyPI |
| `--create-git-tag` | 创建Git标签 |
| `--push-git-tag` | 推送Git标签到远程仓库 |
| `--dry-run` | 试运行模式，不执行实际操作 |
| `--log-level` | 日志级别（debug/info/warning/error/critical） |

## 部署流程

CD脚本按以下顺序执行各个阶段：

1. **环境检查**
   - 检查Python版本
   - 检查uv依赖管理工具
   - 检查Git版本控制

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
python Scripts/cd.py --version-bump patch --create-git-tag --push-git-tag
```

### 场景2：新功能发布

```powershell
# 添加新功能后发布次版本
python Scripts/cd.py --version-bump minor --create-git-tag --push-git-tag
```

### 场景3：重大更新发布

```powershell
# 重大变更后发布主版本
python Scripts/cd.py --version-bump major --create-git-tag --push-git-tag
```

### 场景4：测试发布流程

```powershell
# 在TestPyPI测试发布流程
python Scripts/cd.py --version-bump patch --use-test-pypi --dry-run
```

### 场景5：仅构建包

```powershell
# 只构建包，不发布
python Scripts/cd.py --skip-publish
```

## 环境要求

- Python 3.12+
- uv 依赖管理工具
- Git（可选，用于标签管理）
- PyPI账号（用于发布）
- twine（自动安装）

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
   - patch: 向后兼容的错误修复问题

3. **Git工作区**: 创建标签前建议确保Git工作区干净，无未提交的更改

4. **TestPyPI**: 建议先在TestPyPI测试发布流程，确认无误后再发布到正式PyPI

## 日志文件

CD脚本运行日志保存在 `logs/cd.log`，包含详细的执行信息和错误记录。

## 错误处理

脚本在以下情况会停止执行：

- 环境检查失败
- 代码检查失败
- 测试执行失败
- 包构建失败
- 包发布失败

使用 `--log-level debug` 可以获取更详细的日志信息用于问题排查。

## 与CI脚本的关系

- `ci.py`: 持续集成脚本，用于代码检查和测试
- `cd.py`: 持续部署脚本，用于版本管理和发布

两者可以独立使用，也可以配合使用。CI脚本确保代码质量，CD脚本自动化发布流程。
