"""
Xリプライ生成アプリ
- Streamlit Cloud でデプロイ、スマホブラウザから使用
- キーワード検索 → 返信候補選択 → Claude でリプライ生成 → コピーして手動投稿
"""

import os
import streamlit as st
from tweet_searcher import search_reply_targets
from reply_generator import generate_replies

# ── Streamlit Cloud Secrets を環境変数に展開 ──────────────
# ローカル(.env)でも Streamlit Cloud(secrets)でも動作する
if hasattr(st, "secrets"):
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))

# ── ページ設定 ─────────────────────────────────────────────
st.set_page_config(
    page_title="Xリプライ生成",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── モバイル向け CSS ──────────────────────────────────────
st.markdown("""
<style>
/* ボタンを全幅・大きめに */
.stButton > button {
    width: 100%;
    border-radius: 20px;
    padding: 10px 0;
    font-size: 16px;
    font-weight: bold;
}
/* ツイートカード */
.tweet-card {
    border: 1px solid #cfd9de;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 6px;
    background: white;
    line-height: 1.6;
}
/* リプライカード */
.reply-card {
    border: 2px solid #1d9bf0;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 4px;
    background: #f0f8ff;
    font-size: 15px;
    line-height: 1.7;
}
.meta { color: #536471; font-size: 13px; }
.label { color: #1d9bf0; font-size: 13px; font-weight: bold; }
.char-ok { color: #00ba7c; font-size: 13px; }
.char-ng { color: #f4212e; font-size: 13px; }
/* モバイルで余白調整 */
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── 検索キーワード ─────────────────────────────────────────
KEYWORDS = [
    "転職エージェント",
    "転職サイト おすすめ",
    "転職 未経験",
    "転職 志望動機",
    "転職 面接",
    "転職 年収アップ",
    "転職 30代",
    "転職活動 進め方",
    "転職 書類選考",
    "スキルなし 転職",
]

# ── セッション初期化 ───────────────────────────────────────
defaults = {
    "page": "search",       # "search" | "reply"
    "tweets": [],
    "selected_tweet": None,
    "replies": [],
    "last_keyword": KEYWORDS[0],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════════════════════
# ページ1: キーワード検索 → ツイート一覧
# ════════════════════════════════════════════════════════════
def page_search():
    st.title("💬 Xリプライ生成")

    # キーワード選択
    idx = KEYWORDS.index(st.session_state.last_keyword) if st.session_state.last_keyword in KEYWORDS else 0
    keyword = st.selectbox("検索キーワード", KEYWORDS, index=idx)
    st.session_state.last_keyword = keyword

    max_results = st.select_slider("取得件数", options=[5, 10, 15, 20], value=10)

    if st.button("ツイートを検索する", type="primary"):
        with st.spinner("X を検索中..."):
            try:
                tweets = search_reply_targets(keyword, max_results)
                st.session_state.tweets = tweets
                if not tweets:
                    st.warning("ツイートが見つかりませんでした。別のキーワードを試してください。")
            except Exception as e:
                st.error(f"X API エラー: {e}")

    # ── ツイート一覧 ──
    if st.session_state.tweets:
        st.markdown(f"**{len(st.session_state.tweets)}件見つかりました（エンゲージメント順）**")
        st.divider()

        for tweet in st.session_state.tweets:
            preview = tweet["text"][:110] + ("…" if len(tweet["text"]) > 110 else "")
            st.markdown(f"""
            <div class="tweet-card">
                <b>@{tweet['username']}</b>&nbsp;·&nbsp;{tweet['name']}<br>
                <span class="meta">フォロワー {tweet['followers']:,} &nbsp;|&nbsp; ♡{tweet['likes']} 💬{tweet['replies']} 🔁{tweet['retweets']}</span>
                <br><br>{preview}
            </div>
            """, unsafe_allow_html=True)

            if st.button("この投稿に返信する →", key=f"sel_{tweet['id']}"):
                st.session_state.selected_tweet = tweet
                st.session_state.replies = []
                st.session_state.page = "reply"
                st.rerun()


# ════════════════════════════════════════════════════════════
# ページ2: リプライ生成
# ════════════════════════════════════════════════════════════
def page_reply():
    tweet = st.session_state.selected_tweet

    if st.button("← 検索に戻る"):
        st.session_state.page = "search"
        st.session_state.selected_tweet = None
        st.rerun()

    # 返信先ポスト
    st.subheader("返信先ポスト")
    st.markdown(f"""
    <div class="tweet-card">
        <b>@{tweet['username']}</b>&nbsp;·&nbsp;{tweet['name']}<br>
        <span class="meta">フォロワー {tweet['followers']:,}</span>
        <br><br>{tweet['text']}
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"[X で元ポストを確認 ↗]({tweet['url']})")

    st.divider()

    # リプライ生成ボタン
    gen_label = "リプライを再生成する" if st.session_state.replies else "リプライを生成する"
    if st.button(gen_label, type="primary"):
        with st.spinner("Claude がリプライを生成中..."):
            try:
                replies = generate_replies(tweet["text"])
                st.session_state.replies = replies
            except Exception as e:
                st.error(f"Claude API エラー: {e}")

    # リプライ案を表示
    if st.session_state.replies:
        st.subheader("リプライ案（3案）")

        for i, reply in enumerate(st.session_state.replies, 1):
            text = reply["text"]
            chars = reply["chars"]
            label = reply["label"]
            char_class = "char-ok" if chars <= 140 else "char-ng"

            st.markdown(
                f'<span class="label">案{i}：{label}</span>&emsp;'
                f'<span class="{char_class}">{chars}字</span>',
                unsafe_allow_html=True,
            )
            # リプライ本文（見た目）
            st.markdown(f'<div class="reply-card">{text}</div>', unsafe_allow_html=True)
            # コードブロック = 右上のコピーボタンで1タップコピー可能
            st.code(text, language=None)

            st.markdown("")  # 余白


# ════════════════════════════════════════════════════════════
# ルーティング
# ════════════════════════════════════════════════════════════
if st.session_state.page == "search":
    page_search()
elif st.session_state.page == "reply":
    if st.session_state.selected_tweet:
        page_reply()
    else:
        st.session_state.page = "search"
        st.rerun()
