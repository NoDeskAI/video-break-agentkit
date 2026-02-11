"""
查询分镜拆解任务状态和获取结果的工具
"""
import logging
import time

import httpx
from veadk.config import getenv

logger = logging.getLogger(__name__)


def breakdown_query_status(task_id: str) -> dict:
    """
    查询分镜拆解任务的当前处理状态。

    Args:
        task_id: 任务ID（由 breakdown_submit 返回）

    Returns:
        dict: 包含任务状态、进度、当前步骤等信息
    """
    api_base = getenv("BREAKDOWN_API_BASE", "http://localhost:7114")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_base}/api/v1/breakdown/status/{task_id}")
            response.raise_for_status()
            result = response.json()

        if result["code"] != 0:
            return {"error": result["message"]}

        return result["data"]

    except httpx.ConnectError:
        return {
            "error": f"无法连接到分镜拆解服务 ({api_base})，请确认服务已启动"
        }
    except Exception as e:
        logger.error(f"查询任务状态异常: {e}")
        return {"error": f"查询失败: {str(e)}"}


def breakdown_get_result(task_id: str, max_wait: int = 300) -> dict:
    """
    获取分镜拆解结果。如果任务未完成，会自动轮询等待直到完成或超时。

    Args:
        task_id: 任务ID（由 breakdown_submit 返回）
        max_wait: 最大等待时间（秒），默认300秒（5分钟）

    Returns:
        dict: 包含完整分镜数据、BGM分析、场景分析等结果
    """
    api_base = getenv("BREAKDOWN_API_BASE", "http://localhost:7114")
    start_time = time.time()

    # 轮询等待任务完成
    while time.time() - start_time < max_wait:
        status_result = breakdown_query_status(task_id)

        if "error" in status_result:
            return status_result

        current_status = status_result.get("status", "unknown")
        progress = status_result.get("progress", 0)
        current_step = status_result.get("current_step", "unknown")

        if current_status == "completed":
            logger.info(f"任务 {task_id} 已完成")
            break
        elif current_status == "failed":
            error_msg = status_result.get("error_message", "未知错误")
            return {"error": f"任务处理失败: {error_msg}"}

        logger.info(
            f"任务 {task_id} 处理中: {progress}% - {current_step}"
        )
        time.sleep(5)
    else:
        return {
            "error": f"等待超时（已等待{max_wait}秒），任务可能仍在处理中，请稍后使用 breakdown_query_status 查询状态"
        }

    # 获取完整结果
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{api_base}/api/v1/breakdown/result/{task_id}"
            )
            response.raise_for_status()
            result = response.json()

        if result["code"] != 0:
            return {"error": result["message"]}

        data = result["data"]
        logger.info(
            f"获取结果成功: task_id={task_id}, "
            f"分镜数={data.get('segment_count', 0)}, "
            f"时长={data.get('duration', 0):.1f}s"
        )
        return data

    except Exception as e:
        logger.error(f"获取结果异常: {e}")
        return {"error": f"获取结果失败: {str(e)}"}
