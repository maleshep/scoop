// driver.mjs — minimal POC: spin up the engine, capture 90 frames, pipe to ffmpeg.
//
// This is the integration shape: ~140 lines stripped of everything the producer
// does (lint, compile stage, probe, audio, mux, encode orchestration, dedup).
// What remains is the irreducible path:
//
//   1. fileServer     — serve index.html to headless Chrome
//   2. captureSession — Puppeteer + capture loop bound to window.__hf.seek
//   3. ffmpeg         — encode captured frames into MP4
//
// Run with:  node driver.mjs
// Expects:  Puppeteer's bundled Chromium and @ffmpeg-installer/ffmpeg binaries.

import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import {
  createFileServer,
  createCaptureSession,
  initializeSession,
  captureFrameToBuffer,
  closeCaptureSession,
  getFfmpegBinary,
} from "@hyperframes/engine";
import ffmpegInstaller from "@ffmpeg-installer/ffmpeg";

const FPS = { num: 30, den: 1 };
const DURATION_S = 3.0;
const TOTAL_FRAMES = Math.round(DURATION_S * FPS.num / FPS.den); // 90

const projectDir = import.meta.dirname;
const framesDir = join(projectDir, "frames");
mkdirSync(framesDir, { recursive: true });

console.log(`POC: ${TOTAL_FRAMES} frames @ ${FPS.num}/${FPS.den} fps (${DURATION_S}s)`);

const server = await createFileServer({ projectDir });
console.log(`fileServer up at ${server.url}`);

const session = await createCaptureSession(
  server.url,
  framesDir,
  { width: 640, height: 360, fps: FPS, format: "jpeg", quality: 90 },
);
console.log("captureSession ready");

await initializeSession(session);
// Give the page a moment to render the first frame after init.
await new Promise((r) => setTimeout(r, 500));

// FFmpeg process consuming JPEG frames from stdin.
const ffmpegBin = ffmpegInstaller.path || getFfmpegBinary();
console.log(`ffmpeg: ${ffmpegBin}`);
const ffmpeg = spawn(
  ffmpegBin,
  [
    "-y",
    "-f", "image2pipe",
    "-framerate", `${FPS.num}/${FPS.den}`,
    "-i", "-",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "ultrafast",
    join(projectDir, "output.mp4"),
  ],
  { stdio: ["pipe", "inherit", "inherit"] },
);

let perfTotal = 0;
let perfSeek = 0;
let perfShot = 0;
const t0 = performance.now();

for (let i = 0; i < TOTAL_FRAMES; i++) {
  const t = i / (FPS.num / FPS.den); // seconds
  const { buffer, captureTimeMs } = await captureFrameToBuffer(session, i, t);
  // Capture performance metrics from session if exposed (we approximate here).
  perfTotal += captureTimeMs;
  if (i % 10 === 0) process.stdout.write(`\r  frame ${i + 1}/${TOTAL_FRAMES}`);
  // Write a copy for inspection, then stream to ffmpeg.
  const { writeFileSync } = await import("node:fs");
  writeFileSync(join(framesDir, `f_${String(i).padStart(6, "0")}.jpg`), buffer);
  ffmpeg.stdin.write(buffer);
}

process.stdout.write(`\r  frame ${TOTAL_FRAMES}/${TOTAL_FRAMES}\n`);
ffmpeg.stdin.end();
await new Promise((resolve, reject) => {
  ffmpeg.on("close", (code) => code === 0 ? resolve() : reject(new Error(`ffmpeg exit ${code}`)));
});

const elapsed = ((performance.now() - t0) / 1000).toFixed(2);
console.log(`\nffmpeg done in ${elapsed}s`);

await closeCaptureSession(session);
server.close();

console.log(`\n=== Result ===`);
console.log(`Frames:       ${TOTAL_FRAMES} (${framesDir}/)`);
console.log(`Output:       ${join(projectDir, "output.mp4")}`);
console.log(`Avg capture:  ${(perfTotal / TOTAL_FRAMES).toFixed(1)} ms/frame`);
console.log(`Total wall:   ${elapsed}s`);
