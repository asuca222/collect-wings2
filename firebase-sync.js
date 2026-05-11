/**
 * collect-wings Firebase Realtime Database 同期スクリプト
 *
 * 【モード】読み取り専用
 *   - 閲覧者: DBからデータを受信するだけ（書き込み不可）
 *   - 管理者: ブラウザコンソールから cwPush() で手動送信
 *
 * 【導入手順】
 *   1. このファイルをリポジトリルートに置く
 *   2. index.html の </body> 直前に追加:
 *        <script src="firebase-sync.js"></script>
 *   3. Firebase Console > Realtime Database > ルール を以下に設定:
 *        { "rules": { ".read": true, ".write": false } }
 *
 * 【データ更新方法（管理者）】
 *   公演・楽曲を追加・編集したあと、コンソールで cwPush() を実行すると
 *   現在の localStorage の内容を DB に送信します。
 *   ※ セキュリティルールが ".write": false の場合、送信は失敗します。
 *      更新時だけ一時的に ".write": true にして cwPush() → 戻す、でも OK。
 *      または下記「書き込み専用URL」方式を使ってください。
 */

const FIREBASE_CONFIG = {
  apiKey: "AIzaSyCRhF2zTCpxjCz6oykjBs3kfP33elg236o",
  authDomain: "collect-wings-4554a.firebaseapp.com",
  databaseURL: "https://collect-wings-4554a-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "collect-wings-4554a",
  storageBucket: "collect-wings-4554a.firebasestorage.app",
  messagingSenderId: "742463033970",
  appId: "1:742463033970:web:458d69e71467921083e8eb",
  measurementId: "G-WR5YPVVXMS",
};

const CW_KEYS = ["cw_v3", "cw_lib_v1", "cw_vcap_v1"];

// ============================================================
//  Firebase SDK を動的ロード
// ============================================================
function loadFirebaseSDK() {
  return new Promise((resolve, reject) => {
    if (window.__cwFirebaseLoaded) return resolve();
    const scripts = [
      "https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js",
      "https://www.gstatic.com/firebasejs/10.12.2/firebase-database-compat.js",
    ];
    let loaded = 0;
    scripts.forEach((src) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = () => {
        if (++loaded === scripts.length) {
          window.__cwFirebaseLoaded = true;
          resolve();
        }
      };
      s.onerror = reject;
      document.head.appendChild(s);
    });
  });
}

// ============================================================
//  ステータスバッジ
// ============================================================
function createStatusBadge() {
  const el = document.createElement("div");
  el.id = "cw-sync-status";
  el.style.cssText = [
    "position:fixed",
    "bottom:12px",
    "right:12px",
    "padding:4px 12px",
    "border-radius:999px",
    "font-size:11px",
    "font-family:monospace",
    "z-index:99999",
    "pointer-events:none",
    "transition:background 0.3s",
    "opacity:0.88",
    "background:#6b7280",
    "color:#fff",
  ].join(";");
  el.textContent = "☁ DB 接続中…";
  document.body.appendChild(el);
  return el;
}

function setStatus(el, state) {
  const map = {
    connecting: { text: "☁ DB 接続中…",      bg: "#6b7280" },
    ready:      { text: "✓ 最新データ読込済み", bg: "#16a34a" },
    uptodate:   { text: "✓ 同期済み",          bg: "#16a34a" },
    error:      { text: "✗ DB 接続失敗",        bg: "#dc2626" },
  };
  const s = map[state] || map.error;
  el.textContent = s.text;
  el.style.background = s.bg;
}

// ============================================================
//  Firebase のオブジェクト → 配列を復元
//  Firebase は数値キーの配列をオブジェクトに変換することがある
// ============================================================
function restoreArray(obj, key) {
  if (key === "cw_vcap_v1" || obj === null || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj;
  const keys = Object.keys(obj);
  if (keys.length && keys.every((k) => /^\d+$/.test(k))) {
    const arr = [];
    keys.forEach((k) => (arr[parseInt(k)] = obj[k]));
    return arr;
  }
  return obj;
}

// ============================================================
//  DB → localStorage に取り込む
//  戻り値: true = データが更新された
// ============================================================
async function pullFromDB(db) {
  let updated = false;
  for (const key of CW_KEYS) {
    const snap = await db.ref(key).get();
    if (!snap.exists()) continue;
    const val = restoreArray(snap.val(), key);
    const incoming = JSON.stringify(val);
    if (localStorage.getItem(key) !== incoming) {
      localStorage.setItem(key, incoming);
      updated = true;
    }
  }
  return updated;
}

// ============================================================
//  管理者用: localStorage → DB に全送信
//  ブラウザコンソールで cwPush() を実行する
// ============================================================
async function pushToDB(db) {
  console.log("[CW Sync] DB への送信を開始します…");
  let ok = true;
  for (const key of CW_KEYS) {
    const raw = localStorage.getItem(key);
    if (raw === null) {
      console.log(`[CW Sync]   ${key}: データなし（スキップ）`);
      continue;
    }
    try {
      const val = JSON.parse(raw);
      await db.ref(key).set(val);
      console.log(`[CW Sync]   ✓ ${key} 送信完了`);
    } catch (e) {
      console.error(`[CW Sync]   ✗ ${key} 送信失敗:`, e.message);
      ok = false;
    }
  }
  if (ok) {
    console.log("[CW Sync] 全データの送信完了！他の端末に反映されます。");
  } else {
    console.warn("[CW Sync] 一部失敗しました。Firebase のセキュリティルールを確認してください。");
  }
}

// ============================================================
//  メイン
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
  const badge = createStatusBadge();

  try {
    await loadFirebaseSDK();

    if (!firebase.apps.length) {
      firebase.initializeApp(FIREBASE_CONFIG);
    }
    const db = firebase.database();

    // 起動時に DB → localStorage へ取り込み
    const updated = await pullFromDB(db);

    if (updated) {
      // データが変わっていたらリロードしてアプリに反映させる
      // (2回目のロードでは updated=false になるので無限ループにならない)
      console.log("[CW Sync] DBから新しいデータを受信 → ページを再読み込みします");
      setStatus(badge, "ready");
      location.reload();
      return;
    }

    setStatus(badge, "uptodate");

    // 管理者用グローバル関数を登録
    window.cwPush = () => pushToDB(db);
    console.log(
      "[CW Sync] 準備完了。\n" +
      "  公演・楽曲を追加・編集したあとに cwPush() を実行してDBに送信してください。"
    );

  } catch (e) {
    console.error("[CW Sync] 初期化エラー:", e);
    setStatus(badge, "error");
  }
});
