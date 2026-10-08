"""Even out the growth speed of the joined coconut timelapse.

The three AI clips grow at very different rates (the seedling-to-palm clip
changes ~15x faster per frame than the sprout clip). After the hand has
planted the coconut, frames are re-timed so the amount of visible change per
output frame is roughly constant; in-between frames are synthesised with
optical-flow interpolation.

Usage: python3 data/retime_coconut.py joined.mp4 out.mp4
"""
import cv2, subprocess, sys
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
KEEP = 140          # head hold + hand planting: left at real speed
END = 606           # last frame of growth (the rest is the spare hold)
GROW_OUT = 600      # output frames for the growth section (24 s)
TAIL = 50           # 2 s spare hold at the end
P = 0.5             # how strongly to even out (1 = fully constant pixel change)

cap = cv2.VideoCapture(SRC); F = []
while True:
    ok, f = cap.read()
    if not ok: break
    F.append(f)
H, W = F[0].shape[:2]

small = [cv2.cvtColor(cv2.resize(f, (240, 135), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F]
d = np.array([0.0] + [np.abs(small[i] - small[i - 1]).mean() for i in range(1, len(F))])
k = np.exp(-0.5 * (np.arange(-18, 19) / 6) ** 2); k /= k.sum()
w = np.convolve(np.pad(d, 18, mode="edge"), k, "valid")[KEEP:END] ** P
cum = np.concatenate([[0], np.cumsum(w)])           # cum[j] = progress at source KEEP+j
targets = np.linspace(0, cum[-1], GROW_OUT, endpoint=False)
src_pos = KEEP + np.interp(targets, cum, np.arange(len(cum)))

dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
flow_cache = {}
def flows(i):
    if i not in flow_cache:
        a = cv2.cvtColor(F[i], cv2.COLOR_BGR2GRAY); b = cv2.cvtColor(F[i + 1], cv2.COLOR_BGR2GRAY)
        flow_cache.clear()
        flow_cache[i] = (dis.calc(a, b, None), dis.calc(b, a, None))
    return flow_cache[i]

def interp(pos):
    i = int(np.floor(pos)); t = np.float32(pos - i)
    if t < 0.02 or i + 1 >= len(F): return F[i]
    if t > 0.98: return F[i + 1]
    fab, fba = flows(i)
    a = cv2.remap(F[i], gx - fab[..., 0] * t, gy - fab[..., 1] * t, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(F[i + 1], gx - fba[..., 0] * (1 - t), gy - fba[..., 1] * (1 - t), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(a, 1 - t, b, t, 0)

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "25", "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
n = 0
for f in F[:KEEP]: ff.stdin.write(f.tobytes()); n += 1
for p in src_pos: ff.stdin.write(interp(p).tobytes()); n += 1
for _ in range(TAIL): ff.stdin.write(F[END - 1].tobytes()); n += 1
ff.stdin.close(); ff.wait()
print("frames", n, "=", n / 25, "s; growth speed factors per clip:",
      [round(float(np.diff(src_pos)[(src_pos[:-1] >= a) & (src_pos[:-1] < b)].mean()), 2) for a, b in ((140, 218), (218, 411), (411, 606))])
