"""
投稿カテゴリ・フェーズ管理・プロンプト生成
"""

import random
from account_profile import ACCOUNT_PROFILE

P = ACCOUNT_PROFILE

POST_CATEGORIES = {
    "実績・証拠":     {"weight": 20, "time_slots": ["12:00", "21:30"]},
    "ノウハウ・Tips": {"weight": 30, "time_slots": ["07:30", "21:30"]},
    "煽り・問題提起": {"weight": 20, "time_slots": ["12:00", "21:30"]},
    "ツール紹介":     {"weight": 15, "time_slots": ["07:30", "21:30"]},
    "マインドセット": {"weight": 15, "time_slots": ["07:30", "21:30"]},
}

# account_profile の category_weights で上書き
if P.get("category_weights"):
    for pair in P["category_weights"].split(","):
        pair = pair.strip()
        if ":" in pair:
            name, w = pair.rsplit(":", 1)
            name, w = name.strip(), int(w.strip())
            for key in POST_CATEGORIES:
                if name in key or key in name:
                    POST_CATEGORIES[key]["weight"] = w
                    break

# ── システムプロンプト ──────────────────────────────
SYSTEM_PROMPT = f"""あなたは{P['handle']}として投稿するゴーストライターだ。

【ジャンル】{P['genre']}
【口調】{P['tone']}
【ターゲット】{P['target']}
【ポジショニング】{P['positioning']}
【実績】{P['credential']}

【文体ルール】
・140字以内で完結させろ。途中で切れる文章は絶対禁止。
・1行目は必ず読者を止めるフックにしろ。共感・驚き・疑問のどれかで始めろ。
・数字（◯社・◯割・◯日・◯万円・◯ステップなど）を必ず1つ以上入れろ。
・改行を効果的に使え。箇条書き2〜3点か、Before→Afterの流れで構成しろ。
・絵文字は最小限（0〜1個）。
・ハッシュタグ禁止。URL禁止。★●■などの装飾記号禁止。
・同じ内容・同じフレーズの繰り返し禁止。
・「〜してみてください」「〜しましょう」などの命令調NG。自然な語りかけにしろ。

【NG表現】{P['ng_expressions']}
【ルール】{P['rules']}
【伸びるパターン】{P['top_patterns']}

投稿文のみを出力しろ。説明や補足は一切不要。"""

# ── カテゴリ別プロンプト ────────────────────────────
CATEGORY_PROMPTS = {
    "実績・証拠": f"""{P['handle']}の実績を自然に織り交ぜた投稿を作れ。
実績内容: {P['credential']}
・「〇〇だった自分が→今は〇〇」のBefore/After形式か、具体的な数字（◯人・◯社・◯割など）を入れろ。
・自慢にならず「あなたにもできる」と感じさせる締め方にしろ。
{{phase_context}}Day{{day_number}}の投稿だ。
140字以内で完結する投稿文を出力しろ。途中で切れる文章は禁止。投稿文のみを出力。""",

    "ノウハウ・Tips": f"""{P['genre']}の実用的なノウハウを投稿しろ。
ターゲット: {P['target']}
・「◯つのポイント」「◯日でできる」など数字を1つ以上入れろ。
・箇条書き2〜3点か、「知らない人→知った後の変化」の構成にしろ。
・読んだ人がその日から使える具体的な内容にしろ。
{{phase_context}}Day{{day_number}}の投稿だ。
140字以内で完結する投稿文を出力しろ。途中で切れる文章は禁止。投稿文のみを出力。""",

    "煽り・問題提起": f"""{P['genre']}の領域で問題提起する投稿を作れ。
・「転職を迷い続けた結果◯年が過ぎた」「実は◯割の人が〇〇を知らない」のような数字+事実で刺せ。
・読者が「自分のことだ」と感じる具体的なシチュエーションを入れろ。
・「だから今日から◯だけやれ」など最後は小さな一歩で締めろ。
{{phase_context}}Day{{day_number}}の投稿だ。
140字以内で完結する投稿文を出力しろ。途中で切れる文章は禁止。投稿文のみを出力。""",

    "ツール紹介": f"""{P['genre']}で役立つAIツールや転職サービスを紹介する投稿を作れ。
・具体的なツール名・サービス名を必ず入れろ。
・「使う前は◯だったが、使ったら◯になった」のBefore/After形式か、「◯分でできる」など時短効果を数字で示せ。
・{P['positioning']}の視点で「なぜターゲットに合うか」を一言添えろ。
{{phase_context}}Day{{day_number}}の投稿だ。
140字以内で完結する投稿文を出力しろ。途中で切れる文章は禁止。投稿文のみを出力。""",

    "マインドセット": f"""{P['genre']}に関するマインドセットを語れ。
ターゲット: {P['target']}
・最初の1行は「転職を迷っている人あるある」の共感フックから始めろ。
・「◯ヶ月前の自分」「◯年後の自分」など時間軸を使うと刺さりやすい。
・説教にならず「自分もそうだった→でも◯で変わった」の流れで語れ。
{{phase_context}}Day{{day_number}}の投稿だ。
140字以内で完結する投稿文を出力しろ。途中で切れる文章は禁止。投稿文のみを出力。""",
}


def get_phase_context(day_number: int) -> str:
    if day_number <= 7:
        return "【フェーズ：価値提供期】読者がすぐ使える情報を全力で出す時期。押しつけず、共感と気づきを与えることを最優先にしろ。"
    elif day_number <= 14:
        return "【フェーズ：権威性構築期】具体的な数字・事例・Before/Afterで信頼を積む時期。「この人は本物だ」と感じさせろ。"
    elif day_number <= 21:
        return "【フェーズ：期待感醸成期】「次も読みたい」「もっと知りたい」と思わせる時期。続きを予感させる終わり方や、シリーズ感を出せ。"
    else:
        return "【フェーズ：行動喚起期】読者の背中を強く押す時期。「今日から◯だけやれ」「まず1つだけ動こう」など具体的な小さな一歩を提示しろ。"


def select_category_for_slot(time_slot: str, day_number: int) -> str:
    available, weights = [], []
    for cat, info in POST_CATEGORIES.items():
        if time_slot in info["time_slots"]:
            available.append(cat)
            weights.append(info["weight"])
    if not available:
        available = list(POST_CATEGORIES.keys())
        weights = [i["weight"] for i in POST_CATEGORIES.values()]
    return random.choices(available, weights=weights, k=1)[0]


def build_prompt(category: str, day_number: int) -> str:
    phase_context = get_phase_context(day_number)
    template = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["ノウハウ・Tips"])
    return template.format(day_number=day_number, phase_context=phase_context)
