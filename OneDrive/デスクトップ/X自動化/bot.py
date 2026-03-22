"""
X自動投稿Bot エントリーポイント

実行方法:
  python bot.py                   # 今日のDay番号で1回投稿
  python bot.py --day 5           # Day5として投稿
  python bot.py --dry-run         # 投稿せず生成内容だけ確認
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta

from post_generator import generate_daily_posts
from x_poster import post_tweet
from account_profile import ACCOUNT_PROFILE

# 投稿スケジュール（JST）
POST_SCHEDULE = ["08:00", "12:30", "19:00"]

# プロジェクト開始日（Day1にしたい日付を JST で指定）
# 例: START_DATE = datetime(2025, 1, 1, tzinfo=JST)
JST = timezone(timedelta(hours=9))
START_DATE = datetime(2025, 1, 1, tzinfo=JST)


def get_day_number() -> int:
    """今日が何日目かを計算"""
    today = datetime.now(JST).date()
    delta = (today - START_DATE.date()).days + 1
    return max(1, delta)


def get_current_slot() -> str | None:
    """現在時刻に最も近いスロットを返す（±30分以内）"""
    now = datetime.now(JST)
    now_minutes = now.hour * 60 + now.minute
    for slot in POST_SCHEDULE:
        h, m = map(int, slot.split(":"))
        slot_minutes = h * 60 + m
        if abs(now_minutes - slot_minutes) <= 30:
            return slot
    return None


def main():
    parser = argparse.ArgumentParser(description="X自動投稿Bot")
    parser.add_argument("--day", type=int, help="Day番号を指定（省略時は自動計算）")
    parser.add_argument("--slot", type=str, help="時間スロットを指定（例: 08:00）")
    parser.add_argument("--dry-run", action="store_true", help="投稿せず生成内容だけ確認")
    args = parser.parse_args()

    day_number = args.day if args.day else get_day_number()
    slot = args.slot if args.slot else get_current_slot()

    print(f"{'='*50}")
    print(f"X自動投稿Bot - Day{day_number}")
    print(f"アカウント: {ACCOUNT_PROFILE['handle']}")
    print(f"ジャンル: {ACCOUNT_PROFILE['genre']}")
    print(f"{'='*50}")

    if slot is None:
        # スロット指定なし＝全スロット生成（バッチ確認用）
        slots = POST_SCHEDULE
        print(f"スロット指定なし → 全{len(slots)}スロット分を生成します")
    else:
        slots = [slot]
        print(f"対象スロット: {slot}")

    # 投稿を生成
    print("\n投稿生成中...")
    posts = generate_daily_posts(day_number, slots)

    if args.dry_run:
        print("\n【DRY RUN】以下の内容が生成されました（投稿はしません）:")
        for p in posts:
            print(f"\n[{p['time']}] {p['category']} ({len(p['text'])}字)")
            print(p["text"])
            print("-" * 40)
        return

    # X に投稿
    print("\nXに投稿中...")
    results = []
    for p in posts:
        print(f"\n[{p['time']}] {p['category']}")
        result = post_tweet(p["text"])
        results.append(result)

    # 結果サマリ
    success = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"完了: {success}/{len(results)} 件投稿成功")

    if success < len(results):
        sys.exit(1)  # GitHub Actionsでエラーを検知させる


if __name__ == "__main__":
    main()
