"""Join the three Farm 1 AI clips into one smooth 25 fps 1920x1080 frame sequence
and track label anchor points through the orbit clip.

Each clip's frames are played at 25 fps (source is 24 fps, ~4% faster).
At each cut the end of the outgoing clip is eased (similarity transform) onto
the first frame of the incoming clip, then cross-faded, so there is no jump.
Labels are tracked with a frame-to-frame homography estimated from features on
the farm (background excluded), seeded from hand-picked points on orbit frame 0.
"""
import cv2, json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "farms")
OUT = os.path.join(ROOT, "out", "f1seq")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080

def read(path):
    cap = cv2.VideoCapture(path); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        h, w = f.shape[:2]
        if h != H or w != W:
            if h >= H and w == W: f = f[(h - H) // 2:(h - H) // 2 + H]
            else: f = cv2.resize(f, (W, H), interpolation=cv2.INTER_LANCZOS4)
        frames.append(f)
    return frames

c1 = read(os.path.join(SRC, "farm1_clip1_growthA.mp4"))
c2 = read(os.path.join(SRC, "farm1_clip2_growthB.mp4"))
c3 = read(os.path.join(SRC, "farm1_clip3_orbit.mp4"))
print("frames", len(c1), len(c2), len(c3))

orb = cv2.ORB_create(4000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def similarity(a, b):
    """Similarity transform mapping frame a onto frame b."""
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    ka, da = orb.detectAndCompute(ga, None); kb, db = orb.detectAndCompute(gb, None)
    m = sorted(bf.match(da, db), key=lambda x: x.distance)[:800]
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=4)
    print("  similarity inliers", int(inl.sum()), "of", len(m))
    return M

def ease(k): return k * k * (3 - 2 * k)

def bridge(a_frames, b_first, n_move=22, n_fade=10):
    """Warp the tail of clip A progressively onto B's first frame; return the
    modified tail (n_move frames) whose last n_fade frames cross-fade into B."""
    M = similarity(a_frames[-1], b_first)
    I = np.float32([[1, 0, 0], [0, 1, 0]])
    tail = a_frames[-n_move:]; out = []
    for i, f in enumerate(tail):
        k = ease((i + 1) / n_move)
        Mi = (I + (M - I) * k).astype(np.float32)
        w = cv2.warpAffine(f, Mi, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        j = i - (n_move - n_fade)
        if j >= 0:
            t = ease((j + 1) / (n_fade + 1))
            w = cv2.addWeighted(w, 1 - t, b_first, t, 0)
        out.append(w)
    return out

seq = []
HEAD = 25                                   # 1 s hold on the empty plot (spare frames)
seq += [c1[0]] * HEAD
seq += c1[:-22] + bridge(c1, c2[0])
seq += c2[:-22] + bridge(c2, c3[0])
orbit_start = len(seq)
seq += c3
TAIL = 50                                   # 2 s hold on the final frame (spare frames)
seq += [c3[-1]] * TAIL
print("total frames", len(seq), "=", len(seq) / 25, "s")

# ---------------- tracking through the orbit ----------------
# anchors picked on orbit frame 0 (1916x1080 source, scaled to 1920)
sx = W / 1916
ANCH = {
    "entrance": (1072, 815), "entrance_shed": (1150, 612), "storage_shed": (1530, 545),
    "breadfruit": (520, 470), "watermelon": (690, 540), "irrigation": (432, 590),
    "pump": (292, 330), "fence": (660, 880),
    "cctv1": (186, 168), "cctv2": (1222, 100), "cctv3": (1830, 640), "cctv4": (373, 985),
}
pts = {k: np.float32([v[0] * sx, v[1]]) for k, v in ANCH.items()}
# farm-top mask on frame 0 (polygon around the block top) to keep background out of the fit
mask0 = np.zeros((H, W), np.uint8)
cv2.fillPoly(mask0, [np.int32([[150, 140], [1240, 50], [1910, 640], [1880, 780], [350, 1000], [140, 260]])], 255)

track = {k: [] for k in pts}
H_acc = np.eye(3)
prev = cv2.cvtColor(c3[0], cv2.COLOR_BGR2GRAY)
mask = mask0
for i in range(len(c3)):
    if i > 0:
        cur = cv2.cvtColor(c3[i], cv2.COLOR_BGR2GRAY)
        p0 = cv2.goodFeaturesToTrack(prev, 1500, 0.01, 8, mask=mask)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, p0, None, winSize=(25, 25), maxLevel=4)
        good = st.ravel() == 1
        Hm, _ = cv2.findHomography(p0[good], p1[good], cv2.RANSAC, 3.0)
        H_acc = Hm @ H_acc
        mask = cv2.warpPerspective(mask0, H_acc, (W, H))
        prev = cur
    for k, p in pts.items():
        q = H_acc @ np.array([p[0], p[1], 1.0]); track[k].append([round(float(q[0] / q[2]), 1), round(float(q[1] / q[2]), 1)])

# hold positions over the tail
for k in track: track[k] += [track[k][-1]] * TAIL
json.dump({"orbit_start": orbit_start, "frames": len(seq), "track": track},
          open(os.path.join(ROOT, "data", "farm1_track.json"), "w"))
open(os.path.join(ROOT, "data", "farm1_track.js"), "w").write(
    "window.TRACK = " + json.dumps({"orbit_start": orbit_start, "frames": len(seq), "track": track}) + ";\n")

for i, f in enumerate(seq):
    cv2.imwrite(os.path.join(OUT, f"{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 94])
print("written", len(seq))
