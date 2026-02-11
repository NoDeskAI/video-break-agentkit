"""
提交视频分镜拆解任务工具
"""
import logging

import httpx
from veadk.config import getenv

logger = logging.getLogger(__name__)


def breakdown_submit(video_url: str, priority: int = 5) -> dict:
    """
    提交视频到分镜拆解服务，开始分镜拆解处理。

    Args:
        video_url: 视频URL（支持公开URL或TOS私有路径，例如 https://example.com/video.mp4）
        priority: 任务优先级，数值越大越优先，默认5

    Returns:
        dict: 包含 task_id 和 status 等信息的字典
    """
    api_base = getenv("BREAKDOWN_API_BASE", "http://localhost:7114")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{api_base}/api/v1/breakdown/submit",
                json={"video_source": video_url, "priority": priority},
            )
            response.raise_for_status()
            result = response.json()

        if result["code"] != 0:
            return {"error": f"提交失败: {result['message']}"}

        task_data = result["data"]
        logger.info(f"任务提交成功: task_id={task_data['task_id']}")
        return {
            "task_id": task_data["task_id"],
            "video_source": task_data.get("video_source", video_url),
            "source_type": task_data.get("source_type", "unknown"),
            "status": task_data.get("status", "pending"),
            "message": "任务已成功提交，请使用 breakdown_get_result 获取结果",
        }

    except httpx.ConnectError:
        return {
            "error": f"无法连接到分镜拆解服务 ({api_base})，请确认服务已启动"
        }
    except httpx.TimeoutException:
        return {"error": "请求超时，请稍后重试"}
    except Exception as e:
        logger.error(f"提交任务异常: {e}")
        return {"error": f"提交任务失败: {str(e)}"}
