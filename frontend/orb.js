/* JARVIS orb — light reactor + a ring of working buttons.
   Kept deliberately cheap: small canvas, ~30 FPS cap, NO canvas shadowBlur (that was
   the perf killer). Battery-saver just stops the loop. */

"use strict";

const api = () => window.pywebview && window.pywebview.api;
let STATE = "idle";
let RUN = true;

// ── lay the buttons out in a ring ────────────────────────────────────────────
(function ringLayout() {
  const ring = document.getElementById("ring");
  const btns = [...ring.querySelectorAll(".ob")];
  const R = 232;                       // ring radius (px) inside the 580 orb
  const n = btns.length;
  btns.forEach((b, i) => {
    const ang = (i / n) * Math.PI * 2 - Math.PI / 2;  // start at the top, go clockwise
    b.style.left = `calc(50% + ${Math.cos(ang) * R}px)`;
    b.style.top = `calc(50% + ${Math.sin(ang) * R}px)`;
  });
})();

// ── the reactor (cheap, throttled) ───────────────────────────────────────────
(function reactor() {
  const cv = document.getElementById("reactor");
  const ctx = cv.getContext("2d");
  let W, H, cx, cy;
  function resize() { W = cv.width = cv.clientWidth; H = cv.height = cv.clientHeight; cx = W / 2; cy = H / 2; }
  addEventListener("resize", resize); resize();

  const rings = [
    { r: 0.42, seg: 3,  gap: 0.24, spin:  0.0006, w: 2.5 },
    { r: 0.34, seg: 18, gap: 0.34, spin: -0.0012, w: 1.2 },
    { r: 0.26, seg: 6,  gap: 0.12, spin:  0.0017, w: 2.0 },
  ];
  const dots = Array.from({ length: 26 }, () => ({
    a: Math.random() * Math.PI * 2, d: 0.30 + Math.random() * 0.18,
    s: 0.0002 + Math.random() * 0.0005,
  }));
  const color = (al) => STATE === "thinking" ? `rgba(56,225,255,${al})` : `rgba(255,154,46,${al})`;

  function render(t) {
    ctx.clearRect(0, 0, W, H);
    const base = Math.min(W, H);
    const pulse = 0.5 + 0.5 * Math.sin(t * 0.0018);
    for (const p of dots) {
      p.a += p.s;
      const rr = base * p.d;
      ctx.fillStyle = color(0.22);
      ctx.fillRect(cx + Math.cos(p.a) * rr, cy + Math.sin(p.a) * rr, 2, 2);
    }
    rings.forEach((ring, i) => {
      const Rr = base * ring.r, rot = t * ring.spin;
      const seg = (Math.PI * 2) / ring.seg, arc = seg * (1 - ring.gap);
      ctx.lineWidth = ring.w; ctx.strokeStyle = color(0.65 + 0.25 * pulse - i * 0.08);
      for (let k = 0; k < ring.seg; k++) {
        const a0 = rot + k * seg;
        ctx.beginPath(); ctx.arc(cx, cy, Rr, a0, a0 + arc); ctx.stroke();
      }
    });
    const coreR = base * (0.10 + 0.02 * pulse);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 2.2);
    g.addColorStop(0, color(0.85)); g.addColorStop(0.45, color(0.30)); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, coreR * 2.2, 0, Math.PI * 2); ctx.fill();
  }

  let last = 0;
  function loop(t) {
    if (!RUN) return;
    if (t - last > 33) { render(t); last = t; }   // ~30 FPS cap
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  window.__wake = () => { if (!RUN) { RUN = true; last = 0; requestAnimationFrame(loop); } };
  window.__sleep = () => { RUN = false; render(performance.now() || 0); };
})();

// ── center: status, command box, reply bubble ────────────────────────────────
const status = document.getElementById("orb-status");
const bubble = document.getElementById("bubble");
const bubbleText = document.getElementById("bubble-text");
const askForm = document.getElementById("ask-form");
const askInput = document.getElementById("ask-input");

let hideTimer = null;
function showBubble(text) {
  clearTimeout(hideTimer);
  status.classList.add("hidden");
  bubble.classList.remove("hidden");
  let i = 0;
  (function tick() {
    bubbleText.textContent = text.slice(0, i);
    if (i++ < text.length) setTimeout(tick, 12);
  })();
  const ms = Math.min(15000, 4000 + text.length * 45);
  hideTimer = setTimeout(() => { bubble.classList.add("hidden"); status.classList.remove("hidden"); }, ms);
}

function toggleAsk(force) {
  const show = force !== undefined ? force : askForm.classList.contains("hidden");
  askForm.classList.toggle("hidden", !show);
  status.classList.toggle("hidden", show);
  if (show) setTimeout(() => askInput.focus(), 40);
}
askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = askInput.value.trim();
  if (!text || !api()) return;
  askInput.value = "";
  toggleAsk(false);
  STATE = "thinking"; showBubble("…");
  try { showBubble((await api().ask(text)) || "…"); }
  catch (err) { showBubble("comms dropped — " + err); }
  STATE = "idle";
});
askInput.addEventListener("keydown", (e) => { if (e.key === "Escape") toggleAsk(false); });

// ── buttons ──────────────────────────────────────────────────────────────────
const ACTIONS = {
  async voice()    { if (api()) { await api().voice(); showBubble("Voice mode is firing up, boss — talk to me."); } },
  ask()            { toggleAsk(); },
  youtube()        { if (api()) api().youtube(); },
  whatsapp()       { if (api()) api().whatsapp(); },
  lock()           { if (api()) api().lock(); },
  saver(btn) {
    const saving = RUN;          // about to turn animation OFF if currently running
    if (saving) { window.__sleep(); status.textContent = "SAVER"; }
    else { window.__wake(); status.textContent = "JARVIS"; }
    btn.classList.toggle("saving", saving);
    btn.title = saving ? "Battery saver ON — click to wake" : "Battery saver (pause)";
  },
  off()            { if (api()) api().off(); },
};
document.querySelectorAll(".ob").forEach((btn) => {
  btn.addEventListener("click", () => { const fn = ACTIONS[btn.dataset.act]; if (fn) fn(btn); });
});
