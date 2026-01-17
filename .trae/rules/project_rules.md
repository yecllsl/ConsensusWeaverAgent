 **核心规则（强制执行）：**

1. **代码格式化**
   - 使用 ruff 统一处理代码格式化和 lint 检查
   - 行宽 88 字符，标记：# @tool=ruff

2. **类型安全**
   - 所有函数/方法必须包含完整类型注解
   - 复杂结构使用 `TypedDict` 或 `@dataclass`
   - 标记：`# @type_check=mypy_strict`

3. **测试要求**
   - 使用 **pytest** 编写单元测试
   - 测试文件置于 `tests/` 目录
   - 每个模块对应一个测试文件，文件名与模块名相同（如 `test_schema.py` 测试 `schema.py`）
   - 覆盖正常路径、错误路径和边界情况
   - 使用 `pytest-mock` 隔离外部依赖
   - 标记：`// @test_framework=pytest`

4. **依赖管理**
   - 使用 **uv** 工具管理依赖，禁止 `pip install`
   - 通过 `pyproject.toml` 文件管理依赖
   - 添加依赖：`uv add <package>` 或 `uv add --group <组名> <package>`
   - 变更后执行 `uv sync` 同步环境

5. **安全规范**
   - 禁止 SQL 字符串拼接（使用参数化查询）
   - 禁止 `subprocess` 使用 `shell=True`
   - 避免不安全的反序列化
   - 标记：`// @security_scan=bandit`

6. **项目结构**
   - 模块置于 `src/` 目录
   - 项目内导入使用显式相对导入（如 `from ..schema import User`）

7. **文档要求**
   - 公共模块/类/函数必须包含 **Google 风格** docstring
   - 注释解释"为什么"，而非"做什么"