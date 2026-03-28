// localStorageを使ったシンプルな永続化
const Storage = (() => {
  const KEYS = {
    MESSAGES: "hikky_messages",
    MOOD: "hikky_mood_today",
    GOAL: "hikky_current_goal",
  };

  function getMessages() {
    try {
      return JSON.parse(localStorage.getItem(KEYS.MESSAGES) || "[]");
    } catch { return []; }
  }

  function saveMessages(messages) {
    // 最大40件まで保持
    const trimmed = messages.slice(-40);
    localStorage.setItem(KEYS.MESSAGES, JSON.stringify(trimmed));
  }

  function getTodayMood() {
    try {
      const data = JSON.parse(localStorage.getItem(KEYS.MOOD) || "null");
      if (!data) return null;
      // 日付が変わっていたらクリア
      if (data.date !== new Date().toDateString()) {
        localStorage.removeItem(KEYS.MOOD);
        return null;
      }
      return data;
    } catch { return null; }
  }

  function saveMood(score, note) {
    localStorage.setItem(KEYS.MOOD, JSON.stringify({
      score,
      note,
      date: new Date().toDateString(),
    }));
  }

  function getCurrentGoal() {
    return localStorage.getItem(KEYS.GOAL) || "";
  }

  function saveGoal(goal) {
    localStorage.setItem(KEYS.GOAL, goal);
  }

  return { getMessages, saveMessages, getTodayMood, saveMood, getCurrentGoal, saveGoal };
})();
