"""Synthesised sound-effects bed for a farm growth + orbit clip (no music).

Usage: python3 sfx.py farm2 out.wav
Timings follow the frame sequence built by build_farm_seq.py (25 fps) and the
label delays used in scenes/farm_final.html.
"""
import json, os, sys, wave
import numpy as np

FARM, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(os.path.join(ROOT, "data", f"{FARM}_track.json")))
SR, FPS = 48000, 25
DUR = T["frames"] / FPS
N = int(DUR * SR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

# timeline (s)
HEAD = 1.0
CUT1 = (25 + 193) / FPS            # end of growth A
CUT2 = CUT1 + 193 / FPS            # end of growth B
ORBIT = T["orbit_start"] / FPS
LABEL_DT = [0.4, 1.0, 1.6, 2.4, 2.8, 3.2, 3.6, 4.2, 4.8, 5.6, 5.9, 6.2, 6.5] if FARM == "farm2" else \
           [0.4, 1.0, 1.6, 2.4, 3.0, 3.6, 4.2, 4.8, 5.6, 5.9, 6.2, 6.5]

# ---------- DSP helpers ----------
def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def fft_filter(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    # soft edges
    m = np.convolve(m, np.hanning(64) / np.hanning(64).sum(), mode="same")
    return np.fft.irfft(X * m, n=len(x))

def env_adsr(n, a, d, s_lvl, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR); s = max(0, n - a - d - r)
    return np.concatenate([np.linspace(0, 1, a, False), np.linspace(1, s_lvl, d, False), np.full(s, s_lvl), np.linspace(s_lvl, 0, r)])[:n]

def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:j] += sig[: j - i] * gain * gl * 1.414; R[i:j] += sig[: j - i] * gain * gr * 1.414

def ramp(t0, t1, v0, v1):
    t = np.arange(N) / SR
    return np.clip(v0 + (v1 - v0) * (t - t0) / (t1 - t0), min(v0, v1), max(v0, v1))

# ---------- ambience ----------
t = np.arange(N) / SR
fade = np.clip(t / 1.2, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1)
# ocean: low-passed noise with slow swells, slightly different per channel
for ch, ph in ((L, 0.0), (R, 1.3)):
    n = rng.standard_normal(N)
    wav = fft_filter(n, 60, 900)
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.5 + ph) ** 2
    ch += wav / np.abs(wav).max() * swell * 0.16 * fade
# breeze: band-passed noise, slow gusts; louder over the orbit (palms rustling)
for ch, ph in ((L, 0.4), (R, 2.1)):
    n = fft_filter(rng.standard_normal(N), 900, 5500)
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * t / 4.3 + ph) * np.sin(2 * np.pi * t / 2.9 + ph * 1.7)
    level = 0.035 + 0.04 * np.clip((t - CUT1) / 4, 0, 1)
    ch += n / np.abs(n).max() * gust * level * fade

# distant tropical birds: short FM chirps
def chirp(f0, f1, dur, warble=0.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.linspace(f0, f1, n) * (1 + warble * np.sin(2 * np.pi * 28 * tt))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return s * np.sin(np.pi * np.arange(n) / n) ** 2
bt = 1.5
while bt < DUR - 1.5:
    k = rng.integers(2, 4); f0 = rng.uniform(2600, 3800); pan = rng.uniform(-0.8, 0.8)
    for q in range(k):
        place(chirp(f0, f0 * rng.uniform(1.15, 1.4), rng.uniform(0.05, 0.09), 0.02), bt + q * rng.uniform(0.09, 0.14), 0.035, pan)
    bt += rng.uniform(1.6, 3.4)

# ---------- growth A: fence knocks, pump, water, sprouts ----------
def knock(freq=180, dur=0.16):
    n = int(dur * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 38) + 0.5 * np.sin(2 * np.pi * freq * 2.3 * tt) * np.exp(-tt * 55)
    click = fft_filter(rng.standard_normal(n), 1500, 6000) * np.exp(-tt * 260) * 0.6
    return body + click
for i in range(9):                       # fence posts going in around the plot
    tk = HEAD + 0.25 + i * 0.42
    place(knock(rng.uniform(150, 210)), tk, 0.22, np.sin(i * 0.9) * 0.7)

def pump_hum(t0, t1):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    spin = np.clip(tt / 1.2, 0, 1)
    f = 48 + 12 * spin
    s = np.sin(2 * np.pi * np.cumsum(np.full(n, 1.0) * f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(np.full(n, 2.0) * f) / SR)
    s += fft_filter(rng.standard_normal(n), 200, 1200) * 0.15
    return s * spin * np.clip((t1 - t0 - tt) / 1.0, 0, 1)
place(pump_hum(HEAD + 3.0, DUR - 2.0), HEAD + 3.0, 0.035, -0.6)   # pump sits at the left edge

def trickle(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for _ in range(int(dur * 55)):        # little bubbles
        i0 = rng.integers(0, n - 2400); f = rng.uniform(700, 1900); m = np.arange(2400) / SR
        s[i0:i0 + 2400] += np.sin(2 * np.pi * f * (1 + 2.5 * m) * m) * np.exp(-m * 60)
    s += fft_filter(rng.standard_normal(n), 1800, 6000) * 0.06
    return s * env_adsr(n, 1.0, 0.1, 1.0, 1.5)
place(trickle(DUR - (HEAD + 4.0) - 1.0), HEAD + 4.0, 0.035, -0.2)

def pop(f=900):
    n = int(0.07 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * (1 + 6 * tt) * tt) * np.exp(-tt * 70)
tp = HEAD + 3.6
while tp < CUT1 - 0.2:                   # seedlings sprouting
    place(pop(rng.uniform(700, 1300)), tp, 0.06, rng.uniform(-0.7, 0.7)); tp += rng.uniform(0.12, 0.32)

# ---------- growth B: rustle, construction, panels, lights ----------
for ch, ph in ((L, 0.0), (R, 0.8)):
    n = fft_filter(rng.standard_normal(N), 2500, 9000)
    gusts = np.clip(np.sin(2 * np.pi * t / 1.7 + ph) * np.sin(2 * np.pi * t / 2.3 + 2 * ph), 0, 1) ** 1.5
    shimmer = gusts * np.clip((t - CUT1) / 3, 0, 1) * np.clip((CUT2 + 1.5 - t) / 2, 0, 1)
    ch += n / np.abs(n).max() * shimmer * 0.03

def clank(f=420):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d) for r, d in ((1, 9), (2.76, 14), (5.4, 22), (8.9, 30)))
    return s * 0.3 + fft_filter(rng.standard_normal(n), 2000, 8000) * np.exp(-tt * 120) * 0.5
for i, tc in enumerate(np.linspace(CUT1 + 2.6, CUT1 + 4.8, 5)):
    place(clank(rng.uniform(340, 520)), tc, 0.07, 0.25 + 0.1 * i)

def panel_click():
    n = int(0.09 * SR); tt = np.arange(n) / SR
    return fft_filter(rng.standard_normal(n), 2500, 9000) * np.exp(-tt * 140) + np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 90) * 0.4
for i in range(10):
    place(panel_click(), CUT1 + 5.2 + i * 0.16, 0.09, 0.2 + 0.05 * (i % 4))
place(panel_click(), CUT2 - 0.9, 0.12, 0.3)          # lights switching on

# ---------- transitions + camera ----------
def whoosh(dur, lo=300, hi=3000):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = fft_filter(rng.standard_normal(n), lo, hi)
    return x / np.abs(x).max() * np.sin(np.pi * tt / dur) ** 2
for tc in (CUT1, CUT2):
    place(whoosh(1.2), tc - 0.6, 0.10, 0.0)
place(whoosh(3.0, 200, 2200), ORBIT - 0.3, 0.07, -0.3)

# ---------- label blips ----------
def blip():
    n = int(0.16 * SR); tt = np.arange(n) / SR
    a = np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 28)
    b = np.sin(2 * np.pi * 1980 * tt) * np.exp(-tt * 40) * 0.5
    return (a + b) * np.clip(tt / 0.004, 0, 1)
for dt in LABEL_DT:
    place(blip(), ORBIT + dt, 0.045, 0.0)

# ---------- master ----------
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.6) / 1.6
mix /= np.abs(mix).max() / 0.85
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", OUT, round(DUR, 2), "s; cuts", round(CUT1, 2), round(CUT2, 2), "orbit", round(ORBIT, 2))
