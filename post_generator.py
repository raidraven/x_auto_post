"""
投稿生成モジュール
- APIキーは環境変数から取得（GitHub Secrets経由）
- Anthropic SDK を使用（subprocessのcurl不使用）
"""

import os
import time
import anthropic
from prompts import SYSTEM_PROMPT, build_prompt, select_category_for_slot

# 環境変数からAPIキーを取得（config.pyには書かない）
_client = None


def get_anthropic_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY が環境変数に設定されていません")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── 品質チェック ────────────────────────────────────
_GOOD_ENDINGS = set(
    "るただいくすぞなよねかれんむえうろめてにをはもがぜさけせつみりし？！…。らので"
)
_BAD_ENDINGS = [
    "完", "自", "他", "読ん", "書いて", "感動",
    "こ", "プ", "なりた", "人にな", "仕組み作って",
]


def is_complete_post(text: str) -> bool:
    if not text or text == "投稿生成に失敗":
        return False
    if len(text) > 140:
        return False
    last = text[-1]
    for be in _BAD_ENDINGS:
        if text.endswith(be):
            return False
    return last in _GOOD_ENDINGS


# ── 生成ロジック ────────────────────────────────────
def generate_post_anthropic(category: str, day_number: int) -> str | None:
    try:
        client = get_anthropic_client()
        user_prompt = build_prompt(category, day_number)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  生成エラー: {e}")
        return None


def generate_post(category: str, day_number: int) -> str:
    """品質チェック付き生成（最大5回リトライ）"""
    text = None
    for attempt in range(5):
        text = generate_post_anthropic(category, day_number)
        if text and is_complete_post(text):
            return text
        if text and len(text) > 140:
            print(f"  {len(text)}字 → 再生成 ({attempt + 1}/5)")
            time.sleep(1)

    # 5回失敗したら140字に切り詰め
    if text and len(text) > 140:
        lines = text.split("\n")
        result = ""
        for line in lines:
            if len(result + line + "\n") <= 140:
                result += line + "\n"
            else:
                break
        return result.strip() if result.strip() else text[:140]

    return text if text else "投稿生成に失敗"


def generate_daily_posts(day_number: int, time_slots: list[str]) -> list[dict]:
    posts = []
    used_categories: list[str] = []

    for slot in time_slots:
        # カテゴリ重複を避ける（最大4カテゴリまで）
        for _ in range(10):
            category = select_category_for_slot(slot, day_number)
            if category not in used_categories or len(used_categories) >= 4:
                break
        used_categories.append(category)

        text = generate_post(category, day_number)
        posts.append({
            "time": slot,
            "category": category,
            "text": text,
            "day": day_number,
        })
        preview = text[:50].replace("\n", " ")
        print(f"  [{slot}] {category} ({len(text)}字): {preview}…")

    return posts
