"""
钩子分析输出格式校验 Hook
基于 multimedia/market-agent/hook/format_hook.py 模式实现

通过 after_model_callback 机制，在 LLM 输出后自动校验和修复 JSON 格式
"""
import json
from typing import Optional

import json_repair
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.adk.models import LlmResponse
from pydantic import ValidationError
from veadk.utils.logger import get_logger

logger = get_logger(__name__)


def fix_hook_output_format(
    *,
    callback_context: CallbackContext,
    llm_response: LlmResponse,
    model_response_event: Optional[Event] = None,
) -> Optional[LlmResponse]:
    """
    检查钩子分析输出格式是否符合 HookAnalysis schema，并尝试修复。

    处理场景：
    1. 无 output_schema → 直接返回
    2. 有效 JSON 且符合 schema → 返回
    3. 无效 JSON → json_repair 修复后校验
    4. 修复失败 → 返回错误信息
    """
    agent = callback_context._invocation_context.agent
    user_id = callback_context._invocation_context.user_id
    session_id = callback_context._invocation_context.session.id
    invocation_id = callback_context.invocation_id
    output_schema = agent.output_schema

    tag = f"[fix_hook_output_format] agent:{agent.name} user:{user_id} session:{session_id} invocation:{invocation_id}"
    fixed = False

    # 场景1：无 schema 直接放行
    if not output_schema:
        logger.debug(f"{tag} No output_schema, pass through")
        return llm_response

    text = llm_response.content.parts[0].text
    logger.debug(f"{tag} Original output length: {len(text)}")

    # 尝试解析 JSON
    try:
        output = json.loads(text)
    except json.JSONDecodeError:
        # 尝试修复
        try:
            output = json_repair.loads(text)
            if isinstance(output, list):
                output = output[0]
            fixed = True
            logger.info(f"{tag} JSON repaired successfully")
        except Exception:
            logger.warning(f"{tag} JSON repair failed, original length: {len(text)}")
            llm_response.content.parts[0].text = json.dumps(
                _error_response("钩子分析输出格式异常，JSON 解析失败，请重试"),
                ensure_ascii=False,
            )
            return llm_response

    # 校验 schema
    try:
        output_schema.model_validate(output)

        # 数值范围修正
        for score_field in [
            "overall_score", "visual_impact", "language_hook",
            "emotion_trigger", "information_density", "rhythm_control",
        ]:
            if score_field in output:
                output[score_field] = max(0, min(10, float(output[score_field])))

        llm_response.content.parts[0].text = json.dumps(output, ensure_ascii=False)

        if fixed:
            logger.info(f"{tag} JSON repaired and validated against schema")
        else:
            logger.debug(f"{tag} Output valid against schema")

        return llm_response

    except ValidationError as e:
        if fixed:
            logger.warning(f"{tag} JSON repaired but failed schema validation: {e}")
        else:
            logger.warning(f"{tag} Valid JSON but failed schema validation: {e}")

        llm_response.content.parts[0].text = json.dumps(
            _error_response("钩子分析输出格式不符合规范，请重试"),
            ensure_ascii=False,
        )
        return llm_response


def _error_response(reason: str) -> dict:
    """构造标准化错误响应"""
    return {
        "overall_score": 0,
        "visual_impact": 0,
        "visual_comment": "",
        "language_hook": 0,
        "language_comment": "",
        "emotion_trigger": 0,
        "emotion_comment": "",
        "information_density": 0,
        "info_comment": "",
        "rhythm_control": 0,
        "rhythm_comment": "",
        "hook_type": "未知",
        "strengths": [],
        "weaknesses": [],
        "suggestions": [reason],
        "retention_prediction": "无法评估",
    }
