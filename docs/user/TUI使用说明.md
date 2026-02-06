# TUI使用说明

## 概述

ConsensusWeaverAgent 0.4.0版本引入了基于Trogon的终端用户界面(TUI)，为用户提供更直观的交互体验。TUI模式为所有Click命令生成可视化表单界面，支持交互式选项探索与配置。

## 功能特性

### 1. 可视化命令界面
- 为每个命令及其选项生成可视化表单界面
- 支持交互式选项探索与配置
- 提供清晰的导航和操作指引

### 2. 主题支持
- 深色主题（默认）
- 浅色主题
- Monokai主题

### 3. 鼠标支持
- 支持鼠标操作
- 提供更好的用户体验

## 使用方法

### 启动TUI界面

```bash
# 启动TUI界面（默认深色主题）
python -m src.main tui

# 启动TUI子命令
python -m src.main tui tui
```

### 传统CLI模式

TUI集成不影响原有的纯命令行操作模式，所有命令仍然可以通过传统方式使用：

```bash
# 查看帮助
python -m src.main --help

# 运行交互式会话
python -m src.main run

# 询问单个问题
python -m src.main ask "什么是Python？"

# 检查系统环境
python -m src.main check

# 查看版本信息
python -m src.main version
```

## 命令说明

### run命令

运行交互式问答会话。

**选项：**
- `--iflow, -i`: 使用iflow作为主Agent
- `--qwen, -q`: 使用qwen作为主Agent
- `--codebuddy, -b`: 使用codebuddy作为主Agent

**示例：**
```bash
# 传统CLI模式
python -m src.main run --iflow

# TUI模式
python -m src.main tui
# 然后在TUI界面中选择run命令并配置选项
```

### ask命令

直接询问单个问题。

**选项：**
- `--iflow, -i`: 使用iflow作为主Agent
- `--qwen, -q`: 使用qwen作为主Agent
- `--codebuddy, -b`: 使用codebuddy作为主Agent
- `--output, -o`: 输出文件路径

**参数：**
- `QUESTION`: 要询问的问题

**示例：**
```bash
# 传统CLI模式
python -m src.main ask "什么是Python？" --output result.txt

# TUI模式
python -m src.main tui
# 然后在TUI界面中选择ask命令并配置选项
```

### check命令

检查系统环境和依赖。

**示例：**
```bash
# 传统CLI模式
python -m src.main check

# TUI模式
python -m src.main tui
# 然后在TUI界面中选择check命令
```

### version命令

显示版本信息。

**示例：**
```bash
# 传统CLI模式
python -m src.main version

# TUI模式
python -m src.main tui
# 然后在TUI界面中选择version命令
```

## 全局选项

### --config, -c

指定配置文件路径。

**示例：**
```bash
python -m src.main --config custom.yaml run
```

### --verbose, -v

启用详细日志。

**示例：**
```bash
python -m src.main --verbose run
```

## 环境要求

### 终端支持

TUI界面需要支持以下特性的终端：
- 颜色支持
- Unicode字符支持
- 终端宽度至少80列

### 支持的终端

- Windows Terminal
- macOS Terminal
- Linux终端模拟器（如GNOME Terminal、Konsole等）

### 检查环境兼容性

使用check命令检查环境兼容性：

```bash
python -m src.main check
```

## 键盘快捷键

在TUI界面中，可以使用以下键盘快捷键：

- `Tab`: 在选项之间切换
- `Enter`: 确认选择
- `Esc`: 返回上一级或取消
- `↑/↓`: 在列表中导航
- `←/→`: 在选项值之间切换
- `Ctrl+C`: 退出TUI界面

## 故障排除

### TUI界面无法启动

**问题：** TUI界面无法启动或显示错误

**解决方案：**
1. 检查Trogon是否正确安装
2. 确认终端支持必要的特性
3. 尝试使用传统CLI模式

### 终端显示异常

**问题：** 终端显示不正常或字符显示异常

**解决方案：**
1. 检查终端编码设置（建议使用UTF-8）
2. 尝试调整终端窗口大小
3. 切换主题（深色/浅色）

### 鼠标操作不响应

**问题：** 鼠标操作在TUI界面中不响应

**解决方案：**
1. 确认已启用鼠标支持（`--mouse true`）
2. 检查终端是否支持鼠标操作
3. 使用键盘快捷键作为替代

## 最佳实践

1. **首次使用：** 建议首次使用时先运行`check`命令检查环境兼容性
2. **命令探索：** 使用TUI界面探索所有可用命令和选项
3. **快速操作：** 对于熟悉命令的用户，建议使用传统CLI模式以提高效率
4. **主题选择：** 根据个人偏好和终端环境选择合适的主题
5. **错误处理：** 遇到错误时，查看详细日志（使用`--verbose`选项）

## 开发者信息

### Trogon集成

TUI功能基于Trogon库实现，该库为Click命令自动生成TUI界面。

**技术细节：**
- TUI管理器位于`src/ui/tui_manager.py`
- 通过`setup_tui()`函数启用TUI功能
- TUI命令自动添加到Click命令组中

### 扩展TUI功能

如需扩展TUI功能，可以：

1. 在`src/ui/tui_manager.py`中修改TUI管理器
2. 在`src/main.py`中添加新的Click命令
3. 为新命令编写单元测试和集成测试

### 测试

TUI功能的测试包括：
- 单元测试：`tests/unit/ui/test_tui_manager.py`
- 集成测试：`tests/integration/test_tui_integration.py`

运行测试：
```bash
# 运行TUI相关测试
uv run pytest tests/unit/ui/test_tui_manager.py
uv run pytest tests/integration/test_tui_integration.py

# 运行所有测试
uv run pytest
```

## 版本历史

### 0.4.0.dev0
- 引入基于Trogon的TUI界面
- 支持深色和浅色主题
- 支持鼠标操作
- 保持与原有CLI模式的完全完全兼容性

## 反馈与支持

如有问题或建议，请通过以下方式反馈：
- 提交Issue到项目仓库
- 联系项目维护者

## 许可证

本项目采用MIT许可证。
