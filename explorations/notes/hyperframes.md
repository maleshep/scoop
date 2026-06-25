# hyperframes — Architecture Digest

**Repo:** https://github.com/heygen-com/hyperframes
**Local clone:** `C:/Users/M316235/repo/temp/hyperframes/`
**Date reviewed:** 2026-06-23

## 1. Project shape

Converts HTML/CSS + seekable animations into deterministic MP4 video. Treats composition HTML as a DSL: `data-*` attributes declare clips/tracks/durations; the page exposes a `window.__hf.seek(t)` protocol; Puppeteer seeks each frame and FFmpeg encodes the result.

**Monorepo (pnpm):**
- `cli` (~93K LoC) — `hyperframes` binary: init/preview/render/lint/inspect/add/skills
- `core` (~135K LoC) — types, parsers, HTML compiler, runtime (timeline/clock/player), adapters (GSAP, etc.)
- `engine` (~47K LoC) — Puppeteer capture + FFmpeg orchestration, `HfProtocol` types, static-frame dedup
- `producer` (~69K LoC) — full pipeline orchestrator (6-stage render job), distributed mode, Lambda runner
- `player` — `<hyperframes-player>` web component
- `studio` — browser-based visual editor (SvelteKit)
- `shader-transitions`, `aws-lambda` — WebGL transitions and distributed render deploy
- `sdk`, `sdk-playground`, `gcp-cloud-run` — newer surfaces

**Entry points:** `cli/src/cli.ts` (bin), `cli/src/commands/render.ts` (CLI render), `producer/src/server.ts` (HTTP server), `producer/src/services/renderOrchestrator.ts` (programmatic `executeRenderJob`).

## 2. Core abstractions (load-bearing)

- **`HfProtocol`** — `packages/engine/src/types.ts:69-78`. Seek contract: page exposes `window.__hf = { duration, seek(t), media?, transitions? }`. Engine reads duration, calls seek before each capture.
- **`FrameAdapter`** — `packages/core/src/adapters/types.ts:9-15`. `init / getDurationFrames / seekFrame / destroy` — adapter interface for animation libs.
- **`TransportClock`** — `packages/core/src/runtime/clock.ts:19+`. Composition time source; monotonic or audio-master modes for sample-accurate A/V sync.
- **`Timeline` / `clipTree`** — `packages/core/src/runtime/timeline.ts`, `clipTree.ts`. Parses DOM `data-start`/`data-duration`/`data-end` into stable-ID clip tree.
- **`RenderOrchestrator`** — `packages/producer/src/services/renderOrchestrator.ts` (1,882 LoC). 6-stage state machine: compile → probe → extract → audio → capture → encode → assemble.

## 3. Rendering pipeline (`hyperframes render`)

1. **CLI parse** — `cli/src/commands/render.ts` (1,512 LoC). Validates, runs `lintProject`, loads `Producer`.
2. **`executeRenderJob`** — `renderOrchestrator.ts:executeRenderJob()`. Allocates `workDir`, `FileServer`, browser pool, trackers.
3. **Stage 1: Compile** — `stages/compileStage.ts`. `compileForRender` (linkedom HTML parse, fold `data-*`, rewrite scripts).
4. **Stage 1b: Probe** — `stages/probeStage.ts`. Headless Chrome nav, duration discovery, media reconciliation.
5. **Stage 2: Extract videos** — `stages/extractVideosStage.ts`. Pre-extract frames/audio from `<video>`/`<audio>`.
6. **Stage 3: Audio** — `stages/audioStage.ts`. Mixes extracted tracks, applies volume envelopes.
7. **Stage 4: Capture** — `stages/captureStage.ts` / `captureStreamingStage.ts` / `captureHdrStage.ts`. For each frame: `await page.evaluate(t => window.__hf.seek(t))` → screenshot. Static-frame dedup at `frameCapture.ts:1309+`.
8. **Stage 5: Encode** — `stages/encodeStage.ts`. FFmpeg with exact rational fps.
9. **Stage 6: Assemble** — `stages/assembleStage.ts`. Mux video + audio.
10. **Cleanup** — `render/cleanup.ts` closes browser/file server. `try/finally` guarantees no leaks.

## 4. Patterns worth copying

- **`HfProtocol` as the only contract** (`engine/src/types.ts:69`). 4 fields (duration + seek + media + transitions). Engine is animation-library agnostic. Adopt this: one `window.__protocol.seek(t)` interface, infinite plug-in animation libs.
- **`Fps` rational end-to-end** (`core/src/core.types.ts:18`). `{num, den}` carried CLI → capture → FFmpeg arg. Avoids `29.97` rounding bugs.
- **Static-frame dedup with anchor verification** (`frameCapture.ts:1309-1342`). Predict dedupable set from `window.__timelines`, then empirically verify one frame before reusing buffers. Lossless.
- **Skills-as-router** (`cli/src/commands/skills.ts:17`, `skills/hyperframes/SKILL.md`). `npx skills add` installs domain knowledge for AI agents. `SKILL.md` is an intent router.
- **HTML as DSL via `data-*`** (`core/src/runtime/timeline.ts:22-27`). `data-start`, `data-duration`, `data-end`, `data-composition-id`. `linkedom` does static parsing.

## 5. Things to skip

- **6,000+ LoC CLI for ~1,000 needed** — `render.ts` is 1,512 LoC of flag parsing. Steal the producer layer, not the CLI.
- **`renderOrchestrator.ts` 1,882 LoC** — stage split is correct, orchestrator hard to follow.
- **Monorepo + 5+ agent skill formats** (`.claude-plugin`, `.codex-plugin`, `.cursor-plugin`, root `skills/`) — duplicate metadata.
- **Linkedom for HTML parsing** — full hydration needs runtime; two parsing paths.

## 6. Tech debt / red flags

- **Puppeteer fragility.** `engine/src/services/browserManager.ts` handles acquire/release/force-release — implies real leaks.
- **Git LFS lock-in.** ~240MB golden regression `.mp4` baselines. `GIT_LFS_SKIP_SMUDGE=1` mentioned.
- **Determinism requires locked fonts.** `services/deterministicFonts.ts` — Google Fonts substitution breaks output.
- **Lambda + GCP Cloud Run paths** add fork surface area.
- **Lock-in:** `data-hf-*` attribute namespace, `window.__hf` protocol, `frame.md` design format.
- **Animation adapters are GSAP-heavy**; Lottie/Three.js/Anime.js adapter support depth varies.

## 7. Verdict

**Integration effort:** Moderate. `@hyperframes/engine` alone is usable from any Node app — `executeCapture` with your own file server gives you seek+FFmpeg in ~200 lines.

**Most steal-worthy pattern:** the **`HfProtocol` contract**. 4 fields, gives you animation-library-agnostic, frame-accurate, deterministic capture for free. Combined with rational `Fps`, solves the two hardest problems in web-to-video.

**Engagement verdict:** Use `@hyperframes/engine` as-is or fork the producer's stage primitives. Skip CLI, skip Studio, skip skills system unless specifically needed. Don't extend the full monorepo without first reproducing one of their golden-baseline renders to confirm fork determinism.
