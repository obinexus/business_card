"""Eze portrait — refinement pass (v2).

Same 200 x 200 reference space as eze_trace.py. Every contour is written as a short list of
nodes, each marked:
    'c'  corner  - handles point along their own neighbouring chords, so the direction breaks
                   (jaw angle, cheekbones, nostril wings, lip corners, cupid's bow, feather tip)
    's'  smooth  - handles share one tangent (skull, ears, cap crown, lip curves)
Glasses and eyes are true ellipses so the two lenses stay geometrically consistent; the right
lens is 7 % larger for the slight three-quarter perspective in the sketch.

Stroke tiers: SIL silhouette 2.8 | FEAT major features 1.7 | DET eyelids/creases 0.9 | FINE 0.6
Joins: silhouette/jaw/feather use mitre joins with miterlimit 2.2 (pointed but no spikes);
       rounded joins elsewhere.
Shading is no longer hatching: it is a set of closed facial-plane shapes (see PLANES).
"""
import math

SIL, FEAT, DET, FINE = 2.8, 1.7, 0.9, 0.6

def bez(nodes, closed=False, k=0.36):
    """nodes: [(x, y, 'c'|'s'), ...] -> cubic Bezier path with explicit corner/smooth handles."""
    n = len(nodes)
    pts = [(x, y) for x, y, _ in nodes]
    def nb(i):
        if closed: return pts[(i - 1) % n], pts[(i + 1) % n]
        return pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
    def handles(i):
        (px, py), (nx, ny) = nb(i)
        x, y, kind = nodes[i]
        if kind == "s":
            tx, ty = (nx - px), (ny - py); L = math.hypot(tx, ty) or 1; tx, ty = tx / L, ty / L
            din = math.hypot(x - px, y - py) * k; dout = math.hypot(nx - x, ny - y) * k
            return (x - tx * din, y - ty * din), (x + tx * dout, y + ty * dout)
        # corner: each handle aims along its own chord (independent handles)
        return (x + (px - x) * k * 0.8, y + (py - y) * k * 0.8), (x + (nx - x) * k * 0.8, y + (ny - y) * k * 0.8)
    H = [handles(i) for i in range(n)]
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    segs = range(n) if closed else range(n - 1)
    for i in segs:
        j = (i + 1) % n
        c1 = H[i][1]; c2 = H[j][0]
        d += f" C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {pts[j][0]:.2f} {pts[j][1]:.2f}"
    return d + (" Z" if closed else "")

def ellipse(cx, cy, rx, ry=None):
    ry = ry or rx; k = 0.5523
    return (f"M{cx-rx:.2f} {cy:.2f} C{cx-rx:.2f} {cy-ry*k:.2f} {cx-rx*k:.2f} {cy-ry:.2f} {cx:.2f} {cy-ry:.2f} "
            f"C{cx+rx*k:.2f} {cy-ry:.2f} {cx+rx:.2f} {cy-ry*k:.2f} {cx+rx:.2f} {cy:.2f} "
            f"C{cx+rx:.2f} {cy+ry*k:.2f} {cx+rx*k:.2f} {cy+ry:.2f} {cx:.2f} {cy+ry:.2f} "
            f"C{cx-rx*k:.2f} {cy+ry:.2f} {cx-rx:.2f} {cy+ry*k:.2f} {cx-rx:.2f} {cy:.2f} Z")
circle = ellipse

def arc(cx, cy, rx, ry, a0, a1, steps=4):
    """Open elliptical arc from angle a0 to a1 (degrees, 0 = +x, clockwise on screen)."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), "s"))
    return bez(pts)

# ================================================================ contours (node lists)
# skull / cap crown: smooth
CROWN = [(56, 88, "c"), (61, 50, "s"), (74, 25, "s"), (100, 18, "s"), (124, 15, "s"), (150, 20, "s"),
         (168, 38, "s"), (176, 64, "s"), (178, 84, "c")]
BRIM_LOW = [(55, 89, "c"), (80, 77, "s"), (106, 70, "s"), (128, 68, "s"), (156, 69, "s"), (178, 80, "c")]
BRIM_TOP = [(61, 67, "c"), (88, 58, "s"), (118, 56, "s"), (150, 58, "s"), (174, 67, "c")]

# face silhouette: corners at temple, cheekbone, jaw angle, chin corners
FACE = [(57, 92, "c"), (55, 112, "s"), (56, 137, "c"),       # left temple -> cheekbone (corner)
        (63, 166, "c"),                                          # left jaw angle
        (86, 196, "c"),                                          # left chin corner
        (116, 206, "s"),                                         # chin
        (142, 200, "c"),                                         # right chin corner
        (160, 180, "c"),                                         # right jaw angle
        (170, 149, "c"),                                         # right cheekbone
        (175, 122, "s"), (176, 98, "c")]                         # right temple
EAR_L = [(56, 106, "c"), (44, 103, "s"), (32, 112, "s"), (32, 130, "s"), (42, 145, "s"), (57, 154, "c")]
EAR_L_IN = [(48, 120, "s"), (43, 127, "s"), (47, 136, "c"), (53, 145, "s")]
EAR_R = [(176, 106, "c"), (187, 102, "s"), (196, 111, "s"), (196, 127, "s"), (188, 143, "s"), (172, 151, "c")]
EAR_R_IN = [(183, 118, "s"), (189, 125, "s"), (185, 134, "c"), (181, 144, "s")]
NECK_L = [(80, 192, "c"), (79, 222, "s"), (72, 282, "c")]
NECK_R = [(150, 196, "c"), (154, 226, "s"), (164, 282, "c")]

# feather: pointed tip and base (corners), vane edge with a few split notches (corners)
FEATHER = [(48, 98, "c"), (36, 86, "s"), (22, 70, "c"), (19, 62, "c"), (11, 46, "s"), (7, 26, "c"),
           (11, 20, "c"), (13, 2, "s"), (18, -6, "c"),                       # tip
           (30, 2, "s"), (44, 12, "c"), (48, 20, "c"), (56, 32, "s"), (56, 46, "c"), (53, 56, "c"),
           (52, 70, "s"), (51, 86, "c")]
QUILL = [(48.5, 99, "c"), (44, 80, "s"), (35, 46, "s"), (24, 14, "s"), (17, -4, "c")]

# glasses (ellipses), right lens 7 % larger
LENS_L = (81.5, 121.5, 20.5, 21.5)
LENS_R = (142.0, 118.0, 20.5 * 1.07, 21.5 * 1.07)

# nose: corner nodes at nostril wings and septum
NOSE_BASE = [(95, 150, "c"), (89, 157, "s"), (93, 164, "c"), (102, 162, "c"),   # left wing -> nostril
             (110, 166, "s"), (118, 162, "c"),                                    # septum
             (127, 164, "c"), (131, 157, "s"), (126, 150, "c")]
NOSE_BRIDGE_L = [(104, 129, "c"), (102, 140, "s"), (97, 149, "c")]
NOSE_BRIDGE_R = [(120, 127, "c"), (122, 138, "s"), (125, 148, "c")]

# lips: corners at lip corners and cupid's bow
UPPER_LIP = [(82, 176, "c"), (92, 172, "s"), (101, 169, "c"), (110, 172, "c"), (119, 168, "c"),
             (136, 169, "s"), (152, 174, "c")]
MOUTH = [(84, 179, "c"), (100, 181, "s"), (118, 182, "s"), (136, 180, "s"), (150, 176, "c")]
LOWER_LIP = [(88, 183, "c"), (100, 191, "s"), (117, 194, "s"), (134, 190, "s"), (146, 181, "c")]

# brows: tapered closed shapes sitting just above the frames (separated by a clear gap)
BROW_L = [(64, 96, "c"), (80, 92, "s"), (98, 96, "c"), (80, 94.6, "s")]
BROW_R = [(124, 90, "c"), (142, 86, "s"), (162, 90, "c"), (142, 88.6, "s")]

def P(d, w, fill="none", join="round", cap="round", miter=None):
    return dict(d=d, w=w, fill=fill, join=join, cap=cap, miter=miter)

GROUPS = {
    "feather": [P(bez(FEATHER, closed=True), FEAT, join="miter", miter=2.2),
                P(bez(QUILL), SIL - 0.6, cap="butt")]
               + [P(bez([(qx, qy, "c"), (qx - w * 0.55, qy - 3, "s"), (qx - w, qy - 8, "c")]), FINE)
                  for qx, qy, w in [(45, 86, 12), (42, 72, 16), (39, 60, 18), (35, 47, 18), (31, 34, 15), (27, 22, 11)]]
               + [P(bez([(qx, qy, "c"), (qx + w * 0.5, qy - 4, "s"), (qx + w, qy - 10, "c")]), FINE)
                  for qx, qy, w in [(44, 80, 7), (40, 66, 11), (37, 53, 13), (33, 40, 13), (29, 27, 10)]],
    "cap": [P(bez(CROWN), SIL, join="miter", miter=2.2), P(bez(BRIM_LOW), SIL), P(bez(BRIM_TOP), DET),
            P(bez([(160, 21, "c"), (167, 26, "s"), (171, 32, "c")]), DET)],
    "face outline": [P(bez(FACE), SIL, join="miter", miter=2.2),
                     P(bez(EAR_L), SIL), P(bez(EAR_R), SIL), P(bez(EAR_L_IN), DET), P(bez(EAR_R_IN), DET),
                     P(bez(NECK_L), FEAT), P(bez(NECK_R), FEAT)],
    "glasses": [P(ellipse(*LENS_L), FEAT + 0.5), P(ellipse(*LENS_R), FEAT + 0.5),
                P(ellipse(LENS_L[0], LENS_L[1], LENS_L[2] - 2.8, LENS_L[3] - 2.8), FINE),
                P(ellipse(LENS_R[0], LENS_R[1], LENS_R[2] - 3.0, LENS_R[3] - 3.0), FINE),
                P(bez([(102.0, 117, "c"), (110, 112.5, "s"), (120.1, 114, "c")]), FEAT),    # bridge
                P(bez([(61.0, 117, "c"), (57, 112, "s"), (55.5, 108, "c")]), FEAT),         # left temple arm
                P(bez([(164.0, 113, "c"), (170, 111, "s"), (176, 110.5, "c")]), FEAT)],     # right temple arm
    "facial features": [
        # brows (filled, tapered) — kept clear of the frames
        P(bez(BROW_L, closed=True), 0, fill="ink"), P(bez(BROW_R, closed=True), 0, fill="ink"),
        # eyes: iris ring, pupil, catchlight (upper left), upper eyelid crease
        P(ellipse(81.5, 121.5, 9.6), FEAT), P(ellipse(81.5, 121.5, 3.5), 0, fill="ink"),
        P(ellipse(79.2, 119.0, 1.0), 0, fill="paper"),
        P(ellipse(142, 117.5, 10.3), FEAT), P(ellipse(142, 117.5, 3.8), 0, fill="ink"),
        P(ellipse(139.6, 114.9, 1.1), 0, fill="paper"),
        P(arc(81.5, 121.5, 13.2, 13.2, 205, 335), DET), P(arc(142, 117.5, 14.0, 14.0, 205, 335), DET),
        # brow furrow between the lenses (two short creases with corners)
        P(bez([(105, 104, "c"), (109, 101.5, "s"), (113, 102, "c")]), DET),
        P(bez([(106.5, 108, "c"), (110, 106.5, "s"), (114, 107, "c")]), FINE),
        P(bez([(111.5, 84, "c"), (112.2, 96, "c")]), DET),
        # nose
        P(bez(NOSE_BRIDGE_L), DET), P(bez(NOSE_BRIDGE_R), DET), P(bez(NOSE_BASE), FEAT, join="miter", miter=2.2),
        # lips
        P(bez(UPPER_LIP), FEAT, join="miter", miter=2.2), P(bez(MOUTH), SIL - 0.5), P(bez(LOWER_LIP), FEAT),
        # creases: nasolabial folds and right cheek
        P(bez([(84, 160, "c"), (80, 168, "s"), (79, 175, "c")]), FINE),
        P(bez([(136, 158, "c"), (144, 166, "s"), (149, 173, "c")]), FINE),
    ],
}

# ================================================================ fills and facial planes
BASES = {
    "skin": bez(FACE[:-1] + [(176, 98, "c"), (178, 82, "c")] + [(x, y, k) for x, y, k in BRIM_LOW[::-1][1:]], closed=True),
    "ear-left": bez(EAR_L + [(56, 130, "s")], closed=True),
    "ear-right": bez(EAR_R + [(175, 128, "s")], closed=True),
    "neck": bez([(80, 192, "c"), (79, 222, "s"), (72, 282, "c"), (164, 282, "c"), (154, 226, "s"), (150, 196, "c"),
                 (142, 200, "c"), (116, 206, "s"), (86, 196, "c")], closed=True),
    "cap": bez(CROWN + [(x, y, k) for x, y, k in BRIM_LOW[::-1]], closed=True),
    "brim": bez(BRIM_TOP + [(178, 80, "c")] + [(x, y, k) for x, y, k in BRIM_LOW[::-1]] + [(57, 78, "c")], closed=True),
    "feather": bez(FEATHER, closed=True),
}

# facial planes — light from the upper left. Shadows are closed shapes with deliberate corners.
PLANES = {
    # highlights
    "hl-forehead":  bez([(70, 97, "c"), (96, 88, "s"), (126, 85, "c"), (112, 93, "s"), (82, 100, "c")], closed=True),
    "hl-nose-bridge": bez([(105, 127, "c"), (109, 125, "c"), (110, 140, "s"), (107, 152, "c"), (104, 142, "s")], closed=True),
    "hl-cheekbone-l": bez([(58, 146, "c"), (70, 143, "c"), (80, 148, "c"), (66, 154, "c")], closed=True),
    "hl-cheekbone-r": bez([(127, 145, "c"), (137, 144, "c"), (130, 149, "c")], closed=True),
    "hl-chin":      bez([(104, 199, "c"), (114, 197, "c"), (122, 200, "c"), (112, 202, "c")], closed=True),
    # shadows
    "sh-under-cap": bez([(55, 89, "c"), (80, 77, "s"), (106, 70, "s"), (128, 68, "s"), (156, 69, "s"), (178, 80, "c"),
                         (176, 97, "c"), (150, 85, "s"), (120, 81, "s"), (88, 85, "s"), (58, 96, "c")], closed=True),
    "sh-nose-plane": bez([(120, 127, "c"), (126, 148, "c"), (124, 152, "c"), (119, 146, "s"), (118, 132, "c")], closed=True),
    "sh-under-nose": bez([(97, 164, "c"), (110, 167, "s"), (125, 164, "c"), (117, 170, "s"), (104, 170, "c")], closed=True),
    "sh-glasses-l": bez([(66, 141, "c"), (82, 150, "s"), (97, 145, "c"), (84, 153, "s"), (70, 149, "c")], closed=True),
    "sh-glasses-r": bez([(126, 138, "c"), (143, 147, "s"), (161, 139, "c"), (146, 150, "s"), (131, 146, "c")], closed=True),
    "sh-right-plane": bez([(176, 98, "c"), (175, 122, "s"), (170, 149, "c"), (160, 180, "c"), (142, 200, "c"),
                           (150, 178, "c"), (157, 150, "c"), (163, 120, "s"), (170, 104, "c")], closed=True),
    "sh-under-cheek-l": bez([(56, 137, "c"), (63, 166, "c"), (70, 162, "c"), (62, 146, "c")], closed=True),
    "sh-lower-lip":  bez([(94, 191, "c"), (117, 197, "s"), (140, 189, "c"), (126, 199, "s"), (106, 199, "c")], closed=True),
    "sh-neck":       bez([(81, 204, "c"), (116, 214, "s"), (152, 206, "c"), (153, 214, "c"), (116, 223, "s"), (80, 213, "c")], closed=True),
}

ORDER = ["face outline", "cap", "feather", "glasses", "facial features"]

def svg_groups(ink="#000000", paper="#FFFFFF", scale=1.0, prefix=""):
    out = []
    for name in ORDER:
        gink = ink.get(name, ink["default"]) if isinstance(ink, dict) else ink
        parts = []
        for p in GROUPS[name]:
            fill = {"ink": gink, "paper": paper}.get(p["fill"], p["fill"])
            if p["w"]:
                ml = f' stroke-miterlimit="{p["miter"]}"' if p["miter"] else ""
                stroke = (f' stroke="{gink}" stroke-width="{p["w"]}" stroke-linecap="{p["cap"]}" '
                          f'stroke-linejoin="{p["join"]}"{ml}')
            else:
                stroke = ""
            parts.append(f'<path d="{p["d"]}" fill="{fill}"{stroke}/>')
        out.append(f'<g id="{prefix}{name.replace(" ", "-")}" data-name="{name}">' + "".join(parts) + "</g>")
    return out
