"""OBINexus MMUCO business card — revision 2.

Card 85 x 55 mm. SVG user units = mm. Black on white only.
Layout is set on a 1 mm spacing unit with a 4 mm safe margin, and every
gap is measured ink-to-ink from the real glyph outlines (not from font-size
boxes), so the spacing you see is the spacing specified.

Outputs (in ./out2):
  <name>.svg            live, editable text
  <name>-outlined.svg   text converted to paths (exact Source glyphs)
"""
import json, os, re, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out2"); os.makedirs(OUT, exist_ok=True)
FD = os.path.expanduser("~/.fonts/")

W, H = 85.0, 55.0
SAFE = 4.0              # safe margin, all sides
U = 1.0                 # spacing unit (mm)
PT = 25.4 / 72          # mm per point
INK = "#000000"

# family, CSS weight, VectorCraft style name, file
FONTS = {
    "serif":     ("Source Serif 4", 400, "Regular",  FD + "source-serif-4-latin-400-normal.ttf"),
    "sans":      ("Source Sans 3", 400, "Regular",   FD + "source-sans-3-latin-400-normal.ttf"),
    "sans-semi": ("Source Sans 3", 600, "SemiBold",  FD + "source-sans-3-latin-600-normal.ttf"),
    "sans-bold": ("Source Sans 3", 700, "Bold",      FD + "source-sans-3-latin-700-normal.ttf"),
    "anton":     ("Anton", 400, "Regular",           FD + "Anton-Regular.ttf"),
    "bubbler":   ("Bubbler One", 400, "Regular",     FD + "BubblerOne-Regular.ttf"),
}
_fc = {}
def font(key):
    if key not in _fc:
        p = FONTS[key][3]
        face = hb.Face(hb.Blob.from_file_path(p))
        tt = TTFont(p)
        _fc[key] = (hb.Font(face), tt, tt["head"].unitsPerEm, tt.getGlyphSet(), tt.getGlyphOrder())
    return _fc[key]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Line:
    """One line of type. size in pt, tracking in 1/1000 em.
    Ink box (relative to pen origin at baseline): ink_l, ink_r, ink_t (above baseline, +), ink_b (below, +)."""
    def __init__(self, text, key, size, tracking=0, id=None):
        assert size >= 8 or key in ("anton",), f"{text!r} under 8 pt"
        self.text, self.key, self.size, self.tracking, self.id = text, key, size, tracking, id
        hbf, tt, upem, gs, order = font(key)
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(hbf, buf, {"kern": True, "liga": True})
        s = size * PT / upem; tr = tracking / 1000 * size * PT
        x = 0.0; self.glyphs = []
        l = t = r = b = None
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            gx = x + pos.x_offset * s
            self.glyphs.append((info.codepoint, gx))
            bp = BoundsPen(gs); gs[order[info.codepoint]].draw(bp)
            if bp.bounds:
                x0, y0, x1, y1 = bp.bounds
                l = gx + x0 * s if l is None else min(l, gx + x0 * s)
                r = gx + x1 * s if r is None else max(r, gx + x1 * s)
                t = y1 * s if t is None else max(t, y1 * s)
                b = -y0 * s if b is None else max(b, -y0 * s)
            x += pos.x_advance * s + tr
        self.adv = x - (tr if text else 0)
        self.ink_l, self.ink_r, self.ink_t, self.ink_b = l, r, t, max(b, 0)
        self.cap = tt["OS/2"].sCapHeight * s
        self.ox = self.oy = 0.0
    # placement -------------------------------------------------------------
    def left(self, x):  self.ox = x - self.ink_l; return self          # optical left edge
    def right(self, x): self.ox = x - self.ink_r; return self
    def centre(self, x): self.ox = x - (self.ink_l + self.ink_r) / 2; return self
    def top(self, y):   self.oy = y + self.ink_t; return self          # ink top at y
    def base(self, y):  self.oy = y; return self
    @property
    def box(self): return (self.ox + self.ink_l, self.oy - self.ink_t, self.ox + self.ink_r, self.oy + self.ink_b)
    @property
    def bottom(self): return self.oy + self.ink_b
    @property
    def width(self): return self.ink_r - self.ink_l
    # output ----------------------------------------------------------------
    def live(self):
        fam, wt, _, _ = FONTS[self.key]
        ls = f' letter-spacing="{self.tracking/1000*self.size*PT:.4f}"' if self.tracking else ""
        idattr = f' id="{self.id}"' if self.id else ""
        return (f'<text{idattr} x="{self.ox:.3f}" y="{self.oy:.3f}" font-family="{fam}" font-weight="{wt}" '
                f'font-size="{self.size*PT:.4f}"{ls} fill="{INK}" xml:space="preserve">{esc(self.text)}</text>')
    def outlined(self):
        _, tt, upem, gs, order = font(self.key)
        s = self.size * PT / upem; ds = []
        for gid, gx in self.glyphs:
            pen = SVGPathPen(gs)
            gs[order[gid]].draw(TransformPen(pen, (s, 0, 0, -s, self.ox + gx, self.oy)))
            if pen.getCommands(): ds.append(pen.getCommands())
        d = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.3f}", " ".join(ds))
        idattr = f' id="{self.id}"' if self.id else ""
        return f'<path{idattr} d="{d}" fill="{INK}"><title>{esc(self.text)}</title></path>'

# ---------------------------------------------------------------- emblem (original seal.svg, untouched)
SEAL = open(os.path.join(HERE, "seal.svg")).read()
SEAL_BODY = SEAL[SEAL.index("</title>") + 8: SEAL.rindex("</svg>")]
SEAL_INK = 966.0   # outer ring diameter incl. stroke, in the seal's 1000-unit box
def emblem(cx, top, d):
    s = d / SEAL_INK
    box = 1000 * s
    x, y = cx - box / 2, top - (1000 - SEAL_INK) / 2 * s
    return (f'<g id="Emblem" transform="translate({x:.4f} {y:.4f}) scale({s:.6f})">{SEAL_BODY}</g>',
            (cx - d / 2, top, cx + d / 2, top + d), 4.2 * s / PT)

# ---------------------------------------------------------------- QR (version 3-M, 29 modules)
QR = json.load(open(os.path.join(HERE, "qr.json"))); NQ = len(QR)
def qr(x, y, size):
    m = size / NQ; d = []
    for r, row in enumerate(QR):
        c = 0
        while c < NQ:
            if row[c] == "1":
                c0 = c
                while c < NQ and row[c] == "1": c += 1
                d.append(f"M{x+c0*m:.4f} {y+r*m:.4f}h{(c-c0)*m:.4f}v{m:.4f}h{-(c-c0)*m:.4f}z")
            else: c += 1
    return (f'<path id="QR-website" d="{"".join(d)}" fill="{INK}"><title>QR: https://www.mmuco.obinexus.org</title></path>',
            (x, y, x + size, y + size), m)

# ---------------------------------------------------------------- content (unchanged wording)
NAME = "Nnamdi Michael Okpala"
OBX, MMUCO, SUB = "OBINexus", "MMUCO", "Physical OSes"
EMAIL, PHONE, WEB = "support@obinexus.org", "+44 7488 229054", "www.mmuco.obinexus.org"
MOTTO = ("Spirits of Good and Evil That Bind Us", "in the Physical World")

# ---------------------------------------------------------------- type specification (revision 2)
MMUCO_OLD = 8.0                       # pt == SVG user units in the VectorCraft export (1 unit = 1 pt)
MMUCO_PT = MMUCO_OLD + 5.0            # +5 units -> 13
OBX_PT = MMUCO_PT / 1.5               # OBINexus : MMUCO = 1 : 1.5 -> 8.667
SUB_PT = 9.5                          # 73 % of MMUCO
NAME_PT = 11.0                        # was 14
CONTACT_PT = 8.5                      # was 8
CONTACT_PITCH = 3.8                   # baseline-to-baseline, constant
MOTTO_PT = 8.5
QR_SIZE = 19.2                        # module area, was 15.0 (+28 %)
EMBLEM_D = 38.0                       # outer ring, was 33.0 (+15.2 %)

def write(name, title, items, lines, extra_boxes):
    def build(outline):
        body = [f'<rect id="Background" x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'] + items
        body.append('<g id="Type">' + "".join(l.outlined() if outline else l.live() for l in lines) + "</g>")
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{W:g}mm" height="{H:g}mm" viewBox="0 0 {W:g} {H:g}">\n<title>{esc(title)}</title>\n'
                + "\n".join(body) + "\n</svg>\n")
    open(os.path.join(OUT, name + ".svg"), "w").write(build(False))
    open(os.path.join(OUT, name + "-outlined.svg"), "w").write(build(True))
    bad = []
    for lab, (x0, y0, x1, y1) in extra_boxes + [(l.text, l.box) for l in lines]:
        if x0 < SAFE - 1e-6 or y0 < SAFE - 1e-6 or x1 > W - SAFE + 1e-6 or y1 > H - SAFE + 1e-6:
            bad.append((lab, tuple(round(v, 2) for v in (x0, y0, x1, y1))))
    print(f"{name}: {'OK' if not bad else 'OUTSIDE SAFE AREA ' + str(bad)}")

def brand(key_m="sans-bold", key_o="sans-semi", key_s="sans"):
    o = Line(OBX, key_o, OBX_PT, tracking=30, id="OBINexus")
    m = Line(MMUCO, key_m, MMUCO_PT, tracking=40, id="MMUCO")
    s = Line(SUB, key_s, SUB_PT, tracking=10, id="Physical-OSes")
    return o, m, s

def stack(lines, gaps):
    """Stack lines downward from their current first-line position with ink gaps (mm)."""
    for prev, nxt, g in zip(lines, lines[1:], gaps):
        nxt.top(prev.bottom + g)

# ================================================================= front (T: emblem leads)
def front(name="front", d=EMBLEM_D, motto_pt=MOTTO_PT, pitch=3.5):
    g, ebox, fine = emblem(W / 2, SAFE, d)
    m1 = Line(MOTTO[0], "serif", motto_pt, id="Motto-1").centre(W / 2)
    m2 = Line(MOTTO[1], "serif", motto_pt, id="Motto-2").centre(W / 2)
    # anchor the motto's last descender on the bottom safe edge, then read back the gap
    m2.base(H - SAFE - m2.ink_b); m1.base(m2.oy - pitch)
    gap = (m1.oy - m1.ink_t) - ebox[3]
    write(name, "OBINexus MMUCO business card — front (emblem)", [g], [m1, m2], [("emblem", ebox)])
    return dict(gap=gap, fine=fine, d=d, motto=motto_pt)

# ================================================================= back options
def back_F(name="back-F"):
    """F: brand across the top-left, name, then contacts; QR closes the bottom-right.
    Whole block is centred vertically so top and bottom white space match."""
    o, m, s = brand()
    n = Line(NAME, "serif", NAME_PT, id="Name")
    cs = [Line(t, "sans", CONTACT_PT, id=i) for t, i in ((EMAIL, "Email"), (PHONE, "Phone"), (WEB, "Website"))]
    for l in (o, m, s, n, *cs): l.left(SAFE)
    o.top(0); stack([o, m, s], [1.5 * U, 1.5 * U])
    n.top(s.bottom + 4 * U)
    cs[0].top(n.bottom + 3 * U)
    for a, b in zip(cs, cs[1:]): b.base(a.oy + CONTACT_PITCH)
    top, bot = o.box[1], cs[-1].oy           # contact block ends on a baseline (no descenders)
    shift = (H - (bot - top)) / 2 - top
    for l in (o, m, s, n, *cs): l.oy += shift
    q, qb, mod = qr(W - SAFE - QR_SIZE, cs[-1].oy - QR_SIZE, QR_SIZE)   # QR foot on the last baseline
    write(name, "OBINexus MMUCO business card — back (F)", [q], [o, m, s, n, *cs], [("qr", qb)])
    return locals()

def back_Z(name="back-Z"):
    """Z: brand top-left, QR top-right, name and contacts along the bottom."""
    o, m, s = brand()
    n = Line(NAME, "serif", NAME_PT, id="Name")
    cs = [Line(t, "sans", CONTACT_PT, id=i) for t, i in ((EMAIL, "Email"), (PHONE, "Phone"), (WEB, "Website"))]
    for l in (o, m, s, n, *cs): l.left(SAFE)
    o.top(SAFE); stack([o, m, s], [1.5 * U, 1.5 * U])
    cs[-1].base(H - SAFE - cs[-1].ink_b)
    for a, b in zip(cs[::-1], cs[::-1][1:]): b.base(a.oy - CONTACT_PITCH)
    n.base(cs[0].oy - cs[0].ink_t - 3 * U - n.ink_b)
    q, qb, mod = qr(W - SAFE - QR_SIZE, SAFE, QR_SIZE)
    write(name, "OBINexus MMUCO business card — back (Z)", [q], [o, m, s, n, *cs], [("qr", qb)])
    return locals()

def back_T(name="back-T"):
    """T: brand and name centred on the axis; contacts and QR balanced either side of it below."""
    ax = W / 2
    o, m, s = brand()
    n = Line(NAME, "serif", NAME_PT, id="Name")
    for l in (o, m, s, n): l.centre(ax)
    o.top(SAFE); stack([o, m, s], [1.5 * U, 1.5 * U]); n.top(s.bottom + 3 * U)
    q_top = n.bottom + 4 * U
    qsize = min(QR_SIZE, H - SAFE - q_top)
    cs = [Line(t, "sans", CONTACT_PT, id=i) for t, i in ((EMAIL, "Email"), (PHONE, "Phone"), (WEB, "Website"))]
    wmax = max(c.width for c in cs)
    gutter = 3 * U
    for c in cs: c.left(ax - gutter - wmax)
    # contacts centred vertically against the QR
    block = cs[0].ink_t + 2 * CONTACT_PITCH
    cs[0].base(q_top + (qsize - block) / 2 + cs[0].ink_t)
    for a, b in zip(cs, cs[1:]): b.base(a.oy + CONTACT_PITCH)
    q, qb, mod = qr(ax + gutter, q_top, qsize)
    write(name, "OBINexus MMUCO business card — back (T)", [q], [o, m, s, n, *cs], [("qr", qb)])
    return locals()

FINAL_CONTACT_PT = 9.0
def back_final(name="back", contact_pt=FINAL_CONTACT_PT):
    """Refined F. Brand group, 4 units, then the personal group (name + contacts).
    The QR is exactly as tall as the personal group: its top sits on the name's ink top and
    its foot on the last contact baseline, so the two read as one unit. Contact pitch is
    solved from that constraint and is identical for every line."""
    o, m, s = brand()
    n = Line(NAME, "serif", NAME_PT, id="Name")
    cs = [Line(t, "sans", contact_pt, id=i) for t, i in ((EMAIL, "Email"), (PHONE, "Phone"), (WEB, "Website"))]
    for l in (o, m, s, n, *cs): l.left(SAFE)
    o.top(0); stack([o, m, s], [1.5 * U, 1.5 * U])
    n.top(s.bottom + 4 * U)
    cs[0].top(n.bottom + 4 * U)
    pitch = (n.box[1] + QR_SIZE - cs[0].oy) / 2
    for a, b in zip(cs, cs[1:]): b.base(a.oy + pitch)
    top, bot = o.box[1], cs[-1].oy
    shift = round(((H - (bot - top)) / 2 - top) * 10) / 10          # centre vertically, 0.1 mm grid
    for l in (o, m, s, n, *cs): l.oy += shift
    q, qb, mod = qr(W - SAFE - QR_SIZE, n.box[1], QR_SIZE)
    write(name, "OBINexus MMUCO business card — back (identity and contact)", [q], [o, m, s, n, *cs], [("qr", qb)])
    return locals()

if __name__ == "__main__":
    for mp in (8.5, 8.0):
        r = front("front", motto_pt=mp, pitch=3.5 if mp == 8.5 else 3.4)
        print(f"front: emblem {r['d']} mm, motto {mp} pt -> emblem-to-motto ink gap {r['gap']:.2f} mm, finest line {r['fine']:.2f} pt")
        if r["gap"] >= 2.8: break
    F = back_F(); Z = back_Z(); T = back_T()
    o, m, s = F["o"], F["m"], F["s"]
    print(f"MMUCO {MMUCO_OLD} -> {MMUCO_PT} units; OBINexus {OBX_PT:.3f}; ratio 1:{MMUCO_PT/OBX_PT:.2f}; Physical OSes {SUB_PT} = {SUB_PT/MMUCO_PT*100:.1f}% of MMUCO")
    print(f"cap heights mm: OBINexus {o.cap:.2f}  MMUCO {m.cap:.2f}  Physical OSes {s.cap:.2f}  name {F['n'].cap:.2f}  contact {F['cs'][0].cap:.2f}")
    print(f"QR {QR_SIZE} mm, module {QR_SIZE/NQ:.3f} mm, quiet zone 4 modules = {4*QR_SIZE/NQ:.2f} mm")
    for k, v in (("F", F), ("Z", Z), ("T", T)):
        qb = v["qb"]; txt = [l.box for l in (v["o"], v["m"], v["s"], v["n"], *v["cs"])]
        qz = 4 * (qb[2] - qb[0]) / NQ
        def dist(a, b):
            dx = max(b[0] - a[2], a[0] - b[2], 0); dy = max(b[1] - a[3], a[1] - b[3], 0)
            return (dx * dx + dy * dy) ** 0.5
        clear = min(dist(qb, b) for b in txt)
        print(f"  {k}: QR {qb[2]-qb[0]:.2f} mm at ({qb[0]:.2f},{qb[1]:.2f}); nearest text {clear:.2f} mm (quiet zone {qz:.2f})")
