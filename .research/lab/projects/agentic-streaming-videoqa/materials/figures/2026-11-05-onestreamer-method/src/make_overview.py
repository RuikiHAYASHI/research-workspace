"""OneStreamer 全体像の図（SVG）を作る。引数: 出力 SVG のパス"""
import sys

W, H = 1800, 1080
F = "Noto Sans CJK JP, Noto Sans JP, sans-serif"
MONO = "Noto Sans Mono CJK JP, monospace"
BLUE, BLUE_BG = "#4a5fc1", "#f4f6fd"
GREEN, GREEN_BG = "#2f8f63", "#f1f8f4"
RED, RED_BG = "#c0392b", "#fdf1ef"
ORANGE, ORANGE_BG = "#c9800e", "#fdf7ec"
GRAY, DARK = "#6b7280", "#262a33"

out = []
def add(s): out.append(s)

def text(x, y, s, size=22, color=DARK, weight="normal", anchor="start", family=F):
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{s}</text>')

def rect(x, y, w, h, stroke, fill, r=16, sw=3, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

def arrow(x1, y1, x2, y2, color, sw=4):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" marker-end="url(#ah-{color[1:]})"/>')

def path_arrow(d, color, sw=4):
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#ah-{color[1:]})"/>')

def film(x, y, n, cw, ch, highlight=(), hl_color=None):
    """フィルム風の映像の帯。clip の中心 x のリストを返す"""
    gap = 8
    total = n * cw + (n + 1) * gap
    add(f'<rect x="{x}" y="{y}" width="{total}" height="{ch + 28}" fill="{DARK}" rx="4"/>')
    for i in range(int(total // 22)):
        add(f'<rect x="{x + 6 + i * 22}" y="{y + 4}" width="12" height="7" fill="#ffffff" rx="1"/>')
        add(f'<rect x="{x + 6 + i * 22}" y="{y + ch + 17}" width="12" height="7" fill="#ffffff" rx="1"/>')
    centers = []
    for i in range(n):
        cx = x + gap + i * (cw + gap)
        fill = "#9aa3b5" if i not in highlight else hl_color
        add(f'<rect x="{cx}" y="{y + 14}" width="{cw}" height="{ch}" fill="{fill}" rx="3"/>')
        centers.append(cx + cw / 2)
    return centers, x + total

def token(cx, y, name, color, sub):
    w = 124
    rect(cx - w / 2, y, w, 40, color, "#ffffff", r=8, sw=2.5)
    text(cx, y + 27, f"&lt;/{name}&gt;", 17, color, "bold", "middle", MONO)
    text(cx, y + 68, sub, 20, DARK, "normal", "middle")

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>")
for c in (BLUE, GREEN, RED, ORANGE, GRAY, DARK):
    add(f'<marker id="ah-{c[1:]}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
add("</defs>")
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---- 上段: 追加学習と指示 ----
rect(50, 40, 290, 116, GRAY, "#f7f7f9")
text(195, 95, "Qwen3-VL-4B", 34, DARK, "bold", "middle")
text(195, 132, "元のモデル", 22, GRAY, "normal", "middle")
arrow(345, 98, 545, 98, DARK)
text(445, 82, "追加学習", 26, DARK, "bold", "middle")
rect(555, 30, 400, 136, DARK, DARK)
text(755, 92, "OneStreamer", 40, "#ffffff", "bold", "middle")
text(755, 135, "1つのモデルの重み", 24, "#ffffff", "normal", "middle")
rect(1010, 40, 740, 116, ORANGE, ORANGE_BG)
text(1040, 88, "どちらで動くかは、最初に渡す指示で決まる", 28, ORANGE, "bold")
text(1040, 128, "モデルが自分で判断するわけではない", 23, DARK)

# 指示から各レーンへ
path_arrow("M700,166 L700,205 L460,205 L460,244", BLUE)
path_arrow("M810,166 L810,205 L1340,205 L1340,244", GREEN)
rect(520, 186, 120, 38, BLUE, "#ffffff", r=19, sw=2.5)
text(580, 213, "指示A", 21, BLUE, "bold", "middle")
rect(1010, 186, 120, 38, GREEN, "#ffffff", r=19, sw=2.5)
text(1070, 213, "指示B", 21, GREEN, "bold", "middle")

# ---- レーン A ----
AX, AY, AW, AH = 40, 250, 840, 740
rect(AX, AY, AW, AH, BLUE, BLUE_BG, r=20)
text(AX + 30, AY + 52, "A．質問が来る前から動く", 34, BLUE, "bold")
text(AX + 30, AY + 92, "動画を見ながら記録を書き溜め、質問が来たら記録を使って答える", 22, DARK)

centers, end_x = film(AX + 40, AY + 170, 5, 130, 58)
for i, cx in enumerate(centers):
    text(cx, AY + 278, f"t{i + 1}", 17, GRAY, "normal", "middle", MONO)
arrow(AX + 40, AY + 282, end_x + 10, AY + 282, GRAY, 2.5)
text(end_x + 8, AY + 310, "時間", 19, GRAY, "normal", "end")
toks = [("Silence", GRAY, "黙る"), ("Observe", BLUE, "細部を書く"), ("Silence", GRAY, "黙る"),
        ("Observe", BLUE, "細部を書く"), ("Summary", BLUE, "まとめる")]
for cx, (n, c, s) in zip(centers, toks):
    token(cx, AY + 324, n, c, s)

# 質問（流れの最後に来る）
qx = end_x + 14
add(f'<line x1="{qx}" y1="{AY + 150}" x2="{qx}" y2="{AY + 265}" stroke="{RED}" stroke-width="4"/>')
rect(qx - 66, AY + 132, 112, 40, RED, RED_BG, r=10, sw=2.5)
text(qx - 10, AY + 160, "質問", 22, RED, "bold", "middle")

# 記録（書き溜めたもの）
MX, MY = AX + 40, AY + 440
rect(MX, MY, 680, 170, DARK, DARK, r=14)
text(MX + 24, MY + 40, "記録（時刻付きの文）", 24, "#ffffff", "bold")
rows = [("t2", "Observe", "見終わったばかりの細部"), ("t4", "Observe", "見終わったばかりの細部"),
        ("t5", "Summary", "終わった出来事のまとめ")]
for i, (t, n, s) in enumerate(rows):
    y = MY + 84 + i * 36
    rect(MX + 22, y - 24, 52, 30, "#e3b341", "#3a3420", r=6, sw=1.5)
    text(MX + 48, y - 2, t, 19, "#e3b341", "bold", "middle", MONO)
    text(MX + 88, y - 2, f"&lt;/{n}&gt;", 18, "#9fb0ff", "bold", "start", MONO)
    text(MX + 238, y - 2, s, 20, "#ffffff")
for cx in (centers[1], centers[3], centers[4]):
    arrow(cx, AY + 402, cx, MY - 4, BLUE, 2.5)

# 回答
BX, BY = AX + 40, AY + 650
rect(BX, BY, 500, 66, BLUE, "#ffffff", r=12, sw=2.5)
text(BX + 250, BY + 42, "記録 ＋ 直近の映像 ＋ 質問", 24, BLUE, "bold", "middle")
arrow(MX + 250, MY + 170, MX + 250, BY - 4, BLUE, 3)
path_arrow(f"M{qx},{AY + 265} L{qx},{MY + 188} L{BX + 440},{MY + 188} L{BX + 440},{BY - 4}", RED, 3)
rect(AX + 572, BY, 240, 66, BLUE, BLUE, r=33)
text(AX + 692, BY + 42, "質問の時刻に1回答える", 21, "#ffffff", "bold", "middle")
arrow(BX + 502, BY + 33, AX + 566, BY + 33, BLUE, 3)

# ---- レーン B ----
BXL, BYL, BWL = 920, 250, 840
rect(BXL, BYL, BWL, AH, GREEN, GREEN_BG, r=20)
text(BXL + 30, BYL + 52, "B．質問が来た後に動く", 34, GREEN, "bold")
text(BXL + 30, BYL + 92, "質問を受け取りながら映像を見続け、", 22, DARK)
text(BXL + 30, BYL + 124, "答えられる証拠がそろった時点で答える", 22, DARK)

centers_b, end_b = film(BXL + 70, BYL + 170, 5, 130, 58, highlight=(1, 2, 3), hl_color="#7cc29b")
qbx = BXL + 62
add(f'<line x1="{qbx}" y1="{BYL + 150}" x2="{qbx}" y2="{BYL + 265}" stroke="{RED}" stroke-width="4"/>')
rect(qbx - 20, BYL + 132, 112, 40, RED, RED_BG, r=10, sw=2.5)
text(qbx + 36, BYL + 160, "質問", 22, RED, "bold", "middle")
text((centers_b[1] + centers_b[3]) / 2, BYL + 160, "証拠が映る", 20, GREEN, "bold", "middle")
arrow(BXL + 70, BYL + 282, end_b + 10, BYL + 282, GRAY, 2.5)
text(end_b + 8, BYL + 310, "時間", 19, GRAY, "normal", "end")
toks_b = [("Silence", GRAY, "黙る"), ("Standby", ORANGE, "待つ"), ("Standby", ORANGE, "待つ"),
          ("Response", GREEN, "答える"), ("Silence", GRAY, "黙る")]
for cx, (n, c, s) in zip(centers_b, toks_b):
    token(cx, BYL + 324, n, c, s)
rect(centers_b[3] - 70, BYL + 432, 140, 46, GREEN, GREEN, r=23)
text(centers_b[3], BYL + 462, "答え", 23, "#ffffff", "bold", "middle")
arrow(centers_b[3], BYL + 404, centers_b[3], BYL + 428, GREEN, 2.5)

# 凡例
LX, LY = BXL + 40, BYL + 500
rect(LX, LY, 760, 200, GRAY, "#ffffff", r=14, sw=2)
leg = [("Silence", GRAY, "まだ関係がない"), ("Standby", ORANGE, "証拠が出始めたが、まだ答えられない"),
       ("Response", GREEN, "答えられるので答える")]
for i, (n, c, s) in enumerate(leg):
    y = LY + 58 + i * 52
    text(LX + 28, y, f"&lt;/{n}&gt;", 21, c, "bold", "start", MONO)
    text(LX + 210, y, s, 22, DARK)

# ---- 下の注記 ----
text(W / 2, 1040, "※ A と B を 1 本の動画で同時に行う評価は行っていない（付録 D）", 26, RED, "bold", "middle")

add("</svg>")
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
