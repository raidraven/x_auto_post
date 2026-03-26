"""
Claude API でリプライ文を生成する
- account_profile の情報をもとにキャラクターを維持
- 3つのアプローチ（共感 / 応援 / 気づき提供）でそれぞれ1案生成
"""

import os
import anthropic

# アカウントプロファイル（X自動化bot/account_profile.py と同じ内容）
ACCOUNT_PROFILE = {
    "handle": "@転職したいけど動けない人へ",
    "genre": "転職・キャリア（20代後半向け支援情報発信）",
    "tone": "明るく前向き＋背中を押す（ポジティブ応援系）",
    "target": "20代後半｜スキルなし｜転職したいけど動けない人",
    "positioning": "転職を迷う人に『自分と同じ人がいる』と気づかせるストーリーナビゲーター",
}

P = ACCOUNT_PROFILE

REPLY_SYSTEM_PROMPT = f"""あなたは{P['handle']}のアカウント運用者として返信するゴーストライターだ。

【アカウント情報】
ジャンル: {P['genre']}
口調: {P['tone']}
ターゲット: {P['target']}

【リプライルール】
・140字以内で完結させること（超えたら絶対アウト）
・相手のポストの内容に必ず具体的に触れること
・共感・応援・気づきの提供のどれかのスタンスで返すこと
・売り込み・宣伝・プロフ誘導は絶対にしないこと
・「〇〇さん」などの呼びかけは使わないこと
・ハッシュタグ禁止・URL禁止
・説教・上から目線NG
・自然な会話として続きが生まれる終わり方にすること

返信文のみを出力しろ。説明・補足・かぎかっこは一切不要。"""

APPROACHES = [
    "相手の気持ちに共感を示すアプローチで（「わかる」「それはつらい」「同じ状況の人多い」など）",
    "背中を押す応援のアプローチで（「一歩踏み出せる」「大丈夫」「できる根拠を示す」など）",
    "別の視点や小さな気づきを提供するアプローチで（「実は〇〇という見方もある」「〇〇だけ変えると変わる」など）",
]


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY が設定されていません")
    return anthropic.Anthropic(api_key=api_key)


def generate_replies(tweet_text: str, n: int = 3) -> list[dict]:
    """
    ツイートに対するリプライをn案生成する。
    戻り値: [{"text": str, "chars": int, "approach": str}, ...]
    """
    client = get_client()
    results = []

    for i in range(n):
        approach = APPROACHES[i] if i < len(APPROACHES) else "自然な返答で"
        try:
            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=200,
                system=REPLY_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"以下のポストに対して、{approach}リプライを1つ生成してください。\n\n"
                        f"【相手のポスト】\n{tweet_text}\n\n"
                        "140字以内の返信文のみを出力してください。"
                    ),
                }],
            )
            text = message.content[0].text.strip()
            # 超えていたら切り詰め（フォールバック）
            if len(text) > 140:
                text = text[:140]
            label = ["共感", "応援", "気づき提供"][i] if i < 3 else f"案{i+1}"
            results.append({"text": text, "chars": len(text), "label": label})
        except Exception as e:
            results.append({"text": f"生成エラー: {e}", "chars": 0, "label": "エラー"})

    return results
