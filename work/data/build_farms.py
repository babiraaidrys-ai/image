"""Farm layouts traced from '10 ISLANDS AGRO FORESTRY PLANTATIONS.pdf'.

Coordinates were read off a 2000px-wide render of each page and are
normalised to the plot boundary: (0,0) top-left, (100,100) bottom-right
(each plot is ~100 m x 100 m on the drawing).
"""
import json

def norm(box):
    x0, y0, x1, y1 = box
    return lambda x, y: (round((x - x0) / (x1 - x0) * 100, 2),
                         round((y - y0) / (y1 - y0) * 100, 2))

def seg(n, pts):
    return [list(n(*pts[0])) + list(n(*pts[1]))]

def lines(n, items):
    out = []
    for a, b in items:
        out += seg(n, (a, b))
    return out

def edge_points(n, x0, y0, x1, y1, step):
    """Evenly spaced points along a straight edge (drawing px)."""
    import math
    L = math.hypot(x1 - x0, y1 - y0)
    k = int(L // step)
    return [list(n(x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k)) for i in range(k + 1)]

farms = {}

# ---------------- Farm 1: breadfruit + watermelon ----------------
n = norm((643, 279, 1565, 1199))
trees = [list(n(722 + 70.2 * i, 354 + 70.2 * j)) for j in range(13) for i in range(12)]
melons = []
for i in range(12):
    for j in range(12):
        y0 = 354 + 70.2 * j
        melons += [list(n(722 + 70.2 * i, y0 + 20)), list(n(722 + 70.2 * i, y0 + 48))]
farms["farm1"] = {
    "trees": trees,
    "intercrop": melons,
    "perimeter": edge_points(n, 645, 279, 1563, 279, 22.5)
                 + edge_points(n, 645, 301, 645, 1199, 22.5)
                 + edge_points(n, 1563, 301, 1563, 1199, 22.5),
    "pump": list(n(664, 675)),
    "pumpLink": list(n(705, 675)),
    "water": lines(n, [
        ((676, 675), (705, 675)),
        ((705, 575), (705, 675)), ((705, 675), (705, 903)), ((705, 903), (705, 1178)),
        ((705, 575), (778, 575)), ((778, 575), (987, 575)), ((987, 575), (1230, 575)),
        ((1230, 575), (1480, 575)), ((1480, 575), (1538, 575)),
        ((778, 575), (778, 306)), ((987, 575), (987, 306)),
        ((1230, 575), (1230, 306)), ((1480, 575), (1480, 306)),
        ((705, 903), (914, 903)), ((914, 903), (1198, 903)), ((1198, 903), (1538, 903)),
        ((914, 903), (914, 1178)),
        ((1198, 903), (1198, 1185)), ((1198, 1185), (1538, 1185)),
    ]),
}

# ---------------- Farm 2: coconut palm + bush beans / okra ----------------
n = norm((611, 245, 1531, 1165))
colsL = [661 + 42.2 * i for i in range(10)]
colsR = [1110 + 42.2 * i for i in range(10)]
rows = [287 + 41.8 * j for j in range(21)]
palms = [list(n(x, y)) for y in rows for x in colsL + colsR]
beds_y = [(284 + 120.9 * k, 284 + 120.9 * k + 112) for k in range(7)]
def beds(cols, kind):
    out = []
    for a, b in zip(cols, cols[1:]):
        for off in (11, 28):
            x = a + off
            for y0, y1 in beds_y:
                (u0, v0), (u1, v1) = n(x - 3, y0), n(x + 3, y1)
                out.append({"kind": kind, "x": u0, "y": v0, "w": round(u1 - u0, 2), "h": round(v1 - v0, 2)})
    return out
farms["farm2"] = {
    "trees": palms,
    "beds": beds(colsL, "beans") + beds(colsR, "okra"),
    "perimeter": edge_points(n, 612, 268, 612, 1165, 22.5) + edge_points(n, 1530, 268, 1530, 1165, 22.5),
    "pump": list(n(631, 762)),
    "pumpLink": list(n(643, 762)),
    "water": lines(n, [
        ((643, 762), (876, 762)),
        ((876, 762), (876, 520)), ((876, 520), (876, 256)),
        ((876, 762), (876, 1003)), ((876, 1003), (876, 1118)),
        ((876, 520), (625, 520)), ((876, 1003), (625, 1003)),
        ((1157, 762), (1520, 762)),
        ((1157, 762), (1157, 520)), ((1157, 520), (1157, 256)),
        ((1157, 762), (1157, 1003)),
        ((1157, 520), (1520, 520)), ((1157, 1003), (1520, 1003)),
    ]),
}

# ---------------- Farm 3: lemon ----------------
n = norm((605, 246, 1527, 1166))
cols = [652 + 42.1 * i for i in range(10)] + [1101 + 42.2 * i for i in range(10)]
rows = [324 + 42.1 * j for j in range(20)]
farms["farm3"] = {
    "trees": [list(n(x, y)) for y in rows for x in cols],
    "perimeter": edge_points(n, 606, 268, 606, 1166, 22.5) + edge_points(n, 1525, 268, 1525, 1166, 22.5),
    "pump": list(n(622, 683)),
    "pumpLink": list(n(637, 683)),
    "water": lines(n, [
        ((630, 683), (637, 683)),
        ((637, 683), (637, 425)), ((637, 683), (637, 1024)),
        ((637, 425), (1295, 425)), ((1295, 425), (1512, 425)),
        ((637, 1024), (1116, 1024)), ((1116, 1024), (1512, 1024)),
        ((1116, 1024), (1116, 688)), ((1116, 688), (850, 688)),
        ((1295, 425), (1295, 761)), ((1295, 761), (1512, 761)),
    ]),
}

# ---------------- Farm 4: moringa (drumstick) ----------------
n = norm((627, 191, 1549, 1112))
cols = [678 + 41.7 * i for i in range(10)] + [1122 + 41.8 * i for i in range(10)]
rows = [269 + 42.1 * j for j in range(19)]
farms["farm4"] = {
    "trees": [list(n(x, y)) for y in rows for x in cols],
    "perimeter": edge_points(n, 628, 213, 628, 1112, 22.5) + edge_points(n, 1547, 213, 1547, 1112, 22.5)
                 + edge_points(n, 650, 1112, 1525, 1112, 22.5),
    "pump": list(n(643, 710)),
    "pumpLink": list(n(659, 710)),
    "water": lines(n, [
        ((651, 710), (659, 710)),
        ((659, 710), (659, 629)), ((659, 629), (659, 235)),
        ((659, 710), (659, 929)),
        ((659, 629), (816, 629)), ((816, 629), (1233, 629)), ((1233, 629), (1528, 629)),
        ((816, 629), (816, 411)), ((816, 411), (816, 347)), ((816, 411), (977, 411)),
        ((1233, 629), (1233, 425)), ((1233, 425), (1528, 425)),
        ((659, 929), (786, 929)), ((786, 929), (1149, 929)), ((1149, 929), (1432, 929)), ((1432, 929), (1528, 929)),
        ((786, 929), (786, 1098)), ((1149, 929), (1149, 1098)), ((1432, 929), (1432, 1098)),
    ]),
    "support": [
        {"kind": "fertilizer", "c": list(n(676, 1076)), "r": 2.5},
        {"kind": "waiting", "c": list(n(1086, 1080)), "w": 9.5, "h": 3.7},
        {"kind": "tools", "c": list(n(1498, 1076)), "r": 2.5},
    ],
}

json.dump(farms, open(__file__.replace("build_farms.py", "farms.json"), "w"))
for k, v in farms.items():
    print(k, {kk: len(vv) for kk, vv in v.items() if isinstance(vv, list)})
open(__file__.replace("build_farms.py", "farms.js"), "w").write("window.FARMS = " + json.dumps(farms) + ";\n")
