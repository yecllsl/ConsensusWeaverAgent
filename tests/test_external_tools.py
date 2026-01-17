#!/usr/bin/env python3
"""
外部工具调用测试脚本
用于验证iflow和codebuddy的调用是否正常工作
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.tools.tool_manager import ToolManager

async def test_single_tool_call():
    """测试单个工具调用"""
    print("=== 测试单个工具调用 ===")
    
    # 初始化配置和工具管理器
    config_manager = ConfigManager()
    tool_manager = ToolManager(config_manager)
    
    # 测试问题
    test_question = "推荐三个开发AI Agent的开发框架，并比较他们的优缺点和擅长领域"
    
    # 测试iflow工具
    print("\n1. 测试iflow工具:")
    result = await tool_manager.run_tool("iflow", test_question)
    print(f"   结果: {'成功' if result.success else '失败'}")
    print(f"   执行时间: {result.execution_time:.2f}秒")
    if result.success:
        print(f"   回答: {result.answer[:100]}...")
    else:
        print(f"   错误: {result.error_message}")
    
    # 测试codebuddy工具
    print("\n2. 测试codebuddy工具:")
    result = await tool_manager.run_tool("codebuddy", test_question)
    print(f"   结果: {'成功' if result.success else '失败'}")
    print(f"   执行时间: {result.execution_time:.2f}秒")
    if result.success:
        print(f"   回答: {result.answer[:100]}...")
    else:
        print(f"   错误: {result.error_message}")

async def test_parallel_tool_call():
    """测试并行工具调用"""
    print("\n=== 测试并行工具调用 ===")
    
    # 初始化配置和工具管理器
    config_manager = ConfigManager()
    tool_manager = ToolManager(config_manager)
    
    # 测试问题
    test_question = "推荐三个开发AI Agent的开发框架，并比较他们的优缺点和擅长领域"
    
    # 并行调用所有启用的工具
    print(f"并行调用所有启用的工具...")
    results = await tool_manager.run_multiple_tools(test_question)
    
    # 输出结果
    for result in results:
        print(f"\n工具 {result.tool_name}:")
        print(f"   结果: {'成功' if result.success else '失败'}")
        print(f"   执行时间: {result.execution_time:.2f}秒")
        if result.success:
            print(f"   回答: {result.answer[:100]}...")
        else:
            print(f"   错误: {result.error_message}")

async def test_tool_availability():
    """测试工具是否可用"""
    print("\n=== 测试工具可用性 ===")
    
    # 初始化配置和工具管理器
    config_manager = ConfigManager()
    tool_manager = ToolManager(config_manager)
    
    # 获取所有启用的工具
    enabled_tools = tool_manager.get_enabled_tools()
    print(f"启用的工具数量: {len(enabled_tools)}")
    
    for tool in enabled_tools:
        print(f"\n工具 {tool['name']}:")
        print(f"   命令: {tool['command']}")
        print(f"   参数: {tool['args']}")
        print(f"   需要互联网: {tool['needs_internet']}")
        
        # 检查工具是否可以正常执行
        try:
            result = subprocess.run(
                [tool['command'], "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"   可用性: ✅ 可用")
            else:
                print(f"   可用性: ❌ 不可用 (返回码: {result.returncode})")
        except Exception as e:
            print(f"   可用性: ❌ 不可用 (错误: {str(e)})")

async def main():
    """主测试函数"""
    print("外部工具调用测试")
    print("=" * 50)
    
    try:
        # 测试工具可用性
        await test_tool_availability()
        
        # 测试单个工具调用
        await test_single_tool_call()
        
        # 测试并行工具调用
        await test_parallel_tool_call()
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 50)
        print("测试完成")

if __name__ == "__main__":
    asyncio.run(main())
