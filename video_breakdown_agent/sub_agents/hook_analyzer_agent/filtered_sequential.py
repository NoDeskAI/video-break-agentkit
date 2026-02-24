from __future__ import annotations

from typing import AsyncGenerator

from google.adk.agents import InvocationContext
from google.adk.events import Event
from veadk.agents.sequential_agent import SequentialAgent


class HookAnalyzerSequentialAgent(SequentialAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async for event in super()._run_async_impl(ctx):
            author = str(getattr(event, "author", "") or "")
            if author == "hook_analysis_agent":
                # 中间步骤只参与链路，不对外展示。
                continue
            yield event
