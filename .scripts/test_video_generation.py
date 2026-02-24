#!/usr/bin/env python3
"""
快速测试视频生成功能

用法：
    uv run python .scripts/test_video_generation.py
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

async def test_video_generation():
    """测试视频生成功能"""
    import os
    os.chdir(PROJECT_ROOT)
    
    from agent import runner
    
    # 测试提示词
    test_message = """分镜1（0.0-5.0s）
正向提示词：清晨阳光洒在窗台上，一只橘猫慵懒地伸了个懒腰，然后跳下窗台，镜头跟随猫咪的动作缓缓移动，展现温馨的家居环境，光线柔和温暖
负向提示词：画面模糊、抖动严重、光线过暗、猫咪形态不自然
比例：16:9
时长：5秒

生成视频"""
    
    print("=" * 60)
    print("🎬 视频生成功能测试")
    print("=" * 60)
    print(f"\n📝 测试提示词：\n{test_message}\n")
    print("⏳ 正在处理...（预计需要 2-3 分钟）\n")
    
    try:
        result = await runner.run(
            messages=test_message,
            user_id="test_user",
            session_id=f"test_video_gen_{os.getpid()}",
        )
        
        print("=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        print(f"\n📥 Agent 回复：\n{result}\n")
        
        # 检查结果
        result_str = str(result)
        if "http" in result_str.lower():
            print("✅ 检测到视频链接，生成成功！")
        elif "正在生成" in result_str or "已准备" in result_str:
            print("✅ 提示词准备成功，视频生成流程已启动")
        elif "pipeline" in result_str.lower() or "session" in result_str.lower():
            print("⚠️  警告：回复中包含技术术语")
        else:
            print("⚠️  未检测到预期的视频生成状态")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_video_generation())
