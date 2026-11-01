import gen2 as g
from gen2 import Line, SAFE, U, W, H
def back_variant(name, mkey="sans-bold", msize=g.MMUCO_PT, okey="sans-semi", skey="sans", nkey="serif", ckey="sans", cpt=9.0):
    o = Line(g.OBX, okey, g.OBX_PT, 30, "OBINexus"); m = Line(g.MMUCO, mkey, msize, 40 if mkey!="anton" else 20, "MMUCO")
    s = Line(g.SUB, skey, g.SUB_PT, 10, "Physical-OSes"); n = Line(g.NAME, nkey, g.NAME_PT, 0, "Name")
    cs = [Line(t, ckey, cpt) for t in (g.EMAIL, g.PHONE, g.WEB)]
    for l in (o, m, s, n, *cs): l.left(SAFE)
    o.top(0); g.stack([o, m, s], [1.5, 1.5]); n.top(s.bottom + 4); cs[0].top(n.bottom + 4)
    pitch = (n.box[1] + g.QR_SIZE - cs[0].oy) / 2
    for a, b in zip(cs, cs[1:]): b.base(a.oy + pitch)
    sh = (H - (cs[-1].oy - o.box[1])) / 2 - o.box[1]
    for l in (o, m, s, n, *cs): l.oy += sh
    q, qb, _ = g.qr(W - SAFE - g.QR_SIZE, n.box[1], g.QR_SIZE)
    g.write("spec-" + name, name, [q], [o, m, s, n, *cs], [])
    print(name, "MMUCO cap", round(m.cap, 2), "mm, width", round(m.width, 2))
def emblem_pair(name, mkey, msize):
    e, eb, _ = g.emblem(4 + 15, 12.5, 30)
    o = Line(g.OBX, "sans-semi", g.OBX_PT, 30); m = Line(g.MMUCO, mkey, msize, 40 if mkey!="anton" else 20); s = Line(g.SUB, "sans", g.SUB_PT, 10)
    for l in (o, m, s): l.left(40)
    o.top(0); g.stack([o, m, s], [1.5, 1.5]); hgt = s.bottom - o.box[1]
    sh = 27.5 - hgt / 2 - o.box[1]
    for l in (o, m, s): l.oy += sh
    g.write("spec-" + name, name, [e], [o, m, s], [])
back_variant("final-SourceSans-Bold")
back_variant("Anton-13pt", mkey="anton")
back_variant("Anton-10pt-cap-matched", mkey="anton", msize=10.0)
back_variant("BubblerOne-supporting", skey="bubbler", ckey="bubbler")
back_variant("name-in-Source-Sans", nkey="sans")
emblem_pair("emblem+Anton", "anton", 13)
emblem_pair("emblem+SourceSansBold", "sans-bold", 13)
