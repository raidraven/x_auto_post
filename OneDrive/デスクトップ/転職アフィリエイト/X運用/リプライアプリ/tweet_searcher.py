"""
X API でリプライ候補ツイートを検索する
- Basic プランのアカウントを使用（search_recent_tweets が必要）
- Bearer Token で検索、OAuth1.0a でユーザー情報取得
"""

import os
from datetime import datetime, timezone, timedelta
import tweepy

# ── 選定フィルター設定 ────────────────────────────────────
FILTER = {
    "min_followers": 100,       # フォロワー最小（スパム除外）
    "max_followers": 50000,     # フォロワー最大（大手アカウントは相手にされにくい）
    "hours_within": 24,         # 直近○時間以内の投稿のみ
}


def get_client() -> tweepy.Client:
    return tweepy.Client(
        bearer_token=os.environ.get("X_BEARER_TOKEN"),
        consumer_key=os.environ.get("X_API_KEY"),
        consumer_secret=os.environ.get("X_API_SECRET"),
        access_token=os.environ.get("X_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=False,
    )


def _engagement_rate(likes: int, replies: int, retweets: int, followers: int) -> float:
    """エンゲージメント率 = (いいね + リプライ×2 + RT) / フォロワー数"""
    if followers == 0:
        return 0.0
    return (likes + replies * 2 + retweets) / followers


def search_reply_targets(
    keyword: str,
    max_results: int = 10,
    min_followers: int = FILTER["min_followers"],
    max_followers: int = FILTER["max_followers"],
    hours_within: int = FILTER["hours_within"],
) -> list[dict]:
    """
    キーワードでツイートを検索し、返信候補リストを返す。

    選定基準：
    1. キーワードを含む・日本語・リツイート/リプライ除外
    2. フォロワー数フィルター（min_followers ～ max_followers）
    3. 投稿時間フィルター（hours_within 時間以内）
    4. エンゲージメント率順にソート（いいね+リプライ×2+RT）÷フォロワー数
    """
    client = get_client()

    query = f"{keyword} lang:ja -is:retweet -is:reply"
    # フィルター後に max_results 件残るよう多めに取得
    fetch_count = max(10, min(max_results * 4, 100))

    response = client.search_recent_tweets(
        query=query,
        max_results=fetch_count,
        expansions=["author_id"],
        user_fields=["username", "name", "public_metrics"],
        tweet_fields=["public_metrics", "created_at"],
    )

    if not response.data:
        return []

    users = {u.id: u for u in (response.includes.get("users") or [])}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_within)

    results = []
    for tweet in response.data:
        author = users.get(tweet.author_id)
        author_metrics = getattr(author, "public_metrics", {}) or {}
        tweet_metrics = tweet.public_metrics or {}
        username = getattr(author, "username", "unknown")
        followers = author_metrics.get("followers_count", 0)
        likes = tweet_metrics.get("like_count", 0)
        replies = tweet_metrics.get("reply_count", 0)
        retweets = tweet_metrics.get("retweet_count", 0)

        # ── フィルター ──
        # フォロワー数チェック
        if not (min_followers <= followers <= max_followers):
            continue
        # 投稿時間チェック
        if tweet.created_at and tweet.created_at < cutoff:
            continue

        eng_rate = _engagement_rate(likes, replies, retweets, followers)

        results.append({
            "id": str(tweet.id),
            "text": tweet.text,
            "username": username,
            "name": getattr(author, "name", "unknown"),
            "followers": followers,
            "likes": likes,
            "replies": replies,
            "retweets": retweets,
            "eng_rate": eng_rate,
            "created_at": tweet.created_at,
            "url": f"https://x.com/{username}/status/{tweet.id}",
        })

    # エンゲージメント率順にソート
    results.sort(key=lambda x: x["eng_rate"], reverse=True)
    return results[:max_results]
