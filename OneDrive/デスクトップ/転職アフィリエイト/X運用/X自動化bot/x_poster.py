"""
X投稿モジュール
APIキーはすべて環境変数から取得（GitHub Secrets経由）
"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


def get_client() -> tweepy.Client:
    required = [
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(f"以下の環境変数が設定されていません: {missing}")

    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def post_tweet(text: str) -> dict:
    try:
        client = get_client()
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        me = client.get_me()
        handle = me.data.username
        url = f"https://x.com/{handle}/status/{tweet_id}"
        print(f"投稿成功: {url}")
        return {"success": True, "tweet_id": tweet_id, "url": url, "error": None}
    except tweepy.TooManyRequests:
        print("レート制限に達しました。15分後に再試行してください。")
        return {"success": False, "tweet_id": None, "error": "rate_limit"}
    except tweepy.Forbidden as e:
        print(f"投稿が拒否されました: {e}")
        return {"success": False, "tweet_id": None, "error": f"forbidden: {e}"}
    except Exception as e:
        print(f"エラー: {e}")
        return {"success": False, "tweet_id": None, "error": str(e)}


# ── 接続テスト用 ────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("X API 接続テスト")
    print("=" * 50)
    try:
        client = get_client()
        me = client.get_me()
        print(f"認証成功: @{me.data.username} ({me.data.name})")
    except Exception as e:
        print(f"認証失敗: {e}")
        print("GitHub Secrets の設定を確認してください")
