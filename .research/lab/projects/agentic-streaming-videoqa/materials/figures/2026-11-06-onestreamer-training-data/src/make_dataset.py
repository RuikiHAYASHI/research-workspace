"""OneStreamer-1M の中身（4 つの族）の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1180)
f.text(50, 62, "データ：OneStreamer-1M の中身（表6・表5、付録 B.1）", 36, DARK, "bold")
f.text(50, 104, "1,160,004 件 = 新しく作った OneStreamer-Core 272,620 件 + 既存の公開データ（Streamo・JoyAI・StreamForest など）を共通の形式に直した 887,384 件", 21, DARK)

fam = [("Proactive Caption Memory", 60000, 60000, "記録づくり（見ながら記録を書く）",
        ["Silence", "Observe", "Summary"], "最後に「全体を要約して」→ Response", "上（記録）", BLUE),
       ("Proactive Interaction", 271570, 7941, "1 つの指示に何度も答える（数え上げ・連続した説明・リマインドなど）",
        ["Silence", "Response"], "Standby は使わない", "書かれていない", GRAY),
       ("Proactive QA", 197584, 47683, "先に来た質問に、答えられる時刻で 1 回答える",
        ["Silence", "Standby", "Response"], "", "下（QA）ほぼ確か", GREEN),
       ("Perception &amp; Memory QA", 630850, 156996, "知覚と記憶の QA（一般・空間・時間・数え上げ・未来予測・手順など）",
        [], "表5 に載っていない（論文では書かれていない）", "書かれていない", GRAY)]
BX, BW = 430, 760
mx = 630850
Y = 150
f.text(BX, Y + 10, "件数（濃い色 = Core、薄い色 = 既存の公開データ）", 19, GRAY, "bold")
f.text(1230, Y + 10, "Core を作った手順（図5）", 19, GRAY, "bold")
for i, (name, tot, core, what, toks, tnote, pipe, pc) in enumerate(fam):
    y = Y + 40 + i * 205
    f.rect(40, y - 10, 1720, 190, "#e5e7eb", "#ffffff" if i % 2 else "#fafafa", r=14, sw=1.5)
    f.text(60, y + 32, name, 24, DARK, "bold")
    f.text(60, y + 64, f"{tot:,} 件", 21, DARK)
    f.text(60, y + 92, f"うち Core {core:,}", 18, GRAY)
    w = BW * tot / mx
    wc = BW * core / mx
    f.rect(BX, y + 8, w, 40, "#c7cbd6", "#e3e6ee", r=4, sw=1)
    f.rect(BX, y + 8, max(wc, 4), 40, "#4b5563", "#4b5563", r=4, sw=0)
    f.text(BX, y + 92, what, 20, DARK)
    # トークン
    tx = BX
    f.text(tx, y + 140, "制御トークン：", 19, DARK, "bold")
    tx += 140
    for n in toks:
        f.token(tx + 66, y + 112, n, w=128, size=15)
        tx += 140
    if tnote:
        f.text(tx + 6, y + 140, tnote, 18, DARK)
    f.rect(1230, y + 8, 500, 46, pc, "#ffffff", r=10, sw=2.5)
    f.text(1480, y + 39, pipe, 21, pc, "bold", "middle")
f.text(1230, Y + 40 + 90, "§4.1、付録 B.1", 17, GRAY)
f.text(1230, Y + 40 + 205 + 90, "[AI] 数え上げは下の可能性", 17, GRAY)
f.text(1230, Y + 40 + 410 + 90, "§4.2 の最後の形と同じ。明記した文はない", 17, GRAY)
f.text(1230, Y + 40 + 615 + 90, "[AI] 下の可能性はある", 17, GRAY)

NY = Y + 40 + 4 * 205 + 10
f.text(50, NY, "・学習の手順は 4 族とも同じ（同じ SFT・同じ損失）。違うのは系列の中身と PSTL のアンカーだけ", 20, DARK)
f.text(50, NY + 34, "・これとは別に LLaVA-Video のオフライン動画データも混ぜる（§5）。実際に読み込んだのは 991,773 件、詰めた後の系列は 150,261 本（表7）", 20, DARK)
f.text(50, NY + 68, "・既存データの分は図5 の手順を通らず、公開データを共通の形式に直したもの（直し方は書かれていない）", 20, DARK)
f.text(50, NY + 110, "※ Core の件数は表6 から AI が族ごとに足した値。公開版（Hugging Face）では Perception &amp; Memory QA は制御トークンを使わず、質問の時刻に答えるだけの形（2026-11-06 に 1 件で確認）", 18, GRAY)
f.save(sys.argv[1])
