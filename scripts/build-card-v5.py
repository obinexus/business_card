from fontTools.pens.boundsPen import BoundsPen
from shapely.geometry import Polygon
from shapely.ops import unary_union
"""OBINexus MMUCO business card — v4.
Front (emblem side): filled-disc colour emblem, mailto QR + support@obinexus.org, full motto.
Back (contact side): brand group, Eze avatar beside the name, email + website (no telephone).
Logo, QR and email are wrapped in mailto: links (clickable in SVG and PDF).
"""
import os, sys, json, re
from shapely.geometry import box, Point
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "eze"))
import card3 as C3
from card3 import G, PAL, BLACK, W, H, SAFE, BLEED, PT, pebble, leaf, circle, live, outlined
import eze_trace3 as T3, json as _j

MAILTO = "mailto:support@obinexus.org"
G.QR = json.load(open(os.path.join(HERE, "qr-mailto.json"))); G.NQ = len(G.QR)
col = open(os.path.join(HERE, "col", "seal-colour-D.svg")).read()
G.SEAL_BODY = col[col.index("</title>") + 8: col.rindex("</svg>")]
OUT = os.path.join(HERE, "out5"); os.makedirs(OUT, exist_ok=True)
QR = 19.2
link = lambda body: f'<a xlink:href="{MAILTO}" href="{MAILTO}">{body}</a>'

# ---------------------------------------------------------------- front
EMB_D = 38.0
TXT_PT = 9.0      # every small text line on both sides
PITCH = 4.8       # baseline-to-baseline for every two-line group
def front():
    q, qb, mod = G.qr(W - SAFE - QR, SAFE, QR); qz = 4 * mod
    em = G.Line(G.EMAIL, "bubbler", TXT_PT, tracking=25, id="Email"); em.fill_ = BLACK
    em.right(W - SAFE); em.top(qb[3] + qz + 0.4)
    MOTTO_PT, ARC_TRACK, ARC_GAP = 8.5, 40, 0.8
    m1 = G.Line(G.MOTTO[0], "bubbler", MOTTO_PT, tracking=ARC_TRACK, id="Motto-1"); m2 = G.Line(G.MOTTO[1], "bubbler", MOTTO_PT, tracking=ARC_TRACK, id="Motto-2")
    ecx, ecy = SAFE + EMB_D / 2, SAFE + EMB_D / 2
    R1 = EMB_D / 2 + ARC_GAP + m1.ink_t; R2 = R1 + PITCH
    # keep the curved line 1 inside the left safe margin
    half1 = (m1.adv / 2) / R1
    ecx = max(ecx, SAFE + (R1 + 0.2) * math.sin(half1) + 0.3)
    g, ebox, fine = G.emblem(ecx, SAFE, EMB_D)
    arc1, span1, ink1 = bottom_arc_text(m1, ecx, ecy, R1, BLACK, "Motto-arc-1")
    arc2, span2, ink2 = bottom_arc_text(m2, ecx, ecy, R2, BLACK, "Motto-arc-2")
    arc_zone = unary_union([ink1, ink2])
    panel = f'<rect id="QR-quiet-zone" x="{qb[0]-qz:.3f}" y="{qb[1]-qz:.3f}" width="{QR+2*qz:.3f}" height="{QR+2*qz:.3f}" fill="#FFFFFF"/>'
    motifs = []
    d, p = circle(88.5, 58.5, 13.0); motifs.append(("eze-bubble", d, p, PAL["pale_blue"], None))
    d, p = pebble(27.0, 56.0, 8.0, -10, 3); motifs.append(("pebble-1", d, p, PAL["mint"], None))
    d, p = pebble(34.5, 57.0, 5.5, 18, 4); motifs.append(("pebble-2", d, p, PAL["coral"], None))
    d, p = pebble(20.5, 57.6, 4.0, 8, 5); motifs.append(("pebble-3", d, p, PAL["pale_sand"], None))
    b, v, p = leaf(51.0, 7.5, 9.0, 205); motifs.append(("leaf-1", b, p, PAL["terracotta"], v))
    zones = [("emblem", Point(ecx, ecy).buffer(EMB_D / 2 + 3, 64)), ("motto arc", arc_zone.buffer(1.5)),
             ("QR+quiet zone", box(qb[0] - qz, qb[1] - qz, qb[2] + qz, qb[3] + qz).buffer(0.8))] + [(l.text, box(*l.box).buffer(2)) for l in (em,)]
    items = [link(g), arc1, arc2, panel, link(q)]
    ax0, ay0, ax1, ay1 = arc_zone.bounds
    return dict(name="front", items=items, lines=[em], link_lines={"Email"}, motifs=motifs, zones=zones,
                safe=[("emblem", ebox), ("qr", qb), ("motto arcs", (ax0, ay0, ax1, ay1))],
                info=dict(emblem_d=EMB_D, emblem_cx=ecx, motto_pt=MOTTO_PT, R1=R1, R2=R2, line1_arc_deg=span1, line2_arc_deg=span2,
                          line1_ends_below_horizontal=90 - span1 / 2, arcs_bottom=ay1, arcs_left=ax0, module=mod, quiet=qz))

# ---------------------------------------------------------------- Eze avatar (v3 portrait, warm palette)
SK = {k.lower().replace(" ", "_"): v for k, v in _j.load(open(os.path.join(HERE, "..", "eze", "skin-palette.json"))).items()}
def avatar(cx, cy, d):
    s = d / 205.0                                   # ref units -> mm (feather tips to chin fill the circle)
    tx, ty = cx - 116 * s, cy - 95 * s
    base = "".join(f'<path d="{T3.BASES[k]}" fill="{ {"cap": SK["amber"], "brim": SK["umber"]}.get(k, SK["almond"]) }"/>'
                   for k in ("neck", "ear-left", "ear-right", "skin", "cap", "brim"))
    planes = "".join(f'<path d="{dd}" fill="{SK["honey"] if k.startswith("hl") else SK["espresso"]}"/>' for k, dd in sorted(T3.PLANES.items(), key=lambda kv: kv[0].startswith("hl")))
    planes += "".join(f'<path d="{T3.ellipse(x, y, r)}" fill="{SK["pale_ivory"]}"/>' for x, y, r in ((81.5, 121.5, 9.6), (142, 117.5, 10.3)))
    lines = "".join(T3.svg_groups(ink={"default": SK["chocolate"]}, paper=SK["pale_ivory"]))
    feathers = T3.feathers_svg(vane_front=SK["espresso"], vane_back=SK["chocolate"], base=SK["warm_ivory"], outline=SK["chocolate"], splits=SK["bronze"])
    art = feathers + base + planes + lines
    # print-safe minimum stroke: nothing thinner than 0.1 mm (~0.28 pt) at this scale
    minw = 0.1 / s
    art = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{max(float(m.group(1)), minw):.2f}"', art)
    r = d / 2
    return (f'<g id="Eze-avatar"><defs><clipPath id="avatar-clip" clipPathUnits="userSpaceOnUse"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PAL["pale_blue"]}"/>'
            f'<g clip-path="url(#avatar-clip)"><g transform="translate({tx:.3f} {ty:.3f}) scale({s:.5f})">{art}</g></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r-0.15}" fill="none" stroke="{PAL["slate"]}" stroke-width="0.3"/></g>'), (cx - r, cy - r, cx + r, cy + r), s

# ---------------------------------------------------------------- back
AV_D = 16.0; NAME_PT = 11.0; NAME_R = AV_D / 2 + 1.6          # baseline radius of the circular name
import math
from fontTools.pens.svgPathPen import SVGPathPen
def circular_name(line, cx, cy, R, fill):
    """Name set on the upper arc of a circle, centred over the top, reading left to right.
    Each glyph is a vector path from the supplied Bubbler One font (text-on-path baked to outlines)."""
    _, tt, upem, gs, order = G.font(line.key)
    sc = line.size * PT / upem
    L = line.adv; parts = []
    gl = line.glyphs + [(None, L + line.tracking / 1000 * line.size * PT)]
    for (gid, gx), (_, nx) in zip(gl, gl[1:]):
        adv = nx - gx; mid = gx + adv / 2 - L / 2; th = math.degrees(mid / R)
        pen = SVGPathPen(gs); gs[order[gid]].draw(pen); d = pen.getCommands()
        if d:
            parts.append(f'<path d="{d}" transform="rotate({th:.3f} {cx:.3f} {cy:.3f}) translate({cx - adv/2:.3f} {cy - R:.3f}) scale({sc:.6f} {-sc:.6f})"/>')
    span = math.degrees(L / R)
    return f'<g id="Name-on-circle" fill="{fill}"><title>{G.esc(line.text)}</title>{"".join(parts)}</g>', span


def bottom_arc_text(line, cx, cy, R, fill, gid):
    _, tt, upem, gs, order = G.font(line.key)
    sc = line.size * PT / upem; L = line.adv; parts = []; polys = []
    gl = line.glyphs + [(None, L + line.tracking / 1000 * line.size * PT)]
    for (gid_, gx), (_, nx) in zip(gl, gl[1:]):
        adv = nx - gx; mid = gx + adv / 2 - L / 2; th = math.degrees(mid / R)
        pen = SVGPathPen(gs); gs[order[gid_]].draw(pen); d = pen.getCommands()
        if d:
            bp = BoundsPen(gs); gs[order[gid_]].draw(bp)
            if bp.bounds:
                u0, v0, u1, v1 = bp.bounds
                pts = []
                for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                    x, y = cx - adv / 2 + sc * u, cy + R - sc * v
                    a = math.radians(-th); dx, dy = x - cx, y - cy
                    pts.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
                polys.append(Polygon(pts))
            parts.append(f'<path d="{d}" transform="rotate({-th:.3f} {cx:.3f} {cy:.3f}) translate({cx - adv/2:.3f} {cy + R:.3f}) scale({sc:.6f} {-sc:.6f})"/>')
    return f'<g id="{gid}" fill="{fill}"><title>{G.esc(line.text)}</title>{"".join(parts)}</g>', math.degrees(L / R), unary_union(polys)

def back():
    o = G.Line("OBINexus", "anton", C3.OBX_PT, tracking=20, id="OBINexus"); o.fill_ = PAL["slate"]
    m = G.Line("MMUCO", "anton", C3.MMUCO_PT, tracking=30, id="MMUCO"); m.fill_ = BLACK
    s = G.Line("Physical OSes", "bubbler", C3.SUB_PT, tracking=20, id="Physical-OSes"); s.fill_ = BLACK
    cs = [G.Line(t, "bubbler", TXT_PT, tracking=25, id=i) for t, i in ((G.EMAIL, "Email"), (G.WEB, "Website"))]
    for c in cs: c.fill_ = BLACK
    for l in (o, m, s, *cs): l.left(SAFE)
    TOP, BOT = SAFE, H - SAFE                                 # same 4 mm safe band as the emblem side (4 .. 51 mm)
    o.top(TOP); m.top(o.bottom + 1.5); s.top(m.bottom + 1.5)   # equal 1.5 mm gaps inside the brand group
    cs[1].base(BOT - cs[1].ink_b); cs[0].base(cs[1].oy - PITCH)
    # avatar circle + name ring: ring top = TOP, avatar bottom = BOT, right edge on the safe margin
    nm = G.Line(G.NAME, "bubbler", NAME_PT, tracking=60, id="Name")
    GAP = 1.5                                                 # avatar edge -> name baseline
    r_av = EMB_D / 2                                          # avatar = emblem diameter (38 mm): matched hero size on both sides
    R = r_av + GAP                                            # name baseline radius
    cy = BOT - r_av
    half = (nm.adv / 2) / R                                   # half-angle of the name arc (rad)
    reach = max(r_av, (R + nm.ink_t) * math.sin(min(half, math.pi / 2)))
    cx = W - SAFE - reach
    av_svg, av_box, av_s = avatar(cx, cy, 2 * r_av)
    name_svg, span = circular_name(nm, cx, cy, R, BLACK)
    motifs = []
    b, v, p = leaf(84.0, 3.0, 8.0, 150); motifs.append(("leaf-1", b, p, PAL["mint"], v))
    d, p = pebble(30.0, 56.5, 8.0, -8, 7); motifs.append(("pebble-1", d, p, PAL["coral"], None))
    d, p = pebble(37.5, 57.2, 5.5, 18, 8); motifs.append(("pebble-2", d, p, PAL["mint"], None))
    d, p = pebble(24.0, 57.8, 4.0, 30, 9); motifs.append(("pebble-3", d, p, PAL["teal"], None))
    ring = Point(cx, cy).buffer(R + nm.ink_t, 64)
    zones = [(l.text, box(*l.box).buffer(2.0)) for l in (o, m, s, *cs)] + [("avatar + name ring", ring.buffer(1.5))]
    safe = [("avatar", av_box), ("name ring top", (cx - reach, cy - R - nm.ink_t, cx + reach, cy))]
    # horizontal clearance between the text column and the avatar/ring
    col = max(l.box[2] for l in (o, m, s, *cs))
    clear = min(ring.distance(box(*l.box)) for l in (o, m, s, *cs))
    return dict(name="back", items=[av_svg, name_svg], lines=[o, m, s, *cs], link_lines={"Email"}, motifs=motifs, zones=zones,
                safe=safe, info=dict(avatar_d=2 * r_av, name_pt=NAME_PT, name_R=R, arc_deg=math.degrees(2 * half),
                                     ring_top=cy - R - nm.ink_t, avatar_bottom=cy + r_av, right=cx + reach, text_clearance=clear))

def write(side):
    def build(outline, bleed):
        x0, y0, w, h = (-BLEED, -BLEED, W + 2 * BLEED, H + 2 * BLEED) if bleed else (0, 0, W, H)
        mot = []
        for name, d, p, c, vein in side["motifs"]:
            mot.append(f'<path id="{name}" d="{d}" fill="{c}"/>')
            if vein: mot.append(f'<path id="{name}-vein" d="{vein}" fill="none" stroke="{PAL["slate"]}" stroke-width="0.25" stroke-linecap="round"/>')
        txt = "".join((link if l.id in side["link_lines"] else (lambda x: x))(outlined(l) if outline else live(l)) for l in side["lines"])
        body = [f'<rect id="Background" x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}" fill="#FFFFFF"/>',
                f'<defs><clipPath id="bleed-clip" clipPathUnits="userSpaceOnUse"><rect x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}"/></clipPath></defs>',
                '<g id="Natural-motifs" clip-path="url(#bleed-clip)">' + "".join(mot) + "</g>"] + side["items"] + ['<g id="Type">' + txt + "</g>"]
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{w:g}mm" height="{h:g}mm" viewBox="{x0:g} {y0:g} {w:g} {h:g}">\n<title>OBINexus MMUCO business card v5 — {side["name"]}</title>\n' + "\n".join(body) + "\n</svg>\n")
    for o in (False, True):
        for b in (False, True):
            open(os.path.join(OUT, side["name"] + ("-outlined" if o else "") + ("-bleed" if b else "") + ".svg"), "w").write(build(o, b))

if __name__ == "__main__":
    for s in (front(), back()):
        write(s)
        print(s["name"], "issues:", C3.check(s) or "none", "|", {k: round(v, 3) for k, v in s["info"].items()})
        for l in s["lines"]:
            print(f"   {l.text:38s} {G.FONTS[l.key][0]:11s} {l.size:6.3f} pt  x {l.box[0]:.2f}-{l.box[2]:.2f}  y {l.box[1]:.2f}-{l.box[3]:.2f}")
