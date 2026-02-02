#!/usr/bin/env python3
"""
外部工具调用测试脚本
用于验证iflow、codebuddy和qwen的调用是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

    # 测试工具列表
    tools_to_test = ["iflow", "codebuddy", "qwen"]

    for i, tool_name in enumerate(tools_to_test, 1):
        print(f"\n{i}. 测试{tool_name}工具:")
        try:
            result = await tool_manager.run_tool(tool_name, test_question)
            print(f"   结果: {'成功' if result.success else '失败'}")
            print(f"   执行时间: {result.execution_time:.2f}秒")
            if result.success:
                print(f"   回答: {result.answer[:100]}...")
            else:
                print(f"   错误: {result.error_message}")
        except Exception as e:
            print("   结果: 异常")
            print(f"   错误: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_parallel_tool_call():
    """测试并行工具调用"""
    print("\n=== 测试并行工具调用 ===")

    # 初始化配置和工具管理器
    config_manager = ConfigManager()
    tool_manager = ToolManager(config_manager)

    # 测试问题
    test_question = "推荐三个开发AI Agent的开发框架，并比较他们的优缺点和擅长领域"

    # 并行调用所有启用的工具
    print("并行调用所有启用的工具...")
    try:
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
    except Exception as e:
        print(f"并行调用失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("外部工具调用测试")
    print("=" * 50)

    try:
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
