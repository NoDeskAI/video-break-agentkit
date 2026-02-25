#!/usr/bin/env python3
"""
generate_video_prompts 离线测试脚本

验证：
  1. 生成单个分镜提示词（segment_indexes="1"）
  2. 生成全部分镜提示词（segment_indexes=""）
  3. 返回体干净（无调试字段）

用法：
    cd /Users/edy/Downloads/agentkit-samples-main/02-use-cases/video_breakdown_agent
    uv run python .scripts/test_prompt_generation.py
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

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


# ── Mock ToolContext ───────────────────────────────────
MOCK_SEGMENTS = [
    {
        "序号": 1,
        "start_time": 0.0,
        "end_time": 3.0,
        "duration": 3.0,
        "景别": "近景",
        "运镜": "固定",
        "画面描述": "带美甲的手展示白色乐扣乐扣水杯，背景有日历和彩色衣物；随后将杯子放置桌面，展示品牌标识。",
        "语音内容": "无",
        "功能标签": "产品展示",
        "视觉表现": {
            "光影": {"光源类型": "人工光", "光源方向": "正面光", "明暗对比": "弱", "阴影风格": "柔和"},
            "色调": {"主色调": "暖白", "饱和度": "低", "色彩氛围": "温馨", "滤镜效果": "无"},
            "景深": {"虚化程度": "轻微虚化", "焦点主体": "水杯", "景深范围": "中景深"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图", "画面平衡": "对称"},
            "运动": {"速度": "慢速", "节奏感": "平稳", "特殊效果": "无"},
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
            "光影": {"光源类型": "人工光", "光源方向": "侧面光", "明暗对比": "中等", "阴影风格": "柔和"},
            "色调": {"主色调": "自然", "饱和度": "中等", "色彩氛围": "清新", "滤镜效果": "无"},
            "景深": {"虚化程度": "中等虚化", "焦点主体": "玻璃杯", "景深范围": "中景深"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图", "画面平衡": "对称"},
            "运动": {"速度": "中速", "节奏感": "流畅", "特殊效果": "无"},
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
        "画面描述": "带美甲的手握住透明条纹玻璃杯，随后缓慢移开，玻璃杯保持原位，背景简洁。",
        "语音内容": "无",
        "功能标签": "产品展示",
        "视觉表现": {
            "光影": {"光源类型": "自然光", "光源方向": "正面光", "明暗对比": "弱", "阴影风格": "柔和"},
            "色调": {"主色调": "自然", "饱和度": "低", "色彩氛围": "简约", "滤镜效果": "无"},
            "景深": {"虚化程度": "轻微虚化", "焦点主体": "玻璃杯", "景深范围": "中景深"},
            "构图": {"主体位置": "中心", "构图法则": "中心构图", "画面平衡": "对称"},
            "运动": {"速度": "慢速", "节奏感": "平稳", "特殊效果": "无"},
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


class MockState(dict):
    """可读写的 state 字典"""
    pass


class MockToolContext:
    def __init__(self, state: dict):
        self.state = MockState(state)


# ── 禁止出现的调试字段 ─────────────────────────────────
DEBUG_FIELDS = {"extracted_features", "original_segment_data", "knowledge_used"}


def _check_no_debug_fields(prompts: list, label: str):
    """确认返回列表中不含调试字段"""
    for p in prompts:
        leaked = set(p.keys()) & DEBUG_FIELDS
        if leaked:
            fail(f"{label} 返回体含调试字段", f"泄漏={leaked}")
            return False
    ok(f"{label} 返回体干净（无调试字段）")
    return True


def _check_required_fields(prompts: list, label: str):
    required = {"segment_index", "positive_prompt", "negative_prompt", "duration", "estimated_cost"}
    for p in prompts:
        missing = required - set(p.keys())
        if missing:
            fail(f"{label} 缺少必要字段", f"缺少={missing}")
            return False
    ok(f"{label} 必要字段齐全")
    return True


def _check_state_has_debug(state: MockState, label: str):
    """确认 debug 数据写入了 state 而不是返回体"""
    debug_state = state.get("pending_prompts_debug", {})
    if debug_state and debug_state.get("prompts"):
        ok(f"{label} 调试数据正确写入 state['pending_prompts_debug']")
    else:
        fail(f"{label} 调试数据未写入 state", str(debug_state))


def _check_state_pending(state: MockState, label: str, expected_count: int):
    pending = state.get("pending_prompts", {})
    count = pending.get("total_count", -1)
    if count == expected_count:
        ok(f"{label} state['pending_prompts'].total_count = {count}")
    else:
        fail(f"{label} pending_prompts.total_count 不符", f"期望={expected_count}, 实际={count}")


# ── Test 1: 单分镜（分镜1）─────────────────────────────
async def test_single_segment():
    print("\n[Test 1] 生成单个分镜提示词（分镜1）")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.generate_video_prompts import (
            generate_video_prompts,
        )
    except Exception as e:
        fail("导入 generate_video_prompts 失败", str(e))
        return

    ctx = MockToolContext(
        state={
            "vision_analysis_result": MOCK_SEGMENTS,
            "bgm_analysis_result": MOCK_BGM,
        }
    )

    try:
        result = await generate_video_prompts(
            tool_context=ctx,
            segment_indexes="1",
            use_skill_mode=False,  # 离线使用函数模式（无需 LLM API）
        )
    except Exception as e:
        fail("调用 generate_video_prompts 失败", str(e))
        import traceback
        traceback.print_exc()
        return

    # 状态
    if result.get("status") == "success":
        ok("返回 status=success")
    else:
        fail("返回 status 非 success", result.get("message", ""))
        return

    prompts = result.get("prompts", [])
    # 应该只有1个
    if len(prompts) == 1 and prompts[0]["segment_index"] == 1:
        ok("只返回分镜1，共1条")
    else:
        fail("返回分镜数量或序号不对", f"count={len(prompts)}, indexes={[p.get('segment_index') for p in prompts]}")
        return

    _check_no_debug_fields(prompts, "单分镜")
    _check_required_fields(prompts, "单分镜")
    _check_state_has_debug(ctx.state, "单分镜")
    _check_state_pending(ctx.state, "单分镜", expected_count=1)

    # 输出提示词内容预览（用于人工确认）
    p = prompts[0]
    print(f"\n  📝 分镜1 提示词预览：")
    print(f"     正向：{p['positive_prompt'][:80]}...")
    print(f"     负向：{p['negative_prompt']}")
    print(f"     时长：{p['duration']}s  | 画幅：{p['ratio']}  | 费用：¥{p['estimated_cost']}")


# ── Test 2: 全部分镜 ──────────────────────────────────
async def test_all_segments():
    print("\n[Test 2] 生成全部分镜提示词（3个分镜）")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.tools.generate_video_prompts import (
            generate_video_prompts,
        )
    except Exception as e:
        fail("导入 generate_video_prompts 失败", str(e))
        return

    ctx = MockToolContext(
        state={
            "vision_analysis_result": MOCK_SEGMENTS,
            "bgm_analysis_result": MOCK_BGM,
        }
    )

    try:
        result = await generate_video_prompts(
            tool_context=ctx,
            segment_indexes="",  # 全部
            use_skill_mode=False,
        )
    except Exception as e:
        fail("调用 generate_video_prompts 失败", str(e))
        import traceback
        traceback.print_exc()
        return

    if result.get("status") == "success":
        ok("返回 status=success")
    else:
        fail("返回 status 非 success", result.get("message", ""))
        return

    prompts = result.get("prompts", [])
    if len(prompts) == 3:
        ok(f"返回全部3个分镜")
    else:
        fail("分镜数量不对", f"实际={len(prompts)}")
        return

    _check_no_debug_fields(prompts, "全部分镜")
    _check_required_fields(prompts, "全部分镜")
    _check_state_has_debug(ctx.state, "全部分镜")
    _check_state_pending(ctx.state, "全部分镜", expected_count=3)

    # 内容预览
    print(f"\n  📋 全部分镜提示词预览：")
    for p in prompts:
        print(f"  ─ 分镜{p['segment_index']}（{p['start_time']}-{p['end_time']}s, {p['duration']}s）")
        print(f"    正向：{p['positive_prompt'][:70]}...")
        print(f"    费用：¥{p['estimated_cost']}")

    total_cost = result.get("total_cost", 0)
    print(f"\n  💰 预估总费用：¥{total_cost:.2f}")


# ── Test 3: 空分镜数据 ─────────────────────────────────
async def test_empty_state():
    print("\n[Test 3] 未拆解视频时调用（容错校验）")
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
            segment_indexes="1",
            use_skill_mode=False,
        )
    except Exception as e:
        fail("调用抛出异常（应返回 error 而非抛异常）", str(e))
        return

    if result.get("status") == "error" and "未找到分镜数据" in result.get("message", ""):
        ok("正确返回 error 且消息友好")
    else:
        fail("错误处理不符预期", str(result))


# ── Test 4: generate_video_prompts 已挂到根 Agent ──────
def test_tool_registered():
    print("\n[Test 4] generate_video_prompts 已挂到 video_recreation_agent")
    try:
        from video_breakdown_agent.sub_agents.video_recreation_agent.agent import (
            video_recreation_agent,
        )
        tools = getattr(video_recreation_agent, "tools", None) or []
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        if "generate_video_prompts" in tool_names:
            ok("工具已注册", f"所有工具: {tool_names}")
        else:
            fail("工具未注册", f"当前工具: {tool_names}")
    except Exception as e:
        fail("导入 video_recreation_agent 失败", str(e))


# ── Main ──────────────────────────────────────────────
async def main():
    global passed, failed
    print("=" * 60)
    print("generate_video_prompts 离线测试")
    print("（使用函数模板模式，无需 LLM API Key）")
    print("=" * 60)

    await test_single_segment()
    await test_all_segments()
    await test_empty_state()
    test_tool_registered()

    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"🏁 测试结果: {passed}/{total} 通过, {failed}/{total} 失败")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
