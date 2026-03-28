import os
from typing import AsyncGenerator
import anthropic
from prompts.system_prompt import build_system_prompt, contains_crisis_keyword

client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

CRISIS_RESPONSE = (
    "その気持ちを話してくれてありがとう。今、とてもつらい状況にいるんだね。\n\n"
    "一人で抱え込まないでほしいな。よりそいホットライン（0120-279-338）は24時間話を聞いてくれるよ。\n\n"
    "私もここにいるから、話せる範囲でいつでも聞かせてね。"
)


async def chat_stream(
    messages: list[dict],
    user_name: str = "あなた",
    mood_score: str = "未記録",
    current_goal: str = "未設定",
) -> AsyncGenerator[str, None]:
    # 最新のユーザーメッセージをチェック
    latest_user_msg = ""
    for m in reversed(messages):
        if m["role"] == "user":
            latest_user_msg = m["content"]
            break

    if contains_crisis_keyword(latest_user_msg):
        yield CRISIS_RESPONSE
        return

    system = build_system_prompt(user_name, mood_score, current_goal)

    # 直近10往復に制限
    recent_messages = messages[-20:]

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system,
        messages=recent_messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
