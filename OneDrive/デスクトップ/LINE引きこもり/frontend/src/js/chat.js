const Chat = (() => {
  const MOOD_LABELS = ["", "とてもつらい", "しんどい", "ふつう", "まあまあ", "いい感じ"];
  let messages = [];
  let isStreaming = false;

  const $messages  = () => document.getElementById("messages");
  const $input     = () => document.getElementById("message-input");
  const $sendBtn   = () => document.getElementById("send-btn");

  function init() {
    messages = Storage.getMessages();
    _renderAll();

    // 初回メッセージ（履歴がなければ）
    if (messages.length === 0) {
      const mood = Storage.getTodayMood();
      let greeting;
      if (mood) {
        const label = MOOD_LABELS[mood.score] || "";
        greeting = `こんにちは。今日は「${label}」って記録してくれたんだね。\n何かあった？それとも、ただ話したい感じ？`;
      } else {
        greeting = "こんにちは。私はともこ。\nここに来てくれてよかった。\n今日はどんな気持ちで過ごしてる？";
      }
      _appendAIMessage(greeting);
      messages.push({ role: "assistant", content: greeting });
      Storage.saveMessages(messages);
    }

    // イベント登録
    $sendBtn().addEventListener("click", sendMessage);
    $input().addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    $input().addEventListener("input", _autoResize);
  }

  function _autoResize() {
    const el = $input();
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  function _renderAll() {
    const container = $messages();
    container.innerHTML = "";
    messages.forEach((m) => {
      if (m.role === "assistant") _appendAIMessage(m.content);
      else _appendUserMessage(m.content);
    });
  }

  function _appendUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user";
    div.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="bubble">${_escapeHtml(text)}</div>
    `;
    $messages().appendChild(div);
    _scrollToBottom();
  }

  function _appendAIMessage(text) {
    const div = document.createElement("div");
    div.className = "message ai";
    div.innerHTML = `
      <div class="message-avatar">🌿</div>
      <div class="bubble">${_escapeHtml(text)}</div>
    `;
    $messages().appendChild(div);
    _scrollToBottom();
    return div.querySelector(".bubble");
  }

  function _showTyping() {
    const div = document.createElement("div");
    div.className = "message ai";
    div.id = "typing";
    div.innerHTML = `
      <div class="message-avatar">🌿</div>
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    `;
    $messages().appendChild(div);
    _scrollToBottom();
  }

  function _removeTyping() {
    document.getElementById("typing")?.remove();
  }

  function _scrollToBottom() {
    const el = $messages();
    el.scrollTop = el.scrollHeight;
  }

  function _escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>");
  }

  async function sendMessage() {
    const text = $input().value.trim();
    if (!text || isStreaming) return;

    // ユーザーメッセージ表示
    $input().value = "";
    $input().style.height = "auto";
    _appendUserMessage(text);
    messages.push({ role: "user", content: text });
    Storage.saveMessages(messages);

    // 送信ボタン無効化
    isStreaming = true;
    $sendBtn().disabled = true;

    // タイピングインジケータ
    _showTyping();

    const mood = Storage.getTodayMood();
    const moodScore = mood ? `${MOOD_LABELS[mood.score]}（${mood.score}/5）` : "未記録";
    const currentGoal = Storage.getCurrentGoal();

    // APIコール（ストリーミング）
    let aiText = "";
    let bubble = null;

    try {
      await ApiClient.chatStream({
        messages,
        moodScore,
        currentGoal,
        onChunk(chunk) {
          if (!bubble) {
            _removeTyping();
            bubble = _appendAIMessage("");
          }
          aiText += chunk;
          bubble.innerHTML = _escapeHtml(aiText);
          _scrollToBottom();
        },
        onDone() {
          messages.push({ role: "assistant", content: aiText });
          Storage.saveMessages(messages);
          isStreaming = false;
          $sendBtn().disabled = false;
        },
      });
    } catch (err) {
      _removeTyping();
      _appendAIMessage("ごめん、うまく繋がらなかったみたい。もう一度話しかけてみてね。");
      console.error(err);
      isStreaming = false;
      $sendBtn().disabled = false;
    }
  }

  return { init };
})();
