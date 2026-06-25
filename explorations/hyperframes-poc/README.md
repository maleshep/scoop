# hyperframes POC — proof of integration

**Date:** 2026-06-23
**Verdict:** `@hyperframes/engine` is usable standalone. 140 lines (HTML + Node driver) produces a real MP4.

## What's here

| File | Lines | What it does |
|---|---|---|
| `index.html` | ~30 | Exposes `window.__hf = { duration, seek(t) }`. A box traces a figure-8 path over 3s. |
| `driver.mjs` | ~110 | `createFileServer` → `createCaptureSession` → loop `captureFrameToBuffer` → pipe to FFmpeg. |
| `package.json` | ~10 | Deps: `@hyperframes/engine`, `@ffmpeg-installer/ffmpeg`. |
| `output.mp4` | binary | 640×360 · H.264 · 30fps · 3.00s · 249 KB. |

## Re-running

```bash
cd explorations/hyperframes-poc
npm install   # ~11 min (Puppeteer + Chromium download)
node driver.mjs
```

## What it proved

- `HfProtocol` 4-field contract works as advertised.
- Engine is library-agnostic (no GSAP, no animation lib).
- Windows platform path works (no Linux-only assumptions).
- Engine is genuinely usable without the 1,882-LoC producer orchestrator.

## What it didn't test

- Audio mixing (`HfMediaElement`)
- Video frame injection
- Shader transitions
- Distributed render
- HDR

Those are the producer's job, not the engine's. For a simple web-to-video use case, the engine alone is enough.

See `explorations/hyperframes.md` for the full architecture digest.
