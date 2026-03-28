const Mood = (() => {
  const MOODS = [
    { score: 1, icon: "😔", label: "とてもつらい" },
    { score: 2, icon: "😞", label: "しんどい" },
    { score: 3, icon: "😐", label: "ふつう" },
    { score: 4, icon: "🙂", label: "まあまあ" },
    { score: 5, icon: "😊", label: "いい感じ" },
  ];

  let selectedScore = null;

  function init() {
    document.getElementById("mood-btn").addEventListener("click", openModal);
    document.getElementById("mood-close").addEventListener("click", closeModal);
    document.getElementById("mood-save-btn").addEventListener("click", save);
    document.getElementById("mood-overlay").addEventListener("click", (e) => {
      if (e.target.id === "mood-overlay") closeModal();
    });

    _renderMoodOptions();
    _updateHeaderBtn();
  }

  function _renderMoodOptions() {
    const container = document.getElementById("mood-options");
    container.innerHTML = "";
    MOODS.forEach(({ score, icon, label }) => {
      const btn = document.createElement("button");
      btn.className = "mood-btn";
      btn.dataset.score = score;
      btn.innerHTML = `<span class="icon">${icon}</span><span class="label">${label}</span>`;
      btn.addEventListener("click", () => {
        selectedScore = score;
        container.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
      });
      container.appendChild(btn);
    });
  }

  function _updateHeaderBtn() {
    const mood = Storage.getTodayMood();
    const btn = document.getElementById("mood-btn");
    if (mood) {
      const m = MOODS.find(m => m.score === mood.score);
      btn.textContent = m ? m.icon : "気分記録";
    } else {
      btn.textContent = "今日の気分";
    }
  }

  function openModal() {
    selectedScore = null;
    document.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("selected"));
    document.getElementById("mood-note").value = "";

    // 既存の記録があればプリセット
    const today = Storage.getTodayMood();
    if (today) {
      selectedScore = today.score;
      document.getElementById("mood-note").value = today.note || "";
      const btn = document.querySelector(`.mood-btn[data-score="${today.score}"]`);
      btn?.classList.add("selected");
    }

    document.getElementById("mood-overlay").classList.remove("hidden");
  }

  function closeModal() {
    document.getElementById("mood-overlay").classList.add("hidden");
  }

  async function save() {
    if (!selectedScore) {
      alert("気分を選んでね");
      return;
    }
    const note = document.getElementById("mood-note").value.trim();

    Storage.saveMood(selectedScore, note);
    try {
      await ApiClient.saveMood(selectedScore, note);
    } catch (e) {
      // API失敗してもローカル保存は成功しているので続行
      console.warn("Mood API save failed:", e);
    }

    _updateHeaderBtn();
    closeModal();
  }

  return { init };
})();
