// Minimal deterministic animation helpers. Each scene defines window.DURATION
// and window.render(t) (t in seconds); render.js steps t frame by frame.
const NS = "http://www.w3.org/2000/svg";

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
// progress of t through [t0, t0+dur], 0..1
const prog = (t, t0, dur) => clamp((t - t0) / dur);
const ease = {
  out: (k) => 1 - Math.pow(1 - k, 3),
  inOut: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  sine: (k) => -(Math.cos(Math.PI * k) - 1) / 2,
};

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// seeded PRNG for stable "random" tonal variation
function rng(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

// Grow-in: scale 0.6 -> 1 with opacity, eased (no overshoot)
function growIn(node, x, y, t, t0, dur = 0.6, s1 = 1) {
  const k = ease.out(prog(t, t0, dur));
  node.setAttribute("transform", `translate(${x} ${y}) scale(${(0.6 + 0.4 * k) * s1})`);
  node.setAttribute("opacity", k);
}

// Stroke draw-on for an element with known length
function drawOn(node, len, k) {
  node.setAttribute("stroke-dasharray", `${len} ${len}`);
  node.setAttribute("stroke-dashoffset", len * (1 - k));
}

// Fade + small rise for HTML/SVG text blocks
function fadeUp(node, t, t0, dur = 0.8, dy = 14) {
  const k = ease.out(prog(t, t0, dur));
  node.style.opacity = k;
  node.style.transform = `translateY(${(1 - k) * dy}px)`;
}
