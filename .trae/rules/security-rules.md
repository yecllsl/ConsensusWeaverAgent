---
alwaysApply: false
description: 安全规则：输入验证、敏感数据保护、访问控制
---
# 安全规则

## 输入验证
- 禁止信任未验证的外部数据（FIT文件、配置文件、CLI参数）
- 禁止未校验的文件路径，必须Path.resolve()规范化，拒绝..
- 禁止解析超限文件，FIT文件必须校验大小上限
- 禁止未捕获的解析异常，fitparse必须try-except包裹
- 禁止使用eval()/pickle反序列化不可信数据

## 敏感数据
- 禁止硬编码API密钥、Token、密码
- 禁止将敏感信息提交到Git
- 禁止config.example.json包含真实密钥
- 禁止将用户跑步数据(*.parquet/*.fit)提交到Git
- 禁止在日志中记录敏感数据
- 安全场景禁止使用MD5/SHA1弱加密

## 访问控制
- 禁止操作项目目录之外的文件
- 禁止执行不可逆的系统修改命令
- 禁止越权访问其他Agent职责范围
- .gitignore必须排除*.parquet、*.fit、config.json
- 发现安全问题必须立即停止，修复后再继续
