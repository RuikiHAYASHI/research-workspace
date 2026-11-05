"""PSTL の選び方 の図（論文 図4 の例を数え直したもの）。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1250)
f.text(50, 62, "PSTL：状態の損失に入れる位置を選ぶ（§3.3、図4、式1〜3）", 36, DARK, "bold")
f.text(50, 104, "目的：Silence が圧倒的に多いので、全部の位置を教えると「待つ」ばかり覚える。それを抑える。選ぶのは正解の系列だけから（モデルの出力は要らない）", 21, DARK)

seq = ["Silence"] * 5 + ["Standby"] * 3 + ["Response"] + ["Silence"] * 2
ab = {"Silence": "Sil", "Standby": "Stb", "Response": "Res"}
grp = ["－", "Sil→Sil", "Sil→Sil", "Sil→Sil", "Sil→Sil", "Sil→Stb", "Stb→Stb", "Stb→Stb", "Stb→Res", "Res→Sil", "Sil→Sil"]
pick = [0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0]
x0, cw, gap = 230, 128, 12
xs = [x0 + i * (cw + gap) for i in range(len(seq))]
Y = 150
f.text(50, Y + 30, "位置", 20, GRAY, "bold")
f.text(50, Y + 84, "正解", 20, DARK, "bold")
f.text(50, Y + 150, "組（前→今）", 20, DARK, "bold")
f.text(50, Y + 214, "状態の損失", 20, DARK, "bold")
gcol = {"Sil→Sil": "#9aa3b5", "Sil→Stb": ORANGE, "Stb→Stb": "#e3b341", "Stb→Res": GREEN, "Res→Sil": "#7c8bd6", "－": "#d1d5db"}
for i, n in enumerate(seq):
    cx = xs[i] + cw / 2
    f.text(cx, Y + 30, str(i + 1), 19, GRAY, "normal", "middle", MONO)
    f.token(cx, Y + 56, n, w=cw - 8, size=16)
    f.rect(xs[i] + 4, Y + 122, cw - 8, 40, gcol[grp[i]], "#ffffff", r=8, sw=2.5)
    f.text(cx, Y + 149, grp[i], 16, DARK, "bold", "middle", MONO)
    if pick[i]:
        f.add(f'<circle cx="{cx}" cy="{Y + 206}" r="15" fill="{TOKEN_COLOR[n]}"/>')
    else:
        f.text(cx, Y + 214, "外す", 18, "#9ca3af", "bold", "middle")
f.text(xs[8] + cw / 2, Y + 252, "アンカー", 18, GREEN, "bold", "middle")

# ---- 手順 ----
SY = 470
f.rect(40, SY, 1720, 430, BLUE, BLUE_BG, r=18)
f.text(70, SY + 48, "手順", 26, BLUE, "bold")
f.text(80, SY + 98, "①  隣り合う正解の制御トークンの組（前→今）ごとに数える", 22, DARK, "bold")
cnt = [("Sil→Sil", 5), ("Sil→Stb", 1), ("Stb→Stb", 2), ("Stb→Res", 1), ("Res→Sil", 1)]
for i, (g, n) in enumerate(cnt):
    x = 130 + i * 230
    f.rect(x, SY + 116, 200, 44, gcol[g], "#ffffff", r=8, sw=2.5)
    f.text(x + 100, SY + 145, f"{g}：{n} 個", 18, DARK, "bold", "middle", MONO)
f.text(80, SY + 210, "②  q = アンカー（文を書き始める制御トークン）へ入る組の中で一番多い数（式1）", 22, DARK, "bold")
f.text(130, SY + 246, "Proactive QA のアンカーは Response。Response へ入る組は Stb→Res の 1 個だけ → q = 1（系列ごとに 1 つ決まり、全部の組で共有）", 19, DARK)
f.text(80, SY + 296, "③  各組から min(数, q) 個を、重複なしでランダムに選ぶ（式2）", 22, DARK, "bold")
f.text(130, SY + 332, "どの組も 1 個ずつ → 11 個中 5 個（位置 3・6・7・9・10）。アンカーへ入る組は定義から全部残る", 19, DARK)
f.text(80, SY + 382, "④  選んだ位置だけで状態の損失を平均する（式3）", 22, DARK, "bold")
f.text(700, SY + 382, "→ 学習データ全体では、状態トークンの 27.5% だけを教える", 19, DARK)

# ---- 補足 ----
NY = 935
f.text(50, NY, "・外した位置も系列には残り、後ろの予測から見える。損失から外すだけ。文の損失には影響しない。推論では PSTL を使わない", 20, DARK)
f.text(50, NY + 34, "・アンカーはタスクごと：記録づくりは Observe・Summary、Proactive QA と Proactive Interaction は Response（表5）", 20, DARK)

# ---- 表3 ----
TY = NY + 80
f.text(50, TY, "効果（表3。同じデータ・同じ系列で、状態の損失の取り方だけを変えた）", 22, DARK, "bold")
cols = [("状態の損失の取り方", 520), ("教える割合", 200), ("ProactiveVQA", 230), ("OmniMMI", 200), ("OVO-Timing", 200)]
data = [("全部（普通の交差エントロピー）", "100%", "26.1", "30.8", "1.5"),
        ("全部（Focal、Streamo の方法）", "100%", "47.0", "32.8", "26.5"),
        ("ランダムに間引く", "27.5%", "26.6", "27.4", "1.4"),
        ("切り替わりだけ", "18.1%", "46.7", "27.4", "15.3"),
        ("PSTL", "27.5%", "48.7", "36.6", "41.6")]
x = 50
cx = []
for n, w in cols:
    cx.append(x)
    x += w
rh = 26
f.rect(50, TY + 14, x - 50, rh + 4, DARK, DARK, r=4, sw=1)
for (n, w), c in zip(cols, cx):
    f.text(c + 12, TY + 35, n, 17, "#ffffff", "bold")
for r, row in enumerate(data):
    y = TY + 18 + rh * (r + 1)
    best = r == len(data) - 1
    f.rect(50, y, x - 50, rh, "#d1d5db", BLUE_BG if best else ("#ffffff" if r % 2 else "#f5f6f8"), r=0, sw=1)
    for v, c in zip(row, cx):
        f.text(c + 12, y + 20, v, 17, BLUE if best else DARK, "bold" if best else "normal")
f.text(1420, TY + 70, "減らすこと自体ではなく、", 18, DARK, "bold")
f.text(1420, TY + 96, "何を残すかが効く。", 18, DARK, "bold")
f.text(1420, TY + 122, "状態が続く所も教える", 18, DARK, "bold")
f.text(1420, TY + 148, "必要がある（著者）", 18, DARK, "bold")
f.text(1420, TY + 182, "※ 記録づくりへの効果は", 16, GRAY)
f.text(1420, TY + 204, "　測っていない", 16, GRAY)
f.save(sys.argv[1])
