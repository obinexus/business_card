"""Eze portrait — hand-placed vector trace of the supplied pencil sketch.

Coordinates are in the reference image's own 200 x 200 px space, so the trace can be overlaid
on eze.jpg to check fit. Each feature is a named group; strokes use round caps/joins and
deliberate weights:  W_OUT outlines > W_FEAT features > W_DET details > W_SHADE hatching.
"""
W_OUT, W_FEAT, W_DET, W_SHADE = 2.4, 1.8, 1.1, 0.6

def P(d, w, fill="none", cls="ink", extra=""):
    return dict(d=d, w=w, fill=fill, cls=cls, extra=extra)

GROUPS = {}

# ---------------------------------------------------------------- feather (plume rising from the cap's left side)
quill = "M47 100 C44 82 40 62 34 44 C28 26 22 12 15 -2"
plume = ("M46 96 C34 86 22 72 14 56 C6 40 4 22 8 4 C10 -2 14 -6 18 -6 "
         "C30 -2 42 6 52 16 C58 22 60 30 56 40 C52 54 50 70 50 86 Z")
barbs = []
# barbs along the quill: alternating left/right, sweeping upward
import math
def quill_pt(t):
    # cubic Bezier points of the quill segments (two cubics); t in 0..1 over whole quill
    segs = [((47, 100), (44, 82), (40, 62), (34, 44)), ((34, 44), (28, 26), (22, 12), (15, -2))]
    s = min(int(t * 2), 1); u = t * 2 - s
    p0, p1, p2, p3 = segs[s]
    b = lambda a, b_, c, d: (1-u)**3*a + 3*(1-u)**2*u*b_ + 3*(1-u)*u*u*c + u**3*d
    return b(p0[0], p1[0], p2[0], p3[0]), b(p0[1], p1[1], p2[1], p3[1])
for i in range(1, 15):
    t = i / 15
    x, y = quill_pt(t)
    width = 16 * math.sin(math.pi * min(1, t * 1.15)) + 4
    # left barb
    barbs.append(f"M{x:.1f} {y:.1f} C{x-width*0.4:.1f} {y-2:.1f} {x-width*0.8:.1f} {y-5:.1f} {x-width:.1f} {y-9:.1f}")
    # right barb (shorter: the plume leans left)
    wr = width * 0.75
    barbs.append(f"M{x:.1f} {y:.1f} C{x+wr*0.4:.1f} {y-3:.1f} {x+wr*0.8:.1f} {y-6:.1f} {x+wr:.1f} {y-11:.1f}")
GROUPS["feather"] = [P(plume, W_FEAT), P(quill, W_OUT)] + [P(b, W_SHADE + 0.15) for b in barbs]

# ---------------------------------------------------------------- cap (rounded crown with a brim band)
crown = "M56 86 C58 62 62 36 72 26 C86 16 104 18 120 15 C140 13 156 22 166 38 C174 52 177 70 177 92"
brim_top = "M62 66 C80 58 104 56 128 57 C148 58 164 62 174 70"
brim_low = "M54 89 C74 78 98 71 124 69 C146 68 166 72 178 82"
crown_hl = "M160 20 C166 23 170 27 172 31"   # small sheen mark on the crown (upper right in sketch)
GROUPS["cap"] = [P(crown, W_OUT), P(brim_low, W_OUT), P(brim_top, W_DET), P(crown_hl, W_DET)]

# ---------------------------------------------------------------- face outline (cheeks, jaw, chin + neck start)
face_l = "M58 92 C54 104 54 118 55 132 C56 146 60 160 68 172 C74 182 80 192 88 200 C94 206 104 210 116 210"
face_r = "M174 98 C176 112 176 126 172 140 C168 154 164 166 160 178 C156 190 146 202 134 208 C128 210 122 211 116 210"
ear_l_out = "M52 106 C42 104 32 108 31 120 C30 132 38 142 46 148 C50 152 54 154 58 156"
ear_l_in = "M48 122 C44 124 44 130 48 134 C52 138 54 142 53 146"
ear_r_out = "M176 107 C186 103 196 109 196 121 C196 135 188 145 180 151 C176 153 172 153 170 151"
ear_r_in = "M182 119 C188 121 188 129 184 135 C181 139 180 143 182 147"
neck = "M80 196 C80 214 78 240 72 282 M152 196 C152 214 157 240 164 282"
GROUPS["face outline"] = [P(face_l, W_OUT), P(face_r, W_OUT), P(ear_l_out, W_OUT), P(ear_r_out, W_OUT),
                          P(ear_l_in, W_DET), P(ear_r_in, W_DET), P(neck, W_FEAT)]

# ---------------------------------------------------------------- glasses (two round lenses, bridge, temples)
def circle(cx, cy, rx, ry=None):
    ry = ry or rx; k = 0.5523
    return (f"M{cx-rx} {cy} C{cx-rx} {cy-ry*k:.2f} {cx-rx*k:.2f} {cy-ry} {cx} {cy-ry} "
            f"C{cx+rx*k:.2f} {cy-ry} {cx+rx} {cy-ry*k:.2f} {cx+rx} {cy} "
            f"C{cx+rx} {cy+ry*k:.2f} {cx+rx*k:.2f} {cy+ry} {cx} {cy+ry} "
            f"C{cx-rx*k:.2f} {cy+ry} {cx-rx} {cy+ry*k:.2f} {cx-rx} {cy} Z")
LENS_L = (81, 122, 21.5, 22.5)
LENS_R = (142, 118, 24, 23)
GROUPS["glasses"] = [
    P(circle(*LENS_L), W_OUT), P(circle(*LENS_R), W_OUT),
    P(circle(81, 122, 18.5, 19.5), W_SHADE + 0.2),          # inner rim
    P(circle(142, 118, 21, 20), W_SHADE + 0.2),
    P("M102.5 116 C107 112 113 111 118.2 113", W_FEAT),    # bridge
    P("M60 118 C56 114 54 110 52 108", W_FEAT),             # left temple to ear
    P("M166 114 C170 112 174 112 177 112", W_FEAT),         # right temple to ear
]

# ---------------------------------------------------------------- facial features (eyes, brows, nose, lips)
GROUPS["facial features"] = [
    # eyes: iris ring + filled pupil (wide, staring expression)
    P(circle(81, 121, 9.5, 9.5), W_FEAT), P(circle(81, 121, 3.4), 0, fill="ink"),
    P(circle(141, 117, 11, 10), W_FEAT), P(circle(141, 117, 4.2, 4.0), 0, fill="ink"),
    P(circle(78.5, 118.5, 0.9), 0, fill="paper"), P(circle(138.5, 114.5, 1.1), 0, fill="paper"),  # catchlights (upper left)
    # brow furrow between the lenses
    P("M104 104 C107 101 111 101 114 104", W_DET), P("M106 108 C109 106 113 106 116 108", W_DET),
    P("M112 84 L112.6 96", W_DET), P("M109 90 L110 97", W_SHADE + 0.3),
    # nose: bridge, tip, nostrils, base
    P("M104 128 C103 136 101 142 98 148", W_DET),
    P("M120 126 C121 134 123 140 125 146", W_DET),
    P("M96 150 C90 152 89 160 95 164 C99 166 103 163 106 160", W_FEAT),
    P("M125 149 C131 151 132 159 127 163 C123 166 119 163 117 160", W_FEAT),
    P("M106 160 C110 163 114 163 117 160", W_FEAT),
    # lips: upper lip, mouth line, lower lip
    P("M82 174 C90 169 98 167 104 169 C108 170 111 171 114 170 C122 166 134 166 150 173", W_FEAT),
    P("M84 178 C96 179 106 181 116 181 C128 181 140 178 150 175", W_OUT),
    P("M88 183 C98 191 108 193 118 192 C130 191 140 186 146 180", W_FEAT),
]

# ---------------------------------------------------------------- shading (hatching, stubble, form lines)
shade = []
for i in range(9):   # shadow under the cap brim across the forehead
    x = 68 + i * 12
    shade.append(f"M{x} {84 - (2 if 3 < i < 7 else 0)} C{x+3} {86:.0f} {x+6} {88:.0f} {x+8} {89:.0f}")
for i in range(6):   # shadow on the nose's right flank (light from upper left)
    y = 132 + i * 5
    shade.append(f"M{121 + i*0.6:.1f} {y} C{123+i*0.6:.1f} {y+1.5} {124+i*0.6:.1f} {y+3} {125+i*0.6:.1f} {y+4}")
for i in range(7):   # moustache stubble strokes above the upper lip
    x = 96 + i * 6
    shade.append(f"M{x} {165 + (i % 2)} L{x+2} {168}")
for i in range(5):   # under-lip shadow
    x = 98 + i * 8
    shade.append(f"M{x} {196} C{x+2} {198} {x+4} {199} {x+6} {199}")
for i in range(6):   # right cheek and jaw shadow
    y = 146 + i * 8
    shade.append(f"M{166 - i*1.5:.1f} {y} C{164 - i*1.5:.1f} {y+3} {162 - i*1.5:.1f} {y+5} {160 - i*1.5:.1f} {y+6}")
shade.append("M70 160 C72 168 76 174 80 178")      # left nasolabial / cheek form
shade.append("M152 150 C156 160 156 168 152 176")  # right cheek form
GROUPS["shading"] = [P(s, W_SHADE) for s in shade]

ORDER = ["shading", "face outline", "cap", "feather", "glasses", "facial features"]

def svg_groups(ink="#000000", paper="#FFFFFF", scale=1.0, prefix=""):
    out = []
    for name in ORDER:
        parts = []
        gink = ink.get(name, ink["default"]) if isinstance(ink, dict) else ink
        for p in GROUPS[name]:
            fill = {"ink": gink, "paper": paper}.get(p["fill"], p["fill"])
            stroke = f' stroke="{gink}" stroke-width="{p["w"]}" stroke-linecap="round" stroke-linejoin="round"' if p["w"] else ""
            parts.append(f'<path d="{p["d"]}" fill="{fill}"{stroke}/>')
        gid = prefix + name.replace(" ", "-")
        out.append(f'<g id="{gid}" data-name="{name}">' + "".join(parts) + "</g>")
    return out
