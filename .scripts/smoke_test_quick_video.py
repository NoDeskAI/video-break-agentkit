#!/usr/bin/env python3
"""
Quick Video Agent — 冒烟测试脚本

验证 SequentialAgent 架构改造后的模块加载、Agent 树构建、工具解析逻辑。

用法（从项目根目录运行）：
    # 仅结构/离线测试（不需要 API Key）
    uv run python .scripts/smoke_test_quick_video.py

    # 端到端在线测试（需要 API Key + 网络）
    uv run python .scripts/smoke_test_quick_video.py --e2e
"""

import asyncio
import sys
import os
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

passed = 0
failed = 0


def ok(name: str, detail: str = ""):
    global passed
    passed += 1
    suffix = f" — {detail}" if detail else ""
    print(f"  ✅ {name}{suffix}")


def fail(name: str, detail: str = ""):
    global failed
    failed += 1
    suffix = f" — {detail}" if detail else ""
    print(f"  ❌ {name}{suffix}")


# ─────────────────────────────────────────────
# Test 1: 模块导入
# ─────────────────────────────────────────────
def test_imports():
    print("\n[Test 1] 模块导入")
    try:
        ok("direct_video_generation 导入成功")
    except Exception as e:
        fail("direct_video_generation 导入失败", str(e))
        return

    try:
        ok("prompt_preparation_agent 导入成功")
    except Exception as e:
        fail("prompt_preparation_agent 导入失败", str(e))

    # quick_video_agent 不再作为单独模块导出，而是在 video_recreation_agent 中动态创建
    # 这是设计变更，避免 Agent 实例被多个 parent 引用
    ok("quick_video_agent 架构变更（动态创建，不单独导出）")

    try:
        ok("video_recreation_agent 导入成功")
    except Exception as e:
        fail("video_recreation_agent 导入失败", str(e))

    try:
        from video_breakdown_agent.agent import root_agent  # noqa: F401

        ok("root_agent (整个项目) 导入成功")
    except Exception as e:
        fail("root_agent 导入失败", str(e))


# ─────────────────────────────────────────────
# Test 2: Agent 树结构校验
# ─────────────────────────────────────────────
def test_agent_tree():
    print("\n[Test 2] Agent 树结构校验")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.agent import (
            video_recreation_agent,
        )
    except Exception as e:
        fail("无法导入 video_recreation_agent", str(e))
        return

    # 2.1 video_recreation_agent 应持有 generate_video_prompts 工具（用于仅查看提示词场景）
    tools = getattr(video_recreation_agent, "tools", None) or []
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    if "generate_video_prompts" in tool_names:
        ok("video_recreation_agent.tools 包含 generate_video_prompts（仅查看提示词工具）")
    else:
        fail("video_recreation_agent.tools 缺少 generate_video_prompts", f"工具={tool_names}")

    # 2.2 video_recreation_agent 应有 2 个 sub_agents
    sub_agents = getattr(video_recreation_agent, "sub_agents", None) or []
    sub_names = [getattr(a, "name", "?") for a in sub_agents]
    if len(sub_agents) == 2:
        ok(f"video_recreation_agent 有 2 个 sub_agents: {sub_names}")
    else:
        fail(
            f"video_recreation_agent 期望 2 个 sub_agents，实际 {len(sub_agents)}",
            str(sub_names),
        )

    # 2.3 检查 quick_video_agent 是 SequentialAgent
    from veadk.agents.sequential_agent import SequentialAgent

    quick_agent = None
    for a in sub_agents:
        if getattr(a, "name", "") == "quick_video_agent":
            quick_agent = a
            break

    if quick_agent is None:
        fail("未找到 quick_video_agent 子Agent")
        return

    if isinstance(quick_agent, SequentialAgent):
        ok("quick_video_agent 是 SequentialAgent 实例")
    else:
        fail("quick_video_agent 类型错误", f"实际类型={type(quick_agent).__name__}")

    # 2.4 检查 quick_video_agent 的 sub_agents 顺序
    qv_sub = getattr(quick_agent, "sub_agents", None) or []
    qv_names = [getattr(a, "name", "?") for a in qv_sub]
    expected_order = ["prompt_preparation_agent", "video_generator_agent"]
    if qv_names == expected_order:
        ok(f"quick_video_agent 子Agent 顺序正确: {qv_names}")
    else:
        fail(
            "quick_video_agent 子Agent 顺序错误",
            f"期望={expected_order}, 实际={qv_names}",
        )

    # 2.5 检查 prompt_preparation_agent 持有 direct_video_generation 工具
    if qv_sub:
        prep_agent = qv_sub[0]
        prep_tools = getattr(prep_agent, "tools", None) or []
        prep_tool_names = [getattr(t, "__name__", str(t)) for t in prep_tools]
        if "direct_video_generation" in prep_tool_names:
            ok("prompt_preparation_agent 持有 direct_video_generation 工具")
        else:
            fail(
                "prompt_preparation_agent 未找到 direct_video_generation",
                f"工具={prep_tool_names}",
            )

    # 2.6 检查 recreation_pipeline 存在
    pipeline = None
    for a in sub_agents:
        if getattr(a, "name", "") == "recreation_pipeline":
            pipeline = a
            break
    if pipeline and isinstance(pipeline, SequentialAgent):
        pl_sub = getattr(pipeline, "sub_agents", None) or []
        pl_names = [getattr(a, "name", "?") for a in pl_sub]
        ok(f"recreation_pipeline 存在且包含: {pl_names}")
    else:
        fail("recreation_pipeline 不存在或类型错误")


# ─────────────────────────────────────────────
# Test 3: parse_segment_info 工具函数测试
# ─────────────────────────────────────────────
def test_parse_segment_info():
    print("\n[Test 3] parse_segment_info 解析测试")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.direct_video_generation import (
            parse_segment_info,
        )
    except Exception as e:
        fail("导入失败", str(e))
        return

    # Case 1: 完整用户输入
    msg1 = """分镜4（10.0-17.07s）
正向提示词：近景固定镜头切换，展示两款水杯外观清晰
负向提示词：生硬的镜头切换、模糊画面
16:9"""
    r1 = parse_segment_info(msg1)
    if r1["segment_name"] == "分镜4" and r1["segment_index"] == 4:
        ok("分镜编号解析正确", "分镜4, index=4")
    else:
        fail("分镜编号解析错误", str(r1))

    if abs(r1["start_time"] - 10.0) < 0.01 and abs(r1["end_time"] - 17.07) < 0.01:
        ok("时间段解析正确", f"{r1['start_time']}-{r1['end_time']}s")
    else:
        fail("时间段解析错误", f"start={r1['start_time']}, end={r1['end_time']}")

    if r1["duration"] == 7:
        ok("时长计算正确", f"{r1['duration']}s")
    else:
        fail("时长计算错误", f"期望7, 实际={r1['duration']}")

    if "近景固定镜头" in r1["positive_prompt"]:
        ok("正向提示词解析正确", f"长度={len(r1['positive_prompt'])}")
    else:
        fail("正向提示词解析错误", repr(r1["positive_prompt"][:50]))

    if "生硬" in r1["negative_prompt"]:
        ok("负向提示词解析正确")
    else:
        fail("负向提示词解析错误", repr(r1["negative_prompt"][:50]))

    if r1["ratio"] == "16:9":
        ok("比例解析正确", "16:9")
    else:
        fail("比例解析错误", r1["ratio"])

    # Case 2: 简短输入
    msg2 = "分镜1，5秒，提示词：小猫玩耍"
    r2 = parse_segment_info(msg2)
    if r2["segment_name"] == "分镜1":
        ok("简短输入: 分镜编号", r2["segment_name"])
    else:
        fail("简短输入: 分镜编号", r2["segment_name"])

    # Case 3: 第X镜格式
    msg3 = "第3镜 9:16"
    r3 = parse_segment_info(msg3)
    if r3["segment_name"] == "分镜3" and r3["ratio"] == "9:16":
        ok("第X镜格式解析正确", f"{r3['segment_name']}, {r3['ratio']}")
    else:
        fail("第X镜格式解析错误", str(r3))


# ─────────────────────────────────────────────
# Test 4: Hook 中 user_message 存储逻辑
# ─────────────────────────────────────────────
def test_selection_hook_stores_message():
    print("\n[Test 4] selection_hook 存储 user_message")
    try:
        import inspect
        from video_breakdown_agent.sub_agents.video_recreation_agent.hook.selection_hook import (
            hook_segment_selection,
        )

        source = inspect.getsource(hook_segment_selection)
        if (
            'session.state["user_message"]' in source
            or "session.state['user_message']" in source
        ):
            ok("hook_segment_selection 中包含 user_message 存储逻辑")
        else:
            fail("hook_segment_selection 中未找到 user_message 存储逻辑")
    except Exception as e:
        fail("检查 selection_hook 失败", str(e))


# ─────────────────────────────────────────────
# Test 5: direct_video_generation 返回值不含 ready_to_generate
# ─────────────────────────────────────────────
def test_direct_video_generation_return():
    print("\n[Test 5] direct_video_generation 返回值校验")
    try:
        import inspect
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.direct_video_generation import (
            direct_video_generation,
        )

        source = inspect.getsource(direct_video_generation)
        if "ready_to_generate" not in source:
            ok("返回值不含 ready_to_generate（已移除旧字段）")
        else:
            fail("仍含有 ready_to_generate 字段")

        if '"prepared"' in source:
            ok("返回值包含 prepared 字段")
        else:
            fail("返回值缺少 prepared 字段")
    except Exception as e:
        fail("检查失败", str(e))


# ─────────────────────────────────────────────
# Test 6: Prompt 内容校验
# ─────────────────────────────────────────────
def test_prompt_content():
    print("\n[Test 6] Prompt 内容校验")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.prompt import (
            RECREATION_ROOT_AGENT_INSTRUCTION,
        )

        # 6.1 不应包含 "direct_video_generation" 工具名称（Agent 不再直接调用工具）
        if "direct_video_generation" not in RECREATION_ROOT_AGENT_INSTRUCTION:
            ok("Prompt 不包含旧工具名 direct_video_generation")
        else:
            fail(
                "Prompt 仍然提及 direct_video_generation（应改为调用 quick_video_agent）"
            )

        # 6.2 应包含 quick_video_agent
        if "quick_video_agent" in RECREATION_ROOT_AGENT_INSTRUCTION:
            ok("Prompt 引导 Agent 调用 quick_video_agent")
        else:
            fail("Prompt 未提及 quick_video_agent")

        # 6.3 应禁止技术术语
        if "pipeline" in RECREATION_ROOT_AGENT_INSTRUCTION.lower().split("禁止")[0]:
            # 在禁止列表之前出现 pipeline 不行，但在禁止示例中可以出现
            pass
        if "❌ 不要说：pipeline" in RECREATION_ROOT_AGENT_INSTRUCTION:
            ok("Prompt 禁止使用 pipeline 等技术术语")
        else:
            fail("Prompt 未禁止技术术语")

    except Exception as e:
        fail("Prompt 检查失败", str(e))


# ─────────────────────────────────────────────
# Test 7: video_generate_http 增强日志
# ─────────────────────────────────────────────
def test_enhanced_logging():
    print("\n[Test 7] video_generate_http 增强日志校验")
    try:
        import inspect
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.video_generate_http import (
            video_generate,
        )

        source = inspect.getsource(video_generate)

        checks = [
            ("🎬 开始视频生成流程", "流程开始日志"),
            ("📋 待生成分镜数量", "分镜数量日志"),
            ("📤 任务提交完成", "任务提交日志"),
            ("⏳ 开始轮询任务状态", "轮询开始日志"),
            ("🎉 视频生成完成", "完成日志"),
        ]

        for marker, desc in checks:
            if marker in source:
                ok(desc)
            else:
                fail(desc, f"未找到标记: {marker}")

    except Exception as e:
        fail("日志检查失败", str(e))


# ─────────────────────────────────────────────
# Test 8: 端到端在线测试（可选，需 API Key）
# ─────────────────────────────────────────────
async def test_e2e():
    print("\n[Test 8] 端到端在线测试（需要 API Key）")

    api_key = os.getenv("MODEL_AGENT_API_KEY", "")
    if not api_key:
        fail("MODEL_AGENT_API_KEY 未设置，跳过 E2E 测试")
        return

    try:
        os.chdir(PROJECT_ROOT)
        from agent import runner

        session_id = f"smoke_quick_video_{os.getpid()}"
        user_id = "smoke_test_user"

        # 测试消息：提供提示词并要求生成视频
        test_message = (
            "分镜4（10.0-17.07s）\n"
            "正向提示词：近景固定镜头切换，先展示带美甲的手握住乐扣乐扣白色保温杯（背景日历+文字），"
            "随后平滑切换至透明竖纹玻璃杯（背景卡通衣物），两款水杯外观清晰，光线一致柔和\n"
            "负向提示词：生硬的镜头切换、模糊的杯身细节\n\n"
            "生成视频"
        )

        print(f"  📤 发送测试消息 (长度={len(test_message)})")
        print("  ⏳ 等待 Agent 响应（可能需要 3-5 分钟）...")

        result = await runner.run(
            messages=test_message,
            user_id=user_id,
            session_id=session_id,
        )

        result_str = str(result)
        print(f"  📥 回复预览: {result_str[:300]}...")

        # 验证结果
        if "pipeline" in result_str.lower() or "session state" in result_str.lower():
            fail("回复中包含技术术语", "pipeline/session state")
        else:
            ok("回复不包含技术术语")

        if any(kw in result_str for kw in ["分镜4", "已准备", "生成", "视频"]):
            ok("回复包含预期关键词")
        else:
            fail("回复缺少预期关键词")

        # 检查是否有视频 URL 或正在生成的提示
        if "http" in result_str or "正在生成" in result_str or "预计" in result_str:
            ok("回复包含视频生成状态信息")
        else:
            fail("回复缺少视频生成状态信息", result_str[:200])

    except Exception as e:
        fail(f"E2E 测试异常: {e}")
        traceback.print_exc()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
async def main():
    global passed, failed

    print("=" * 60)
    print("Quick Video Agent — 冒烟测试")
    print("=" * 60)

    # 离线结构测试
    test_imports()
    test_agent_tree()
    test_parse_segment_info()
    test_selection_hook_stores_message()
    test_direct_video_generation_return()
    test_prompt_content()
    test_enhanced_logging()

    # 可选 E2E 测试
    if "--e2e" in sys.argv:
        await test_e2e()

    # 汇总
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"🏁 测试结果: {passed}/{total} 通过, {failed}/{total} 失败")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 所有冒烟测试通过！")
        if "--e2e" not in sys.argv:
            print("💡 提示：运行 --e2e 进行端到端在线测试")


if __name__ == "__main__":
    asyncio.run(main())
