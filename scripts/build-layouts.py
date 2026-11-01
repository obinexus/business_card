"""OBINexus MMUCO business card — layout generator (F / Z / T options).

Card: 85 x 55 mm, SVG user units = mm. Black on white only.
Writes <opt>-front.svg / <opt>-back.svg (live text) and *-outlined.svg (text as paths).
"""
import json, re, sys, os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

W, H = 85.0, 55.0
M = 5.0           # working margin (safe margin is 4 mm; we keep 5)
PT = 25.4 / 72    # mm per point
INK = "#000000"

FONTS = {
    "serif":      ("Source Serif 4", "normal", 400, "/root/.fonts/source-serif-4-latin-400-normal.ttf"),
    "sans":       ("Source Sans 3", "normal", 400, "/root/.fonts/source-sans-3-latin-400-normal.ttf"),
    "sans-semi":  ("Source Sans 3", "normal", 600, "/root/.fonts/source-sans-3-latin-600-normal.ttf"),
}
_cache = {}
def font(key):
    if key not in _cache:
        path = FONTS[key][3]
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        _cache[key] = (hb.Font(face), TTFont(path), face.upem)
    return _cache[key]

def shape(text, key, size_pt, tracking=0):
    """Returns (glyph list [(gid, x_mm)], advance width mm). tracking in 1/1000 em."""
    hbf, tt, upem = font(key)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(hbf, buf, {"kern": True, "liga": True})
    s = size_pt * PT / upem
    x = 0.0; glyphs = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        glyphs.append((info.codepoint, x + pos.x_offset * s))
        x += pos.x_advance * s + tracking / 1000 * size_pt * PT
    if tracking and glyphs:
        x -= tracking / 1000 * size_pt * PT  # no trailing tracking
    return glyphs, x

class T:
    """A text line. anchor: start|middle|end. y = baseline (mm)."""
    def __init__(self, text, key, size_pt, x, y, anchor="start", tracking=0, id=None):
        assert size_pt >= 8, f"{text!r} below 8 pt"
        self.text, self.key, self.size, self.x, self.y = text, key, size_pt, x, y
        self.anchor, self.tracking, self.id = anchor, tracking, id
        self.glyphs, self.w = shape(text, key, size_pt, tracking)
        self.x0 = x - {"start": 0, "middle": self.w / 2, "end": self.w}[anchor]
        _, tt, upem = font(key)
        s = size_pt * PT / upem
        self.top = y - tt["hhea"].ascent * s * 0.72   # approx ink top (cap height)
        self.cap = tt["OS/2"].sCapHeight * s
        self.desc = -tt["hhea"].descent * s * 0.62

    def bbox(self):  # approximate ink box (cap height to descender)
        return (self.x0, self.y - self.cap, self.x0 + self.w, self.y + self.desc)

    def live(self):
        fam, style, wt, _ = FONTS[self.key]
        ls = f' letter-spacing="{self.tracking/1000*self.size*PT:.4f}"' if self.tracking else ""
        idattr = f' id="{self.id}"' if self.id else ""
        # x is the left edge so every renderer agrees on placement (no text-anchor ambiguity)
        return (f'<text{idattr} x="{self.x0:.3f}" y="{self.y:.3f}" font-family="{fam}" '
                f'font-weight="{wt}" font-size="{self.size*PT:.4f}"{ls} fill="{INK}" '
                f'xml:space="preserve">{esc(self.text)}</text>')

    def outlined(self):
        _, tt, upem = font(self.key)
        gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
        s = self.size * PT / upem
        ds = []
        for gid, gx in self.glyphs:
            pen = SVGPathPen(gs)
            tp = TransformPen(pen, (s, 0, 0, -s, self.x0 + gx, self.y))
            gs[order[gid]].draw(tp)
            d = pen.getCommands()
            if d: ds.append(d)
        d = " ".join(ds)
        d = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.3f}", d)
        idattr = f' id="{self.id}"' if self.id else ""
        return f'<path{idattr} d="{d}" fill="{INK}"><title>{esc(self.text)}</title></path>'

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------------------------------------------------------------- seal
SEAL_RAW = open(os.path.join(HERE, "seal.svg")).read()
SEAL_BODY = SEAL_RAW[SEAL_RAW.index("</title>") + 8: SEAL_RAW.rindex("</svg>")]
SEAL_CIRCLE = 960 / 1000  # outer ring diameter as a fraction of the 1000-unit box (ring stroke 6)

def seal(cx, cy, ring_d):
    """Place the seal so its outer ring is ring_d mm across, centred at (cx, cy)."""
    box = ring_d / SEAL_CIRCLE * (966 / 960)  # include outer stroke
    box = ring_d / 0.966
    s = box / 1000
    x, y = cx - box / 2, cy - box / 2
    finest = 4.2 * s / PT
    return (f'<g id="Emblem" transform="translate({x:.4f} {y:.4f}) scale({s:.6f})">{SEAL_BODY}</g>',
            (cx - ring_d / 2, cy - ring_d / 2, cx + ring_d / 2, cy + ring_d / 2), finest)

# ---------------------------------------------------------------- QR
QR = json.load(open(os.path.join(HERE, "qr.json")))
def qr(x, y, size):
    n = len(QR); m = size / n
    d = []
    for r, row in enumerate(QR):
        c = 0
        while c < n:
            if row[c] == "1":
                c0 = c
                while c < n and row[c] == "1": c += 1
                d.append(f"M{x+c0*m:.3f} {y+r*m:.3f}h{(c-c0)*m:.3f}v{m:.3f}h{-(c-c0)*m:.3f}z")
            else:
                c += 1
    return (f'<path id="QR-website" d="{"".join(d)}" fill="{INK}"><title>QR: https://www.mmuco.obinexus.org</title></path>',
            (x, y, x + size, y + size), m)

def rule(x1, y1, x2, y2, w=0.25):
    return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{INK}" stroke-width="{w}"/>'

# ---------------------------------------------------------------- content
NAME = "Nnamdi Michael Okpala"
ORG = "OBINexus MMUCO"
SUB = "Physical OSes"
EMAIL = "support@obinexus.org"
PHONE = "+44 7488 229054"
WEB = "www.mmuco.obinexus.org"
MOTTO = ("Spirits of Good and Evil That Bind Us", "in the Physical World")

def card(name, title, items, texts, checks):
    def build(outline):
        body = []
        body.append(f'<rect id="Background" x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>')
        body += [i for i in items]
        body.append('<g id="Type">' + "".join(t.outlined() if outline else t.live() for t in texts) + "</g>")
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
                f'<title>{esc(title)}</title>\n' + "\n".join(body) + "\n</svg>\n")
    open(os.path.join(OUT, f"{name}.svg"), "w").write(build(False))
    open(os.path.join(OUT, f"{name}-outlined.svg"), "w").write(build(True))
    # safe-area check
    for label, bb in checks + [(t.text, t.bbox()) for t in texts]:
        x0, y0, x1, y1 = bb
        ok = x0 >= 4 and y0 >= 4 and x1 <= W - 4 and y1 <= H - 4
        if not ok: print(f"  !! {name}: {label!r} outside 4 mm safe area {tuple(round(v,2) for v in bb)}")

# ================================================================= options
LOG = []
def opt_T():
    # Emblem side: emblem centred on the vertical axis, motto centred beneath.
    ring = 33.0
    g, bb, fine = seal(W / 2, M + ring / 2, ring)
    mot = [T(MOTTO[0], "serif", 8.5, W / 2, 44.6, "middle", id="Motto-1"),
           T(MOTTO[1], "serif", 8.5, W / 2, 48.6, "middle", id="Motto-2")]
    card("T-front", "OBINexus MMUCO — emblem side (T)", [g], mot, [("emblem", bb)])
    LOG.append(("T", ring, fine))
    # Contact side: name centred across the top, then a balanced split on the axis.
    name = T(NAME, "serif", 14, W / 2, 13.2, "middle", id="Name")
    org = T(ORG, "sans-semi", 8, W / 2, 19.0, "middle", tracking=120, id="Organisation")
    sub = T(SUB, "sans", 8, W / 2, 22.6, "middle", tracking=40, id="Division")
    axis = W / 2
    lines = [T(t, "sans", 8, axis - 3, y, "end", id=i) for t, y, i in
             [(EMAIL, 37.2, "Email"), (PHONE, 41.4, "Phone"), (WEB, 45.6, "Website")]]
    q, qb, mod = qr(axis + 3, 32.4, 15.0)
    card("T-back", "OBINexus MMUCO — contact side (T)", [rule(axis - 6, 27.6, axis + 6, 27.6), q],
         [name, org, sub] + lines, [("qr", qb)])

def opt_F():
    # Emblem side: identity band across the top (emblem + organisation), motto left-aligned beneath.
    ring = 25.0
    g, bb, fine = seal(M + ring / 2, M + ring / 2, ring)
    tx = M + ring + 5
    org = T(ORG, "sans-semi", 9, tx, 15.4, tracking=120, id="Organisation")
    sub = T(SUB, "sans", 8.5, tx, 19.6, tracking=40, id="Division")
    mot = [T(MOTTO[0], "serif", 8.5, M, 43.4, id="Motto-1"),
           T(MOTTO[1], "serif", 8.5, M, 47.4, id="Motto-2")]
    card("F-front", "OBINexus MMUCO — emblem side (F)", [g, rule(M, 36.0, M + 12, 36.0)], [org, sub] + mot, [("emblem", bb)])
    LOG.append(("F", ring, fine))
    # Contact side: name across the top, left-aligned stack beneath, QR at lower right.
    name = T(NAME, "serif", 14, M, 13.0, id="Name")
    o = T(ORG, "sans-semi", 8, M, 18.8, tracking=120, id="Organisation")
    s = T(SUB, "sans", 8, M, 22.4, tracking=40, id="Division")
    lines = [T(t, "sans", 8, M, y, id=i) for t, y, i in
             [(EMAIL, 39.4, "Email"), (PHONE, 43.6, "Phone"), (WEB, 47.8, "Website")]]
    qs = 15.0
    q, qb, mod = qr(W - M - qs, 48.6 - qs, qs)
    card("F-back", "OBINexus MMUCO — contact side (F)", [rule(M, 29.0, M + 12, 29.0), q], [name, o, s] + lines, [("qr", qb)])

def opt_Z():
    # Emblem side: emblem upper-left, organisation upper-right, motto across the lower area.
    ring = 28.0
    g, bb, fine = seal(M + ring / 2, M + ring / 2, ring)
    org = T(ORG, "sans-semi", 9, W - M, 12.4, "end", tracking=120, id="Organisation")
    sub = T(SUB, "sans", 8.5, W - M, 16.6, "end", tracking=40, id="Division")
    mot = [T(MOTTO[0], "serif", 8.5, W - M, 44.6, "end", id="Motto-1"),
           T(MOTTO[1], "serif", 8.5, W - M, 48.6, "end", id="Motto-2")]
    card("Z-front", "OBINexus MMUCO — emblem side (Z)", [g], [org, sub] + mot, [("emblem", bb)])
    LOG.append(("Z", ring, fine))
    # Contact side: name upper-left, QR upper-right, contacts along the bottom.
    name = T(NAME, "serif", 14, M, 13.0, id="Name")
    o = T(ORG, "sans-semi", 8, M, 18.8, tracking=120, id="Organisation")
    s = T(SUB, "sans", 8, M, 22.4, tracking=40, id="Division")
    qs = 15.0
    q, qb, mod = qr(W - M - qs, M, qs)
    l1 = T(EMAIL, "sans", 8, M, 44.0, id="Email")
    l2 = T(PHONE, "sans", 8, W - M, 44.0, "end", id="Phone")
    l3 = T(WEB, "sans", 8, M, 48.4, id="Website")
    card("Z-back", "OBINexus MMUCO — contact side (Z)", [rule(M, 38.6, W - M, 38.6), q], [name, o, s, l1, l2, l3], [("qr", qb)])

opt_T(); opt_F(); opt_Z()
for o, ring, fine in LOG:
    print(f"{o}: emblem ring {ring} mm, finest emblem line {fine:.2f} pt")
print("QR module:", round(15 / len(QR), 3), "mm")

# ================================================================= final (T emblem side + F contact side)
def final():
    ring = 33.0
    g, bb, fine = seal(W / 2, M + ring / 2, ring)
    mot = [T(MOTTO[0], "serif", 8.5, W / 2, 44.6, "middle", id="Motto-1"),
           T(MOTTO[1], "serif", 8.5, W / 2, 48.6, "middle", id="Motto-2")]
    card("obinexus-mmuco-front", "OBINexus MMUCO business card — front (emblem)", [g], mot, [("emblem", bb)])
    name = T(NAME, "serif", 14, M, 13.0, id="Name")
    o = T(ORG, "sans-semi", 8, M, 18.8, tracking=120, id="Organisation")
    s = T(SUB, "sans", 8, M, 22.4, tracking=40, id="Division")
    lines = [T(t, "sans", 8, M, y, id=i) for t, y, i in
             [(EMAIL, 39.4, "Email"), (PHONE, 43.6, "Phone"), (WEB, 47.8, "Website")]]
    qs = 15.0
    q, qb, mod = qr(W - M - qs, 47.8 - qs, qs)
    card("obinexus-mmuco-back", "OBINexus MMUCO business card — back (identity and contact)",
         [rule(M, 29.0, M + 12, 29.0), q], [name, o, s] + lines, [("qr", qb)])
    for t in [name, o, s] + lines + mot: print(f"  {t.text!r}: {t.size} pt, x {t.x0:.2f}-{t.x0+t.w:.2f} mm")
final()
