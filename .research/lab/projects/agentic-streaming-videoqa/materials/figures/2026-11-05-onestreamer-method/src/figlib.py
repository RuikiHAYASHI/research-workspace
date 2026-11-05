"""図を描く小さな道具（SVG の文字列を作る）"""

F = "Noto Sans CJK JP, Noto Sans JP, sans-serif"
MONO = "Noto Sans Mono CJK JP, monospace"
BLUE, BLUE_BG = "#4a5fc1", "#f4f6fd"
GREEN, GREEN_BG = "#2f8f63", "#f1f8f4"
RED, RED_BG = "#c0392b", "#fdf1ef"
ORANGE, ORANGE_BG = "#c9800e", "#fdf7ec"
GRAY, DARK = "#6b7280", "#262a33"
TOKEN_COLOR = {"Silence": GRAY, "Observe": BLUE, "Summary": BLUE, "Standby": ORANGE, "Response": GREEN}


class Fig:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
        self.add("<defs>")
        for c in (BLUE, GREEN, RED, ORANGE, GRAY, DARK):
            self.add(f'<marker id="ah-{c[1:]}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
                     f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
        self.add("</defs>")
        self.add(f'<rect width="{w}" height="{h}" fill="#ffffff"/>')

    def add(self, s):
        self.out.append(s)

    def text(self, x, y, s, size=22, color=DARK, weight="normal", anchor="start", family=F, opacity=1):
        self.add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" opacity="{opacity}">{s}</text>')

    def rect(self, x, y, w, h, stroke, fill, r=16, sw=3, dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" opacity="{opacity}"{d}/>')

    def line(self, x1, y1, x2, y2, color, sw=3, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def arrow(self, x1, y1, x2, y2, color, sw=4):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" '
                 f'marker-end="url(#ah-{color[1:]})"/>')

    def path_arrow(self, d, color, sw=4, dash=None):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{ds} marker-end="url(#ah-{color[1:]})"/>')

    def token(self, cx, y, name, sub=None, w=124, size=17):
        c = TOKEN_COLOR[name]
        self.rect(cx - w / 2, y, w, 40, c, "#ffffff", r=8, sw=2.5)
        self.text(cx, y + 27, f"&lt;/{name}&gt;", size, c, "bold", "middle", MONO)
        if sub:
            self.text(cx, y + 68, sub, 20, DARK, "normal", "middle")

    def bracket(self, x1, x2, y, color, label=None, size=19, up=True):
        """区間を示す角かっこ。up=True なら下向きの足（ラベルは上）"""
        k = 10 if up else -10
        self.add(f'<path d="M{x1},{y + k} L{x1},{y} L{x2},{y} L{x2},{y + k}" fill="none" stroke="{color}" stroke-width="3"/>')
        if label:
            self.text((x1 + x2) / 2, y - 10 if up else y + 28, label, size, color, "bold", "middle")

    def clip(self, x, y, w, h, frames=1, fill="#9aa3b5", opacity=1):
        """1 回に届く映像。frames 枚の小さな画像を並べる"""
        self.rect(x, y, w, h, DARK, DARK, r=4, sw=1, opacity=opacity)
        g = 4
        fw = (w - g * (frames + 1)) / frames
        for i in range(frames):
            self.rect(x + g + i * (fw + g), y + g, fw, h - 2 * g, fill, fill, r=2, sw=0, opacity=opacity)

    def save(self, path):
        self.add("</svg>")
        open(path, "w", encoding="utf-8").write("\n".join(self.out))
