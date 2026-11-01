"""Eze landing page — v5: logo + identity, Anton / Bubbler One text, extended calm palette.

Builds on compose3 (v4 geometry). Fonts are the supplied files, used only at their single
available weight (Anton Regular 400, Bubbler One Regular 400). No synthetic bold/italic.

python3 compose5.py   -> eze-landing-v5-src.svg (live text + guides + reference)
                         eze-landing-v5-clean.svg (live text, export view)
                         eze-landing-v5-outlined.svg (text as paths from the supplied TTFs)
                         eze-landing-v5-notext.svg (background only — used for contrast sampling)
"""
import os, re, math, json
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from shapely.geometry import box, Point
import compose3 as C
import eze_trace3 as T3

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "..", "fonts2", "a")
FONTS = {"Anton": os.path.join(FD, "Anton", "Anton-Regular.ttf"),
         "Bubbler One": os.path.join(FD, "Bubbler_One", "BubblerOne-Regular.ttf")}

# ---------------------------------------------------------------- palette
PAL = dict(C.COOL)                                   # coral, cream, mint, pale_blue, slate — read from palette.svg
ACC = dict(teal="#4F8580", violet="#867495", terracotta="#BA796C", ochre="#B58B59", pale_sand="#E5DACA")

# ---------------------------------------------------------------- type
SIZES = {"heading": ("Anton", 48), "obinexus": ("Anton", 32), "sub": ("Bubbler One", 36),
         "support": ("Bubbler One", 20), "nav": ("Bubbler One", 18), "label": ("Bubbler One", 18)}
_f = {}
def font(fam):
    if fam not in _f:
        p = FONTS[fam]; face = hb.Face(hb.Blob.from_file_path(p)); tt = TTFont(p)
        _f[fam] = (hb.Font(face), tt, tt["head"].unitsPerEm, tt.getGlyphSet(), tt.getGlyphOrder())
    return _f[fam]

class Text:
    def __init__(self, id_, text, role, x, y, fill, anchor="start", tracking=0):
        fam, size = SIZES[role]
        self.id, self.text, self.role, self.fam, self.size, self.fill, self.tracking = id_, text, role, fam, size, fill, tracking
        hbf, tt, upem, gs, order = font(fam)
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(hbf, buf, {"kern": True})
        s = size / upem; tr = tracking / 1000 * size; px = 0; self.glyphs = []
        l = t = r = b = None
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            gx = px + pos.x_offset * s; self.glyphs.append((info.codepoint, gx))
            bp = BoundsPen(gs); gs[order[info.codepoint]].draw(bp)
            if bp.bounds:
                x0, y0, x1, y1 = bp.bounds
                l = gx + x0 * s if l is None else min(l, gx + x0 * s); r = gx + x1 * s if r is None else max(r, gx + x1 * s)
                t = y1 * s if t is None else max(t, y1 * s); b = -y0 * s if b is None else max(b, -y0 * s)
            px += pos.x_advance * s + tr
        self.adv = px - tr
        self.ink = (l, t, r, b)
        self.x = x - {"start": 0, "end": self.adv, "middle": self.adv / 2}[anchor] - (l if anchor == "start" else 0)
        self.y = y
    @property
    def bbox(self):
        l, t, r, b = self.ink
        return (self.x + l, self.y - t, self.x + r, self.y + b)
    def live(self):
        ls = f' letter-spacing="{self.tracking/1000*self.size:.2f}"' if self.tracking else ""
        return (f'<text id="{self.id}" x="{self.x:.2f}" y="{self.y:.2f}" font-family="{self.fam}" font-weight="400" '
                f'font-style="normal" font-size="{self.size}"{ls} fill="{self.fill}" xml:space="preserve">{self.text}</text>')
    def outlined(self):
        _, tt, upem, gs, order = font(self.fam); s = self.size / upem; ds = []
        for gid, gx in self.glyphs:
            pen = SVGPathPen(gs); gs[order[gid]].draw(TransformPen(pen, (s, 0, 0, -s, self.x + gx, self.y)))
            if pen.getCommands(): ds.append(pen.getCommands())
        d = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.2f}", " ".join(ds))
        return f'<path id="{self.id}" d="{d}" fill="{self.fill}"><title>{self.text} ({self.fam} 400, {self.size}px)</title></path>'

# ---------------------------------------------------------------- layout
M = 72                                   # page margin (left/right)
LOGO_D = 128
LOGO = dict(cx=M + LOGO_D / 2, cy=56 + LOGO_D / 2)          # 72..200 x 56..184
CLEAR = LOGO_D / 4                                           # 32 px clear space
ID_X = M + LOGO_D + CLEAR                                    # identity starts after the clear space (232)

def layout():
    T = []
    # identity lockup, vertically centred on the logo; spacing (not weight) balances heavy Anton vs light Bubbler One
    ob = Text("OBINexus", "OBINexus", "obinexus", ID_X, 0, ACC["violet"], tracking=10)
    mm = Text("MMUCO", "MMUCO", "heading", ID_X, 0, PAL["slate"], tracking=20)
    ph = Text("Physical-OSes", "Physical OSes", "sub", ID_X, 0, PAL["slate"], tracking=30)
    g1, g2 = 10, 16
    h = ob.ink[1] + g1 + mm.ink[1] + g2 + ph.ink[1] + ph.ink[3]
    top = LOGO["cy"] - h / 2
    ob.y = top + ob.ink[1]; mm.y = ob.y + g1 + mm.ink[1]; ph.y = mm.y + g2 + ph.ink[1]
    T += [ob, mm, ph]
    # navigation, top-right on a 54 px baseline, clear of Eze's bubble
    navs = ["About", "Projects", "Contact"]; xr = 1440 - M; items = []
    for name in reversed(navs):
        t = Text(f"nav-{name.lower()}", name, "nav", xr, 54, PAL["slate"], anchor="end", tracking=40); items.append(t); xr = t.bbox[0] - 30
    T += items[::-1]
    # supporting text (approved motto) + labels + call to action, left column below the lockup
    s1 = Text("support-1", "Spirits of Good and Evil That Bind Us", "support", M, 300, PAL["slate"], tracking=30)
    s2 = Text("support-2", "in the Physical World", "support", M, 300 + 34, PAL["slate"], tracking=30)
    l1 = Text("label-web", "www.mmuco.obinexus.org", "label", M, 410, PAL["slate"], tracking=40)
    l2 = Text("label-email", "support@obinexus.org", "label", M, 440, PAL["slate"], tracking=40)
    cta = Text("label-cta", "Get in touch", "label", M + 28, 0, PAL["cream"], tracking=40)
    T += [s1, s2, l1, l2]
    # CTA pill: slate panel, cream label (5.34 : 1)
    pill_y, pill_h = 482, 52
    cta.y = pill_y + pill_h / 2 + (cta.ink[1] - cta.ink[3]) / 2
    pill = (M, pill_y, cta.bbox[2] - cta.bbox[0] + 56, pill_h)
    T.append(cta)
    return T, pill

TEXTS, PILL = layout()

# ---------------------------------------------------------------- background edits for the text and logo
PAD = 32                                                    # quiet padding round every text box
REMOVE = {"form-top-left", "rock-tr-S"}                     # sat in the logo clear space / under the navigation
C.CURVES[:] = [c for c in C.CURVES if c[0] != "curve-upper"]   # crossed the identity and supporting text
MOVES = {"leaf-top-left-S": ("leaf", "S", 640, 600, -32),   # out of the logo clear space
         "leaf-left-M": ("leaf", "M", 1186, 790, -152)}     # out of the text column; terracotta beside mint
def apply_edits():
    keep = []
    for s in C.SHAPES:
        if s.name in REMOVE: continue
        if s.name in MOVES:
            kind, size, x, y, ang = MOVES[s.name]
            n = len(C.SHAPES); C.leaf(s.name, size, x, y, ang); s = C.SHAPES.pop()
        keep.append(s)
    C.SHAPES[:] = keep
apply_edits()

COLOURS = {   # explicit, so accents stay deliberate and sparing
    "form-bottom-left": PAL["mint"], "form-bottom-right": PAL["mint"],
    "rock-bl-L": PAL["pale_blue"], "rock-bl-S": PAL["pale_blue"], "rock-br-M": PAL["pale_blue"],
    "pebble-bl-L": PAL["pale_blue"], "pebble-bl-M": PAL["coral"], "pebble-bl-S": ACC["teal"],        # teal opposite coral
    "pebble-bl-S2": ACC["pale_sand"],                                                                  # pale sand beside the slate rock shadow
    "pebble-br-L": PAL["coral"], "pebble-br-S": ACC["ochre"], "pebble-br-M": PAL["pale_blue"],       # ochre beside pale blue rock
    "leaf-top-L": PAL["mint"], "leaf-bottom-S": PAL["coral"], "leaf-top-left-S": PAL["mint"], "leaf-right-M": PAL["coral"],
    "leaf-left-M": ACC["terracotta"],                                                                  # terracotta beside mint
    "blob-top-M": PAL["pale_blue"], "blob-lower-S": ACC["violet"], "blob-right-L": PAL["mint"],      # violet on cream
}

def clear_zones():
    zones = [(t.id, box(*t.bbox).buffer(PAD)) for t in TEXTS]
    zones.append(("cta-pill", box(PILL[0], PILL[1], PILL[0] + PILL[2], PILL[1] + PILL[3]).buffer(PAD)))
    zones.append(("logo", Point(LOGO["cx"], LOGO["cy"]).buffer(LOGO_D / 2 + CLEAR, 64)))
    return zones

def checks():
    issues = []
    zones = clear_zones()
    for s in C.SHAPES:
        for zn, z in zones:
            if s.poly.intersects(z): issues.append(f"{s.name} inside quiet zone of {zn}")
    for zn, z in zones:
        if zn != "logo" and z.intersects(C.BUB_POLY): issues.append(f"{zn} zone touches Eze bubble")
    for n, pts, w in C.CURVES:
        from shapely.geometry import LineString
        ln = LineString(C.segs_poly(C.catmull_pts(pts, closed=False))).buffer(w / 2)
        for zn, z in zones:
            if ln.intersects(z): issues.append(f"{n} inside quiet zone of {zn}")
    for i, a in enumerate(C.SHAPES):
        for b in C.SHAPES[i + 1:]:
            if a.poly.intersects(b.poly):
                inter = a.poly.intersection(b.poly)
                if inter.area / max(inter.length, 1) * 2 < 6: issues.append(f"near-tangent {a.name}/{b.name}")
                if COLOURS[a.name] == COLOURS[b.name]: issues.append(f"same colour overlap {a.name}/{b.name}")
            elif a.poly.distance(b.poly) < 8: issues.append(f"near-tangent gap {a.name}/{b.name}")
    return issues

# ---------------------------------------------------------------- logo (approved colour emblem)
SEAL = open(os.path.join(HERE, "..", "work", "col", "seal-colour-B.svg")).read()
SEAL_BODY = SEAL[SEAL.index("</title>") + 8: SEAL.rindex("</svg>")]
def logo_svg():
    s = LOGO_D / 966; x = LOGO["cx"] - 500 * s; y = LOGO["cy"] - 500 * s
    return f'<g id="MMUCO-logo" transform="translate({x:.2f} {y:.2f}) scale({s:.6f})">{SEAL_BODY}</g>'

# ---------------------------------------------------------------- build
def build(text_mode="live", guides=False, reference=False):
    svg = C.build("coolors", guides=False, reference=False)
    # recolour background shapes to the v5 assignment (geometry from compose3, edits above)
    for name, col in COLOURS.items():
        svg = re.sub(rf'(<path id="{re.escape(name)}" d="[^"]+" fill=")#[0-9A-Fa-f]{{6}}', rf'\g<1>{col}', svg)
    lv_vein = PAL["slate"]
    svg = svg.replace("</svg>", "")
    pill = (f'<rect id="cta-pill" x="{PILL[0]}" y="{PILL[1]}" width="{PILL[2]:.1f}" height="{PILL[3]}" rx="{PILL[3]/2}" fill="{PAL["slate"]}"/>')
    if text_mode == "none":
        texts = ""
    else:
        texts = "".join(t.live() if text_mode == "live" else t.outlined() for t in TEXTS)
    groups = [C.g("Logo", logo_svg()), C.g("Text", pill + texts)]
    if guides:
        zones = "".join(f'<path d="M{" L".join(f"{x:.1f} {y:.1f}" for x, y in z.exterior.coords)} Z" fill="none" stroke="#FF00B4" stroke-width="1" stroke-dasharray="6 6"/>' for _, z in clear_zones())
        groups.append(C.g("Text safe area", zones))
    if reference:
        import base64
        img = base64.b64encode(open(os.path.join(HERE, "eze.jpg"), "rb").read()).decode()
        groups.append(C.g("Eze reference", f'<image x="{C.TX:.2f}" y="{C.TY:.2f}" width="{200*C.S:.1f}" height="{200*C.S:.1f}" xlink:href="data:image/jpeg;base64,{img}" opacity="0.55"/>'))
    svg = svg.replace("<title>Eze — landing illustration v4 (palette.svg background)</title>", "<title>Eze — landing page v5</title>")
    return svg + "\n".join(groups) + "\n</svg>\n"

if __name__ == "__main__":
    C.SHAPES.sort(key=lambda s: s.z)
    issues = checks()
    print("layout issues:", issues or "none")
    for t in TEXTS: print(f"  {t.id:14s} {t.fam:11s} 400 {t.size:>3}px  fill {t.fill}  bbox {tuple(round(v) for v in t.bbox)}")
    print("pill", PILL)
    open(os.path.join(HERE, "eze-landing-v5-src.svg"), "w").write(build("live", guides=True, reference=True))
    open(os.path.join(HERE, "eze-landing-v5-clean.svg"), "w").write(build("live"))
    open(os.path.join(HERE, "eze-landing-v5-outlined.svg"), "w").write(build("outlined"))
    open(os.path.join(HERE, "eze-landing-v5-notext.svg"), "w").write(build("none"))
