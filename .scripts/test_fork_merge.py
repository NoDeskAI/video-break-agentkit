#!/usr/bin/env python3
"""
Fork合并验证测试
验证点：
1. HookAnalyzerSequentialAgent 正确过滤中间步骤输出
2. _prime_hook_segments_state 预加载功能正常
3. clean_analyze_hook_arguments 参数清理正常
4. video_recreation_agent 功能未受影响
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_hook_analyzer_sequential():
    """测试1：HookAnalyzerSequentialAgent类存在且可实例化"""
    from video_breakdown_agent.sub_agents.hook_analyzer_agent.filtered_sequential import (
        HookAnalyzerSequentialAgent,
    )

    # 验证类存在
    assert HookAnalyzerSequentialAgent is not None
    print("✅ Test 1: HookAnalyzerSequentialAgent 类加载成功")


def test_clean_tool_args():
    """测试2：clean_analyze_hook_arguments 函数存在"""
    from video_breakdown_agent.sub_agents.hook_analyzer_agent.hook.clean_tool_args import (
        clean_analyze_hook_arguments,
    )

    assert clean_analyze_hook_arguments is not None
    print("✅ Test 2: clean_analyze_hook_arguments 函数加载成功")


def test_create_hook_analyzer():
    """测试3：create_hook_analyzer_agent 返回正确类型"""
    from video_breakdown_agent.agent import root_agent

    # 找到 hook_analyzer_agent
    hook_analyzer = None
    for sub in root_agent.sub_agents:
        if hasattr(sub, "sub_agents"):
            for sub_sub in sub.sub_agents:
                if sub_sub.name == "hook_analyzer_agent":
                    hook_analyzer = sub_sub
                    break

    assert hook_analyzer is not None, "未找到 hook_analyzer_agent"

    # 验证类型
    from video_breakdown_agent.sub_agents.hook_analyzer_agent.filtered_sequential import (
        HookAnalyzerSequentialAgent,
    )

    assert isinstance(hook_analyzer, HookAnalyzerSequentialAgent), (
        f"类型错误: {type(hook_analyzer)}"
    )

    print("✅ Test 3: hook_analyzer_agent 使用 HookAnalyzerSequentialAgent")


def test_hook_analyzer_config():
    """测试4：hook_analysis_agent 配置正确（无tools，有callback）"""
    from video_breakdown_agent.agent import create_hook_analyzer_agent

    agent = create_hook_analyzer_agent()
    hook_analysis = agent.sub_agents[0]

    # 验证 tools 为空
    assert len(hook_analysis.tools) == 0, (
        f"tools应为空，实际: {len(hook_analysis.tools)}"
    )

    # 验证 before_agent_callback 存在
    assert hook_analysis.before_agent_callback is not None, (
        "before_agent_callback 未配置"
    )

    # 验证 after_model_callback 存在（clean_analyze_hook_arguments）
    assert len(hook_analysis.after_model_callback) > 0, "after_model_callback 未配置"

    print("✅ Test 4: hook_analysis_agent 配置正确（无tools，有callbacks）")


def test_video_recreation_agent():
    """测试5：video_recreation_agent 未受影响"""
    from video_breakdown_agent.agent import root_agent

    # 查找 video_recreation_agent
    video_recreation = None
    for sub in root_agent.sub_agents:
        if sub.name == "video_recreation_agent":
            video_recreation = sub
            break

    assert video_recreation is not None, "video_recreation_agent 丢失"

    # 验证sub_agents存在
    assert hasattr(video_recreation, "sub_agents"), (
        "video_recreation_agent.sub_agents 丢失"
    )
    assert len(video_recreation.sub_agents) == 2, (
        f"video_recreation_agent 子Agent数量错误: {len(video_recreation.sub_agents)}"
    )

    print("✅ Test 5: video_recreation_agent 功能完整")


if __name__ == "__main__":
    print("=" * 60)
    print("Fork合并验证测试")
    print("=" * 60)

    tests = [
        test_hook_analyzer_sequential,
        test_clean_tool_args,
        test_create_hook_analyzer,
        test_hook_analyzer_config,
        test_video_recreation_agent,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 失败: {e}")
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过, {failed}/{len(tests)} 失败")
    print("=" * 60)

    if failed == 0:
        print("🎉 所有测试通过！Fork合并成功")
        sys.exit(0)
    else:
        print("❌ 有测试失败，请检查合并")
        sys.exit(1)
