#!/usr/bin/env python3
"""
简化提示词生成链路 - 离线验证测试

模拟真实场景：
  场景A：视频分析完成后，用户说"给出第二个分镜的提示词"
  场景B：视频未分析时，用户要求生成提示词（容错）
  场景C：验证 video_recreation_agent 已关闭 thinking
  场景D：验证 prompt_generator_agent 已移除 prompt_review_agent

用法：
    cd /Users/edy/Downloads/agentkit-samples-main/02-use-cases/video_breakdown_agent
    uv run python .scripts/test_simplified_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 简易统计 ──────────────────────────────────────────
passed = 0
failed = 0


def ok(name: str, detail: str = ""):
    global passed
    passed += 1
    suffix = f"  →  {detail}" if detail else ""
    print(f"  ✅ {name}{suffix}")


def fail(name: str, detail: str = ""):
    global failed
    failed += 1
    suffix = f"  →  {detail}" if detail else ""
    print(f"  ❌ {name}{suffix}")


# ── Mock 数据（模拟视频拆解后的真实 state）─────────────
# 格式来自 analyze_segments_vision 实际写入 state 的数据结构
MOCK_VISION_RESULT = [
    {
        "序号": 1,
        "start_time": 0.0,
        "end_time": 3.0,
        "duration": 3.0,
        "景别": "近景",
        "运镜": "固定",
        "画面描述": "带美甲的手展示白色乐扣乐扣水杯，背景有日历和彩色衣物；随后将杯子放置桌面。",
        "语音内容": "无",
        "功能标签": "产品展示",
        "视觉表现": {
            "光影": {"光源类型": "人工光", "光源方向": "正面光", "明暗对比": "弱"},
            "色调": {"主色调": "暖白", "饱和度": "低", "色彩氛围": "温馨"},
            "景深": {"虚化程度": "轻微虚化", "焦点主体": "水杯"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图"},
            "运动": {"速度": "慢速", "节奏感": "平稳"},
        },
        "frame_urls": [],
    },
    {
        "序号": 2,
        "start_time": 3.0,
        "end_time": 5.0,
        "duration": 2.0,
        "景别": "近景",
        "运镜": "固定",
        "画面描述": "手握白色杯子移开，露出透明条纹玻璃杯，桌面与背景保持不变。",
        "语音内容": "无",
        "功能标签": "产品展示",
        "视觉表现": {
            "光影": {"光源类型": "人工光", "光源方向": "侧面光", "明暗对比": "中等"},
            "色调": {"主色调": "自然", "饱和度": "中等", "色彩氛围": "清新"},
            "景深": {"虚化程度": "中等虚化", "焦点主体": "玻璃杯"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图"},
            "运动": {"速度": "中速", "节奏感": "流畅"},
        },
        "frame_urls": [],
    },
    {
        "序号": 3,
        "start_time": 5.0,
        "end_time": 7.05,
        "duration": 2.05,
        "景别": "近景",
        "运镜": "固定",
        "画面描述": "带美甲的手握住透明条纹玻璃杯，随后缓慢移开，玻璃杯保持原位。",
        "语音内容": "无",
        "功能标签": "产品展示",
        "视觉表现": {
            "光影": {"光源类型": "自然光", "光源方向": "正面光", "明暗对比": "弱"},
            "色调": {"主色调": "自然", "饱和度": "低", "色彩氛围": "简约"},
            "景深": {"虚化程度": "轻微虚化", "焦点主体": "玻璃杯"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图"},
            "运动": {"速度": "慢速", "节奏感": "平稳"},
        },
        "frame_urls": [],
    },
]

MOCK_BGM = {
    "has_bgm": True,
    "style": "轻音乐",
    "tags": ["舒缓", "治愈", "简约"],
    "emotion": "平静舒缓",
    "bpm": "65-75",
    "instruments": ["钢琴", "小提琴"],
}


class MockToolContext:
    def __init__(self, state: dict):
        self.state = dict(state)


# ═══════════════════════════════════════════════════════════════
# 场景A：视频已分析，用户说"给出第二个分镜的提示词"
# ═══════════════════════════════════════════════════════════════
async def test_scenario_a_get_segment2():
    print("\n[场景A] 视频已分析 → 用户: '给出第二个分镜的提示词'")
    print("  期望：直接调用 generate_video_prompts(segment_indexes='2') → 输出提示词")

    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.generate_video_prompts import (
            generate_video_prompts,
        )
    except Exception as e:
        fail("导入 generate_video_prompts 失败", str(e))
        return

    ctx = MockToolContext(
        state={
            "vision_analysis_result": MOCK_VISION_RESULT,
            "bgm_analysis_result": MOCK_BGM,
        }
    )

    try:
        result = await generate_video_prompts(
            tool_context=ctx,
            segment_indexes="2",
            use_skill_mode=False,  # 离线：跳过 LLM，用函数模板
        )
    except Exception as e:
        fail("调用 generate_video_prompts 抛出异常", str(e))
        import traceback
        traceback.print_exc()
        return

    # 基础检查
    status = result.get("status")
    if status == "success":
        ok("返回 status=success")
    else:
        fail("status 非 success", f"status={status}, message={result.get('message')}")
        return

    prompts = result.get("prompts", [])
    if len(prompts) == 1 and prompts[0].get("segment_index") == 2:
        ok("只返回分镜2，共1条")
    else:
        fail("分镜筛选不对", f"count={len(prompts)}, indexes={[p.get('segment_index') for p in prompts]}")
        return

    p = prompts[0]
    # 必要字段
    required = {"segment_index", "positive_prompt", "negative_prompt", "duration", "estimated_cost"}
    missing = required - set(p.keys())
    if not missing:
        ok("必要字段齐全")
    else:
        fail("缺少字段", f"{missing}")

    # state 写入
    pending = ctx.state.get("pending_prompts", {})
    if pending.get("total_count") == 1:
        ok("state['pending_prompts'].total_count = 1")
    else:
        fail("pending_prompts 未正确写入 state", str(pending))

    # 输出预览
    print(f"\n  📝 分镜2 提示词预览")
    print(f"     时段：{p.get('start_time')}s → {p.get('end_time')}s（{p.get('duration')}s）")
    print(f"     正向：{p['positive_prompt'][:100]}...")
    print(f"     负向：{p['negative_prompt'][:80]}")
    print(f"     画幅：{p.get('ratio', '未指定')}  | 预估费用：¥{p.get('estimated_cost', '?')}")


# ═══════════════════════════════════════════════════════════════
# 场景B：视频未分析（空 state），容错检查
# ═══════════════════════════════════════════════════════════════
async def test_scenario_b_empty_state():
    print("\n[场景B] 未分析视频 → 用户: '给出第二个分镜的提示词'")
    print("  期望：返回 status=error，提示用户先做视频拆解，不抛异常")

    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.generate_video_prompts import (
            generate_video_prompts,
        )
    except Exception as e:
        fail("导入失败", str(e))
        return

    ctx = MockToolContext(state={})  # 空 state

    try:
        result = await generate_video_prompts(
            tool_context=ctx,
            segment_indexes="2",
            use_skill_mode=False,
        )
    except Exception as e:
        fail("调用抛出异常（应返回 error 而非抛异常）", str(e))
        return

    status = result.get("status")
    message = result.get("message", "")
    if status == "error":
        ok(f"正确返回 error", f"message='{message[:60]}'")
    else:
        fail("未正确处理空 state", f"status={status}")


# ═══════════════════════════════════════════════════════════════
# 场景C：验证 video_recreation_agent thinking 已关闭
# ═══════════════════════════════════════════════════════════════
def test_scenario_c_recreation_agent_thinking():
    print("\n[场景C] 验证 video_recreation_agent 的 thinking 默认值为 disabled")

    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.agent import (
            video_recreation_agent,
        )
    except Exception as e:
        fail("导入 video_recreation_agent 失败", str(e))
        return

    # 检查 model_extra_config
    config = getattr(video_recreation_agent, "model_extra_config", None) or {}
    thinking_type = (
        config
        .get("extra_body", {})
        .get("thinking", {})
        .get("type", "UNKNOWN")
    )
    if thinking_type == "disabled":
        ok("thinking.type = disabled ✓")
    else:
        fail(f"thinking.type 非 disabled", f"当前值={thinking_type!r}")

    # 确认 generate_video_prompts 工具已挂到根 agent
    tools = getattr(video_recreation_agent, "tools", []) or []
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    if "generate_video_prompts" in tool_names:
        ok("generate_video_prompts 工具已挂到根 agent")
    else:
        fail("generate_video_prompts 工具未找到", f"现有工具={tool_names}")


# ═══════════════════════════════════════════════════════════════
# 场景D：验证 prompt_generator_agent 不再含 prompt_review_agent
# ═══════════════════════════════════════════════════════════════
def test_scenario_d_no_prompt_review_agent():
    print("\n[场景D] 验证 prompt_generator_agent 已移除 prompt_review_agent")

    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.sub_agents.prompt_generator.agent import (
            create_prompt_generator_agent,
        )
        agent = create_prompt_generator_agent()
    except Exception as e:
        fail("导入 prompt_generator_agent 失败", str(e))
        return

    sub_agents = getattr(agent, "sub_agents", []) or []
    sub_names = [getattr(a, "name", str(a)) for a in sub_agents]

    # 不应含 prompt_review_agent
    if "prompt_review_agent" not in sub_names:
        ok("prompt_review_agent 已移除")
    else:
        fail("prompt_review_agent 仍在 sub_agents 中")

    # 应只含 generate + format 两步
    expected = {"prompt_generate_agent", "prompt_format_agent"}
    actual = set(sub_names)
    if actual == expected:
        ok(f"sub_agents 精确为两步：{sorted(expected)}")
    else:
        fail(f"sub_agents 不符预期", f"期望={sorted(expected)}, 实际={sorted(actual)}")

    # prompt_generate_agent thinking 也应 disabled
    gen_agent = next((a for a in sub_agents if getattr(a, "name", "") == "prompt_generate_agent"), None)
    if gen_agent:
        config = getattr(gen_agent, "model_extra_config", None) or {}
        thinking_type = config.get("extra_body", {}).get("thinking", {}).get("type", "UNKNOWN")
        if thinking_type == "disabled":
            ok("prompt_generate_agent thinking.type = disabled ✓")
        else:
            fail("prompt_generate_agent thinking 未关闭", f"当前={thinking_type!r}")
    else:
        fail("未找到 prompt_generate_agent 子 Agent")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
async def main():
    global passed, failed
    print("=" * 65)
    print("  简化提示词生成链路 — 离线验证测试")
    print("  （模拟真实场景，无需 LLM API）")
    print("=" * 65)

    await test_scenario_a_get_segment2()
    await test_scenario_b_empty_state()
    test_scenario_c_recreation_agent_thinking()
    test_scenario_d_no_prompt_review_agent()

    total = passed + failed
    print(f"\n{'=' * 65}")
    print(f"🏁  结果：{passed}/{total} 通过  |  {failed}/{total} 失败")
    print(f"{'=' * 65}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 所有场景验证通过！")


if __name__ == "__main__":
    asyncio.run(main())
