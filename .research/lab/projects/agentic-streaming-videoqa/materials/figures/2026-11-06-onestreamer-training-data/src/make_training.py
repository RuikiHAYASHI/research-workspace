"""学習の 1 例と損失 の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1230)
f.text(50, 62, "学習：正解の系列を一度に読み、出す側の位置で損失を取る", 36, DARK, "bold")

# ---- 上: 全体 ----
f.rect(40, 95, 1720, 92, GRAY, "#fafafa", r=16)
items = [("Qwen3-VL-4B-Instruct", DARK), ("→", GRAY), ("教師ありの追加学習（SFT）を 1 段・1 回", BLUE), ("→", GRAY), ("OneStreamer-4B", DARK)]
for (s, c), x in zip(items, (70, 345, 395, 850, 900)):
    f.text(x, 136, s, 23, c, "bold")
f.text(70, 170, "全データ（4 つの族 + LLaVA-Video）を混ぜて学習。映像のエンコーダ（ViT）は固定し、projector と LLM を動かす。強化学習はない（§5、表7）", 19, DARK)

# ---- 系列 ----
SY = 225
f.text(50, SY + 20, "学習の 1 例（Proactive QA の正解の系列。データづくりで前もって全部作ってある）", 24, DARK, "bold")
cols = ["Silence", "Silence", "Silence", "Silence", "Standby", "Standby", "Response"]
x0, cw, gap = 330, 140, 14
xs = [x0 + i * (cw + gap) for i in range(len(cols))]
r1, r2, r3 = SY + 110, SY + 200, SY + 290
f.text(60, r1 + 36, "入力（映像）", 21, DARK, "bold")
f.text(60, r2 + 28, "正解の出力", 21, DARK, "bold")
f.text(60, r3 + 30, "損失", 21, DARK, "bold")
# 質問
f.rect(200, r1 - 4, 112, 58, RED, RED_BG, r=10, sw=2.5)
f.text(256, r1 + 33, "質問", 22, RED, "bold", "middle")
for i, n in enumerate(cols):
    f.clip(xs[i], r1, cw, 50, frames=4, fill="#7cc29b" if i >= 4 else "#9aa3b5")
    f.text(xs[i] + cw / 2, r1 + 76, f"{i + 1} 秒", 16, GRAY, "normal", "middle")
    f.token(xs[i] + cw / 2, r2, n, w=cw - 6, size=17)
# 答えの文
ax = xs[-1] + cw + 18
f.rect(ax, r2 - 2, 1760 - ax - 10, 44, GREEN, GREEN_BG, r=8, sw=2.5)
f.text(ax + 10, r2 + 27, "The dough is shaped into a ring.", 15, GREEN, "bold", "start", MONO)
f.text(ax + 10, r1 + 32, "← 証拠が映り始める（緑）", 18, GREEN, "bold")
# 損失の行
sel = {0: "?", 1: "x", 2: "o", 3: "x", 4: "o", 5: "o", 6: "o"}
for i, s in sel.items():
    cx = xs[i] + cw / 2
    if s == "o":
        f.add(f'<circle cx="{cx}" cy="{r3 + 22}" r="15" fill="{TOKEN_COLOR[cols[i]]}"/>')
    elif s == "x":
        f.text(cx, r3 + 32, "外す", 19, "#9ca3af", "bold", "middle")
    else:
        f.text(cx, r3 + 32, "？", 22, "#9ca3af", "bold", "middle")
for k in range(6):
    f.add(f'<circle cx="{ax + 40 + k * 46}" cy="{r3 + 22}" r="12" fill="{GREEN}"/>')
f.text(ax + 155, r3 + 64, "文は全トークン", 18, GREEN, "bold", "middle")
f.text(330, r3 + 78, "状態の損失：PSTL で選んだ位置だけ（ここでは Silence→Silence の組 3 個から 1 個を選ぶ。次の図）。最初の 1 個の扱いは書かれていない", 18, DARK)
f.text(330, r3 + 106, "文の損失：Response の後の答えの文は全部。Observe・Summary の後の記録の文も同じ", 18, DARK)
# 見える範囲（Standby の位置）
bx2 = xs[4] + cw
f.bracket(200, bx2, SY + 78, ORANGE)
f.text(200, SY + 66, "5 秒目の Standby を予測するときに見えるのは、ここまで（質問・1〜5 秒の映像・正解の Silence 4 個）", 19, ORANGE, "bold")

# ---- teacher forcing ----
TY = 680
f.rect(40, TY, 1720, 300, BLUE, BLUE_BG, r=18)
f.text(70, TY + 48, "やり方（teacher forcing、付録 A.1）", 26, BLUE, "bold")
steps = [("①", "モデルは何も生成しない。正解の系列を 1 回で全部読む"),
         ("②", "各位置で「それより前だけ」を見て、次のトークンの確率を出す（予測）。後ろは隠す（因果的なマスク）"),
         ("③", "次の入力には、モデルの予測ではなく正解が入る（2 秒目に Standby を出しそうでも、3 秒目の入力は正解の Silence）"),
         ("④", "正解のトークンの確率が低いほど損失が大きい。選んだ位置の損失をまとめて 1 回更新する")]
for i, (a, s) in enumerate(steps):
    y = TY + 98 + i * 48
    f.text(80, y, a, 22, BLUE, "bold")
    f.text(120, y, s, 21, DARK)
f.text(80, TY + 282, "推論では損失を計算しない。予測から 1 つ選んで出し（生成）、それを次の入力にする、を繰り返すだけ。答えた結果から学ぶ強化学習はしていない", 19, GRAY)

# ---- 損失のまとめ ----
LY = 1020
f.text(50, LY, "損失は 2 種類（§3.3、付録 A.1）", 24, DARK, "bold")
rows = [("文の損失", "Observe・Summary の後の記録の文、Response の後の答えの文の全トークン", "間引かない"),
        ("状態の損失", "制御トークン（Silence・Standby・Observe・Summary・Response）の位置", "PSTL で選んだ位置だけ")]
f.rect(50, LY + 18, 1700, 44, DARK, DARK, r=6, sw=1)
for t, x in (("損失", 64), ("どこに付くか", 264), ("間引くか", 1404)):
    f.text(x, LY + 48, t, 20, "#ffffff", "bold")
for i, (a, b, c) in enumerate(rows):
    y = LY + 62 + i * 44
    f.rect(50, y, 1700, 44, "#d1d5db", "#ffffff" if i % 2 else "#f5f6f8", r=0, sw=1)
    f.text(64, y + 30, a, 20, DARK, "bold")
    f.text(264, y + 30, b, 19, DARK)
    f.text(1404, y + 30, c, 19, DARK, "bold")
f.text(50, LY + 185, "※ 書かれていないこと：2 つの損失の足し合わせ方（重み）、入力側（映像・質問）に損失を付けるか。系列は説明用に簡略化した例", 19, GRAY)
f.save(sys.argv[1])
