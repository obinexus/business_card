"""OBINexus MMUCO business card — v3 (print sizes in points, Anton + Bubbler One, subtle natural motifs).

Units: mm. Trim 85 x 55, safe margin 4, bleed 3.
Writes out3/<side>{,-outlined}{,-bleed}.svg  (side = front [emblem], back [contact]).
"""
import os, re, math, json
from shapely.geometry import box, Point, Polygon
import gen2 as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out3"); os.makedirs(OUT, exist_ok=True)
W, H, SAFE, BLEED, PT = 85.0, 55.0, 4.0, 3.0, 25.4 / 72

FD = os.path.expanduser("~/.fonts/")
G.FONTS["anton"] = ("Anton", 400, "Regular", FD + "Anton-Regular.ttf")
G.FONTS["bubbler"] = ("Bubbler One", 400, "Regular", FD + "BubblerOne-Regular.ttf")

# approved palette (palette.svg) + approved accents
PAL = dict(coral="#FFA69E", cream="#FAF3DD", mint="#B8F2E6", pale_blue="#AED9E0", slate="#5E6472",
           teal="#4F8580", violet="#867495", terracotta="#BA796C", ochre="#B58B59", pale_sand="#E5DACA")
BLACK = "#000000"

# colour emblem (approved variant B)
col = open(os.path.join(HERE, "col", "seal-colour-B.svg")).read()
G.SEAL_BODY = col[col.index("</title>") + 8: col.rindex("</svg>")]

# ---------------------------------------------------------------- shapes (mm)
def cat(pts, closed=True):
    n = len(pts); P = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in (range(n) if closed else range(n - 1)):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + (" Z" if closed else "")

def pebble(cx, cy, w, rot, seed):
    import random
    r = random.Random(seed); ph = [r.uniform(0, 6.3) for _ in range(3)]; a0 = math.radians(rot); pts = []
    for i in range(9):
        a = i / 9 * 2 * math.pi; k = 1 + 0.06 * (math.sin(2 * a + ph[0]) + .5 * math.sin(3 * a + ph[1]))
        x, y = w / 2 * k * math.cos(a), w / 2 * 0.66 * k * math.sin(a) * (0.86 if math.sin(a) > 0 else 1)
        pts.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return cat(pts), Polygon(pts)

def leaf(bx, by, L, ang):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a); Wd = L * 0.36; bend = 0.1
    T = lambda u, v: (bx + u * ca - v * sa, by + u * sa + v * ca)
    tip = T(L, L * bend); c = [T(L * .22, -Wd * .62), T(L * .62, -Wd * .55 + L * bend * .4), T(L * .62, Wd * .48 + L * bend * .8), T(L * .22, Wd * .62)]
    body = (f"M{bx:.2f} {by:.2f} C{c[0][0]:.2f} {c[0][1]:.2f} {c[1][0]:.2f} {c[1][1]:.2f} {tip[0]:.2f} {tip[1]:.2f} "
            f"C{c[2][0]:.2f} {c[2][1]:.2f} {c[3][0]:.2f} {c[3][1]:.2f} {bx:.2f} {by:.2f} Z")
    v1, v2, ve = T(L * .35, L * bend * .15), T(L * .7, L * bend * .55), T(L * .88, L * bend * .82)
    vein = f"M{bx:.2f} {by:.2f} C{v1[0]:.2f} {v1[1]:.2f} {v2[0]:.2f} {v2[1]:.2f} {ve[0]:.2f} {ve[1]:.2f}"
    poly = Polygon([T(u, v) for u, v in [(0, 0), (.3, -Wd * .5), (.7 * L, -Wd * .4), (L, L * bend), (.7 * L, Wd * .45), (.3 * L, Wd * .5)]])
    return body, vein, poly

def circle(cx, cy, r): return f"M{cx-r:.2f} {cy:.2f} a{r:.2f} {r:.2f} 0 1 0 {2*r:.2f} 0 a{r:.2f} {r:.2f} 0 1 0 {-2*r:.2f} 0 Z", Point(cx, cy).buffer(r, 64)

# ---------------------------------------------------------------- emblem side (front)
EMB_D = 38.0
def front():
    g, ebox, fine = G.emblem(W / 2, SAFE, EMB_D)
    m1 = G.Line(G.MOTTO[0], "bubbler", 8.5, tracking=20, id="Motto-1").centre(W / 2)
    m2 = G.Line(G.MOTTO[1], "bubbler", 8.5, tracking=20, id="Motto-2").centre(W / 2)
    for m in (m1, m2): m.fill_ = BLACK
    m2.base(H - SAFE - m2.ink_b); m1.base(m2.oy - 3.6)
    motifs = []
    d, p = circle(-1.5, 58.5, 15.5); motifs.append(("eze-bubble", d, p, PAL["pale_blue"], None))
    d, p = pebble(80.5, 52.5, 9.0, -14, 3); motifs.append(("pebble-1", d, p, PAL["mint"], None))
    d, p = pebble(86.0, 46.5, 6.0, 22, 4); motifs.append(("pebble-2", d, p, PAL["coral"], None))
    d, p = pebble(74.0, 56.5, 4.5, 8, 5); motifs.append(("pebble-3", d, p, PAL["pale_sand"], None))
    b, v, p = leaf(-2.0, 7.5, 13.0, -18); motifs.append(("leaf-1", b, p, PAL["mint"], v))
    b, v, p = leaf(87.0, 6.0, 9.0, 200); motifs.append(("leaf-2", b, p, PAL["terracotta"], v))
    zones = [("emblem", Point(W / 2, SAFE + EMB_D / 2).buffer(EMB_D / 2 + 3, 64))] + [(l.text, box(*l.box).buffer(2.0)) for l in (m1, m2)]
    gap = (m1.oy - m1.ink_t) - ebox[3]
    return dict(name="front", items=[g], lines=[m1, m2], motifs=motifs, zones=zones, safe=[("emblem", ebox)],
                info=dict(emblem_d=EMB_D, fine_pt=fine, motto_gap=gap))

# ---------------------------------------------------------------- contact side (back)
MMUCO_PT = 13.0; OBX_PT = MMUCO_PT / 1.5; SUB_PT = 9.5; NAME_PT = 12.0; CONTACT_PT = 9.0; QR = 19.2
def back():
    o = G.Line("OBINexus", "anton", OBX_PT, tracking=20, id="OBINexus"); o.fill_ = PAL["slate"]
    m = G.Line("MMUCO", "anton", MMUCO_PT, tracking=30, id="MMUCO"); m.fill_ = BLACK
    s = G.Line("Physical OSes", "bubbler", SUB_PT, tracking=20, id="Physical-OSes"); s.fill_ = BLACK
    n = G.Line(G.NAME, "bubbler", NAME_PT, tracking=10, id="Name"); n.fill_ = BLACK
    cs = [G.Line(t, "bubbler", CONTACT_PT, tracking=25, id=i) for t, i in ((G.EMAIL, "Email"), (G.WEB, "Website"))]
    for c in cs: c.fill_ = BLACK
    for l in (o, m, s, n, *cs): l.left(SAFE)
    o.top(0); m.top(o.bottom + 1.2); s.top(m.bottom + 1.4)
    n.top(s.bottom + 4.0); cs[0].top(n.bottom + 3.0)
    pitch = 4.8
    for a, b in zip(cs, cs[1:]): b.base(a.oy + pitch)
    top, bot = o.box[1], max(cs[-1].box[3], n.box[1] + QR)
    sh = round(((H - (bot - top)) / 2 - top) * 10) / 10
    for l in (o, m, s, n, *cs): l.oy += sh
    q, qb, mod = G.qr(W - SAFE - QR, n.box[1], QR)
    qz = 4 * mod
    motifs = []
    d, p = circle(85.5, -2.0, 17.0); motifs.append(("eze-bubble", d, p, PAL["pale_blue"], None))
    b, v, p = leaf(62.0, 4.5, 9.5, 12); motifs.append(("leaf-1", b, p, PAL["mint"], v))
    d, p = pebble(52.0, 55.0, 8.0, -8, 7); motifs.append(("pebble-1", d, p, PAL["coral"], None))
    d, p = pebble(59.5, 55.8, 5.5, 18, 8); motifs.append(("pebble-2", d, p, PAL["mint"], None))
    d, p = pebble(46.0, 56.5, 4.0, 30, 9); motifs.append(("pebble-3", d, p, PAL["teal"], None))
    zones = [(l.text, box(*l.box).buffer(2.0)) for l in (o, m, s, n, *cs)] + [("QR+quiet zone", box(qb[0] - qz, qb[1] - qz, qb[2] + qz, qb[3] + qz).buffer(0.8))]
    # QR sits on a white quiet-zone panel so nothing can ever print under it
    panel = f'<rect id="QR-quiet-zone" x="{qb[0]-qz:.3f}" y="{qb[1]-qz:.3f}" width="{QR+2*qz:.3f}" height="{QR+2*qz:.3f}" fill="#FFFFFF"/>'
    return dict(name="back", items=[panel, q], lines=[o, m, s, n, *cs], motifs=motifs, zones=zones, safe=[("qr", qb)],
                info=dict(mmuco=MMUCO_PT, obx=OBX_PT, ratio=MMUCO_PT / OBX_PT, qr=QR, module=mod, quiet=qz, pitch=pitch))

# ---------------------------------------------------------------- output
def live(l):
    fam, wt, _, _ = G.FONTS[l.key]
    ls = f' letter-spacing="{l.tracking/1000*l.size*PT:.4f}"' if l.tracking else ""
    return (f'<text id="{l.id}" x="{l.ox:.3f}" y="{l.oy:.3f}" font-family="{fam}" font-weight="400" font-style="normal" '
            f'font-size="{l.size*PT:.4f}"{ls} fill="{l.fill_}" xml:space="preserve">{G.esc(l.text)}</text>')
def outlined(l):
    return l.outlined().replace(f'fill="{G.INK}"', f'fill="{l.fill_}"', 1)

def write(side):
    def build(outline, bleed):
        x0, y0, w, h = (-BLEED, -BLEED, W + 2 * BLEED, H + 2 * BLEED) if bleed else (0, 0, W, H)
        mot = []
        for name, d, p, c, vein in side["motifs"]:
            mot.append(f'<path id="{name}" d="{d}" fill="{c}"/>')
            if vein: mot.append(f'<path id="{name}-vein" d="{vein}" fill="none" stroke="{PAL["slate"]}" stroke-width="0.25" stroke-linecap="round"/>')
        body = [f'<rect id="Background" x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}" fill="#FFFFFF"/>',
                f'<defs><clipPath id="bleed-clip" clipPathUnits="userSpaceOnUse"><rect x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}"/></clipPath></defs>',
                '<g id="Natural-motifs" clip-path="url(#bleed-clip)">' + "".join(mot) + "</g>"] + side["items"]
        body.append('<g id="Type">' + "".join(outlined(l) if outline else live(l) for l in side["lines"]) + "</g>")
        clip = "" if bleed else ""
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}mm" height="{h:g}mm" '
                f'viewBox="{x0:g} {y0:g} {w:g} {h:g}">\n<title>OBINexus MMUCO business card v3 — {side["name"]}</title>\n' + "\n".join(body) + "\n</svg>\n")
    for o in (False, True):
        for b in (False, True):
            open(os.path.join(OUT, side["name"] + ("-outlined" if o else "") + ("-bleed" if b else "") + ".svg"), "w").write(build(o, b))

def check(side):
    issues = []
    for lab, (x0, y0, x1, y1) in side["safe"] + [(l.text, l.box) for l in side["lines"]]:
        if x0 < SAFE - 1e-6 or y0 < SAFE - 1e-6 or x1 > W - SAFE + 1e-6 or y1 > H - SAFE + 1e-6: issues.append(f"{lab} outside safe area")
    for l in side["lines"]:
        if l.size < 8: issues.append(f"{l.text} < 8 pt")
    for name, d, p, c, v in side["motifs"]:
        for zn, z in side["zones"]:
            if p.intersects(z): issues.append(f"{name} inside clear zone of {zn}")
        if p.bounds[0] < -BLEED or p.bounds[1] < -BLEED or p.bounds[2] > W + BLEED or p.bounds[3] > H + BLEED: pass  # cropped at bleed edge
    return issues

if __name__ == "__main__":
    for s in (front(), back()):
        write(s)
        print(s["name"], "issues:", check(s) or "none", "|", {k: round(v, 3) for k, v in s["info"].items()})
        for l in s["lines"]:
            print(f"   {l.text:38s} {G.FONTS[l.key][0]:11s} 400 {l.size:6.3f} pt  {l.fill_}  x {l.box[0]:.2f}-{l.box[2]:.2f}  y {l.box[1]:.2f}-{l.box[3]:.2f}")
