"""Join the three coconut timelapse clips (plant -> sprout -> seedling -> palm)
into one silent 25 fps 1920x1080 MP4, with the same cut bridging as the farms.

Usage: python3 data/build_coconut.py out.mp4
"""
import cv2, os, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "coconut")
OUT = sys.argv[1]
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

clips = [read(os.path.join(SRC, n)) for n in ("coco_clip1_plant.mp4", "coco_clip2_sprout.mp4", "coco_clip3_tree.mp4")]
print("frames", [len(c) for c in clips])

orb = cv2.ORB_create(4000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def similarity(a, b):
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    ka, da = orb.detectAndCompute(ga, None); kb, db = orb.detectAndCompute(gb, None)
    m = sorted(bf.match(da, db), key=lambda x: x.distance)[:800]
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=4)
    print("  similarity inliers", int(inl.sum()), "of", len(m), M.round(3).tolist())
    return M

def ease(k): return k * k * (3 - 2 * k)

def bridge(a_frames, b_first, n_move=22, n_fade=10):
    M = similarity(a_frames[-1], b_first)
    I = np.float32([[1, 0, 0], [0, 1, 0]])
    out = []
    for i, f in enumerate(a_frames[-n_move:]):
        Mi = (I + (M - I) * ease((i + 1) / n_move)).astype(np.float32)
        w = cv2.warpAffine(f, Mi, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        j = i - (n_move - n_fade)
        if j >= 0:
            t = ease((j + 1) / (n_fade + 1))
            w = cv2.addWeighted(w, 1 - t, b_first, t, 0)
        out.append(w)
    return out

c1, c2, c3 = clips
seq = [c1[0]] * 25                          # 1 s spare hold at the start
seq += c1[:-22] + bridge(c1, c2[0])
seq += c2[:-22] + bridge(c2, c3[0])
seq += c3 + [c3[-1]] * 50                   # 2 s spare hold at the end
print("total frames", len(seq), "=", len(seq) / 25, "s")

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "25", "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for f in seq: ff.stdin.write(f.tobytes())
ff.stdin.close(); ff.wait()
print("wrote", OUT)
