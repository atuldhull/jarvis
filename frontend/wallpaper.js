/* JARVIS wallpaper — the visual-only layer that lives behind the desktop icons.
   Paints the arc reactor + telemetry. Exposes window.JARVIS_setPower('save'|'full')
   so the dock's battery-saver button can FREEZE the animation (no more redraws =
   no GPU/battery drain) and wake it back up. */

"use strict";

let STATE = "idle";
let RUN = true;   // is the animation loop running?

(function reactor() {
  const cv = document.getElementById("reactor");
  const ctx = cv.getContext("2d");
  let W, H, cx, cy;
  function resize() { W = cv.width = innerWidth; H = cv.height = innerHeight; cx = W / 2; cy = H / 2; }
  addEventListener("resize", resize); resize();

  const rings = [
    { r: 0.30, seg: 3,  gap: 0.22, spin:  0.0006, w: 2.5 },
    { r: 0.24, seg: 24, gap: 0.30, spin: -0.0011, w: 1.2 },
    { r: 0.19, seg: 6,  gap: 0.10, spin:  0.0016, w: 2.0 },
    { r: 0.135,seg: 48, gap: 0.45, spin: -0.0022, w: 1.0 },
  ];
  const dots = Array.from({ length: 70 }, () => ({
    a: Math.random() * Math.PI * 2, d: 0.32 + Math.random() * 0.5,
    s: 0.0001 + Math.random() * 0.0004, z: Math.random(),
  }));
  const color = (al) => STATE === "thinking" ? `rgba(56,225,255,${al})` : `rgba(255,154,46,${al})`;

  function render(t) {
    ctx.clearRect(0, 0, W, H);
    const base = Math.min(W, H);
    const pulse = 0.5 + 0.5 * Math.sin(t * 0.0016);
    for (const p of dots) {
      p.a += p.s;
      const rr = base * p.d * (0.5 + p.z * 0.5);
      ctx.fillStyle = color(0.08 + p.z * 0.18);
      ctx.fillRect(cx + Math.cos(p.a) * rr, cy + Math.sin(p.a) * rr * 0.62, 2, 2);
    }
    rings.forEach((ring, i) => {
      const R = base * ring.r, rot = t * ring.spin;
      const seg = (Math.PI * 2) / ring.seg, arc = seg * (1 - ring.gap);
      ctx.lineWidth = ring.w; ctx.strokeStyle = color(0.5 + 0.3 * pulse - i * 0.06);
      ctx.shadowBlur = 14; ctx.shadowColor = color(0.6);
      for (let k = 0; k < ring.seg; k++) {
        const a0 = rot + k * seg;
        ctx.beginPath(); ctx.arc(cx, cy, R, a0, a0 + arc); ctx.stroke();
      }
    });
    ctx.shadowBlur = 0;
    const coreR = base * (0.05 + 0.012 * pulse);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 3);
    g.addColorStop(0, color(0.9)); g.addColorStop(0.4, color(0.35)); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, coreR * 3, 0, Math.PI * 2); ctx.fill();
  }

  // one calm, dim, motionless frame — the "battery saver / asleep" look
  function staticDim() {
    const base = Math.min(W, H);
    ctx.clearRect(0, 0, W, H);
    ctx.lineWidth = 2; ctx.strokeStyle = "rgba(255,154,46,0.16)";
    ctx.beginPath(); ctx.arc(cx, cy, base * 0.19, 0, Math.PI * 2); ctx.stroke();
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, base * 0.12);
    g.addColorStop(0, "rgba(255,154,46,0.20)"); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, base * 0.12, 0, Math.PI * 2); ctx.fill();
  }

  function loop(t) { render(t); if (RUN) requestAnimationFrame(loop); }
  requestAnimationFrame(loop);

  // dock's battery-saver button calls this
  window.JARVIS_setPower = (mode) => {
    const save = (mode === "save");
    if (save && RUN) { RUN = false; staticDim(); document.getElementById("status-text").textContent = "SAVER"; }
    else if (!save && !RUN) { RUN = true; document.getElementById("status-text").textContent = "STANDBY"; requestAnimationFrame(loop); }
  };
})();

// ── live telemetry: clock, uptime, a slow department "scan" ──────────────────
const started = Date.now();
const pad = (n) => String(n).padStart(2, "0");
const depts = [...document.querySelectorAll(".depts li")];
let scan = 0;

setInterval(() => {
  const now = new Date();
  document.getElementById("clock").textContent = pad(now.getHours()) + ":" + pad(now.getMinutes());
  const up = Math.floor((Date.now() - started) / 1000);
  document.getElementById("uptime").textContent = pad(Math.floor(up / 60)) + ":" + pad(up % 60);
}, 1000);

setInterval(() => {
  if (!RUN) return;  // hold still in battery-saver mode
  depts.forEach((d) => d.classList.remove("active"));
  if (depts.length) depts[scan++ % depts.length].classList.add("active");
}, 1400);
