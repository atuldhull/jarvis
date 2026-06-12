/* JARVIS dashboard — live clock, system stats, weather, and button wiring. */
"use strict";
const api = () => window.pywebview && window.pywebview.api;
const $ = (id) => document.getElementById(id);
const set = (id, v) => { const e = $(id); if (e) e.textContent = v; };

// ── clock ────────────────────────────────────────────────────────────────
const DAYS = ["SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"];
const MON = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
function tick() {
  const n = new Date();
  let h = n.getHours(), m = String(n.getMinutes()).padStart(2, "0");
  const ap = h >= 12 ? "PM" : "AM"; h = h % 12 || 12;
  set("time", `${h}:${m} ${ap}`);
  set("date", `${DAYS[n.getDay()]}, ${MON[n.getMonth()]} ${n.getDate()}, ${n.getFullYear()}`);
}
setInterval(tick, 1000); tick();

// ── sparklines ─────────────────────────────────────────────────────────────
const hist = { cpu: [], ram: [], disk: [], net: [] };
function push(k, v) { hist[k].push(v); if (hist[k].length > 48) hist[k].shift(); }
function spark(id, arr, color, fixedMax) {
  const c = $(id); if (!c) return;
  const x = c.getContext("2d"), w = c.width, h = c.height;
  x.clearRect(0, 0, w, h);
  if (arr.length < 2) return;
  const mx = fixedMax || Math.max(1, ...arr);
  x.beginPath();
  arr.forEach((v, i) => {
    const px = (i / (arr.length - 1)) * w, py = h - (v / mx) * (h - 3) - 2;
    i ? x.lineTo(px, py) : x.moveTo(px, py);
  });
  x.strokeStyle = color; x.lineWidth = 1.6; x.stroke();
  x.lineTo(w, h); x.lineTo(0, h); x.closePath();
  x.fillStyle = color.replace("rgb", "rgba").replace(")", ",0.12)");
  x.fill();
}

function setGauge(pct) {
  const C = 327; const e = $("gauge");
  if (e) e.style.strokeDashoffset = C * (1 - pct / 100);
}

// ── poll system stats ──────────────────────────────────────────────────────
async function poll() {
  if (!api()) return;
  let s; try { s = await api().stats(); } catch (e) { return; }
  push("cpu", s.cpu); push("ram", s.ram); push("disk", s.disk); push("net", s.net);
  set("d-cpu", s.cpu + "%"); set("p-cpu", s.cpu + "%");
  set("d-ram", s.ram + "%"); set("p-ram", s.ram + "%");
  set("d-disk", s.disk + "%"); set("p-disk", s.disk + "%");
  set("d-net", s.net + " KB"); set("p-net", s.net + " KB");
  spark("sp-cpu", hist.cpu, "rgb(72,198,255)", 100); spark("pf-cpu", hist.cpu, "rgb(72,198,255)", 100);
  spark("sp-ram", hist.ram, "rgb(120,210,255)", 100); spark("pf-ram", hist.ram, "rgb(120,210,255)", 100);
  spark("sp-disk", hist.disk, "rgb(70,224,160)", 100); spark("pf-disk", hist.disk, "rgb(70,224,160)", 100);
  spark("sp-net", hist.net, "rgb(190,233,255)"); spark("pf-net", hist.net, "rgb(190,233,255)");
  setGauge(s.optimal); set("optimal", s.optimal + "%");
  set("uptime", s.uptime);
  set("battery", s.battery == null ? "—" : s.battery + "%" + (s.plugged ? " (Plugged In)" : ""));
}
setInterval(poll, 1500);

// ── weather ─────────────────────────────────────────────────────────────────
async function loadWeather(refresh) {
  if (!api()) return;
  let w; try { w = await api().weather(refresh || false); } catch (e) { return; }
  set("wtemp", w.temp + "°"); set("wdesc", w.desc); set("wcity", w.city || "");
  set("wfeels", w.feels + "°"); set("whum", w.humidity + "%"); set("wwind", w.wind + "km/h");
  const f = $("forecast"); if (f) {
    f.innerHTML = "";
    (w.days || []).forEach(d => {
      const dt = new Date(d.date);
      f.innerHTML += `<div>${DAYS[dt.getDay()].slice(0,3)}<b>${d.max}°/${d.min}°</b></div>`;
    });
  }
}

// ── actions ─────────────────────────────────────────────────────────────────
function feed(msg) { const e = $("feedmsg"); if (e) e.innerHTML = msg; }
function focusAsk(prefix) { const a = $("ask"); a.value = prefix || ""; a.focus(); }

function doAct(name) {
  if (!api()) return;
  if (name === "quit") return api().quit();
  if (name === "voice") { api().voice(); return feed("Voice mode is firing up, sir — talk to me."); }
  if (name === "weather") return loadWeather(true);
  if (name === "home") return;
  if (name === "translate") return focusAsk("Translate to Hindi: ");
  api().action(name).then(r => feed(typeof r === "string" ? r.toUpperCase() : "done"));
}
document.querySelectorAll("[data-act]").forEach(b => b.addEventListener("click", () => {
  if (b.classList.contains("navitem")) {
    document.querySelectorAll(".navitem").forEach(n => n.classList.remove("active"));
    b.classList.add("active");
  }
  doAct(b.dataset.act);
}));

// ── ask box ─────────────────────────────────────────────────────────────────
async function submitAsk() {
  const a = $("ask"), t = a.value.trim();
  if (!t || !api()) return;
  a.value = ""; feed("Processing…");
  try { feed((await api().ask(t)) || "…"); } catch (e) { feed("comms dropped — " + e); }
}
$("asksend").addEventListener("click", submitAsk);
$("ask").addEventListener("keydown", e => { if (e.key === "Enter") submitAsk(); });
$("feedrun").addEventListener("click", () => doAct("tools"));

// ── voice waveform (idle animation) ────────────────────────────────────────
(function wave() {
  const c = $("wave"); if (!c) return;
  const x = c.getContext("2d"), w = c.width, h = c.height; let t = 0;
  (function f() {
    x.clearRect(0, 0, w, h); t += 0.18;
    x.strokeStyle = "rgba(72,198,255,.8)"; x.lineWidth = 2; x.beginPath();
    for (let i = 0; i < w; i += 4) {
      const a = Math.sin(i * 0.05 + t) * Math.sin(i * 0.013 + t * 0.6);
      const y = h / 2 + a * (h / 2 - 3);
      i ? x.lineTo(i, y) : x.moveTo(i, y);
    }
    x.stroke(); requestAnimationFrame(f);
  })();
})();

// ── boot ────────────────────────────────────────────────────────────────────
window.addEventListener("pywebviewready", async () => {
  try {
    const i = await api().info();
    set("user", i.user); set("version", i.version); set("os", i.os);
    if (i.photo) {
      const p = $("portrait"); p.style.backgroundImage = `url('${i.photo}')`;
      const s = p.querySelector(".silhouette"); if (s) s.style.display = "none";
    }
  } catch (e) {}
  poll(); loadWeather(false);
});
