// LIFF初期化とユーザー情報取得
const LiffManager = (() => {
  let _idToken = null;
  let _profile = { displayName: "あなた", pictureUrl: null };

  async function init() {
    if (CONFIG.DEV_MODE) {
      // 開発モード: LIFFなしで動作確認
      _idToken = "dev-token";
      _profile = { displayName: "テストユーザー", pictureUrl: null };
      console.log("[DEV] LIFF init skipped");
      return;
    }

    await liff.init({ liffId: CONFIG.LIFF_ID });

    if (!liff.isLoggedIn()) {
      liff.login();
      return;
    }

    _idToken = liff.getIDToken();
    _profile = await liff.getProfile();
  }

  function getIdToken()     { return _idToken; }
  function getProfile()     { return _profile; }
  function getDisplayName() { return _profile.displayName || "あなた"; }

  return { init, getIdToken, getProfile, getDisplayName };
})();
