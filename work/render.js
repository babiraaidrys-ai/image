// Usage:
//   node render.js <scene.html?query> --still <t1,t2,...> --out <prefix>      (PNG stills)
//   node render.js <scene.html?query> --video --out <file.mp4> [--fps 25]     (4K MP4)
const { chromium } = require("/opt/node22/lib/node_modules/playwright");
const { spawn } = require("child_process");
const path = require("path");

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const [scene, query = ""] = args[0].split("?");
const url = "file://" + path.resolve(__dirname, "scenes", scene) + (query ? "?" + query : "");
const fps = +opt("--fps", 25), out = opt("--out", "out/test"), scale = +opt("--scale", 2);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
  page.on("pageerror", (e) => console.error("PAGE ERROR", e.message));
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  const dur = await page.evaluate(() => window.DURATION);
  console.log("duration", dur);

  if (args.includes("--still")) {
    for (const t of opt("--still").split(",").map(Number)) {
      await page.evaluate((t) => window.render(t), t);
      await page.screenshot({ path: `${out}_${t}.png` });
    }
  } else {
    const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "png", "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", out],
      { stdio: ["pipe", "inherit", "inherit"] });
    const n = Math.round(dur * fps);
    for (let f = 0; f < n; f++) {
      await page.evaluate((t) => window.render(t), f / fps);
      const buf = await page.screenshot({ type: "png" });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
      if (f % 100 === 0) console.log(`frame ${f}/${n}`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on("close", r));
  }
  await browser.close();
})();
