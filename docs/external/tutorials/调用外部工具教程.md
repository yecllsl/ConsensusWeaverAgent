**先给你一个结论版思路：**
- 这三个本质上都是「命令行程序」，Python 要控制它们，核心就是：
  - 用标准库 subprocess 把命令跑起来；
  - 把你要传的「自然语言问题」当成命令行参数传进去；
  - 把 stdout/stderr 捕获回来；
  - 尽量用它们的“非交互 / headless / 打印模式”，让它们跑完就退出，而不是卡在交互式 REPL 里。
下面我按三个工具分别讲，并给出可以直接抄用的 Python 示例。
---
## 一、总体思路：subprocess + 非交互模式
Python 控制外部 CLI 最推荐的写法是 subprocess.run（Python 官方推荐用法）。
一个最小模板大概长这样：
```python
import subprocess
import shlex
def run_cli(cmd: list[str], input_text: str | None = None) -> tuple[int, str, str]:
    """
    通用调用 CLI 的辅助函数：
    - cmd: 命令 + 参数列表，例如 ["iflow", "-y", "-p", "帮我写个快速排序"]
    - input_text: 如果需要把内容通过 stdin 喂进去，就传这个字符串；否则传 None
    - 返回: (returncode, stdout_text, stderr_text)
    """
    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,  # 自己手动判断 returncode
    )
    return result.returncode, result.stdout, result.stderr
```
后面三个工具我们都会用这个模式来封装。
---
## 二、控制 iFlow CLI
### 1. 典型命令形式（终端里怎么用）
根据 iFlow CLI 的 GitHub 仓库和 issue，可以直接在命令行这样用：
- 直接交互（你会进入 TUI）：
  - iflow
- 非交互/headless 模式（跑完就退出）：
  - iflow -y -p "帮我写一个 Python 快速排序"
  - `-y`：自动确认 / 不需要交互式确认；
  - `-p`：相当于“print/打印模式”，执行一次就退出，而不是进入交互式 REPL。
Issue 里的示例也印证了这个用法，例如：  
npx -y @iflow-ai/iflow-cli@latest -y -p "My name is XYZ."
### 2. Python 调用示例
假设你已经全局安装好了 iflow（命令行能直接敲 iflow）：
```python
import subprocess
def call_iflow(prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
    """
    调用 iFlow CLI 的非交互模式
    - prompt: 你要用自然语言描述的任务，例如 "帮我写一个 Python 快速排序"
    - cwd:    可选，指定在哪个目录下执行（默认当前目录）
    - 返回:   (returncode, stdout, stderr)
    """
    cmd = [
        "iflow",
        "-y",        # 自动确认，减少交互
        "-p", prompt # 打印模式：执行一次就退出，适合脚本调用
    ]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
# 使用示例
code, out, err = call_iflow("帮我用 Python 写一个快速排序，并写出简单单测")
if code != 0:
    print("iFlow 出错:", err)
else:
    print("iFlow 返回:", out)
```
如果你是从管道传内容给 iFlow（比如把某个文件喂进去），可以这样：
```python
def call_iflow_with_stdin(prompt: str, stdin_content: str, cwd: str | None = None):
    cmd = ["iflow", "-y", "-p", prompt]
    result = subprocess.run(
        cmd,
        input=stdin_content,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
code, out, err = call_iflow_with_stdin(
    "帮我读这段代码并找出潜在 bug",
    "def add(a, b):\n    return a + b\n",
)
print("iFlow 输出:", out)
```
---
## 三、控制 CodeBuddy（腾讯云代码助手 CLI）
### 1. 典型命令形式
根据腾讯官方 CLI 参考文档，CodeBuddy CLI 的可执行命令是 codebuddy，并且有专门的「打印模式」参数 -p/--print，用于非交互式调用，非常适合在脚本中使用。
常见用法：
- 交互式 REPL：
  - codebuddy
- 非交互模式（打印响应后退出）：
  - codebuddy -p "解释这个项目"
  - codebuddy -p "分析日志"
- 带管道：
  - cat logs.txt | codebuddy -p "分析日志"
文档还建议：  
在做自动化或脚本集成时，可以配合 --output-format json 来拿到结构化输出，方便 Python 解析。
### 2. Python 调用示例（非交互 + JSON 输出）
```python
import subprocess
import json
def call_codebuddy(prompt: str,
                   cwd: str | None = None,
                   output_format: str = "text") -> tuple[int, dict | str, str]:
    """
    调用 CodeBuddy CLI 的非交互打印模式
    - prompt: 自然语言任务描述
    - cwd:    工作目录（可选）
    - output_format: "text" 或 "json"
    - 返回:   (returncode, parsed_result, raw_stderr)
    """
    cmd = [
        "codebuddy",
        "-p", prompt,          # 打印模式：执行完就退出
        "--output-format", output_format,
        # 如果涉及写文件、跑命令等，可能还需要：
        # "-y",  # 对应 --dangerously-skip-permissions（视你安全策略而定）
    ]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = result.stdout
    if output_format == "json" and result.returncode == 0:
        try:
            parsed = json.loads(stdout)
            return result.returncode, parsed, result.stderr
        except json.JSONDecodeError:
            # JSON 解析失败，fallback 成字符串
            return result.returncode, stdout, result.stderr
    else:
        return result.returncode, stdout, result.stderr
# 使用示例：文本模式
code, out, err = call_codebuddy("解释当前项目结构，输出中文说明", cwd="./my-project")
if code != 0:
    print("CodeBuddy 出错:", err)
else:
    print("CodeBuddy 返回:", out)
# 使用示例：JSON 模式（脚本里解析）
code, out, err = call_codebuddy(
    "把当前项目的目录结构输出成 JSON",
    output_format="json",
)
if code == 0 and isinstance(out, dict):
    # 假设返回里有个 "result" 字段包含你真正关心的内容
    print(out.get("result"))
else:
    print("原始输出:", out)
```
如果你需要把文件内容通过 stdin 传给 CodeBuddy：
```python
def call_codebuddy_with_stdin(prompt: str, stdin_content: str, cwd: str | None = None):
    cmd = ["codebuddy", "-p", prompt]
    result = subprocess.run(
        cmd,
        input=stdin_content,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
code, out, err = call_codebuddy_with_stdin(
    "从这段代码中抽取函数签名列表，并用 JSON 返回",
    open("main.py").read(),
)
print(out)
```
---
## 四、控制 Qwen（Qwen Code CLI）
### 1. 典型命令形式
Qwen Code CLI 是阿里开源的终端 AI 编程助手，也是一个“住在终端里的 agent”。它的命令行名通常是 qwen-code（或类似），文档里明确有“Headless Mode（无头模式）”用于脚本调用和自动化。
一般模式：
- 交互式：
  - qwen-code
- Headless / 非交互模式（命令可能类似）：
  - qwen-code --non-interactive "帮我重构这段代码"
  - 或者 qwen-code -h 查看当前版本支持的 headless 相关参数（不同版本参数名可能有细微差别）
Qwen 文档强调：它的 Headless Mode 就是为了在 CI/CD、脚本、IDE 插件里进行自动化操作设计的，所以非常适合从 Python 控制它。
（注意：实际命令参数请在你终端里用 qwen-code -h/--help 看一下，下面示例假设参数是 --non-interactive）
### 2. Python 调用示例
```python
import subprocess
def call_qwen_code(prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
    """
    调用 Qwen Code CLI 的 headless / 非交互模式
    - prompt: 自然语言任务描述
    - cwd:    工作目录（可选）
    - 返回:   (returncode, stdout, stderr)
    """
    # 注意：参数名请以本地 qwen-code -h 为准，这里以常见形式示例
    cmd = [
        "qwen-code",
        "--non-interactive",  # 非交互/headless 模式（实际参数可能略有差异）
        prompt,
    ]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
# 使用示例
code, out, err = call_qwen_code("把这个目录下的所有 .py 文件列出来，并按大小排序", cwd="./my-project")
if code != 0:
    print("Qwen Code 出错:", err)
else:
    print("Qwen Code 返回:", out)
```
如果 Qwen Code 也支持 JSON 输出（类似 CodeBuddy），你可以同样加参数 + json.loads 解析：
```python
import json
def call_qwen_code_json(prompt: str, cwd: str | None = None) -> tuple[int, dict | None, str]:
    cmd = [
        "qwen-code",
        "--non-interactive",
        "--output-format", "json",  # 假设它有类似参数，以实际 help 为准
        prompt,
    ]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        parsed = json.loads(result.stdout)
        return result.returncode, parsed, result.stderr
    except Exception:
        return result.returncode, None, result.stderr
```
---
## 五、实战建议：把三个 CLI 抽象成统一接口
你可以把 iflow / codebuddy / qwen 抽象成一个统一类，然后在代码里按需切换：
```python
import subprocess
from abc import ABC, abstractmethod
class CliAgent(ABC):
    name: str
    @abstractmethod
    def run(self, prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
        ...
class IFlowAgent(CliAgent):
    name = "iflow"
    def run(self, prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
        cmd = ["iflow", "-y", "-p", prompt]
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
class CodeBuddyAgent(CliAgent):
    name = "codebuddy"
    def run(self, prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
        cmd = ["codebuddy", "-p", prompt]
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
class QwenAgent(CliAgent):
    name = "qwen"
    def run(self, prompt: str, cwd: str | None = None) -> tuple[int, str, str]:
        cmd = ["qwen-code", "--non-interactive", prompt]  # 参数以实际 help 为准
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
# 使用
agents: list[CliAgent] = [IFlowAgent(), CodeBuddyAgent(), QwenAgent()]
task = "用 Python 实现一个简单的 HTTP 服务器"
for agent in agents:
    code, out, err = agent.run(task, cwd="./my-project")
    print(f"[{agent.name}] returncode={code}")
    print("输出:", out)
    if err:
        print("错误:", err)
    print("-" * 40)
```
---
## 六、几个重要细节和坑
1. 优先用非交互/headless 模式
   - iFlow：用 `-y -p` 组合；
   - CodeBuddy：用 `-p` 或 `-p --output-format json`；
   - Qwen：用 `--non-interactive` 或文档推荐的 headless 参数。
   这样可以避免 Python 调用时卡在交互式输入里。
2. 环境和路径问题
   - 确保这三个命令在你的 PATH 里，Python 才能直接用 `["iflow", ...]`。
   - 如果是 Windows + WSL，注意你在哪一侧运行 Python（WSL 里 vs Windows 里）。
   - 可以在 Python 里先检测一下命令是否存在，例如：
     - subprocess.run(["iflow", "--help"], capture_output=True) 看看 returncode。
3. 权限/风险操作
   - CodeBuddy 文档明确写了：涉及文件读写、执行命令、网络请求时，非交互模式通常还需要加 `-y`（`--dangerously-skip-permissions`），否则操作会被阻止。
   - 如果你在 CI 脚本中调用，建议：
     - 把 repo 放在专门的沙箱目录；
     - 或者用它们自带的沙箱模式（比如 CodeBuddy 的 --sandbox 选项）。
4. 异常和超时控制
   - 可以给 subprocess.run 加 timeout，避免某个模型响应太慢把 Python 进程卡死：
     ```python
     subprocess.run(cmd, timeout=120, ...)
     ```
   - 注意 TimeoutExpired 异常要自己捕获处理。
5. 日志与调试
   - 临时调试时可以：
     - 把 stderr 打出来看；
     - 在命令中加 `--verbose` 等参数（如果工具支持）。
   - 真正上线时再关掉或定向到日志文件。

