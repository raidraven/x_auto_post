"""
週次報告書生成モジュール
X投稿データのCSVを読み込み、ClaudeでAI分析＋改善案をmd形式で保存
"""

import csv
import glob
import os
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

from account_profile import ACCOUNT_PROFILE

load_dotenv()

DATA_DIR   = "X投稿データ"
REPORT_DIR = "X週次報告書"


def load_latest_analytics() -> list[dict]:
    """X投稿データの最新 analytics_*.csv を読み込む"""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "analytics_*.csv")))
    if not files:
        return []
    with open(files[-1], "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_post_logs() -> list[dict]:
    """X投稿データの posts_*.csv を全件読み込む"""
    rows = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "posts_*.csv"))):
        with open(path, "r", encoding="utf-8-sig") as f:
            rows.extend(csv.DictReader(f))
    return rows


def build_prompt(tweets: list[dict], posts: list[dict]) -> str:
    profile = ACCOUNT_PROFILE

    # --- サマリー集計 ---
    def safe_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    total      = len(tweets)
    imp_vals   = [safe_int(t["impressions"]) for t in tweets if t.get("impressions") not in ("", "N/A", None)]
    total_imp  = sum(imp_vals)
    total_like = sum(safe_int(t["likes"])    for t in tweets)
    total_rt   = sum(safe_int(t["reposts"])  for t in tweets)
    total_rep  = sum(safe_int(t["replies"])  for t in tweets)
    total_bm   = sum(safe_int(t["bookmarks"])for t in tweets)

    ranked = sorted(tweets,
                    key=lambda t: safe_int(t["likes"]) + safe_int(t["reposts"]) + safe_int(t["replies"]),
                    reverse=True)

    top3_lines = ""
    for i, t in enumerate(ranked[:3], 1):
        top3_lines += (
            f"{i}. [{t.get('created_at','')}] "
            f"いいね:{t.get('likes',0)} RT:{t.get('reposts',0)} "
            f"リプライ:{t.get('replies',0)} 印象:{t.get('impressions','N/A')}\n"
            f"   {t.get('text','')[:100]}\n"
        )

    category_count: dict[str, int] = {}
    for p in posts:
        cat = p.get("category", "不明")
        category_count[cat] = category_count.get(cat, 0) + 1
    cat_lines = "\n".join(f"  {k}: {v}件" for k, v in sorted(category_count.items(), key=lambda x: -x[1]))

    prompt = f"""あなたはXアカウントの運用コンサルタントです。
以下のアカウント情報と週次データをもとに、日本語で詳細な週次報告書を作成してください。

## アカウント情報
- ジャンル: {profile['genre']}
- ターゲット: {profile['target']}
- ポジショニング: {profile['positioning']}
- 30日目標: {profile['goal_30day']}
- カテゴリ配分目標: {profile['category_weights']}

## 今週の投稿データ（過去7日間）
- 総投稿数: {total}件
- 総インプレッション: {total_imp}
- 総いいね: {total_like}
- 総リポスト: {total_rt}
- 総リプライ: {total_rep}
- 総ブックマーク: {total_bm}

## エンゲージメント上位3件
{top3_lines}

## カテゴリ別投稿数（累計）
{cat_lines if cat_lines else "データなし"}

---

上記データを分析し、以下の構成でmarkdown形式の報告書を作成してください。
コードブロックは使わず、markdownそのままで出力してください。

# 週次X運用報告書

## 今週のサマリー
（数値の要約と簡単なコメント）

## パフォーマンス分析
（何が伸びたか、何が伸びなかったか。エンゲージメント率の評価）

## 上位コンテンツの共通点
（エンゲージメントが高かった投稿の傾向・フック・構成パターン）

## 課題と考察
（数値から見える問題点とその原因仮説）

## 来週の改善アクション
（具体的で実行可能な施策を3〜5点、箇条書き）

## 投稿カテゴリの最適化提案
（目標配分と実績のズレがあれば指摘し、調整案を提示）
"""
    return prompt


def generate_report(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def save_report(content: str) -> str:
    os.makedirs(REPORT_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(REPORT_DIR, f"report_{date_str}.md")

    header = f"---\n生成日: {date_str}\n---\n\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + content)

    return path


if __name__ == "__main__":
    print("X投稿データを読み込み中...")
    tweets = load_latest_analytics()
    posts  = load_post_logs()

    if not tweets:
        print("analytics_*.csv が見つかりません。先に analytics.py を実行してください。")
        raise SystemExit(1)

    print(f"{len(tweets)}件のツイートデータを取得。Claude で分析中...")
    prompt  = build_prompt(tweets, posts)
    content = generate_report(prompt)

    path = save_report(content)
    print(f"報告書を保存しました: {path}")
