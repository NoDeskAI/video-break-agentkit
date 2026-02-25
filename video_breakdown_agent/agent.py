"""
主编排 Root Agent 定义（veadk web 的唯一真相来源）

架构说明：root agent 直接持有 web_search 工具，无需独立的 search_agent 子 Agent。
VeADK 支持 Agent 同时持有 tools 和 sub_agents（video_recreation_agent 已验证）。
"""

import logging
import os

from veadk import Agent
from veadk.agents.sequential_agent import SequentialAgent
from veadk.memory.short_term_memory import ShortTermMemory
from veadk.tools.builtin_tools.web_search import web_search

from .hook.final_output_hook import guard_final_user_output
from .hook.video_upload_hook import hook_video_upload
from .prompt import ROOT_AGENT_INSTRUCTION
from .sub_agents.breakdown_agent.prompt import (
    BREAKDOWN_AGENT_INSTRUCTION,
    HOOK_ANALYSIS_ADDENDUM,
)
from .sub_agents.report_generator_agent.prompt import REPORT_AGENT_INSTRUCTION
from .sub_agents.report_generator_agent.direct_output_callback import (
    direct_output_callback,
)
from .tools.process_video import process_video
from .tools.analyze_segments_vision import analyze_segments_vision
from .tools.analyze_bgm import analyze_bgm
from .tools.video_upload import video_upload_to_tos
from .tools.report_generator import generate_video_report

# ==================== 视频复刻Agent导入（新增） ====================
from .sub_agents.video_recreation_agent.agent import video_recreation_agent


logger = logging.getLogger(__name__)

# ==================== 内容安全护栏（LLM Shield） ====================
# 仅当配置了 TOOL_LLM_SHIELD_APP_ID 时启用，否则静默跳过

shield_callbacks = {}
if os.getenv("TOOL_LLM_SHIELD_APP_ID"):
    try:
        from veadk.tools.builtin_tools.llm_shield import content_safety

        shield_callbacks = {
            "before_model_callback": content_safety.before_model_callback,
            "after_model_callback": content_safety.after_model_callback,
        }
        logger.info("内容安全护栏: 已启用 (before_model + after_model)")
    except Exception as e:
        logger.warning(f"llm_shield 加载失败，跳过内容安全护栏: {e}")
else:
    logger.debug("未配置 TOOL_LLM_SHIELD_APP_ID，跳过内容安全护栏")

root_before_model_callback = shield_callbacks.get("before_model_callback")
root_after_model_callbacks = []
if shield_callbacks.get("after_model_callback"):
    root_after_model_callbacks.append(shield_callbacks["after_model_callback"])
# 最后一层输出守卫：仅在泄露过程信息时触发 LLM 重写
root_after_model_callbacks.append(guard_final_user_output)
root_callback_kwargs = {
    "after_model_callback": root_after_model_callbacks,
}
if root_before_model_callback:
    root_callback_kwargs["before_model_callback"] = root_before_model_callback

# ==================== Factory functions (避免 SequentialAgent 共享 parent) ====================


def create_breakdown_agent(include_hook_analysis: bool = False) -> Agent:
    """
    创建分镜拆解 Agent。

    Args:
        include_hook_analysis: 为 True 时在 instruction 末尾附加钩子分析模板，
                               用于 hook_only_pipeline 和 full_analysis_pipeline。
    """
    instruction = BREAKDOWN_AGENT_INSTRUCTION
    if include_hook_analysis:
        instruction += HOOK_ANALYSIS_ADDENDUM
    return Agent(
        name="breakdown_agent",
        description=(
            "负责视频分镜拆解：视频预处理（FFmpeg + ASR）、"
            "视觉分析（doubao-vision）、BGM 分析。"
            "支持URL链接和本地文件上传，输出完整分镜结构化数据。"
        ),
        instruction=instruction,
        tools=[
            process_video,
            analyze_segments_vision,
            analyze_bgm,
            video_upload_to_tos,
        ],
        output_key="breakdown_result",
        model_extra_config={
            "extra_body": {
                "thinking": {"type": os.getenv("THINKING_BREAKDOWN_AGENT", "disabled")}
            }
        },
    )


def create_report_generator_agent() -> Agent:
    return Agent(
        name="report_generator_agent",
        description="整合分镜拆解数据和钩子分析结果，生成专业的视频分析报告",
        instruction=REPORT_AGENT_INSTRUCTION,
        tools=[generate_video_report],
        after_tool_callback=[direct_output_callback],
        output_key="final_report",
        model_extra_config={
            "extra_body": {
                "thinking": {"type": os.getenv("THINKING_REPORT_AGENT", "disabled")}
            }
        },
    )


# ==================== Pipelines ====================

full_analysis_pipeline = SequentialAgent(
    name="full_analysis_pipeline",
    description="完整分析生产线：分镜拆解 + 钩子分析 -> 报告生成",
    sub_agents=[
        create_breakdown_agent(include_hook_analysis=True),
        create_report_generator_agent(),
    ],
)

hook_only_pipeline = SequentialAgent(
    name="hook_only_pipeline",
    description="钩子分析生产线：分镜拆解 + 钩子分析（在同一个 Agent 内完成）",
    sub_agents=[create_breakdown_agent(include_hook_analysis=True)],
)

report_only_pipeline = SequentialAgent(
    name="report_only_pipeline",
    description="报告生产线：补齐分镜 -> 生成报告",
    sub_agents=[create_breakdown_agent(), create_report_generator_agent()],
)

breakdown_only_pipeline = SequentialAgent(
    name="breakdown_only_pipeline",
    description="分镜拆解生产线：仅执行分镜拆解",
    sub_agents=[create_breakdown_agent()],
)

agent = Agent(
    name="video_breakdown_agent",
    description=(
        "专业的视频分镜拆解和深度分析助手，"
        "支持URL链接和本地文件上传，"
        "能够自动拆解视频分镜、分析前三秒钩子、生成专业报告、复刻爆款视频"
    ),
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[web_search],
    sub_agents=[
        full_analysis_pipeline,
        hook_only_pipeline,
        report_only_pipeline,
        breakdown_only_pipeline,
        video_recreation_agent,
    ],
    short_term_memory=ShortTermMemory(backend="local"),
    # 拦截 veadk web UI 上传的文件（inline_data → 文本 URL/路径）
    before_agent_callback=hook_video_upload,
    model_extra_config={
        "extra_body": {
            "thinking": {"type": os.getenv("THINKING_ROOT_AGENT", "disabled")}
        }
    },
    **root_callback_kwargs,
)

root_agent = agent
