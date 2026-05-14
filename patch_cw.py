#!/usr/bin/env python3
# Collect Wings — index.html パッチスクリプト
# 使い方: python3 patch_cw.py index.html
# 出力:   index_patched.html

import sys, re, os

if len(sys.argv) < 2:
    print("Usage: python3 patch_cw.py index.html")
    sys.exit(1)

src = sys.argv[1]
dst = os.path.splitext(src)[0] + "_patched.html"

with open(src, encoding="utf-8") as f:
    html = f.read()

errors = []

# ────────────────────────────────────────
# PATCH 1: サイドバー「統計」ナビ削除
# ────────────────────────────────────────
p1_old = r'    <div class="ni" id="ni-stat" onclick="sw\(\'stat\'\)"><svg class="nico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1\.4"><path d="M2 12V8h3v4H2zM6\.5 12V5h3v7h-3zM11 12V2h3v10h-3z"/></svg>統計</div>\n'
if re.search(p1_old, html):
    html = re.sub(p1_old, '', html)
    print("[OK] PATCH 1: 統計ナビ削除")
else:
    errors.append("PATCH 1: 統計ナビが見つかりません")

# ────────────────────────────────────────
# PATCH 2: STATISTICSパネル削除
# ────────────────────────────────────────
p2_old = (
    "    <!-- STATISTICS -->\n"
    "    <div class=\"panel\" id=\"panel-stat\">\n"
    "      <div id=\"stat-content\"></div>\n"
    "    </div>\n"
)
if p2_old in html:
    html = html.replace(p2_old, '')
    print("[OK] PATCH 2: STATISTICSパネル削除")
else:
    errors.append("PATCH 2: STATISTICSパネルが見つかりません")

# ────────────────────────────────────────
# PATCH 3: ATS配列から 'stat' 削除
# ────────────────────────────────────────
p3_old = "const ATS=['songs','cons','cast','xr','att','stat','lib','sched','add','tips'];"
p3_new = "const ATS=['songs','cons','cast','xr','att','lib','sched','add','tips'];"
if p3_old in html:
    html = html.replace(p3_old, p3_new)
    print("[OK] PATCH 3: ATS配列修正")
else:
    errors.append("PATCH 3: ATS配列が見つかりません")

# ────────────────────────────────────────
# PATCH 4: PT辞書から stat:'統計', 削除
# ────────────────────────────────────────
p4_old = "att:'出欠一覧',stat:'統計',lib:'楽曲を追加'"
p4_new = "att:'出欠一覧',lib:'楽曲を追加'"
if p4_old in html:
    html = html.replace(p4_old, p4_new)
    print("[OK] PATCH 4: PT辞書修正")
else:
    errors.append("PATCH 4: PT辞書が見つかりません")

# ────────────────────────────────────────
# PATCH 5: rCur関数から rStat() 分岐削除
# ────────────────────────────────────────
p5_old = "else if(curTab==='att')rAtt();else if(curTab==='stat')rStat();else if(curTab==='lib')"
p5_new = "else if(curTab==='att')rAtt();else if(curTab==='lib')"
if p5_old in html:
    html = html.replace(p5_old, p5_new)
    print("[OK] PATCH 5: rCur関数修正")
else:
    errors.append("PATCH 5: rCur関数が見つかりません")

# ────────────────────────────────────────
# PATCH 6: Vcapモーダル削除
# ────────────────────────────────────────
p6_old = (
    "\n<!-- Vcap Modal (会場キャパ設定) -->\n"
    "<div class=\"settings-modal\" id=\"vcap-modal\" onclick=\"if(event.target===this)closeVcapModal()\">\n"
    "  <div class=\"settings-box\" style=\"max-width:420px;\">\n"
    "    <div class=\"settings-hdr\"><span class=\"settings-hdr-t\">⚙ 会場キャパシティ設定</span><button class=\"settings-close\" onclick=\"closeVcapModal()\">✕</button></div>\n"
    "    <div class=\"settings-body\" id=\"vcap-modal-body\">\n"
    "      <p style=\"font-size:11px;color:var(--text3);margin-bottom:10px;\">公演に紐づいた会場ごとにキャパ数を設定します。</p>\n"
    "      <div id=\"vcap-modal-rows\"></div>\n"
    "    </div>\n"
    "    <div style=\"padding:12px 18px;border-top:1px solid var(--line);display:flex;justify-content:flex-end;\">\n"
    "      <button class=\"btn btn-a\" onclick=\"closeVcapModal()\">確定</button>\n"
    "    </div>\n"
    "  </div>\n"
    "</div>\n"
)
if p6_old in html:
    html = html.replace(p6_old, '\n')
    print("[OK] PATCH 6: Vcapモーダル削除")
else:
    errors.append("PATCH 6: Vcapモーダルが見つかりません")

# ────────────────────────────────────────
# PATCH 7: STATISTICS JS関数群削除
# ────────────────────────────────────────
# VCAP_KEY〜rStatChips関数の末尾までを削除
p7_pat = r"const VCAP_KEY='cw_vcap_v1';.*?^function rStatChips\(\)\{.*?^\}"
m = re.search(p7_pat, html, re.MULTILINE | re.DOTALL)
if m:
    html = html[:m.start()] + html[m.end():]
    print("[OK] PATCH 7: STATISTICS JS関数群削除")
else:
    errors.append("PATCH 7: STATISTICS JS関数群が見つかりません（手動削除が必要な場合あり）")

# ────────────────────────────────────────
# PATCH 8: cSum関数 — MBR配列順に修正
# ────────────────────────────────────────
p8_old = (
    "function cSum(c){\n"
    "  // Returns array of {name, color, unitColor}\n"
    "  const res=[];const seen=new Set();\n"
    "  Object.entries(c.castPresent||{}).forEach(([ch,v])=>{\n"
    "    if(!v)return;\n"
    "    const m=MBR.find(x=>x.ch===ch);\n"
    "    if(m&&!seen.has(ch)){seen.add(ch);res.push({name:mname(m),color:m.c,unitColor:UNITS.find(x=>x.id===m.u)?.color||'#888'});}\n"
    "  });"
)
p8_new = (
    "function cSum(c){\n"
    "  // Returns array of {name, color, unitColor} — MBR配列順（イルミネ→…→コメティック）\n"
    "  const res=[];const seen=new Set();\n"
    "  const cp=c.castPresent||{};\n"
    "  MBR.filter(m=>m.u!=='other').forEach(m=>{\n"
    "    if(!cp[m.ch])return;\n"
    "    if(!seen.has(m.ch)){seen.add(m.ch);res.push({name:mname(m),color:m.c,unitColor:UNITS.find(x=>x.id===m.u)?.color||'#888'});}\n"
    "  });"
)
if p8_old in html:
    html = html.replace(p8_old, p8_new)
    print("[OK] PATCH 8: cSum関数修正")
else:
    errors.append("PATCH 8: cSum関数が見つかりません")

# ────────────────────────────────────────
# 結果出力
# ────────────────────────────────────────
if errors:
    print("\n⚠️  以下のパッチが適用できませんでした:")
    for e in errors:
        print("  -", e)
else:
    print("\n✅ 全パッチ適用完了")

with open(dst, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"出力: {dst}")
