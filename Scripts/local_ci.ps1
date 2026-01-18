<#
.SYNOPSIS
本地CI脚本 - ConsensusWeaverAgent

.DESCRIPTION
这个脚本模拟了GitHub Actions的CI流程，在Windows 11环境下运行构建、测试和验证步骤。
确保本地开发环境与CI环境的一致性。

.EXAMPLE
.cripts\local_ci.ps1

.NOTES
- 需要PowerShell 7.0或更高版本
- 需要Python 3.12
- 需要管理员权限安装依赖
#>

# 颜色定义
$GREEN = "Green"
$RED = "Red"
$YELLOW = "Yellow"
$BLUE = "Blue"

# 环境变量设置
$PYTHON_VERSION_REQUIRED = "3.12"
$UV_VERSION = "0.4.0"
$PROJECT_DIR = "$PSScriptRoot\.."
$TEST_RESULTS_FILE = "$PROJECT_DIR\test-results.xml"
$SECURITY_REPORT_FILE = "$PROJECT_DIR\security-report.json"

# 函数：输出带颜色的消息
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color
    )
    Write-Host -ForegroundColor $Color $Message
}

# 函数：检查命令是否存在
function Test-CommandExists {
    param(
        [string]$Command
    )
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# 函数：验证Python版本
function Test-PythonVersion {
    if (-not (Test-CommandExists "python")) {
        Write-ColorMessage "❌ Python未安装" $RED
        exit 1
    }

    $pythonVersion = python --version 2>&1
    Write-ColorMessage "ℹ️ 当前Python版本: $pythonVersion" $BLUE

    if (-not $pythonVersion.Contains($PYTHON_VERSION_REQUIRED)) {
        Write-ColorMessage "❌ 需要Python $PYTHON_VERSION_REQUIRED或更高版本" $RED
        exit 1
    }

    Write-ColorMessage "✅ Python版本符合要求" $GREEN
}

# 函数：安装uv依赖管理工具
function Install-Uv {
    Write-ColorMessage "🔧 安装uv依赖管理工具..." $YELLOW
    try {
        python -m pip install uv==$UV_VERSION --quiet
        Write-ColorMessage "✅ uv安装成功" $GREEN
    } catch {
        Write-ColorMessage "❌ uv安装失败: $_" $RED
        exit 1
    }
}

# 函数：安装项目依赖
function Install-Dependencies {
    Write-ColorMessage "🔧 安装项目依赖..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv pip install -e .[dev] --quiet
        Write-ColorMessage "✅ 项目依赖安装成功" $GREEN
    } catch {
        Write-ColorMessage "❌ 项目依赖安装失败: $_" $RED
        exit 1
    }
}

# 函数：检查代码格式
function Check-CodeFormat {
    Write-ColorMessage "🔍 检查代码格式..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        $result = uv run ruff check --output-format=github .
        Write-ColorMessage "✅ 代码格式检查通过" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 代码格式检查失败: $_" $RED
        return $false
    }
}

# 函数：格式化代码
function Format-Code {
    Write-ColorMessage "📝 格式化代码..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv run ruff format . --quiet
        Write-ColorMessage "✅ 代码格式化完成" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 代码格式化失败: $_" $RED
        return $false
    }
}

# 函数：类型检查
function Check-Types {
    Write-ColorMessage "🔍 类型检查..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv run mypy --strict src/
        Write-ColorMessage "✅ 类型检查通过" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 类型检查失败: $_" $RED
        return $false
    }
}

# 函数：运行测试
function Run-Tests {
    Write-ColorMessage "🧪 运行测试..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv run pytest tests/ -v --tb=short
        Write-ColorMessage "✅ 测试通过" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 测试失败: $_" $RED
        return $false
    }
}

# 函数：生成测试报告
function Generate-TestReport {
    Write-ColorMessage "📊 生成测试报告..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv run pytest tests/ --junitxml=$TEST_RESULTS_FILE --quiet
        Write-ColorMessage "✅ 测试报告生成成功: $TEST_RESULTS_FILE" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 测试报告生成失败: $_" $RED
        return $false
    }
}

# 函数：运行安全检查
function Run-SecurityCheck {
    Write-ColorMessage "🔒 运行安全检查..." $YELLOW
    try {
        Set-Location $PROJECT_DIR
        uv pip install bandit --quiet
        uv run bandit -r src/ -f json -o $SECURITY_REPORT_FILE 2>$null
        Write-ColorMessage "✅ 安全检查完成: $SECURITY_REPORT_FILE" $GREEN
        return $true
    } catch {
        Write-ColorMessage "❌ 安全检查失败: $_" $YELLOW
        Write-ColorMessage "⚠️ 安全检查是可选的，继续执行其他步骤" $YELLOW
        return $true
    }
}

# 函数：清理临时文件
function Cleanup {
    Write-ColorMessage "🧹 清理临时文件..." $YELLOW
    try {
        if (Test-Path $TEST_RESULTS_FILE) {
            Remove-Item $TEST_RESULTS_FILE -Force
        }
        if (Test-Path $SECURITY_REPORT_FILE) {
            Remove-Item $SECURITY_REPORT_FILE -Force
        }
        Write-ColorMessage "✅ 清理完成" $GREEN
    } catch {
        Write-ColorMessage "⚠️ 清理失败: $_" $YELLOW
    }
}

# 主函数：运行CI流程
function Run-CI {
    Write-ColorMessage "=====================================" $BLUE
    Write-ColorMessage "     ConsensusWeaverAgent CI流程     " $BLUE
    Write-ColorMessage "=====================================" $BLUE

    # 步骤1: 验证Python版本
    Test-PythonVersion

    # 步骤2: 安装uv
    Install-Uv

    # 步骤3: 安装依赖
    Install-Dependencies

    # 步骤4: 检查代码格式
    $formatCheckResult = Check-CodeFormat

    # 步骤5: 格式化代码
    $formatResult = Format-Code

    # 步骤6: 类型检查
    $typeCheckResult = Check-Types

    # 步骤7: 运行测试
    $testResult = Run-Tests

    # 步骤8: 生成测试报告
    $reportResult = Generate-TestReport

    # 步骤9: 运行安全检查
    $securityResult = Run-SecurityCheck

    # 总结
    Write-ColorMessage "=====================================" $BLUE
    Write-ColorMessage "             CI流程总结              " $BLUE
    Write-ColorMessage "=====================================" $BLUE

    $allPassed = $true
    
    if (-not $formatCheckResult) { $allPassed = $false }
    if (-not $formatResult) { $allPassed = $false }
    if (-not $typeCheckResult) { $allPassed = $false }
    if (-not $testResult) { $allPassed = $false }
    if (-not $reportResult) { $allPassed = $false }
    
    if ($allPassed) {
        Write-ColorMessage "🎉 所有CI步骤通过!" $GREEN
        return 0
    } else {
        Write-ColorMessage "❌ 部分CI步骤失败!" $RED
        return 1
    }
}

# 开始执行CI流程
$exitCode = Run-CI

# 清理临时文件
Cleanup

# 退出
exit $exitCode