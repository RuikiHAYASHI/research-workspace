"""共通の仕組み：制御トークン の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1040)
f.text(50, 62, "共通の仕組み：制御トークン", 36, DARK, "bold")

# ---- 左: 5 つの専用トークン ----
f.rect(40, 100, 560, 470, GRAY, "#fafafa", r=18)
f.text(70, 150, "Qwen の語彙に専用のトークンを5つ足す", 25, DARK, "bold")
f.text(70, 186, "どれも 1 トークンとして登録されている", 21, GRAY)
rows = [("Silence", "黙る"), ("Observe", "細部を書く"), ("Summary", "まとめる"),
        ("Standby", "待つ"), ("Response", "答える")]
for i, (n, s) in enumerate(rows):
    y = 222 + i * 66
    f.token(200, y, n, w=200, size=21)
    f.text(330, y + 29, s, 25, DARK, "bold")

# ---- 右: 1 回の出力 ----
f.rect(640, 100, 1120, 470, GRAY, "#fafafa", r=18)
f.text(670, 150, "モデルはまずトークンを1つ出し、必要なら続けて文章を出す", 25, DARK, "bold")
f.rect(680, 250, 290, 150, BLUE, "#ffffff", r=14, sw=2.5)
f.text(825, 298, "入力", 24, BLUE, "bold", "middle")
f.text(825, 336, "直近の映像", 21, DARK, "normal", "middle")
f.text(825, 368, "＋ これまでの会話", 21, DARK, "normal", "middle")
f.arrow(974, 325, 1036, 325, DARK)
f.rect(1042, 270, 200, 110, DARK, DARK, r=14)
f.text(1142, 334, "OneStreamer", 25, "#ffffff", "bold", "middle")
f.path_arrow("M1246,325 L1280,325 L1280,240 L1306,240", DARK, 3)
f.path_arrow("M1280,325 L1306,325", DARK, 3)
f.path_arrow("M1280,325 L1280,410 L1306,410", DARK, 3)
f.text(1310, 210, "出力の例", 20, GRAY)
outs = [(240, "Silence", "（文は続かない）", GRAY), (325, "Observe", "細部の文…", DARK),
        (410, "Response", "答えの文…", DARK)]
for y, n, s, c in outs:
    f.token(1380, y - 20, n, w=150, size=18)
    f.text(1470, y + 8, s, 21, c)
f.text(670, 520, "トークンの種類で、文章を続けるかが決まる（Observe・Summary・Response は文章が続く）", 21, GRAY)

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
f.text(900, 912, "Observe・Summary の返事は、記録として別に保存される（窓から外れても消えない）", 21, BLUE, "bold", "middle")
for i in (1, 3, 5):
    x = x0 + i * 205 + 146
    f.arrow(x, y0 + 92, x, 870, BLUE, 2.5)

f.text(50, 990, "※ 窓の長さや、1 回に届く映像（clip）の長さはベンチマークによって違う", 21, DARK)
f.text(50, 1024, "※ 窓から外れた返事が見えなくなるのは公式コードの動き。論文（§3.2・付録 A.2）は「記録は後の予測で使える」と書いている", 21, RED)
f.save(sys.argv[1])
