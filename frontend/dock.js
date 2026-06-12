/* JARVIS dock — the clickable control bar. Each button calls into Python
   (window.pywebview.api). The dock window grows upward to show a reply bubble or the
   command box, then shrinks back to a slim bar. */

"use strict";

const api = () => window.pywebview && window.pywebview.api;
const bubble = document.getElementById("bubble");
const bubbleText = document.getElementById("bubble-text");
const askForm = document.getElementById("ask-form");
const askInput = document.getElementById("ask-input");

// ── grow / shrink the OS window so the bubble + command box have room ────────
let expanded = false;
async function setExpanded(on) {
  if (on === expanded || !api()) return;
  expanded = on;
  try { await api().expand(on); } catch (e) { /* non-fatal */ }
}
function refreshExpand() {
  setExpanded(!bubble.classList.contains("hidden") || !askForm.classList.contains("hidden"));
}

// ── reply bubble (light typewriter, auto-hides) ──────────────────────────────
let hideTimer = null;
function showBubble(text) {
  clearTimeout(hideTimer);
  bubble.classList.remove("hidden");
  refreshExpand();
  let i = 0;
  (function tick() {
    bubbleText.textContent = text.slice(0, i);
    if (i++ < text.length) setTimeout(tick, 12);
  })();
  const ms = Math.min(16000, 4000 + text.length * 45);
  hideTimer = setTimeout(() => { bubble.classList.add("hidden"); refreshExpand(); }, ms);
}

// ── the command box ──────────────────────────────────────────────────────────
function toggleAsk(force) {
  const show = force !== undefined ? force : askForm.classList.contains("hidden");
  askForm.classList.toggle("hidden", !show);
  refreshExpand();
  if (show) setTimeout(() => askInput.focus(), 50);
}
askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = askInput.value.trim();
  if (!text || !api()) return;
  askInput.value = "";
  toggleAsk(false);
  showBubble("…");
  try { showBubble((await api().ask(text)) || "…"); }
  catch (err) { showBubble("comms dropped — " + err); }
});
askInput.addEventListener("keydown", (e) => { if (e.key === "Escape") toggleAsk(false); });

// ── button wiring ────────────────────────────────────────────────────────────
const ACTIONS = {
  async voice()    { if (api()) { await api().voice(); showBubble("Voice mode is firing up, boss — talk to me."); } },
  ask()            { toggleAsk(); },
  async youtube()  { if (api()) api().youtube(); },
  async whatsapp() { if (api()) api().whatsapp(); },
  async lock()     { if (api()) api().lock(); },
  async saver(btn) {
    if (!api()) return;
    const saving = await api().saver();
    btn.classList.toggle("saving", !!saving);
    btn.title = saving ? "Battery saver ON — click to wake" : "Battery saver (pause animation)";
  },
  async off()      { if (api()) api().off(); },
};

document.querySelectorAll(".db").forEach((btn) => {
  btn.addEventListener("click", () => {
    const fn = ACTIONS[btn.dataset.act];
    if (fn) fn(btn);
  });
});
