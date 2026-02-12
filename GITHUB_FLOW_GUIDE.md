# GitHub Flow工作流程指南

## 概述

本项目使用改进的GitHub Flow工作流程，旨在简化分支管理，支持快速迭代和持续部署。本指南详细说明工作流程的各个方面，供团队成员参考执行。

## 核心原则

1. **简单性**：只使用main分支和功能分支
2. **快速迭代**：支持频繁发布和持续部署
3. **质量保证**：所有代码变更必须通过Pull Request和CI检查
4. **自动化**：自动化版本管理和部署流程
5. **透明度**：清晰的分支命名和提交规范

## 分支策略

### 1. 分支结构

```
main (生产环境) ── 始终保持可部署状态
  ├── feature/xxx (功能分支) ── 开发新功能
  ├── bugfix/xxx (修复分支) ── 修复非紧急bug
  └── hotfix/xxx (紧急修复分支) ── 生产环境紧急修复
```

### 2. 分支说明

#### main分支

- **用途**：生产环境分支，始终保持可部署状态
- **保护规则**：
  - 禁止直接推送
  - 必须通过Pull Request合并
  - CI检查必须通过
  - 至少需要1人审查（团队协作时）
- **版本号**：使用正式版本号（如v1.0.0）

#### 功能分支

- **命名格式**：`feature/<功能描述>`
- **来源**：从main分支创建
- **生命周期**：短生命周期，开发完成后立即合并
- **合并方式**：Pull Request合并
- **版本号**：使用开发版本号（如v1.1.0.dev0）

#### 修复分支

- **命名格式**：`bugfix/<问题描述>`
- **来源**：从main分支创建
- **生命周期**：短生命周期，修复完成后立即合并
- **合并方式**：Pull Request合并
- **版本号**：使用开发版本号（如v1.1.0.dev0）

#### 紧急修复分支

- **命名格式**：`hotfix/<问题描述>`
- **来源**：从main分支创建
- **生命周期**：极短生命周期，快速修复和部署
- **合并方式**：Pull Request快速合并
- **版本号**：使用正式版本号（如v1.0.1）

## 工作流程

### 1. 功能开发流程

#### 步骤1：准备工作

1. **更新main分支**：
   ```bash
   git checkout main
   git pull origin main
   ```

2. **创建功能分支**：
   ```bash
   git checkout -b feature/add-batch-query
   ```

#### 步骤2：开发功能

1. **编写代码**：实现新功能
2. **添加测试**：确保测试覆盖
3. **运行测试**：验证功能
   ```bash
   python Scripts/cicd.py --mode ci --skip-nltk
   ```

4. **提交代码**：
   ```bash
   git add .
   git commit -m "feat(batch): add batch query support"
   git push origin feature/add-batch-query
   ```

#### 步骤3：创建Pull Request

1. **在GitHub上创建PR**：
   - 选择main作为目标分支
   - 填写PR标题和描述
   - 选择相关标签
   - 关联相关Issue

2. **PR描述模板**：使用`.github/pull_request_template.md`中的模板

3. **等待CI检查**：确保所有检查通过

#### 步骤4：代码审查

1. **审查者职责**：
   - 检查代码质量和可维护性
   - 验证功能正确性
   - 确保测试覆盖充分
   - 检查文档更新

2. **提交者职责**：
   - 及时回应审查意见
   - 进行必要的修改
   - 重新运行测试

#### 步骤5：合并到main分支

1. **审查通过后合并**：
   - 使用Squash and merge方式合并
   - 添加合并提交信息

2. **删除功能分支**：
   ```bash
   git branch -d feature/add-batch-query
   git push origin --delete feature/add-batch-query
   ```

### 2. Bug修复流程

#### 步骤1：准备工作

1. **更新main分支**：
   ```bash
   git checkout main
   git pull origin main
   ```

2. **创建修复分支**：
   ```bash
   git checkout -b bugfix/fix-encoding-error
   ```

#### 步骤2：实施修复

1. **定位问题**：分析bug根源
2. **编写修复**：实现最小化修复
3. **添加测试**：确保修复有效且无回归
4. **提交代码**：
   ```bash
   git add .
   git commit -m "fix(encoding): resolve encoding error in Windows"
   git push origin bugfix/fix-encoding-error
   ```

#### 步骤3：创建Pull Request

1. **在GitHub上创建PR**：选择main作为目标分支
2. **填写PR描述**：使用模板，说明问题和修复方案
3. **等待CI检查**：确保所有检查通过

#### 步骤4：代码审查与合并

1. **代码审查**：重点检查修复正确性和无回归
2. **合并到main**：审查通过后合并
3. **删除分支**：合并后删除修复分支

### 3. 紧急修复流程

#### 步骤1：准备工作

1. **更新main分支**：
   ```bash
   git checkout main
   git pull origin main
   ```

2. **创建hotfix分支**：
   ```bash
   git checkout -b hotfix/critical-security-fix
   ```

#### 步骤2：快速修复

1. **分析问题**：快速定位问题根源
2. **实施修复**：编写最小化的修复代码
3. **验证修复**：本地测试确保修复有效
4. **提交代码**：
   ```bash
   git add .
   git commit -m "fix(security): patch critical security vulnerability"
   git push origin hotfix/critical-security-fix
   ```

#### 步骤3：紧急审查与合并

1. **创建PR**：标记为"紧急"，请求快速审查
2. **快速审查**：团队成员优先审查
3. **合并到main**：24小时内完成合并

#### 步骤4：版本更新与发布

1. **更新版本号**：增加修订号
   ```bash
   # 更新pyproject.toml中的版本号
   # 从1.0.0更新为1.0.1
   git add pyproject.toml
   git commit -m "chore: bump version to 1.0.1"
   ```

2. **创建标签**：
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   ```

3. **推送与发布**：
   ```bash
   git push origin main v1.0.1
   ```

4. **监控部署**：确保修复部署成功

#### 步骤5：清理

1. **删除hotfix分支**：
   ```bash
   git branch -d hotfix/critical-security-fix
   git push origin --delete hotfix/critical-security-fix
   ```

2. **记录修复**：更新CHANGELOG和文档

### 4. 版本发布流程

#### 步骤1：准备发布

1. **更新main分支**：
   ```bash
   git checkout main
   git pull origin main
   ```

2. **更新版本号**：移除`.devN`后缀
   ```bash
   # 更新pyproject.toml中的版本号
   # 从1.1.0.dev2更新为1.1.0
   git add pyproject.toml
   git commit -m "chore: bump version to 1.1.0"
   ```

3. **更新CHANGELOG**：
   - 添加版本发布说明
   - 记录新功能、改进和修复

#### 步骤2：创建标签

1. **创建带注释的标签**：
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   ```

#### 步骤3：发布

1. **推送main分支和标签**：
   ```bash
   git push origin main v1.1.0
   ```

2. **触发CI/CD**：
   - GitHub Actions自动运行
   - 构建和发布到PyPI
   - 创建GitHub Release

#### 步骤4：准备下一版本

1. **更新版本号**：增加次版本号并添加`.dev0`后缀
   ```bash
   # 更新pyproject.toml中的版本号
   # 从1.1.0更新为1.2.0.dev0
   git add pyproject.toml
   git commit -m "chore: prepare for 1.2.0 development"
   git push origin main
   ```

## 代码规范与质量保证

### 1. 代码规范

- **代码检查**：使用ruff进行代码规范检查
  ```bash
  uv run ruff check .
  ```

- **代码格式化**：使用ruff进行代码格式化
  ```bash
  uv run ruff format .
  ```

- **类型检查**：使用mypy进行类型检查
  ```bash
  uv run mypy src/
  ```

- **安全检查**：使用bandit进行安全检查
  ```bash
  uv run bandit -r src/
  ```

### 2. 测试

- **运行测试**：使用pytest运行测试
  ```bash
  uv run pytest tests/ -v
  ```

- **测试覆盖率**：使用pytest-cov生成覆盖率报告
  ```bash
  uv run pytest tests/ --cov=src --cov-report=html
  ```

- **覆盖率要求**：测试覆盖率不低于75%

### 3. 代码审查标准

- **安全性**：无安全漏洞
- **正确性**：功能按预期工作
- **性能**：无明显性能问题
- **可维护性**：代码清晰易懂
- **测试覆盖**：测试充分覆盖
- **文档**：必要的文档已更新

## CI/CD集成

### 1. 自动化流程

- **Pull Request检查**：
  - 代码规范检查
  - 代码格式验证
  - 类型检查
  - 安全检查
  - 单元测试
  - 测试覆盖率检查

- **合并到main检查**：
  - 所有Pull Request检查
  - 构建验证

- **标签触发发布**：
  - 构建和发布到PyPI
  - 创建GitHub Release
  - 部署到生产环境（如配置）

### 2. CI/CD配置

配置文件：`.github/workflows/ci-cd.yml`

**主要作业**：
- `quality-check`：代码质量检查
- `test`：多平台测试
- `build-verify`：构建验证
- `release`：版本发布（标签触发）

## 版本管理

### 1. 版本号格式

- **正式版本**：`X.Y.Z`（如v1.0.0）
- **开发版本**：`X.Y.Z.devN`（如v1.1.0.dev0）
- **发布候选**：`X.Y.Z-rcN`（如v1.1.0-rc1）
- **补丁版本**：`X.Y.Z.P`（如v1.0.0.1）

### 2. 版本号变更规则

- **X**（主版本号）：不兼容的API变更
- **Y**（次版本号）：向下兼容的功能性新增
- **Z**（修订号）：向下兼容的问题修正
- **P**（补丁号）：紧急修复

### 3. CHANGELOG管理

- **格式**：遵循[Keep a Changelog](https://keepachangelog.com/)规范
- **内容**：
  - 版本号和发布日期
  - 新功能
  - 改进
  - 修复
  - 移除
  - 安全

## 最佳实践

### 1. 分支管理

- **保持分支轻量**：每个分支只包含一个功能或修复
- **频繁合并**：功能完成后立即合并，避免分支老化
- **清理分支**：合并后及时删除分支
- **命名规范**：使用清晰的分支命名

### 2. 提交管理

- **频繁提交**：小步快跑，频繁提交
- **清晰消息**：使用Conventional Commits规范
- **提交粒度**：每个提交是一个完整的逻辑单元
- **避免大提交**：拆分为多个小提交

### 3. 代码审查

- **及时审查**：24-48小时内完成审查
- **建设性反馈**：提供具体的改进建议
- **关注重点**：安全性、正确性、性能
- **尊重时间**：保持PR小而专注

### 4. 测试

- **测试先行**：编写功能前先写测试
- **覆盖边界**：测试边界情况和异常处理
- **集成测试**：测试关键路径的集成
- **性能测试**：测试重要功能的性能

### 5. 文档

- **更新及时**：代码变更后立即更新文档
- **清晰准确**：文档应清晰易懂
- **示例充分**：提供足够的示例代码
- **版本同步**：文档版本与代码版本保持一致

## 常见问题与解决方案

### 1. 合并冲突

**解决方案**：
```bash
# 拉取最新代码
git checkout main
git pull origin main

# 切换到功能分支
git checkout feature/add-batch-query

# 合并main分支
git merge main

# 解决冲突
# ...

# 提交解决后的代码
git add .
git commit -m "resolve merge conflicts"

git push origin feature/add-batch-query
```

### 2. CI检查失败

**解决方案**：
- 查看CI日志，定位失败原因
- 修复代码规范问题
- 修复类型检查错误
- 修复测试失败
- 重新运行CI检查

### 3. 测试覆盖率不足

**解决方案**：
- 添加缺失的测试
- 优先测试关键路径
- 测试边界情况
- 使用测试生成工具

### 4. 版本号冲突

**解决方案**：
- 建立版本号管理流程
- 使用自动化工具管理版本号
- 定期同步版本号

### 5. 紧急修复流程执行缓慢

**解决方案**：
- 提前组建紧急响应团队
- 建立明确的紧急修复流程
- 定期演练紧急修复流程
- 保持沟通渠道畅通

## 工具与资源

### 1. 开发工具

- **代码编辑器**：VS Code, PyCharm
- **版本控制**：Git, GitHub Desktop
- **CI/CD**：GitHub Actions
- **代码质量**：ruff, mypy, bandit
- **测试**：pytest, pytest-cov
- **依赖管理**：uv

### 2. 文档资源

- **分支命名规范**：BRANCHING_GUIDELINES.md
- **代码审查标准**：CODE_REVIEW_STANDARDS.md
- **版本号管理策略**：VERSIONING_STRATEGY.md
- **紧急修复流程**：EMERGENCY_FIX_PROCEDURE.md
- **CI/CD配置**：.github/workflows/ci-cd.yml
- **Pull Request模板**：.github/pull_request_template.md

### 3. 命令参考

**常用Git命令**：

```bash
# 查看分支
git branch -a

# 切换分支
git checkout main

# 拉取代码
git pull origin main

# 创建分支
git checkout -b feature/new-feature

# 提交代码
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature

# 合并分支
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature
git push origin --delete feature/new-feature

# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

**常用CI/CD命令**：

```bash
# 运行完整CI流程
python Scripts/cicd.py --mode ci

# 跳过NLTK数据下载
python Scripts/cicd.py --mode ci --skip-nltk

# 运行CD流程
python Scripts/cicd.py --mode cd

# 运行完整流程
python Scripts/cicd.py --mode all
```

## 团队协作

### 1. 沟通渠道

- **日常沟通**：团队聊天工具（如Slack, 钉钉）
- **代码审查**：GitHub Pull Request评论
- **会议**：定期站会、代码审查会议
- **文档**：项目Wiki、README文件

### 2. 角色与职责

- **项目负责人**：协调项目进展，决策重大事项
- **开发者**：实现功能，修复bug，参与代码审查
- **测试人员**：编写测试，验证功能，确保质量
- **运维人员**：部署代码，监控系统，处理运维问题

### 3. 工作流程改进

- **定期回顾**：每月回顾工作流程，识别改进点
- **流程优化**：根据实际情况调整工作流程
- **培训学习**：定期组织技术培训，提高团队技能
- **工具升级**：及时升级开发工具和依赖

## 总结

改进的GitHub Flow工作流程为ConsensusWeaverAgent项目提供了：

1. **简单清晰**的分支结构，易于理解和使用
2. **快速迭代**的开发流程，支持频繁发布
3. **质量保证**的自动化检查，确保代码质量
4. **安全可靠**的部署流程，减少生产风险
5. **高效协作**的团队流程，提高开发效率

通过遵循本指南，团队可以：
- 更高效地开发和发布新功能
- 更快速地响应和修复问题
- 更可靠地保证代码质量
- 更顺畅地协作和沟通

本工作流程将随着项目的发展和团队的成熟不断优化和改进。