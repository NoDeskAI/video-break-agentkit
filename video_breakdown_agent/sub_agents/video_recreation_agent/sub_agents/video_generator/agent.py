"""
视频生成Sub-Agent
参考: multimedia/director-agent/src/director_agent/sub_agents/video/agent.py
"""
import os

from veadk import Agent
from veadk.agents.sequential_agent import SequentialAgent
from veadk.config import getenv

from ...tools.video_generate_http import video_generate
from ...tools.merge_video_segments import merge_segments
from .prompt import VIDEO_GENERATOR_INSTRUCTION


def create_video_generator_agent() -> SequentialAgent:
    """
    创建视频生成Agent（骨架实现）
    """
    
    # 视频生成Agent（调用Doubao-Seedance API）
    video_generate_agent = Agent(
        name="video_generate_agent",
        description="根据提示词批量生成视频分镜",
        instruction=VIDEO_GENERATOR_INSTRUCTION,
        tools=[video_generate],  # 集成工具
        model_extra_config={
            "extra_body": {
                "thinking": {"type": getenv("THINKING_VIDEO_GENERATOR", "enabled")}
            }
        },
    )
    
    # 视频拼接Agent（单分镜自动跳过，多分镜执行拼接）
    video_merge_agent = Agent(
        name="video_merge_agent",
        description="将生成的分镜视频拼接为完整视频（单分镜自动跳过）",
        instruction="""调用 merge_segments 工具，然后根据返回结果展示：

- 工具返回 merged_video_url（不为null）时：
  直接展示视频链接，格式：
  "📺 视频链接：<URL>"
  不做其他说明。

- 工具返回 merged_video_url 为 null 且 status 为 error 时：
  简洁告知失败原因。

- 保持简洁，不重复之前已展示的信息，不输出技术细节。""",
        tools=[merge_segments],
    )
    
    # 完整视频生成流程（生成 → 拼接/展示）
    video_generator_agent = SequentialAgent(
        name="video_generator_agent",
        description="视频生成流程：生成 → 拼接/展示链接",
        sub_agents=[
            video_generate_agent,
            video_merge_agent
        ]
    )
    
    return video_generator_agent


# 导出
video_generator_agent = create_video_generator_agent()
