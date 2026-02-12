# 分支命名规范

## 分支结构

本项目使用改进的GitHub Flow工作流程，分支结构如下：

```
main (生产环境)
  ├── feature/xxx (功能分支)
  ├── bugfix/xxx (修复分支)
  └── hotfix/xxx (紧急修复分支)
```

## 分支命名规则

### 1. 功能分支 (feature/)

**命名格式**：`feature/<功能描述>`

**示例**：
- `feature/add-batch-query`
- `feature/improve-cache-performance`
- `feature/support-pdf-report`

**使用场景**：
- 开发新功能
- 添加新特性
- 实现新需求

**工作流程**：
1. 从main分支创建功能分支
2. 在功能分支上开发功能
3. 提交代码并创建Pull Request
4. 代码审查通过后合并到main分支
5. 删除功能分支

### 2. 修复分支 (bugfix/)

**命名格式**：`bugfix/<问题描述>`

**示例**：
- `bugfix/fix-memory-leak`
- `bugfix/fix-encoding-error`
- `bugfix/fix-type-checking-error`

**使用场景**：
- 修复非紧急bug
- 修复已知问题
- 改进错误处理

**工作流程**：
1. 从main分支创建修复分支
2. 在修复分支上修复问题
3. 提交代码并创建Pull Request
4. 代码审查通过后合并到main分支
5. 删除修复分支

### 3. 紧急修复分支 (hotfix/)

**命名格式**：`hotfix/<问题描述>`

**示例**：
- `hotfix/critical-security-fix`
- `hotfix/production-crash-fix`
- `hotfix/data-corruption-fix`

**使用场景**：
- 生产环境紧急问题
- 安全漏洞修复
- 数据损坏修复

**工作流程**：
1. 从main分支创建紧急修复分支
2. 在紧急修复分支上快速修复问题
3. 提交代码并创建Pull Request（快速审查）
4. 合并到main分支
5. 创建补丁标签（如v0.4.2.1）
6. 立即部署
7. 删除紧急修复分支

## Commit Message规范

使用Conventional Commits规范：

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关
- `perf`: 性能优化
- `ci`: CI/CD相关

### 示例

```
feat(batch): add batch query support

- Add batch query manager
- Support concurrent query execution
- Generate structured batch reports

Closes #123
```

```
fix(cache): resolve encoding error in Windows

- Add UTF-8 encoding to subprocess calls
- Handle UnicodeDecodeError gracefully
- Improve error messages

Fixes #456
```

## Pull Request规范

### 标题格式

```
<type>: <description>
```

### 描述模板

```markdown
## 变更说明

简要描述本次PR的变更内容

## 变更类型

- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 其他

## 测试

- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 检查清单

- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 没有引入新的警告

## 相关Issue

Closes #<issue_number>
```

## 工作流程图

### 功能开发流程

```mermaid
graph LR
    A[创建feature分支] --> B[开发功能]
    B --> C[提交代码]
    C --> D[创建Pull Request]
    D --> E[代码审查]
    E --> F[CI检查]
    F --> G[合并到main]
    G --> H[删除feature分支]
```

### 紧急修复流程

```mermaid
graph LR
    A[创建hotfix分支] --> B[修复问题]
    B --> C[提交代码]
    C --> D[创建Pull Request]
    D --> E[快速审查]
    E --> F[CI检查]
    F --> G[合并到main]
    G --> H[创建补丁标签]
    H --> I[紧急部署]
    I --> J[删除hotfix分支]
```