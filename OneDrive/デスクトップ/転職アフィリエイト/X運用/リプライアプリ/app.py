"""
Xリプライ生成アプリ
- Streamlit Cloud でデプロイ、スマホブラウザから使用
- キーワード検索 → 返信候補選択 → Claude でリプライ生成 → コピーして手動投稿
"""

import os
import html
import streamlit as st
from tweet_searcher import search_reply_targets
from reply_generator import generate_replies

# ── Streamlit Cloud Secrets を環境変数に展開 ──────────────
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
.stButton > button {
    width: 100%;
    border-radius: 20px;
    padding: 10px 0;
    font-size: 16px;
    font-weight: bold;
}
.tweet-card {
    border: 1px solid #cfd9de;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 6px;
    background: white;
    color: #0f1419;
    line-height: 1.6;
}
.tweet-card.selected {
    border: 2px solid #1d9bf0;
    background: #f0f8ff;
}
.reply-card {
    border: 2px solid #1d9bf0;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 4px;
    background: #f0f8ff;
    color: #0f1419;
    font-size: 15px;
    line-height: 1.7;
}
.section-title {
    font-size: 18px;
    font-weight: bold;
    margin: 16px 0 8px 0;
    padding-top: 8px;
}
.meta { color: #536471; font-size: 13px; }
.label { color: #1d9bf0; font-size: 13px; font-weight: bold; }
.char-ok { color: #00ba7c; font-size: 13px; }
.char-ng { color: #f4212e; font-size: 13px; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── パスワード認証 ─────────────────────────────────────────
def check_auth():
    if st.session_state.get("authenticated"):
        return True
    st.title("💬 Xリプライ生成")
    st.markdown("#### パスワードを入力してください")
    pw = st.text_input("パスワード", type="password", placeholder="password")
    if st.button("ログイン", type="primary"):
        correct = os.environ.get("APP_PASSWORD", "")
        if pw == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

if not check_auth():
    st.stop()

# ── セッション初期化（設定は保存） ────────────────────────
defaults = {
    "tweets": [],
    "selected_tweet": None,
    "replies": [],
    "keyword": "",
    # 設定保存（セッション中は維持）
    "cfg_max_results": 10,
    "cfg_min_followers": 100,
    "cfg_max_followers": 50000,
    "cfg_hours_within": 24,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════════════════════
# 検索フォーム（常に最上部）
# ════════════════════════════════════════════════════════════
st.title("💬 Xリプライ生成")

keyword = st.text_input(
    "検索キーワード",
    value=st.session_state.keyword,
    placeholder="例: 転職 20代 未経験",
)
st.session_state.keyword = keyword

with st.expander("表示件数・絞り込み設定"):
    col1, col2 = st.columns(2)
    with col1:
        max_results = st.select_slider(
            "表示件数",
            options=[5, 10, 15, 20],
            value=st.session_state.cfg_max_results,
        )
        min_followers = st.number_input(
            "フォロワー最小",
            value=st.session_state.cfg_min_followers,
            step=100, min_value=0,
        )
    with col2:
        hours_within = st.selectbox(
            "投稿時間",
            [6, 12, 24, 48, 72],
            index=[6, 12, 24, 48, 72].index(st.session_state.cfg_hours_within),
            format_func=lambda x: f"{x}時間以内",
        )
        max_followers = st.number_input(
            "フォロワー最大",
            value=st.session_state.cfg_max_followers,
            step=1000, min_value=1,
        )
    # 設定をセッションに保存
    st.session_state.cfg_max_results = max_results
    st.session_state.cfg_min_followers = int(min_followers)
    st.session_state.cfg_max_followers = int(max_followers)
    st.session_state.cfg_hours_within = hours_within

if st.button("ツイートを検索する", type="primary"):
    if not keyword.strip():
        st.warning("キーワードを入力してください")
    else:
        with st.spinner("X を検索中..."):
            try:
                tweets = search_reply_targets(
                    keyword.strip(), max_results,
                    min_followers=int(min_followers),
                    max_followers=int(max_followers),
                    hours_within=hours_within,
                )
                st.session_state.tweets = tweets
                st.session_state.selected_tweet = None
                st.session_state.replies = []
                if not tweets:
                    st.warning("条件に合うツイートが見つかりませんでした。絞り込み設定を緩めてみてください。")
            except Exception as e:
                st.error(f"X API エラー: {e}")


# ════════════════════════════════════════════════════════════
# ツイート一覧（検索後に表示）
# ════════════════════════════════════════════════════════════
if st.session_state.tweets:
    st.divider()
    st.markdown(f"**{len(st.session_state.tweets)}件（エンゲージメント率順）**")

    for tweet in st.session_state.tweets:
        is_selected = (
            st.session_state.selected_tweet is not None
            and st.session_state.selected_tweet["id"] == tweet["id"]
        )
        preview = html.escape(tweet["text"][:110]) + ("…" if len(tweet["text"]) > 110 else "")
        username = html.escape(tweet["username"])
        name = html.escape(tweet["name"])
        eng_pct = f"{tweet['eng_rate'] * 100:.2f}%"
        card_class = "tweet-card selected" if is_selected else "tweet-card"

        st.markdown(f"""
        <div class="{card_class}">
            <b>@{username}</b>&nbsp;·&nbsp;{name}<br>
            <span class="meta">フォロワー {tweet['followers']:,} &nbsp;|&nbsp; ♡{tweet['likes']} 💬{tweet['replies']} 🔁{tweet['retweets']} &nbsp;|&nbsp; 率 {eng_pct}</span>
            <br><br>{preview}
        </div>
        """, unsafe_allow_html=True)

        btn_label = "✅ 選択中" if is_selected else "この投稿に返信する →"
        if st.button(btn_label, key=f"sel_{tweet['id']}"):
            st.session_state.selected_tweet = tweet
            st.session_state.replies = []
            st.rerun()


# ════════════════════════════════════════════════════════════
# リプライ生成（ツイート選択後にスクロールで到達）
# ════════════════════════════════════════════════════════════
if st.session_state.selected_tweet:
    tweet = st.session_state.selected_tweet

    st.divider()
    st.markdown('<div class="section-title">返信先ポスト</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tweet-card selected">
        <b>@{html.escape(tweet['username'])}</b>&nbsp;·&nbsp;{html.escape(tweet['name'])}<br>
        <span class="meta">フォロワー {tweet['followers']:,}</span>
        <br><br>{html.escape(tweet['text'])}
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"[X で元ポストを確認 ↗]({tweet['url']})")

    gen_label = "リプライを再生成する" if st.session_state.replies else "リプライを生成する"
    if st.button(gen_label, type="primary"):
        with st.spinner("Claude がリプライを生成中..."):
            try:
                st.session_state.replies = generate_replies(tweet["text"])
            except Exception as e:
                st.error(f"Claude API エラー: {e}")

    if st.session_state.replies:
        st.markdown('<div class="section-title">リプライ案（3案）</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="reply-card">{html.escape(text)}</div>', unsafe_allow_html=True)
            st.code(text, language=None)
            st.markdown("")
