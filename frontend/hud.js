/* JARVIS HUD — front-end logic.
   Two jobs: (1) paint the living arc-reactor on the canvas, and (2) run the chat,
   talking to Python through window.pywebview.api (the bridge in jarvis_hud.py). */

"use strict";

// ── shared state the animation reads ────────────────────────────────────────
let STATE = "idle";            // idle | thinking | speaking
function setState(s) {
  STATE = s;
  document.body.className = "state-" + s;
  document.getElementById("status-text").textContent =
    s === "thinking" ? "PROCESSING" : (s === "speaking" ? "SPEAKING" : "ONLINE");
}

// ── the arc reactor (concentric rotating rings + breathing core) ─────────────
(function reactor() {
  const cv = document.getElementById("reactor");
  const ctx = cv.getContext("2d");
  let W, H, cx, cy;

  function resize() {
    W = cv.width = window.innerWidth;
    H = cv.height = window.innerHeight;
    cx = W / 2; cy = H / 2;
  }
  window.addEventListener("resize", resize);
  resize();

  // each ring: radius factor, segment count, gap, spin speed, line width
  const rings = [
    { r: 0.30, seg: 3,  gap: 0.22, spin:  0.0006, w: 2.5 },
    { r: 0.24, seg: 24, gap: 0.30, spin: -0.0011, w: 1.2 },
    { r: 0.19, seg: 6,  gap: 0.10, spin:  0.0016, w: 2.0 },
    { r: 0.135,seg: 48, gap: 0.45, spin: -0.0022, w: 1.0 },
  ];
  const dots = Array.from({ length: 70 }, () => ({
    a: Math.random() * Math.PI * 2,
    d: 0.32 + Math.random() * 0.5,
    s: 0.0001 + Math.random() * 0.0004,
    z: Math.random(),
  }));

  function color(alpha) {
    return STATE === "thinking"
      ? `rgba(56,225,255,${alpha})`      // cyan while it works
      : `rgba(255,154,46,${alpha})`;     // amber at rest
  }

  function draw(t) {
    ctx.clearRect(0, 0, W, H);
    const base = Math.min(W, H);
    const pulseSpeed = STATE === "thinking" ? 0.004 : 0.0016;
    const pulse = 0.5 + 0.5 * Math.sin(t * pulseSpeed);

    // floating telemetry dots
    for (const p of dots) {
      p.a += p.s * (STATE === "thinking" ? 3 : 1);
      const rr = base * p.d * (0.5 + p.z * 0.5);
      const x = cx + Math.cos(p.a) * rr;
      const y = cy + Math.sin(p.a) * rr * 0.62;
      ctx.fillStyle = color(0.08 + p.z * 0.18);
      ctx.fillRect(x, y, 2, 2);
    }

    // segmented rotating rings
    rings.forEach((ring, i) => {
      const R = base * ring.r;
      const rot = t * ring.spin;
      const seg = (Math.PI * 2) / ring.seg;
      const arc = seg * (1 - ring.gap);
      ctx.lineWidth = ring.w;
      ctx.strokeStyle = color(0.5 + 0.3 * pulse - i * 0.06);
      ctx.shadowBlur = 14; ctx.shadowColor = color(0.6);
      for (let k = 0; k < ring.seg; k++) {
        const a0 = rot + k * seg;
        ctx.beginPath();
        ctx.arc(cx, cy, R, a0, a0 + arc);
        ctx.stroke();
      }
    });
    ctx.shadowBlur = 0;

    // breathing core
    const coreR = base * (0.05 + 0.012 * pulse);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 3);
    g.addColorStop(0, color(0.9));
    g.addColorStop(0.4, color(0.35));
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, coreR * 3, 0, Math.PI * 2); ctx.fill();

    // crosshair ticks
    ctx.strokeStyle = color(0.5); ctx.lineWidth = 1.5;
    for (let a = 0; a < 4; a++) {
      const ang = a * Math.PI / 2 + t * 0.0004;
      const r1 = base * 0.33, r2 = base * 0.355;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1);
      ctx.lineTo(cx + Math.cos(ang) * r2, cy + Math.sin(ang) * r2);
      ctx.stroke();
    }

    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

// ── conversation ────────────────────────────────────────────────────────────
const log = document.getElementById("log");
const input = document.getElementById("input");
const form = document.getElementById("composer");

function addLine(who, text) {
  const el = document.createElement("div");
  el.className = "line " + (who === "you" ? "you" : "jarvis");
  el.innerHTML = `<span class="who">${who === "you" ? "YOU" : "JARVIS"}</span>` +
                 `<b></b><span class="body"></span>`;
  el.querySelector(".body").textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el.querySelector(".body");
}

// light typewriter so replies "stream" in
function typeOut(node, text) {
  setState("speaking");
  let i = 0;
  (function tick() {
    node.textContent = text.slice(0, i);
    log.scrollTop = log.scrollHeight;
    if (i++ < text.length) setTimeout(tick, 12);
    else setState("idle");
  })();
}

let busy = false;
async function send(text) {
  if (busy || !text.trim()) return;
  busy = true;
  addLine("you", text);
  input.value = "";
  setState("thinking");
  try {
    const reply = await window.pywebview.api.ask(text);
    typeOut(addLine("jarvis", ""), reply || "…");
  } catch (e) {
    typeOut(addLine("jarvis", ""), "comms dropped, bro — " + e);
  }
  busy = false;
  input.focus();
}

form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });

// ── power button: switch off → normal desktop ───────────────────────────────
document.getElementById("power").addEventListener("click", () => {
  window.pywebview.api.power_off();
});
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") window.pywebview.api.power_off();
});

// ── boot: pull a couple of real readouts once the Python bridge is ready ─────
window.addEventListener("pywebviewready", async () => {
  try {
    const info = await window.pywebview.api.info();
    document.getElementById("r-core").textContent = info.model;
    document.getElementById("brain").textContent =
      (info.cloud ? "HYBRID" : "LOCAL") + " // " + info.model;
    document.getElementById("r-router").textContent = info.cloud ? "cloud+local" : "local";
  } catch (e) { /* non-fatal — HUD still runs */ }
  addLine("jarvis", "Online, sir. What are we breaking today?");
  input.focus();
});
