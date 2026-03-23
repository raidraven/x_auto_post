"""
週次アナリティクス取得モジュール
過去7日間の投稿データ（いいね・リポスト・引用・リプライ・インプレッション）を取得してCSV保存
"""

import csv
import glob
import os
from datetime import datetime, timedelta, timezone

import tweepy

from x_poster import get_client

LOG_DIR = "X投稿データ"


def get_my_user_id(client: tweepy.Client) -> str:
    me = client.get_me()
    return me.data.id


def fetch_weekly_metrics(client: tweepy.Client, user_id: str) -> list[dict]:
    """過去7日間のツイートとメトリクスを取得"""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    tweets = []
    pagination_token = None

    while True:
        response = client.get_users_tweets(
            id=user_id,
            max_results=100,
            start_time=start_time,
            end_time=end_time,
            tweet_fields=["public_metrics", "created_at", "text"],
            pagination_token=pagination_token,
        )

        if not response.data:
            break

        for tweet in response.data:
            m = tweet.public_metrics or {}
            tweets.append({
                "tweet_id": tweet.id,
                "created_at": tweet.created_at.strftime("%Y-%m-%d %H:%M") if tweet.created_at else "",
                "text": tweet.text[:80].replace("\n", " "),
                "impressions":  m.get("impression_count", "N/A"),
                "likes":        m.get("like_count", 0),
                "reposts":      m.get("retweet_count", 0),
                "quotes":       m.get("quote_count", 0),
                "replies":      m.get("reply_count", 0),
                "bookmarks":    m.get("bookmark_count", 0),
            })

        next_token = response.meta.get("next_token") if response.meta else None
        if not next_token:
            break
        pagination_token = next_token

    return tweets


def save_csv(tweets: list[dict], output_dir: str = "analytics") -> str:
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(output_dir, f"weekly_{date_str}.csv")

    fields = ["tweet_id", "created_at", "text",
              "impressions", "likes", "reposts", "quotes", "replies", "bookmarks"]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(tweets)

    return path


def print_summary(tweets: list[dict]):
    if not tweets:
        print("過去7日間の投稿が見つかりませんでした。")
        return

    total_likes       = sum(t["likes"]     for t in tweets)
    total_reposts     = sum(t["reposts"]   for t in tweets)
    total_quotes      = sum(t["quotes"]    for t in tweets)
    total_replies     = sum(t["replies"]   for t in tweets)
    total_bookmarks   = sum(t["bookmarks"] for t in tweets)
    impressions_list  = [t["impressions"]  for t in tweets if t["impressions"] != "N/A"]
    total_impressions = sum(impressions_list) if impressions_list else "N/A"

    print("=" * 55)
    print(f"  週次レポート  ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})")
    print("=" * 55)
    print(f"  投稿数        : {len(tweets)} 件")
    print(f"  インプレッション: {total_impressions}")
    print(f"  いいね        : {total_likes}")
    print(f"  リポスト      : {total_reposts}")
    print(f"  引用          : {total_quotes}")
    print(f"  リプライ      : {total_replies}")
    print(f"  ブックマーク  : {total_bookmarks}")
    print("=" * 55)

    # エンゲージメント上位3件
    ranked = sorted(tweets, key=lambda t: t["likes"] + t["reposts"] + t["replies"], reverse=True)
    print("\n  [エンゲージメント上位3件]")
    for i, t in enumerate(ranked[:3], 1):
        print(f"  {i}. {t['created_at']}  いいね:{t['likes']} RT:{t['reposts']} 返信:{t['replies']}")
        print(f"     {t['text']}")
    print()


def update_post_log_metrics(tweets: list[dict]):
    """X投稿データのCSVをtweet_idで照合してメトリクスを更新"""
    if not os.path.isdir(LOG_DIR):
        return

    metrics_by_id = {str(t["tweet_id"]): t for t in tweets}
    updated_total = 0

    for csv_path in glob.glob(os.path.join(LOG_DIR, "posts_*.csv")):
        rows = []
        changed = False

        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row in reader:
                tid = row.get("tweet_id", "")
                if tid and tid in metrics_by_id:
                    m = metrics_by_id[tid]
                    row["likes"]     = m["likes"]
                    row["reposts"]   = m["reposts"]
                    row["replies"]   = m["replies"]
                    row["quotes"]    = m["quotes"]
                    row["bookmarks"] = m["bookmarks"]
                    changed = True
                    updated_total += 1
                rows.append(row)

        if changed:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"投稿ログを更新しました: {csv_path}")

    if updated_total:
        print(f"メトリクス更新: {updated_total} 件")


if __name__ == "__main__":
    client  = get_client()
    user_id = get_my_user_id(client)
    print(f"ユーザーID: {user_id} のデータを取得中...")

    tweets = fetch_weekly_metrics(client, user_id)
    print_summary(tweets)

    if tweets:
        path = save_csv(tweets)
        print(f"CSVを保存しました: {path}")
        update_post_log_metrics(tweets)
        print("X投稿データのメトリクスを更新しました")
