"""共通の仕組み：制御トークン の図。引数: 出力 SVG（paper-crops/ を SVG と同じ場所に置く）"""
import sys
from figlib import *

W = 1800
f = Fig(W, 2510)
f.text(50, 62, "共通の仕組み：制御トークン", 36, DARK, "bold")

# ================= 上: トークンと使う場面 =================
f.rect(40, 100, 1720, 460, GRAY, "#fafafa", r=18)
f.text(70, 148, "Qwen の語彙に専用のトークンを5つ足す（どれも 1 トークン）。モデルはまずこれを 1 つ出し、必要なら続けて文章を出す", 23, DARK, "bold")
cols = [(380, "A", "記録づくり", BLUE), (520, "A", "回答", BLUE), (660, "B", "Proactive QA", GREEN), (800, "B", "Interaction", GREEN)]
for x, a, b, c in cols:
    f.text(x + 65, 196, a, 20, c, "bold", "middle")
    f.text(x + 65, 222, b, 18, c, "bold", "middle")
use = {"Silence": (1, 0, 1, 1), "Observe": (1, 0, 0, 0), "Summary": (1, 0, 0, 0),
       "Standby": (0, 0, 1, 0), "Response": (0, 0, 1, 1)}
mean = {"Silence": "黙る", "Observe": "細部を書く", "Summary": "まとめる", "Standby": "待つ", "Response": "答える"}
for i, n in enumerate(("Silence", "Observe", "Summary", "Standby", "Response")):
    y = 244 + i * 52
    f.rect(60, y - 4, 900, 48, "#e5e7eb", "#ffffff" if i % 2 else "#f3f4f6", r=6, sw=1)
    f.token(165, y, n, w=180, size=18)
    f.text(275, y + 28, mean[n], 21, DARK, "bold")
    for (x, *_), u in zip(cols, use[n]):
        if u:
            f.add(f'<circle cx="{x + 65}" cy="{y + 20}" r="11" fill="{TOKEN_COLOR[n]}"/>')
        else:
            f.text(x + 65, y + 27, "–", 20, "#c0c4cc", "normal", "middle")
f.text(70, 528, "A の回答では制御トークンを使わず、答えを直接出す", 20, BLUE, "bold")

# 右: 各列の意味
DX = 1000
f.text(DX, 200, "それぞれの場面", 22, DARK, "bold")
desc = [("A 記録づくり", "質問を知らないまま、見たことを記録に書く", BLUE),
        ("A 回答", "質問が来たら、記録と直近の映像で 1 回答える", BLUE),
        ("B Proactive QA", "先に質問を受け、証拠がそろったら 1 回答える", GREEN),
        ("B Interaction", "先に指示を受け、新しい証拠が出るたびに", GREEN),
        ("", "何度も答える（数え上げ・手順の実況など）", GREEN)]
for i, (a, b, c) in enumerate(desc):
    y = 244 + i * 52 + 28
    if a:
        f.text(DX, y, a, 20, c, "bold")
    f.text(DX + 180, y, b, 19, DARK)

# ================= 中: 論文の例 =================
EY = 590
f.rect(40, EY, 1720, 1380, GRAY, "#ffffff", r=18)
f.text(70, EY + 50, "論文の例（図6・図11 から切り出し）", 26, DARK, "bold")
ex = [("paper-crops/fig6-top-memory.png", 2002, 443, "A：見ながら記録を書き（Observe・Summary）、後から来た質問に記録で答える（図6 上段）", BLUE,
       "※ 論文のデモでは &lt;/Response&gt; を付けて答えている。評価の回答では制御トークンを使わない"),
      ("paper-crops/fig11-row3-proactive-qa.png", 2002, 375, "B Proactive QA：先に質問。黙る → 証拠が出始めたら待つ → 答える（図11 の 3 段目）", GREEN, None),
      ("paper-crops/fig6-bottom-counting.png", 2002, 456, "B Interaction：先に指示。新しい証拠が出るたびに答える（図6 下段、数え上げ）", GREEN, None)]
iw = 1640
y = EY + 80
for path, w0, h0, label, c, note in ex:
    f.text(80, y + 26, label, 22, c, "bold")
    ih = iw * h0 / w0
    f.add(f'<image x="80" y="{y + 40}" width="{iw}" height="{ih:.0f}" href="{path}"/>')
    y += 40 + ih
    if note:
        f.text(80, y + 24, note, 18, GRAY)
        y += 30
    y += 26

# ================= 下: 窓 =================
WY = 2000
f.rect(40, WY, 1720, 440, GRAY, "#fafafa", r=18)
f.text(70, WY + 50, "モデルが見られる範囲は窓で決まっている（A でも B でも同じ）", 26, DARK, "bold")
f.text(70, WY + 86, "新しい 1 秒の映像が入ると窓がずれ、窓から外れた一番古い映像とそのときの返事は、モデルから見えなくなる（窓を 32 秒とした例）", 20, DARK)

slots = ["1", "2", "3", None, "31", "32", "33"]
sx, sw, sg = 330, 150, 20


def slot_x(i):
    return sx + i * (sw + sg)


def row(y, t_label, visible_from, show_upto, new_idx=None):
    f.text(70, y + 50, t_label, 22, DARK, "bold")
    for i, s in enumerate(slots):
        x = slot_x(i)
        if s is None:
            f.text(x + sw / 2, y + 44, "…", 30, GRAY, "bold", "middle")
            continue
        if i > show_upto:
            f.rect(x, y + 6, sw, 54, "#c0c4cc", "none", r=6, sw=2, dash="6 5")
            f.text(x + sw / 2, y + 40, "まだ来ていない", 16, "#9ca3af", "normal", "middle")
            continue
        op = 1 if i >= visible_from else 0.3
        fill = "#7cc29b" if i == new_idx else "#9aa3b5"
        f.rect(x, y + 6, sw * 0.48, 54, DARK, fill, r=4, sw=2, opacity=op)
        f.text(x + sw * 0.24, y + 40, f"{s}秒", 17, "#ffffff", "bold", "middle", opacity=op)
        f.rect(x + sw * 0.53, y + 13, sw * 0.47, 40, GRAY, "#ffffff", r=6, sw=2, opacity=op)
        f.text(x + sw * 0.765, y + 39, "返事", 16, DARK, "normal", "middle", opacity=op)
    x1 = slot_x(visible_from) - 10
    last = min(show_upto, len(slots) - 1)
    x2 = slot_x(last) + sw + 10
    f.rect(x1, y - 6, x2 - x1, 78, BLUE, "none", r=10, sw=3.5)
    f.text(x1 + 8, y - 14, "窓（直近 32 秒）", 19, BLUE, "bold")
    if visible_from > 0:
        f.text(slot_x(0) + sw / 2, y + 96, "見えない", 18, GRAY, "bold", "middle")
    if new_idx is not None:
        f.text(slot_x(new_idx) + sw / 2, y + 96, "新しく入った", 18, GREEN, "bold", "middle")


row(WY + 130, "32 秒の時点", 0, 5)
row(WY + 260, "33 秒の時点", 1, 6, new_idx=6)
f.text(70, WY + 412, "A の記録（Observe・Summary）は会話とは別に保存されていて、回答のときに使う。B で残るのは質問の文だけ", 19, DARK)

f.text(50, 2476, "※ 窓で古い部分が見えなくなるのは公式コードの動き（論文には書かれていない）。論文の図は Zeng et al., arXiv 2610.01762（CC BY 4.0）より", 19, GRAY)
f.save(sys.argv[1])
