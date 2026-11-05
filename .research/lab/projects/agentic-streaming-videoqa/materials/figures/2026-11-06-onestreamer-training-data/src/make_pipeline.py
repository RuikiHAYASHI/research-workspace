"""データの作り方（図5 の上下）の図。引数: 出力 SVG"""
import sys
from figlib import *

f = Fig(1800, 1330)
f.text(50, 62, "データの作り方：図5 の上下で作るのは Core だけ（§4、付録 B.2・B.3）", 36, DARK, "bold")


def step(x, y, w, h, num, title, lines, c, bg):
    f.rect(x, y, w, h, c, bg, r=14, sw=2.5)
    f.text(x + 18, y + 38, num, 22, c, "bold")
    f.text(x + 64, y + 38, title, 22, c, "bold")
    for i, s in enumerate(lines):
        f.text(x + 18, y + 76 + i * 30, s, 18, DARK)


def out(x, y, w, h, title, sub, c, dash=None):
    f.rect(x, y, w, h, c, "#ffffff", r=14, sw=3, dash=dash)
    f.text(x + w / 2, y + 40, title, 21, c, "bold", "middle")
    f.text(x + w / 2, y + 70, sub, 18, DARK, "normal", "middle")


# ================= 上 =================
UY = 100
f.rect(40, UY, 1720, 330, BLUE, BLUE_BG, r=18)
f.text(70, UY + 46, "上：記録のデータ（図5 の 01〜03）", 26, BLUE, "bold")
sw, sh, sy = 400, 220, UY + 80
step(70, sy, sw, sh, "01", "動画を選ぶ", ["変化が多く、出来事がはっきりした動画", "画質が悪い・静止が長い・暗転・", "カットが多すぎるものは除く"], BLUE, "#ffffff")
step(510, sy, sw, sh, "02", "3 段の注釈と確認", ["Gemini・Seed に時刻付きで書かせる：", "短い区間の細部 / 出来事のまとまり /", "動画全体", "動画と照らして、根拠なし・時刻ずれ・", ][:4], BLUE, "#ffffff")
f.text(528, sy + 196, "食い違いは捨てる", 18, DARK)
step(950, sy, sw, sh, "03", "系列にする", ["細部 → 区間が終わった時刻に Observe", "まとまり → 終わった時刻に Summary", "全体 → 最後の「全体を要約して」に", "　Response"], BLUE, "#ffffff")
for x in (470, 910):
    f.arrow(x + 4, sy + sh / 2, x + 36, sy + sh / 2, BLUE, 3.5)
f.arrow(1354, sy + sh / 2, 1386, sy + sh / 2, BLUE, 3.5)
out(1392, sy + 50, 340, 110, "Proactive Caption Memory", "Core 60,000 件（確か）", BLUE)

# ================= 下 =================
LY = 470
f.rect(40, LY, 1720, 560, GREEN, GREEN_BG, r=18)
f.text(70, LY + 46, "下：QA のデータ", 26, GREEN, "bold")
f.text(380, LY + 46, "（図5 の 04〜06）", 26, GREEN, "bold")
f.text(640, LY + 46, "狙い：早すぎると先入観で答えて幻覚、遅すぎると待ちすぎ。証拠が足りる範囲で一番早く答えさせる", 19, DARK)
sy2, sh2, sw2 = LY + 80, 250, 300
step(70, sy2, sw2, sh2, "04", "QA を作る", ["材料：上で確かめた注釈 +", "既存データの注釈", "能力ごとの型（状態の追跡・", "行動の予測・リマインド・", "数え上げなど）で Gemini・Seed"], GREEN, "#ffffff")
step(410, sy2, sw2, sh2, "05", "証拠区間を決める", ["Gemini・Seed が区間を出す", "その区間の映像だけを", "Qwen3.5-397B に見せて、", "答えられなければ捨てる"], GREEN, "#ffffff")
step(750, sy2, 560, sh2, "06", "答える時刻を決める", ["区間内の 1 秒ごとの候補時刻で「答えられそうか」を点数に", "　推論系：Qwen3.5-9B が正解文を出す確率（直前 4 秒）", "　知覚系：出来事の文と直前 2 秒の映像の近さ", "ならして、最高点から 0.04 以内で一番早い時刻", "その時刻までの映像で答えられなければ捨てる"], GREEN, "#ffffff")
for x in (370, 710):
    f.arrow(x + 4, sy2 + sh2 / 2, x + 36, sy2 + sh2 / 2, GREEN, 3.5)
f.arrow(1314, sy2 + sh2 / 2, 1346, sy2 + sh2 / 2, GREEN, 3.5)
# 系列
f.rect(1352, sy2, 380, sh2, GREEN, "#ffffff", r=14, sw=2.5)
f.text(1370, sy2 + 38, "系列にする", 22, GREEN, "bold")
for i, (n, s) in enumerate((("Silence", "証拠が出る前"), ("Standby", "出始めたら"), ("Response", "決めた時刻に"))):
    f.token(1440, sy2 + 66 + i * 58, n, w=140, size=16)
    f.text(1524, sy2 + 93 + i * 58, s, 18, DARK)
f.text(70, sy2 + sh2 + 200, "[実験] 元の注釈より平均 13.72 秒早まり、86.62% が早まった（付録 B.3）", 19, GREEN, "bold")
# 出力
oy = sy2 + sh2 + 60
out(70, oy, 520, 100, "Proactive QA", "Core 47,683 件（ほぼ確か）", GREEN)
out(620, oy, 1110, 100, "Proactive Interaction・Perception &amp; Memory QA の Core", "どちらで作ったかは書かれていない（[AI] 下の可能性はある）", GRAY, dash="8 6")
f.path_arrow(f"M{1542},{sy2 + sh2} L{1542},{sy2 + sh2 + 20} L{330},{sy2 + sh2 + 20} L{330},{oy - 4}", GREEN, 3)
# 上 → 下
f.path_arrow(f"M{710},{sy + sh} L{710},{LY - 14} L{345},{LY - 14} L{345},{sy2 - 4}", BLUE, 3, dash="9 6")
f.text(730, LY - 20, "確かめた注釈を材料に使う（図5 の 04「Streaming Captions」）", 18, BLUE, "bold")

# ================= 既存データ =================
EY = 1060
f.rect(40, EY, 1720, 130, GRAY, "#fafafa", r=18)
f.text(70, EY + 46, "既存の公開データ（Streamo・JoyAI・ViSpeak・StreamForest・MMDuet2・Seeker・VideoChat-OL・VST）", 23, DARK, "bold")
f.text(70, EY + 88, "上下の手順を通らず、掃除して共通のストリーミング形式に直す → 4 つの族の既存分（887,384 件）。直し方（制御トークンや時刻を付け直したか）は書かれていない", 19, DARK)
f.text(50, EY + 180, "※ 注釈・確認の多くを大きな閉じたモデル（Gemini3.1Pro・Seed2.1Pro）に頼っている。手順の細部は付録 B.2・B.3 にある。族との対応の確かさは論文の書き方から AI が判断", 18, GRAY)
f.text(50, EY + 210, "※ 評価ベンチと同じ元動画を使う学習データは、区間が重ならなくても全部除いた（付録 B.1）", 18, GRAY)
f.save(sys.argv[1])
