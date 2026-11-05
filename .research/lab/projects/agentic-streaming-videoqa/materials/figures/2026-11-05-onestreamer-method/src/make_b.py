"""B．質問が来た後に動く の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1330)
f.text(50, 62, "B．質問が来た後に動く：待ち受けて、答えられるときに答える", 36, GREEN, "bold")
f.text(50, 100, "ProactiveVideoQA・OVO-Timing・ViSpeak・OmniMMI の PA の評価", 22, GRAY)

# ---- 指示文 ----
f.rect(40, 130, 1720, 200, GREEN, GREEN_BG, r=18)
f.text(70, 180, "使うトークンと、指示文（システムプロンプト）での説明", 26, GREEN, "bold")
rows = [("Silence", "出来事が始まっていない（質問と関係がない）"),
        ("Standby", "進行中・まだ答えられない"),
        ("Response", "答えられる → 続けて答えを書く")]
for i, (n, s) in enumerate(rows):
    y = 200 + i * 40
    f.token(170, y, n, w=180, size=18)
    f.text(285, y + 27, "→", 22, DARK, "bold")
    f.text(320, y + 27, s, 22, DARK)
f.text(1000, 228, "答えるタイミングはモデルが決める", 24, DARK, "bold")
f.text(1000, 266, "最初の &lt;/Response&gt; のあとも続けるか、", 21, DARK)
f.text(1000, 298, "どの答えを採点に使うかは、ベンチ（評価コード）が決める", 21, DARK)


def lane(y, title, sub, outs, answers, highlight, note, sub_x):
    f.rect(40, y, 1720, 286, GRAY, "#fafafa", r=18)
    f.text(70, y + 46, title, 26, DARK, "bold")
    f.text(sub_x, y + 46, sub, 21, GRAY)
    cw, gap = 150, 18
    x0 = 210
    f.rect(70, y + 82, 112, 42, RED, RED_BG, r=10, sw=2.5)
    f.text(126, y + 111, "質問", 22, RED, "bold", "middle")
    f.arrow(184, y + 103, x0 - 6, y + 103, RED, 3)
    xs = []
    for i in range(len(outs)):
        x = x0 + i * (cw + gap)
        xs.append(x)
        f.clip(x, y + 74, cw, 58, frames=1, fill="#7cc29b" if i in highlight else "#9aa3b5")
    f.arrow(x0, y + 152, xs[-1] + cw + 20, y + 152, GRAY, 2.5)
    f.text(xs[-1] + cw + 20, y + 176, "時間", 18, GRAY, "normal", "end")
    for i, n in enumerate(outs):
        cx = xs[i] + cw / 2
        f.token(cx, y + 180, n, w=146, size=17)
        if answers.get(i):
            f.rect(cx - 66, y + 226, 132, 34, GREEN, GREEN, r=17)
            f.text(cx, y + 250, answers[i], 19, "#ffffff", "bold", "middle")
    f.text(1745, y + 46, note, 21, GREEN, "bold", "end")


lane(360, "Proactive QA", "証拠がそろったら 1 回答える",
     ["Silence", "Silence", "Standby", "Standby", "Response", "Silence", "Silence", "Silence"],
     {4: "答え"}, (2, 3, 4), "", 260)
f.text((210 + 2 * 168 + 210 + 4 * 168 + 150) / 2, 425, "証拠が映る", 20, GREEN, "bold", "middle")

lane(676, "Proactive Interaction", "新しい証拠が出るたびに何回も答える（数え上げ・手順の実況など）。&lt;/Standby&gt; は使わない（表 5）",
     ["Silence", "Response", "Silence", "Silence", "Response", "Silence", "Response", "Silence"],
     {1: "1 回", 4: "2 回", 6: "3 回"}, (1, 4, 6), "", 370)

# ---- ベンチごとの違い ----
TY = 1010
f.text(50, TY, "ベンチごとの違い（公式コードで確認）", 24, DARK, "bold")
cols = [("ベンチ", 260), ("1 回に届く分", 270), ("窓", 220), ("映像の始まり", 470), ("最初の &lt;/Response&gt; のあと", 400)]
data = [("ProactiveVideoQA", "0.5 秒・1 枚（2fps）", "32 秒（64 枚）", "0 秒（質問も 0 秒から）", "最後まで続ける"),
        ("ViSpeak", "1 秒・1 枚（1fps）", "32 秒（32 枚）", "質問の時刻から", "打ち切る"),
        ("OmniMMI PA", "1 秒・1 枚（1fps）", "32 秒（32 枚）", "0 秒（質問も 0 秒から）", "最後まで続ける（Standby なし）"),
        ("OVO-Timing", "1 秒・4 枚（4fps）", "16 秒（64 枚）", "CRR は質問の時刻から、REC・SSR は 0 秒から", "最後まで続ける")]
x = 50
xs = []
for name, w in cols:
    xs.append(x)
    x += w
rh = 46
y = TY + 20
f.rect(50, y, x - 50, rh, DARK, DARK, r=6, sw=1)
for (name, w), cx in zip(cols, xs):
    f.text(cx + 14, y + 31, name, 20, "#ffffff", "bold")
for r, row in enumerate(data):
    yy = y + rh * (r + 1)
    f.rect(50, yy, x - 50, rh, "#d1d5db", "#ffffff" if r % 2 else "#f5f6f8", r=0, sw=1)
    for v, cx in zip(row, xs):
        f.text(cx + 14, yy + 31, v, 19, DARK, "bold" if cx == xs[0] else "normal")
f.text(50, y + rh * 5 + 40, "※ 映像・出力の並びは説明用の例。指示文はベンチによって少し違う（OmniMMI PA は Silence と Response だけ）", 20, GRAY)
f.save(sys.argv[1])
