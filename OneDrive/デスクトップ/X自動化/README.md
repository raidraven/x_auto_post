# X 自動投稿 Bot

Claude APIで口調を学習し、カテゴリ・フェーズ管理つきで自動投稿するBotです。  
**APIキーはすべてGitHub Secretsで管理**するため、コードに機密情報は一切含まれません。

---

## ファイル構成

```
x_bot/
├── account_profile.py          # ★ あなたの口調・プロファイルを設定
├── prompts.py                  # カテゴリ・フェーズ・プロンプト管理
├── post_generator.py           # 投稿生成（Claude API）
├── x_poster.py                 # X投稿（tweepy）
├── bot.py                      # エントリーポイント
├── requirements.txt
├── .gitignore
└── .github/
    └── workflows/
        └── post.yml            # GitHub Actions（定期実行）
```

---

## セットアップ手順

### 1. プロファイルをカスタマイズ

`account_profile.py` を開いて、自分の情報に書き換えます：

```python
ACCOUNT_PROFILE = {
    "handle": "@yourhandle",
    "genre": "AIビジネス活用",
    "tone": "断言・言い切り",
    "target": "副業を始めたい会社員",
    "credential": "AI活用で月収100万円達成",
    ...
}
```

### 2. X (Twitter) APIキーの取得

1. [X Developer Portal](https://developer.twitter.com/) でアプリを作成
2. アプリの権限を **Read and Write** に設定（重要）
3. 以下の4つを取得：
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

### 3. Anthropic APIキーの取得

[Anthropic Console](https://console.anthropic.com/) で取得。

### 4. GitHubにpush

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/あなた/x-bot.git
git push -u origin main
```

> **privateリポジトリ推奨**

### 5. GitHub Secretsに登録

`Settings → Secrets and variables → Actions → New repository secret` で以下を登録：

| 名前 | 値 |
|---|---|
| `X_API_KEY` | X API Key |
| `X_API_SECRET` | X API Secret |
| `X_ACCESS_TOKEN` | X Access Token |
| `X_ACCESS_TOKEN_SECRET` | X Access Token Secret |
| `ANTHROPIC_API_KEY` | Anthropic APIキー |

---

## 投稿スケジュール

| 時刻 (JST) | cron (UTC) |
|---|---|
| 08:00 | `0 23 * * *` |
| 12:30 | `30 3 * * *` |
| 19:00 | `0 10 * * *` |

変更する場合は `.github/workflows/post.yml` の `cron` を編集してください。  
→ [crontab.guru](https://crontab.guru/) で確認できます。

---

## 手動実行・テスト

GitHub の `Actions` タブ → `X Auto Post Bot` → `Run workflow` から：

- **Dry run**: 投稿せず生成内容だけ確認できます（最初はこれで確認推奨）
- **Day番号上書き**: `5` と入れると Day5 のプロンプトで生成します
- **スロット上書き**: `08:00` と入れると朝スロット用の内容で生成します

---

## フェーズ管理

Day番号に応じて自動でプロンプトのフェーズが切り替わります：

| Day | フェーズ |
|---|---|
| 1〜7 | 価値提供期（役立つ情報を全力投稿） |
| 8〜14 | 権威性構築期（実績・数字を見せる） |
| 15〜21 | 期待感醸成期（次のコンテンツへの期待） |
| 22〜 | ローンチ期（行動喚起を強める） |

`bot.py` の `START_DATE` を変更することで、Day1の基準日を設定できます。

---

## ローカルテスト

```bash
pip install -r requirements.txt

export X_API_KEY="..."
export X_API_SECRET="..."
export X_ACCESS_TOKEN="..."
export X_ACCESS_TOKEN_SECRET="..."
export ANTHROPIC_API_KEY="..."

# 接続テスト
python x_poster.py

# 生成内容だけ確認（投稿しない）
python bot.py --dry-run

# Day5・朝スロットで生成確認
python bot.py --day 5 --slot 08:00 --dry-run
```
