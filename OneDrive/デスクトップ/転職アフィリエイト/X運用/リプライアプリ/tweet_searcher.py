"""
X API でリプライ候補ツイートを検索する
- Basic プランのアカウントを使用（search_recent_tweets が必要）
- Bearer Token で検索、OAuth1.0a でユーザー情報取得
"""

import os
import tweepy


def get_client() -> tweepy.Client:
    return tweepy.Client(
        bearer_token=os.environ.get("X_BEARER_TOKEN"),
        consumer_key=os.environ.get("X_API_KEY"),
        consumer_secret=os.environ.get("X_API_SECRET"),
        access_token=os.environ.get("X_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=False,
    )


def search_reply_targets(keyword: str, max_results: int = 10) -> list[dict]:
    """
    キーワードでツイートを検索し、返信候補リストを返す。
    - リツイート・リプライを除外
    - 日本語のみ
    - エンゲージメント順にソート
    """
    client = get_client()

    # リツイート・リプライを除外し日本語に絞る
    query = f"{keyword} lang:ja -is:retweet -is:reply"

    response = client.search_recent_tweets(
        query=query,
        max_results=max(10, min(max_results, 100)),
        expansions=["author_id"],
        user_fields=["username", "name", "public_metrics"],
        tweet_fields=["public_metrics", "created_at"],
    )

    if not response.data:
        return []

    # author_id -> User オブジェクトの辞書を作る
    users = {u.id: u for u in (response.includes.get("users") or [])}

    results = []
    for tweet in response.data:
        author = users.get(tweet.author_id)
        author_metrics = getattr(author, "public_metrics", {}) or {}
        tweet_metrics = tweet.public_metrics or {}
        username = getattr(author, "username", "unknown")

        results.append({
            "id": str(tweet.id),
            "text": tweet.text,
            "username": username,
            "name": getattr(author, "name", "unknown"),
            "followers": author_metrics.get("followers_count", 0),
            "likes": tweet_metrics.get("like_count", 0),
            "replies": tweet_metrics.get("reply_count", 0),
            "retweets": tweet_metrics.get("retweet_count", 0),
            "url": f"https://x.com/{username}/status/{tweet.id}",
        })

    # いいね + リプライ数×2 でエンゲージメント順ソート
    results.sort(key=lambda x: x["likes"] + x["replies"] * 2, reverse=True)
    return results[:max_results]
