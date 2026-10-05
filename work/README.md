# Agroforestry video – motion graphics

Animated scenes are HTML/SVG pages in `scenes/`, rendered frame-by-frame to MP4 by `render.js`
(Playwright + ffmpeg, 25 fps; `--scale 2` = 3840×2160).

```
node render.js "farm.html?farm=1" --video --out out/farm1_4K.mp4          # 4K clip
node render.js map.html --still 28,42 --out out/map --scale 1               # test stills
```

## Data sources
- **Farm layouts** – traced from `10 ISLANDS AGRO FORESTRY PLANTATIONS.pdf` (`data/build_farms.py` → `data/farms.js`).
- **Islands** – geoBoundaries `MDV ADM0` (gbOpen, derived from OpenStreetMap), `data/gb_ADM0.geojson`.
  The soft teal atoll shading is a buffer around those islands, not separate reef data.
- **Island coordinates** – Wikipedia infobox coordinates; every point falls on its island polygon.
- **Fonts** – MV Typewriter, Mv MAG Round (supplied); Inter (OFL, Google Fonts).
- **Logo** – supplied ministry logo (`assets/ministry_logo.png`).
