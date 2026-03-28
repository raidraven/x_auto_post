// バックエンドAPIクライアント
const ApiClient = (() => {
  function _headers() {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${LiffManager.getIdToken()}`,
    };
  }

  // チャットメッセージ送信（ストリーミング）
  // onChunk(text): チャンクが届くたびに呼ばれる
  // onDone(): 完了時
  async function chatStream({ messages, moodScore, currentGoal, onChunk, onDone }) {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: _headers(),
      body: JSON.stringify({
        messages,
        mood_score: moodScore || "未記録",
        current_goal: currentGoal || "未設定",
      }),
    });

    if (!resp.ok) throw new Error(`API error: ${resp.status}`);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      onChunk(chunk);
    }

    onDone();
  }

  // 気分記録保存
  async function saveMood(score, note = "") {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/api/mood`, {
      method: "POST",
      headers: _headers(),
      body: JSON.stringify({ score, note }),
    });
    return resp.json();
  }

  return { chatStream, saveMood };
})();
