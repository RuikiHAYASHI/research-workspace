"""共通の仕組み：制御トークン の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1050)
f.text(50, 62, "共通の仕組み：制御トークン", 36, DARK, "bold")

# ---- 左: 5 つの専用トークンと、どの状況で使うか ----
f.rect(40, 100, 960, 470, GRAY, "#fafafa", r=18)
f.text(70, 148, "Qwen の語彙に専用のトークンを5つ足す（どれも 1 トークン）", 25, DARK, "bold")
f.text(70, 182, "使うトークンは状況によって違う", 21, GRAY)
cols = [(70, ""), (260, ""), (420, "A\n記録づくり"), (600, "A\n回答"), (780, "B\n待ち受けて答える")]
for x, h in cols[2:]:
    a, b = h.split("\n")
    c = BLUE if a == "A" else GREEN
    f.text(x + 65, 214, a, 20, c, "bold", "middle")
    f.text(x + 65, 240, b, 18, c, "bold", "middle")
use = {"Silence": (1, 0, 1), "Observe": (1, 0, 0), "Summary": (1, 0, 0),
       "Standby": (0, 0, 1), "Response": (0, 0, 1)}
mean = {"Silence": "黙る", "Observe": "細部を書く", "Summary": "まとめる", "Standby": "待つ", "Response": "答える"}
for i, n in enumerate(("Silence", "Observe", "Summary", "Standby", "Response")):
    y = 262 + i * 52
    f.rect(60, y - 4, 930, 48, "#e5e7eb", "#ffffff" if i % 2 else "#f3f4f6", r=6, sw=1)
    f.token(165, y, n, w=180, size=18)
    f.text(275, y + 28, mean[n], 21, DARK, "bold")
    for (x, _), u in zip(cols[2:], use[n]):
        if u:
            f.add(f'<circle cx="{x + 65}" cy="{y + 20}" r="11" fill="{TOKEN_COLOR[n]}"/>')
        else:
            f.text(x + 65, y + 27, "–", 20, "#c0c4cc", "normal", "middle")
f.text(70, 538, "A の回答：制御トークンを使わず、答えを直接出す", 20, BLUE, "bold")
f.text(560, 538, "B：&lt;/Response&gt; の後に答えの文章を出す", 19, GREEN, "bold")

# ---- 右: 1 回の出力 ----
f.rect(1040, 100, 720, 470, GRAY, "#fafafa", r=18)
f.text(1070, 148, "まずトークンを1つ出し、必要なら続けて文章を出す", 24, DARK, "bold")
f.rect(1090, 180, 620, 58, BLUE, "#ffffff", r=12, sw=2.5)
f.text(1400, 217, "入力：直近の映像 ＋ これまでの会話", 22, BLUE, "bold", "middle")
f.arrow(1400, 240, 1400, 270, DARK)
f.rect(1290, 274, 220, 60, DARK, DARK, r=12)
f.text(1400, 313, "OneStreamer", 23, "#ffffff", "bold", "middle")
f.path_arrow("M1400,336 L1400,356 L1150,356 L1150,394", DARK, 3)
f.text(1180, 386, "出力の例", 18, GRAY)
outs = [(400, "Silence", "（文は続かない）"), (452, "Observe", "細部の文…"), (504, "Response", "答えの文…")]
for y, n, t in outs:
    f.token(1250, y, n, w=170, size=18)
    f.text(1350, y + 28, t, 21, DARK)
f.line(1150, 394, 1150, 524, DARK, 3)
for y, _, _ in outs:
    f.arrow(1150, y + 20, 1160, y + 20, DARK, 3)

# ---- 下: 会話に残る・窓だけ見る ----
f.rect(40, 600, 1720, 360, GRAY, "#fafafa", r=18)
f.text(70, 650, "出した返事は会話に残り、次の入力になる。映像は直近の窓だけ残す", 25, DARK, "bold")
seq = ["Silence", "Observe", "Silence", "Summary", "Silence", "Observe", "Silence"]
x0, uw, y0 = 80, 228, 730
win_from = 3   # ここから窓の中
for i, n in enumerate(seq + [None]):
    x = x0 + i * 205
    op = 0.35 if i < win_from else 1
    f.clip(x, y0, 90, 54, frames=1, opacity=op)
    f.text(x + 45, y0 + 80, "映像", 18, GRAY, "normal", "middle", opacity=op)
    if n:
        c = TOKEN_COLOR[n]
        f.rect(x + 98, y0 + 7, 96, 40, c, "#ffffff", r=8, sw=2.5, opacity=op)
        f.text(x + 146, y0 + 33, f"&lt;/{n}&gt;", 14, c, "bold", "middle", MONO, opacity=op)
        f.text(x + 146, y0 + 80, "返事", 18, GRAY, "normal", "middle", opacity=op)
    else:
        f.text(x + 146, y0 + 36, "→ 今", 22, DARK, "bold", "middle")
# 窓
wx1 = x0 + win_from * 205 - 12
wx2 = x0 + 7 * 205 + 200
f.rect(wx1, y0 - 22, wx2 - wx1, 120, BLUE, "none", r=12, sw=3.5)
f.text((wx1 + wx2) / 2, y0 - 34, "窓：モデルが見る範囲（直近の映像と返事）", 21, BLUE, "bold", "middle")
f.text((x0 + wx1) / 2, y0 - 34, "窓から外れた映像と返事：見えなくなる", 21, GRAY, "bold", "middle")
# 記録として残る
f.rect(80, 875, 1640, 58, BLUE, BLUE_BG, r=12, sw=2.5)
f.text(900, 912, "A の記録づくりでは、Observe・Summary の返事を記録として別に保存する（窓から外れても消えない）", 21, BLUE, "bold", "middle")
for i in (1, 3, 5):
    x = x0 + i * 205 + 146
    f.arrow(x, y0 + 92, x, 870, BLUE, 2.5)

f.text(50, 990, "※ B でも、窓から外れた映像と返事は見えない。残るのは質問の文だけ（B は記録を書かない）", 21, DARK, "bold")
f.text(50, 1024, "※ 窓から外れた返事が見えなくなるのは公式コードの動き。論文（§3.2・付録 A.2）は「記録や対話は後の予測で使える」と書いている", 21, RED)
f.save(sys.argv[1])
