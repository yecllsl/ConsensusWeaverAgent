---
alwaysApply: false
description: 质量规则：测试覆盖、代码规范、文档完整
---
# 质量规则

## 测试覆盖
- core覆盖率必须≥80%
- agents覆盖率必须≥70%
- cli覆盖率必须≥60%
- 禁止交付无单元测试的核心代码
- 禁止Mock内部业务逻辑（保持测试真实性）
- 必须Mock外部API调用（飞书、LLM）

## 开发方法论
- 禁止先写实现后补测试，必须TDD顺序（RED→GREEN→REFACTOR）
- 禁止无失败测试就写生产代码
- 禁止未经验证就声称完成，必须运行验证命令拿证据
- 禁止跳过根因分析直接修复Bug，必须先systematic-debugging
- 禁止需求不明确时直接编码，必须先brainstorming澄清

## 代码规范
- 禁止裸Exception，必须使用自定义异常
- 禁止# type: ignore，必须写正确类型注解
- 禁止Dict[str, Any]，使用TypedDict或dataclass
- 禁止print()调试，使用logging
- 禁止LazyFrame过早collect()
- 禁止直接实例化核心组件，必须get_context()
- 禁止可变默认参数def f(x=[])
- 禁止函数超50行、嵌套超4层

## 文档完整
- 公共API必须有文档字符串
- 新增功能必须更新CHANGELOG
- 架构变更必须更新架构设计说明书
- 版本发布必须同步更新AGENTS.md
