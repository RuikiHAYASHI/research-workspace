"""A．質問が来る前から動く（記録づくり → 回答）の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1260)
f.text(50, 62, "A．質問が来る前から動く：記録づくり → 回答", 36, BLUE, "bold")
f.text(50, 100, "OVO-Bench・StreamingBench の評価", 22, GRAY)

# ================= ① 記録づくり =================
PX, PY, PW, PH = 40, 130, 1140, 900
f.rect(PX, PY, PW, PH, BLUE, BLUE_BG, r=20)
f.text(PX + 30, PY + 50, "① 記録づくり（質問を知らないまま書く）", 30, BLUE, "bold")
f.text(PX + 30, PY + 90, "使うトークン：", 22, DARK)
for i, n in enumerate(("Silence", "Observe", "Summary")):
    f.token(PX + 260 + i * 140, PY + 62, n, w=130, size=17)
f.text(PX + 30, PY + 132, "1 秒ごとに 4 枚（4fps）が届き、1 秒に 1 回、トークンを出す", 22, DARK)

# タイムライン: 8 つの 1 秒の clip。最初の 2 つは窓の外
cw, gap, ty = 112, 14, PY + 250
xs = []
x = PX + 40
for i in range(8):
    if i == 2:
        f.text(x + 4, ty + 40, "…", 30, GRAY, "bold")
        x += 46
    xs.append(x)
    op = 0.35 if i < 2 else 1
    f.clip(x, ty, cw, 60, frames=4, opacity=op)
    f.text(x + cw / 2, ty + 88, f"{i + 1}", 18, GRAY, "normal", "middle", MONO, opacity=op)
    x += cw + gap
end = xs[-1] + cw
f.text(end + 8, ty + 128, "（1 つ = 1 秒）", 18, GRAY, "normal", "end")
# 窓
wx1, wx2 = xs[2] - 16, end + 12
f.rect(wx1, ty - 20, wx2 - wx1, 120, BLUE, "none", r=12, sw=3.5)
f.text((wx1 + wx2) / 2, ty - 32, "窓：直近 32 秒（128 枚）だけ見える", 22, BLUE, "bold", "middle")
f.text((PX + 40 + xs[1] + cw) / 2, ty - 32, "32 秒より前", 21, GRAY, "bold", "middle")
f.text((PX + 40 + xs[1] + cw) / 2, ty + 128, "映像も返事も見えない", 19, GRAY, "bold", "middle")
f.text((PX + 40 + xs[1] + cw) / 2, ty + 154, "（記録は残っている）", 19, GRAY, "normal", "middle")

# 出力
outs = ["Silence", "Summary", "Observe", "Silence", "Silence", "Observe", "Summary", "Silence"]
oy = ty + 190
for i, n in enumerate(outs):
    f.rect(xs[i] + 2, oy, cw - 4, 38, TOKEN_COLOR[n], "#ffffff", r=8, sw=2.5, opacity=0.35 if i < 2 else 1)
    f.text(xs[i] + cw / 2, oy + 25, f"&lt;/{n}&gt;", 15, TOKEN_COLOR[n], "bold", "middle", MONO,
           opacity=0.35 if i < 2 else 1)

# Observe の範囲（clip 5〜6）と Summary の範囲（clip 3〜7）
by = oy + 78
f.bracket(xs[4], xs[5] + cw, by, BLUE)
f.text(xs[4] - 10, by + 32, "&lt;/Observe&gt;：見終わったばかりの細部。", 19, BLUE, "bold")
f.text(xs[4] - 10, by + 58, "今の 1 秒だけでなく、少し前から続く出来事も", 19, BLUE)
by2 = by + 100
f.bracket(xs[2], xs[6] + cw, by2, BLUE)
f.text(xs[2], by2 + 32, "&lt;/Summary&gt;：意味のまとまりが終わったら、まとめを書く", 19, BLUE, "bold")
f.text(xs[2], by2 + 58, "付く時刻は、前の &lt;/Summary&gt; の後から今まで（公式コード）", 19, BLUE)
f.text(xs[2], by2 + 84, "見えているのは直近 32 秒だけ", 19, BLUE)

# 記録
MX, MY = PX + 40, PY + 720
f.rect(MX, MY, 1060, 150, DARK, DARK, r=14)
f.text(MX + 24, MY + 40, "記録（時刻付きの文。会話とは別に保存される）", 23, "#ffffff", "bold")
recs = [("2", "Summary", "（前のまとまりのまとめ）"), ("3", "Observe", "（細部の文）"),
        ("5-6", "Observe", "（細部の文）"), ("3-7", "Summary", "（まとまりのまとめ）")]
for i, (t, n, s) in enumerate(recs):
    cx = MX + 24 + (i % 2) * 520
    cy = MY + 84 + (i // 2) * 42
    f.rect(cx, cy - 24, 64, 32, "#e3b341", "#3a3420", r=6, sw=1.5)
    f.text(cx + 32, cy - 1, t, 18, "#e3b341", "bold", "middle", MONO)
    f.text(cx + 78, cy - 1, f"&lt;/{n}&gt;", 17, "#9fb0ff", "bold", "start", MONO)
    f.text(cx + 222, cy - 1, s, 19, "#ffffff")

# ================= ② 回答 =================
QX, QY, QW = 1220, 130, 540
f.rect(QX, QY, QW, PH, RED, "#ffffff", r=20)
f.text(QX + 30, QY + 50, "② 回答（質問の時刻に 1 回）", 30, RED, "bold")
f.rect(QX + 30, QY + 80, 140, 44, RED, RED_BG, r=10, sw=2.5)
f.text(QX + 100, QY + 110, "質問", 23, RED, "bold", "middle")
f.text(QX + 186, QY + 110, "が来た時刻に、新しく入力を作る", 20, DARK)

f.text(QX + 30, QY + 170, "入力", 24, DARK, "bold")
boxes = [("質問の時刻までの記録すべて", "Summary と Observe の両方", BLUE),
         ("直近 16 枚", "1 秒に 1 枚・元の解像度", DARK),
         ("質問", "", RED)]
by = QY + 190
for i, (a, b, c) in enumerate(boxes):
    h = 82 if b else 56
    f.rect(QX + 30, by, 480, h, c, "#ffffff", r=12, sw=2.5)
    f.text(QX + 270, by + 36, a, 22, c, "bold", "middle")
    if b:
        f.text(QX + 270, by + 66, b, 19, DARK, "normal", "middle")
    by += h
    if i < 2:
        f.text(QX + 270, by + 26, "＋", 26, DARK, "bold", "middle")
        by += 36
f.arrow(QX + 270, by + 6, QX + 270, by + 52, DARK)
f.rect(QX + 150, by + 58, 240, 64, DARK, DARK, r=14)
f.text(QX + 270, by + 99, "OneStreamer", 23, "#ffffff", "bold", "middle")
f.arrow(QX + 270, by + 124, QX + 270, by + 166, DARK)
f.rect(QX + 70, by + 172, 400, 60, GREEN, GREEN, r=30)
f.text(QX + 270, by + 210, "答え（選択肢の記号など）", 22, "#ffffff", "bold", "middle")
f.text(QX + 270, by + 262, "制御トークンは使わず、答えを直接出す", 19, DARK, "normal", "middle")

# 記録 → 回答
f.path_arrow(f"M{MX + 1060},{MY + 75} L{QX - 20},{MY + 75} L{QX - 20},{QY + 231} L{QX + 26},{QY + 231}", BLUE, 3)

# ================= 下: 補足 =================
f.text(50, 1070, "・記録が 12,000 トークンを超えたときだけ、質問の単語との重なりなどで選んで減らす（論文に記載なし・公式コード）", 20, DARK)
f.text(50, 1104, "・記録は Observe と Summary の両方を入れる。Observe が効果の大部分を担い、Summary は補う（付録 E.2・表 18）", 20, DARK)
f.text(50, 1138, "・StreamingBench は同じ動画の問題で記録を共有する。OVO-Bench は問題ごとに切った動画なので、問題ごとに記録を作る（公式コード）", 20, DARK)
f.text(50, 1180, "※ 記録づくりの最中に 32 秒より古い自分の記録が見えないのは公式コードの動き。論文（§3.2・付録 A.2）は「記録は後の予測で使える」と書いている", 20, RED)
f.text(50, 1214, "※ clip の番号・記録の中身は説明用の例", 20, GRAY)
f.save(sys.argv[1])
