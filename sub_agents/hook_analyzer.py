"""
前三秒钩子分析 Sub-Agent

使用 SequentialAgent 模式：
1. hook_analysis_agent — LLM 分析前三秒分镜数据
2. hook_format_agent  — 格式化和校验 JSON 输出
"""
import logging
from typing import Dict, List

from veadk import Agent
from veadk.agents.sequential_agent import SequentialAgent
from veadk.config import getenv

from hook.format_hook import fix_hook_output_format
from prompts.hook_analyzer_prompt import HOOK_ANALYZER_INSTRUCTION
from utils.types import HookAnalysis, json_response_config

logger = logging.getLogger(__name__)


# ==================== 工具定义 ====================

def analyze_hook_segments(segments: List[Dict]) -> dict:
    """
    提取并分析视频前三秒的分镜数据，为钩子分析提供结构化的上下文信息。

    Args:
        segments: 完整的分镜列表数据（由 breakdown_get_result 返回的 segments 字段）

    Returns:
        dict: 前三秒分镜的结构化分析上下文，包含分镜数量、总时长和每个分镜的详细信息
    """
    if not segments:
        return {
            "error": "没有分镜数据",
            "segment_count": 0,
            "total_duration": 0,
            "segments": [],
        }

    # 提取前三秒的分镜
    first_segments = []
    cumulative_time = 0

    for seg in segments:
        end_time = seg.get("end_time", 0)
        if cumulative_time >= 3.0 and first_segments:
            break
        first_segments.append(seg)
        cumulative_time = end_time

    # 构造分析上下文（支持多模态）
    context = {
        "segment_count": len(first_segments),
        "total_duration": cumulative_time,
        "total_video_segments": len(segments),
        "analysis_mode": "multimodal",  # 标记为多模态分析
        "segments": [],
    }
    
    # 为每个分镜构造详细信息
    for s in first_segments:
        frame_urls = s.get("frame_urls", [])
        
        # 构造基础信息
        segment_info = {
            "index": s.get("segment_index", 0),
            "start_time": s.get("start_time", 0),
            "end_time": s.get("end_time", 0),
            "duration": s.get("duration", 0),
            "visual_content": s.get("visual_content", ""),
            "speech_text": s.get("speech_text", ""),
            "shot_type": s.get("shot_type", ""),
            "camera_movement": s.get("camera_movement", ""),
            "function_tag": s.get("function_tag", ""),
            "headline": s.get("headline", ""),
            "content_tags": s.get("content_tags", []),
            "voice_type": s.get("voice_type", ""),
            "clip_url": s.get("clip_url", ""),
        }
        
        # 添加关键帧图片（供 vision 模型使用）
        # 每个分镜最多取前3帧，避免 token 超限
        if frame_urls:
            segment_info["frame_images"] = [
                {"type": "image_url", "image_url": {"url": url}}
                for url in frame_urls[:3]
            ]
            segment_info["frame_count"] = len(frame_urls)
        else:
            segment_info["frame_images"] = []
            segment_info["frame_count"] = 0
        
        context["segments"].append(segment_info)
    
    # 统计总关键帧数
    total_frames = sum(s.get("frame_count", 0) for s in context["segments"])

    logger.info(
        f"前三秒分镜提取完成: {len(first_segments)}个分镜, "
        f"总时长{cumulative_time:.1f}s, 关键帧{total_frames}张"
    )
    return context


# ==================== Agent 定义 ====================

# 分析 Agent：执行钩子分析（多模态视觉分析）
hook_analysis_agent = Agent(
    name="hook_analysis_agent",
    model_name=getenv("MODEL_VISION_NAME", "doubao-seed-1-6-vision"),  # 使用 vision 模型
    description="对视频前三秒分镜进行深度钩子分析，具备视觉分析能力，可直接观察关键帧图片进行专业评估",
    instruction=HOOK_ANALYZER_INSTRUCTION,
    tools=[analyze_hook_segments],
    output_key="hook_analysis",
    model_extra_config={
        "extra_body": {
            "thinking": {"type": getenv("THINKING_HOOK_ANALYZER_AGENT", "disabled")}
        }
    },
)

# 格式化 Agent：校验和修复 JSON 输出
HOOK_FORMAT_INSTRUCTION = """
你是一个 JSON 格式转换器。请将输入的钩子分析内容严格按照规定的 JSON schema 格式化输出。

注意：
1. 所有评分字段必须是 0-10 的数字
2. strengths、weaknesses、suggestions 必须是字符串数组
3. 不要修改分析内容本身，只做格式转换
4. 如果输入已经是合法 JSON 且字段完整，直接输出即可
"""

hook_format_agent = Agent(
    name="hook_format_agent",
    model_name=getenv("MODEL_FORMAT_NAME", "doubao-seed-1-6-250615"),  # 格式化用小模型，降低成本
    description="将钩子分析输出格式化为标准 JSON",
    instruction=HOOK_FORMAT_INSTRUCTION,
    generate_content_config=json_response_config,
    output_schema=HookAnalysis,
    output_key="hook_analysis",
    after_model_callback=[fix_hook_output_format],
    model_extra_config={
        "extra_body": {
            "thinking": {"type": getenv("THINKING_HOOK_FORMAT_AGENT", "disabled")}
        }
    },
)

# 组合 Agent：顺序执行 分析 → 格式化
hook_analyzer_agent = SequentialAgent(
    name="hook_analyzer_agent",
    description="专门负责视频前三秒钩子分析的专家Agent，从视觉冲击力、语言钩子、情绪唤起、信息密度、节奏掌控5个维度进行深度分析，并输出标准化 JSON 结果",
    sub_agents=[hook_analysis_agent, hook_format_agent],
)
