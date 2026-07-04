---
name: ConsensusWeaver
description: 多 AI 平台答案聚合工具，通过 MCP Server 并行向豆包、智谱清言、DeepSeek、千问、元宝提问，收集原始答案后由 TRAE 整合合成，输出去重互补的综合答案。
---

# ConsensusWeaver

## 描述

ConsensusWeaver 是一个多 AI 平台答案聚合工具。它通过 MCP Server 并行向多个中文 AI WebApp（豆包、智谱清言、DeepSeek、千问、元宝）提问，收集原始答案后由 TRAE 进行整合与合成，最终为用户输出一份去重、互补、结构清晰的综合答案。

## 调用方式

当用户在 TRAEwork 中提出需要多角度参考、对比或综合的问题时，自动调用本 Skill。

典型触发场景：

- 用户问 "如何学习 Python？"
- 用户问 "比较一下 Vue 和 React"
- 用户问 "给我几个不同的方案"
- 用户明确说 "用 ConsensusWeaver 问一下"

## 工作流

### 1. 接收用户问题

直接提取用户当前消息中的问题内容，不需要二次确认。

### 2. 调用 ConsensusWeaver MCP 的 `ask_ai` 工具

使用以下参数调用：

```json
{
  "question": "<用户原始问题>",
  "platforms": ["deepseek", "yuanbao"],
  "timeout": 120,
  "min_success": 2
}
```

默认优先使用当前最稳定的两个平台：`deepseek`、`yuanbao`。

如果用户明确要求更多平台，可扩展为 `["doubao", "deepseek", "chatglm", "qianwen", "yuanbao"]`，并将 `min_success` 保持为 3。

### 3. 读取 `ask_ai` 返回结果

解析返回的 JSON，重点关注：

- `success`：整体是否成功
- `success_count` / `total_count`：成功平台数量
- `results`：每个平台的原始回答
  - `platform_name`：平台名称
  - `status`：`success` 或 `failed`
  - `answer`：平台返回的原始文本
  - `error`：失败原因

### 4. 合成最终答案

基于所有 `status` 为 `success` 的回答，生成综合答案。合成规则：

1. 先简要复述用户问题
2. 综合各平台观点，去除重复内容
3. 保留互补信息，分点列出核心建议（最多 5 点）
4. 若某平台回答为空、错误或与主题无关，直接忽略
5. 在末尾用一句话总结各平台的主要贡献

### 5. 输出格式

```markdown
## 综合回答

<最终合成内容>

---

## 参考来源

- DeepSeek：<一句话总结其贡献>
- 元宝：<一句话总结其贡献>
```

## 异常处理

- 如果 `ask_ai` 返回 `success: false`，向用户说明当前平台可用性不足，并展示失败的详细原因。
- 如果只有一个平台成功，直接输出该平台的答案，并提示用户当前聚合结果有限。
- 如果所有平台均失败，建议用户检查 MCP Server 状态或稍后再试。

## 注意事项

- 不要修改用户的原始问题。
- 不要在调用 `ask_ai` 前询问用户是否确认。
- 合成时应优先保证信息的准确性和可读性，而不是简单拼接。
