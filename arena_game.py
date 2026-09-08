"""
NEON DOMINATION: AI Arena — HTML5 Canvas payload.

Streamlit embeds this document through ``st.iframe`` / ``components.html``.
Realtime simulation stays in JavaScript so the match can hold 60 FPS.
"""

from __future__ import annotations

import json
from typing import Any


def build_arena_html(config: dict[str, Any]) -> str:
    """Return a self-contained HTML document for the neon arena."""
    payload = json.dumps(config, ensure_ascii=True)
    return ARENA_DOCUMENT.replace("%%CONFIG%%", payload)


ARENA_DOCUMENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NEON DOMINATION: AI Arena</title>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap");
    :root { --p: #00f0ff; --s: #7b61ff; --a: #ff2bd6; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 100%; height: 100%; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
      background: #010104;
      font-family: "Rajdhani", "Segoe UI", sans-serif;
      color: #e8f6ff;
    }
    .shell {
      position: relative;
      width: min(100%, calc(100vh * 1080 / 700));
      height: min(100%, calc(100vw * 700 / 1080));
      max-width: 100%; max-height: 100%;
      display: flex; flex-direction: column;
      background:
        radial-gradient(700px 240px at 20% 0%, rgba(0,240,255,.16), transparent 60%),
        radial-gradient(600px 220px at 90% 10%, rgba(255,43,214,.12), transparent 55%),
        #050510;
      border: 2px solid var(--p);
      box-shadow: 0 0 0 1px rgba(255,43,214,.4), 0 0 36px rgba(0,240,255,.32);
    }
    .topbar {
      flex: 0 0 36px; height: 36px; display: flex; align-items: center; justify-content: space-between;
      padding: 0 18px;
      background: linear-gradient(90deg, #031018, #12061c 52%, #031018);
      border-bottom: 1px solid var(--p);
    }
    .brand {
      font-family: "Orbitron", "Segoe UI", sans-serif;
      font-size: 13px; font-weight: 900; color: var(--p);
      text-shadow: 0 0 14px var(--p);
    }
    .brand span { color: var(--a); }
    .chip {
      font-family: "Orbitron", sans-serif; font-size: 10px; letter-spacing: .2em;
      padding: 5px 12px; border: 1px solid var(--p); color: var(--p);
      background: rgba(0,240,255,.08); text-shadow: 0 0 8px var(--p);
    }
    #arena {
      display: block; flex: 1 1 auto; width: 100%; min-height: 0;
      aspect-ratio: 1080 / 620; max-height: calc(100% - 64px);
      background: #000; outline: none; cursor: crosshair;
    }
    .hint {
      flex: 0 0 28px; height: 28px; display: flex; align-items: center; justify-content: center; gap: 14px;
      font-size: 12px; letter-spacing: .1em; color: #9fd9e8;
      border-top: 1px solid var(--p); background: #04040c;
    }
    .hint b { color: var(--p); }
    .scan, .vignette { pointer-events: none; position: absolute; inset: 36px 0 28px 0; }
    .scan {
      background: repeating-linear-gradient(to bottom, rgba(255,255,255,.03) 0 1px, transparent 1px 3px);
    }
    .vignette { box-shadow: inset 0 0 120px rgba(0,0,0,.7); }
  </style>
</head>
<body>
  <div class="shell">
    <div class="topbar">
      <div class="brand">NEON <span>DOMINATION</span> // AI ARENA</div>
      <div class="chip" id="protocolChip">STANDBY</div>
    </div>
    <canvas id="arena" width="1080" height="620" tabindex="0"></canvas>
    <div class="scan"></div>
    <div class="vignette"></div>
    <div class="hint">
      <span><b>WASD</b> MOVE</span>
      <span><b>1-6</b> WEAPONS</span>
      <span><b>F</b> PLASMA</span>
      <span><b>ARROWS</b> STEER</span>
      <span><b>R</b> PURGE 30s</span>
      <span><b>SPACE</b> DASH</span>
      <span><b>B</b> SHOP</span>
    </div>
  </div>
  <script>
  const CFG = %%CONFIG%%;
  (function () {
    "use strict";
    const W = 1080, H = 620, BAR_W = 168, BAR_X = W - BAR_W - 8;
    const canvas = document.getElementById("arena");
    const ctx = canvas.getContext("2d");
    const theme = CFG.theme || {};
    const P = theme.primary || "#00f0ff";
    const S = theme.secondary || "#7b61ff";
    const A = theme.accent || "#ff2bd6";
    const D = theme.danger || "#ff2a6d";
    const BG = theme.bg || "#050510";
    const GRID = theme.grid || "rgba(0,240,255,0.1)";
    const HUD = theme.hud || "#c8f7ff";
    const FONT = "Orbitron, Segoe UI, sans-serif";
    const FONT2 = "Rajdhani, Segoe UI, sans-serif";
    document.documentElement.style.setProperty("--p", P);
    document.documentElement.style.setProperty("--s", S);
    document.documentElement.style.setProperty("--a", A);
    const chip = document.getElementById("protocolChip");
    if (chip) chip.textContent = (theme.name || "ION EQUILIBRIUM") + "  " + CFG.label;

    const keys = Object.create(null);
    const TAU = Math.PI * 2;
    const mouse = { x: 0, y: 0 };
    let uid = 1, audioCtx = null;

    const WEAPONS = [
      { id: "pulse", slot: 1, name: "PULSE CANNON", short: "PULSE", cost: 0, dmg: 1, rate: 0.28, speed: 540, shots: 1, spread: 0, splash: 0, pierce: 0, homing: false, r: 3.4, life: 0.85, bars: { dmg: 3, rate: 6, vel: 5, aoe: 1 }, tint: "#7ef9ff", note: "Stock lock-fire. Always in the rack." },
      { id: "rocket", slot: 2, name: "ROCKET POD", short: "ROCKET", cost: 160, dmg: 4, rate: 0.78, speed: 250, shots: 1, spread: 0, splash: 54, pierce: 0, homing: false, r: 6.2, life: 1.45, bars: { dmg: 9, rate: 3, vel: 3, aoe: 9 }, tint: "#ff8a3d", note: "Heavy warhead. Blast radius on impact." },
      { id: "needle", slot: 3, name: "VELOCITY NEEDLE", short: "NEEDLE", cost: 150, dmg: 1, rate: 0.14, speed: 980, shots: 1, spread: 0, splash: 0, pierce: 0, homing: false, r: 2.1, life: 0.65, bars: { dmg: 3, rate: 9, vel: 10, aoe: 1 }, tint: "#d4f7ff", note: "Bullet-speed booster. Hyper-velocity pins." },
      { id: "scatter", slot: 4, name: "SCATTER VOLT", short: "SCATTER", cost: 140, dmg: 1, rate: 0.4, speed: 470, shots: 5, spread: 0.4, splash: 0, pierce: 0, homing: false, r: 2.5, life: 0.52, bars: { dmg: 5, rate: 5, vel: 4, aoe: 4 }, tint: "#c9a6ff", note: "Five-bolt cone. Shreds close swarms." },
      { id: "lance", slot: 5, name: "ION LANCE", short: "LANCE", cost: 180, dmg: 2, rate: 0.36, speed: 720, shots: 1, spread: 0, splash: 0, pierce: 4, homing: false, r: 3.8, life: 0.95, bars: { dmg: 6, rate: 5, vel: 7, aoe: 2 }, tint: "#5cffb0", note: "Piercing beam-bolt. Walks through hulls." },
      { id: "seeker", slot: 6, name: "SEEKER SWARM", short: "SEEKER", cost: 200, dmg: 2, rate: 0.58, speed: 290, shots: 2, spread: 0.22, splash: 0, pierce: 0, homing: true, r: 4.2, life: 1.9, bars: { dmg: 6, rate: 4, vel: 3, aoe: 3 }, tint: "#ff4fd8", note: "Twin homing mites. Track the nearest drone." }
    ];
    const MODULES = [
      { id: "velocity", name: "VEL BOOSTER", cost: 120, note: "+35% projectile speed on every gun." },
      { id: "rapid", name: "RAPID COIL", cost: 110, note: "+30% fire rate on the equipped gun." },
      { id: "shield", name: "SHIELD CELL", cost: 90, note: "Absorb one hit. Carry up to 3." }
    ];

    const state = {
      mode: "boot", t: 0, wave: 1, cores: 0, score: 0, combo: 0, comboTimer: 0,
      capturedBonusArmed: true, shake: 0, banner: "", bannerT: 0, spawnTimer: 1.2,
      enemiesAliveTarget: 4, shopNote: "", shopNoteT: 0,
      high: Number(localStorage.getItem("neonDominationHi") || 0)
    };
    const player = {
      x: (W - BAR_W) * 0.5, y: H * 0.55, vx: 0, vy: 0, angle: -Math.PI / 2, r: 16,
      hp: CFG.player_max_hp, maxHp: CFG.player_max_hp, fireCd: 0,
      shields: 0, dashCd: 0, dashT: 0, hitT: 0, specialCd: 0, specialMax: 5, healCd: 0, purgeCd: 0, purgeMax: 30,
      equip: "pulse", owned: { pulse: true }, velocity: false, rapid: false
    };
    const bullets = [], hostile = [], specials = [], enemies = [], particles = [], floaters = [];
    const bases = [
      { x: 200, y: 190, r: 50, progress: 0, owner: 0, spin: 0, guns: null },
      { x: 690, y: 190, r: 50, progress: 0, owner: 0, spin: 1.2, guns: null },
      { x: 445, y: 470, r: 50, progress: 0, owner: 0, spin: 2.4, guns: null }
    ];

    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function rand(a, b) { return a + Math.random() * (b - a); }
    function dist(ax, ay, bx, by) { return Math.hypot(bx - ax, by - ay); }
    function lerpAngle(a, b, t) {
      return a + (((b - a + Math.PI) % TAU + TAU) % TAU - Math.PI) * t;
    }
    function canvasPos(ev) {
      const r = canvas.getBoundingClientRect();
      return { x: (ev.clientX - r.left) * (canvas.width / Math.max(r.width, 1)), y: (ev.clientY - r.top) * (canvas.height / Math.max(r.height, 1)) };
    }
    function weaponById(id) {
      for (let i = 0; i < WEAPONS.length; i++) if (WEAPONS[i].id === id) return WEAPONS[i];
      return WEAPONS[0];
    }
    function weaponBySlot(n) {
      for (let i = 0; i < WEAPONS.length; i++) if (WEAPONS[i].slot === n) return WEAPONS[i];
      return null;
    }
    function equipped() { return weaponById(player.equip); }
    function capturedCount() { return bases.filter(function (b) { return b.owner === 1; }).length; }
    function captureMult() { return 1 + capturedCount() * 0.35; }

    function shopHits() {
      const cards = [];
      for (let i = 0; i < WEAPONS.length; i++) {
        const col = i % 3, row = Math.floor(i / 3);
        cards.push({ kind: "weapon", id: WEAPONS[i].id, x: 16 + col * 294, y: 52 + row * 214, w: 282, h: 204 });
      }
      for (let i = 0; i < MODULES.length; i++) {
        cards.push({ kind: "module", id: MODULES[i].id, x: 16 + i * 294, y: 484, w: 282, h: 72 });
      }
      return cards;
    }

    function ensureAudio() {
      if (!audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) audioCtx = new AC();
      }
      if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
    }
    function beep(freq, dur, type, gain) {
      if (!audioCtx) return;
      const o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.type = type || "square"; o.frequency.value = freq; g.gain.value = gain || 0.04;
      o.connect(g); g.connect(audioCtx.destination);
      o.start(); g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + dur);
      o.stop(audioCtx.currentTime + dur);
    }
    function burst(x, y, color, n, speed, size) {
      for (let i = 0; i < n; i++) {
        const ang = rand(0, TAU), sp = rand(speed * 0.25, speed);
        particles.push({ x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, life: rand(0.2, 0.7), color: color, size: rand(size * 0.5, size) });
      }
    }
    function floater(x, y, text, color) { floaters.push({ x: x, y: y, text: text, color: color, life: 1 }); }

    function spawnEnemy() {
      const edge = Math.floor(Math.random() * 4);
      let x, y;
      if (edge === 0) { x = rand(40, BAR_X - 40); y = -26; }
      else if (edge === 1) { x = rand(40, BAR_X - 40); y = H + 26; }
      else if (edge === 2) { x = -26; y = rand(40, H - 40); }
      else { x = BAR_X + 8; y = rand(40, H - 40); }
      const kindRoll = Math.random();
      let kind = "drone";
      if (state.wave >= 3 && kindRoll > 0.66) kind = "hunter";
      if (state.wave >= 5 && kindRoll > 0.84) kind = "tank";
      const hpBase = kind === "tank" ? 5 : 2;
      const speedBase = kind === "hunter" ? 86 : kind === "tank" ? 46 : 56;
      enemies.push({
        id: uid++, x: x, y: y, kind: kind, r: kind === "tank" ? 20 : 15,
        hp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        maxHp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        speed: speedBase * (CFG.enemy_speed_mult || 1) * (0.9 + state.wave * 0.018),
        angle: 0, spin: rand(0, TAU), fireCd: rand(0.4, 1.5)
      });
    }
    function nearestEnemy(from) {
      let best = null, bestD = 1e9;
      for (let i = 0; i < enemies.length; i++) {
        const d = dist(from.x, from.y, enemies[i].x, enemies[i].y);
        if (d < bestD) { bestD = d; best = enemies[i]; }
      }
      return best;
    }

    function fireAt(target) {
      if (!target) return;
      const w = equipped();
      const ang = Math.atan2(target.y - player.y, target.x - player.x);
      player.angle = ang;
      const vel = w.speed * (player.velocity ? 1.35 : 1);
      const n = w.shots;
      for (let i = 0; i < n; i++) {
        const off = n === 1 ? 0 : (i - (n - 1) / 2) * (w.spread);
        const a = ang + off;
        bullets.push({
          kind: w.id, tint: w.tint, dmg: w.dmg, splash: w.splash, pierce: w.pierce, homing: w.homing,
          x: player.x + Math.cos(a) * 22, y: player.y + Math.sin(a) * 22,
          vx: Math.cos(a) * vel, vy: Math.sin(a) * vel, life: w.life, r: w.r, hit: Object.create(null)
        });
      }
      burst(player.x + Math.cos(ang) * 18, player.y + Math.sin(ang) * 18, w.tint, 5, 90, 2);
      beep(w.id === "rocket" ? 140 : 640, 0.05, w.id === "rocket" ? "sawtooth" : "square", 0.03);
    }

    function launchSpecial() {
      if (state.mode !== "play" || player.specialCd > 0 || specials.length > 0) return;
      const ang = player.angle;
      specials.push({ x: player.x + Math.cos(ang) * 24, y: player.y + Math.sin(ang) * 24, vx: Math.cos(ang) * 360, vy: Math.sin(ang) * 360, r: 9, life: 4.2, dmg: 3, hit: Object.create(null) });
      player.specialCd = player.specialMax;
      state.banner = "PLASMA BOLT  ·  STEER WITH ARROWS"; state.bannerT = 1.3;
      burst(player.x, player.y, A, 16, 180, 3); beep(160, 0.2, "sawtooth", 0.07);
    }

    function purgeAll() {
      if (state.mode !== "play") return false;
      if (player.purgeCd > 0) {
        state.banner = "PURGE READY IN  " + Math.ceil(player.purgeCd) + "s";
        state.bannerT = 1.1;
        beep(90, 0.08, "square", 0.04);
        return false;
      }
      player.purgeCd = 30;
      state.shake = 14;
      state.banner = "ALL DRONES DOWN";
      state.bannerT = 1.6;
      beep(80, 0.28, "sawtooth", 0.08);
      burst(player.x, player.y, A, 36, 320, 5);
      for (let i = enemies.length - 1; i >= 0; i--) {
        burst(enemies[i].x, enemies[i].y, P, 14, 200, 3);
        killEnemy(enemies[i], i);
      }
      hostile.length = 0;
      return true;
    }

    function hurtPlayer(amount) {
      if (player.hitT > 0 || player.dashT > 0) return;
      if (player.shields > 0) {
        player.shields -= 1; player.hitT = 0.45;
        burst(player.x, player.y, S, 16, 170, 3);
        floater(player.x, player.y - 22, "SHIELD BROKEN", S); beep(300, 0.08, "triangle", 0.05);
        return;
      }
      player.hp -= amount; player.hitT = 0.55; state.shake = 8;
      burst(player.x, player.y, D, 16, 180, 3); beep(90, 0.16, "sawtooth", 0.07);
      if (player.hp <= 0) { player.hp = 0; state.mode = "over"; burst(player.x, player.y, P, 42, 300, 4); }
    }

    function killEnemy(e, index) {
      enemies.splice(index, 1);
      burst(e.x, e.y, e.kind === "tank" ? A : D, 22, 240, 3.6);
      state.shake = Math.min(10, state.shake + 4);
      state.comboTimer = 1.8; state.combo += 1;
      const basePts = e.kind === "tank" ? 28 : e.kind === "hunter" ? 16 : 10;
      const pts = Math.round(basePts * (CFG.score_mult || 1) * captureMult() * (1 + state.combo * 0.08));
      const cores = Math.round((e.kind === "tank" ? 8 : e.kind === "hunter" ? 5 : 3) * (CFG.score_mult || 1));
      state.score += pts; state.cores += cores;
      floater(e.x, e.y - 10, "+" + cores + " CORES", P); beep(140, 0.1, "sawtooth", 0.05);
      if (state.score > state.high) { state.high = state.score; localStorage.setItem("neonDominationHi", String(state.high)); }
    }

    function splashDamage(x, y, radius, dmg, skipId) {
      for (let k = enemies.length - 1; k >= 0; k--) {
        const e = enemies[k];
        if (e.id === skipId) continue;
        if (dist(x, y, e.x, e.y) < radius + e.r) {
          e.hp -= Math.max(1, Math.floor(dmg * 0.6));
          burst(e.x, e.y, "#ff8a3d", 8, 120, 2);
          if (e.hp <= 0) killEnemy(e, k);
        }
      }
    }

    function resetRun() {
      player.x = (W - BAR_W) * 0.5; player.y = H * 0.55; player.vx = 0; player.vy = 0;
      player.hp = player.maxHp; player.fireCd = 0; player.shields = 0;
      player.dashCd = 0; player.dashT = 0; player.hitT = 0; player.specialCd = 0; player.healCd = 0; player.purgeCd = 0;
      player.equip = "pulse"; player.owned = { pulse: true }; player.velocity = false; player.rapid = false;
      bullets.length = 0; hostile.length = 0; specials.length = 0; enemies.length = 0; particles.length = 0; floaters.length = 0;
      bases.forEach(function (b) { b.progress = 0; b.owner = 0; b.guns = null; });
      state.wave = 1; state.cores = 0; state.score = 0; state.combo = 0; state.comboTimer = 0;
      state.capturedBonusArmed = true; state.shake = 0; state.spawnTimer = 0.6;
      state.enemiesAliveTarget = 4; state.banner = "WAVE 01"; state.bannerT = 2.2; state.mode = "play";
    }

    function note(msg, ok) {
      state.shopNote = msg; state.shopNoteT = 1.6;
      state.banner = msg; state.bannerT = 1.3;
      beep(ok ? 880 : 90, 0.1, ok ? "triangle" : "square", 0.05);
    }

    function buy(id) {
      for (let i = 0; i < WEAPONS.length; i++) {
        const w = WEAPONS[i];
        if (w.id !== id) continue;
        if (player.owned[w.id]) { note(w.short + " ALREADY IN RACK", false); return false; }
        if (state.cores < w.cost) { note("NEED " + w.cost + " CORES", false); return false; }
        state.cores -= w.cost; player.owned[w.id] = true; player.equip = w.id;
        note("RACKED  ·  " + w.name, true);
        return true;
      }
      if (id === "velocity") {
        if (player.velocity) { note("VEL BOOSTER ALREADY FITTED", false); return false; }
        if (state.cores < 120) { note("NEED 120 CORES", false); return false; }
        state.cores -= 120; player.velocity = true; note("VEL BOOSTER ONLINE", true); return true;
      }
      if (id === "rapid") {
        if (player.rapid) { note("RAPID COIL ALREADY FITTED", false); return false; }
        if (state.cores < 110) { note("NEED 110 CORES", false); return false; }
        state.cores -= 110; player.rapid = true; note("RAPID COIL ONLINE", true); return true;
      }
      if (id === "shield") {
        if (player.shields >= 3) { note("SHIELD BANK FULL", false); return false; }
        if (state.cores < 90) { note("NEED 90 CORES", false); return false; }
        state.cores -= 90; player.shields += 1; note("SHIELD LAYER +" + player.shields, true); return true;
      }
      return false;
    }

    function tryBuyAt(x, y) {
      const cards = shopHits();
      for (let i = 0; i < cards.length; i++) {
        const c = cards[i];
        if (x >= c.x && x <= c.x + c.w && y >= c.y && y <= c.y + c.h) { buy(c.id); return true; }
      }
      return false;
    }

    function equipSlot(n) {
      const w = weaponBySlot(n);
      if (!w) return;
      if (!player.owned[w.id]) { note(w.short + " LOCKED  ·  BUY IN SHOP", false); return; }
      player.equip = w.id;
      note(w.name + " EQUIPPED", true);
    }

    function updatePlayer(dt) {
      const boltLive = specials.length > 0;
      let ax = 0, ay = 0;
      if (keys.KeyW) ay -= 1; if (keys.KeyS) ay += 1; if (keys.KeyA) ax -= 1; if (keys.KeyD) ax += 1;
      if (!boltLive) {
        if (keys.ArrowUp) ay -= 1; if (keys.ArrowDown) ay += 1; if (keys.ArrowLeft) ax -= 1; if (keys.ArrowRight) ax += 1;
      }
      const len = Math.hypot(ax, ay) || 1; ax /= len; ay /= len;
      const speed = player.dashT > 0 ? 640 : 275;
      player.vx = lerp(player.vx, ax * speed, 0.18);
      player.vy = lerp(player.vy, ay * speed, 0.18);
      player.x = clamp(player.x + player.vx * dt, 24, BAR_X - 22);
      player.y = clamp(player.y + player.vy * dt, 24, H - 24);
      if (player.dashT > 0) { player.dashT -= dt; burst(player.x, player.y, P, 2, 40, 2); }
      player.dashCd = Math.max(0, player.dashCd - dt);
      player.hitT = Math.max(0, player.hitT - dt);
      player.fireCd = Math.max(0, player.fireCd - dt);
      player.specialCd = Math.max(0, player.specialCd - dt);
      player.purgeCd = Math.max(0, player.purgeCd - dt);
      const target = nearestEnemy(player);
      const w = equipped();
      if (target) {
        player.angle = lerpAngle(player.angle, Math.atan2(target.y - player.y, target.x - player.x), 0.2);
        if (player.fireCd <= 0) {
          fireAt(target);
          player.fireCd = w.rate / (player.rapid ? 1.3 : 1);
        }
      } else if (Math.hypot(player.vx, player.vy) > 12) {
        player.angle = lerpAngle(player.angle, Math.atan2(player.vy, player.vx), 0.12);
      }
    }

    function enemyFire(e) {
      const ang = Math.atan2(player.y - e.y, player.x - e.x);
      const shots = e.kind === "tank" ? [-0.16, 0.16] : [0];
      const spd = e.kind === "hunter" ? 300 : e.kind === "tank" ? 210 : 240;
      for (let i = 0; i < shots.length; i++) {
        const a = ang + shots[i];
        hostile.push({ x: e.x + Math.cos(a) * 18, y: e.y + Math.sin(a) * 18, vx: Math.cos(a) * spd, vy: Math.sin(a) * spd, life: 2.3, r: e.kind === "tank" ? 4.6 : 3.3, dmg: e.kind === "tank" ? 14 : e.kind === "hunter" ? 10 : 8 });
      }
      burst(e.x + Math.cos(ang) * 14, e.y + Math.sin(ang) * 14, D, 4, 70, 2);
    }

    function updateEnemies(dt) {
      const aggro = CFG.aggro || 1;
      for (let i = enemies.length - 1; i >= 0; i--) {
        const e = enemies[i];
        e.spin += dt * (e.kind === "hunter" ? 6 : 3.4);
        const ang = Math.atan2(player.y - e.y, player.x - e.x);
        e.angle = lerpAngle(e.angle, ang, 0.08);
        e.x += (Math.cos(ang) * e.speed + Math.sin(state.t * 3 + e.spin) * 10) * dt;
        e.y += Math.sin(ang) * e.speed * dt;
        e.fireCd -= dt;
        if (e.fireCd <= 0 && dist(e.x, e.y, player.x, player.y) < (e.kind === "hunter" ? 480 : 400)) {
          enemyFire(e);
          e.fireCd = (e.kind === "hunter" ? 1.05 : e.kind === "tank" ? 1.9 : 1.55) / Math.max(0.75, aggro);
        }
        if (dist(e.x, e.y, player.x, player.y) < e.r + player.r - 2) hurtPlayer(e.kind === "tank" ? 12 : 7);
      }
    }

    function updateBullets(dt) {
      for (let i = bullets.length - 1; i >= 0; i--) {
        const b = bullets[i];
        if (b.homing) {
          const t = nearestEnemy(b);
          if (t) {
            const desired = Math.atan2(t.y - b.y, t.x - b.x);
            const cur = Math.atan2(b.vy, b.vx);
            const next = lerpAngle(cur, desired, 0.08);
            const spd = Math.hypot(b.vx, b.vy);
            b.vx = Math.cos(next) * spd; b.vy = Math.sin(next) * spd;
          }
        }
        b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt;
        if (b.life <= 0 || b.x < -30 || b.x > W + 30 || b.y < -30 || b.y > H + 30) { bullets.splice(i, 1); continue; }
        for (let j = enemies.length - 1; j >= 0; j--) {
          const e = enemies[j];
          if (b.hit[e.id]) continue;
          if (dist(b.x, b.y, e.x, e.y) < e.r + b.r) {
            e.hp -= b.dmg; b.hit[e.id] = true;
            burst(b.x, b.y, b.tint || P, 7, 100, 2);
            if (b.splash > 0) { burst(b.x, b.y, "#ff8a3d", 20, 220, 4); splashDamage(b.x, b.y, b.splash, b.dmg, e.id); }
            if (e.hp <= 0) killEnemy(e, j);
            if (!b.pierce) { bullets.splice(i, 1); break; }
            b.pierce -= 1;
            if (b.pierce < 0) { bullets.splice(i, 1); break; }
          }
        }
      }
    }

    function updateHostile(dt) {
      for (let i = hostile.length - 1; i >= 0; i--) {
        const b = hostile[i];
        b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt;
        if (b.life <= 0 || b.x < -24 || b.x > W + 24 || b.y < -24 || b.y > H + 24) { hostile.splice(i, 1); continue; }
        if (dist(b.x, b.y, player.x, player.y) < player.r + b.r) { hurtPlayer(b.dmg); burst(b.x, b.y, D, 8, 110, 2.4); hostile.splice(i, 1); }
      }
    }

    function updateSpecials(dt) {
      for (let i = specials.length - 1; i >= 0; i--) {
        const s = specials[i];
        let ax = 0, ay = 0;
        if (keys.ArrowLeft) ax -= 1; if (keys.ArrowRight) ax += 1; if (keys.ArrowUp) ay -= 1; if (keys.ArrowDown) ay += 1;
        if (ax || ay) { const L = Math.hypot(ax, ay); s.vx += (ax / L) * 780 * dt; s.vy += (ay / L) * 780 * dt; }
        const spd = Math.hypot(s.vx, s.vy) || 1;
        if (spd > 440) { s.vx *= 440 / spd; s.vy *= 440 / spd; }
        else if (spd < 300) { s.vx *= 300 / spd; s.vy *= 300 / spd; }
        s.x += s.vx * dt; s.y += s.vy * dt; s.life -= dt; burst(s.x, s.y, A, 1, 16, 2.2);
        for (let j = enemies.length - 1; j >= 0; j--) {
          const e = enemies[j];
          if (s.hit[e.id]) continue;
          if (dist(s.x, s.y, e.x, e.y) < e.r + s.r) {
            e.hp -= s.dmg; s.hit[e.id] = true; burst(e.x, e.y, A, 14, 160, 3);
            if (e.hp <= 0) killEnemy(e, j);
          }
        }
        if (s.life <= 0 || s.x < -40 || s.x > W + 40 || s.y < -40 || s.y > H + 40) { burst(s.x, s.y, A, 28, 260, 4); specials.splice(i, 1); }
      }
    }

    function armNode(b) {
      b.guns = [];
      for (let i = 0; i < 3; i++) {
        b.guns.push({ a: i * TAU / 3, fireCd: i * 0.15, aim: i * TAU / 3, x: b.x, y: b.y });
      }
      burst(b.x, b.y, P, 22, 180, 3);
      state.banner = "3 GUN BARRELS  ONLINE";
      state.bannerT = 1.5;
    }

    function disarmNode(b) {
      if (b.guns) {
        for (let i = 0; i < b.guns.length; i++) burst(b.guns[i].x, b.guns[i].y, D, 8, 90, 2);
      }
      b.guns = null;
    }

    function fireShell(gx, gy, ang) {
      bullets.push({
        kind: "shell", tint: P, dmg: 1, splash: 0, pierce: 0, homing: false,
        x: gx + Math.cos(ang) * 14, y: gy + Math.sin(ang) * 14,
        vx: Math.cos(ang) * 400, vy: Math.sin(ang) * 400,
        life: 1.15, r: 3.6, hit: Object.create(null)
      });
      beep(320, 0.04, "square", 0.018);
    }

    function updateNodeGuns(b, dt) {
      const target = nearestEnemy(b);
      for (let i = 0; i < b.guns.length; i++) {
        const g = b.guns[i];
        const ring = g.a + b.spin * 0.18;
        g.x = b.x + Math.cos(ring) * (b.r + 7);
        g.y = b.y + Math.sin(ring) * (b.r + 7);
        g.fireCd -= dt;
        if (target) {
          g.aim = lerpAngle(g.aim, Math.atan2(target.y - g.y, target.x - g.x), 0.2);
          if (g.fireCd <= 0 && dist(g.x, g.y, target.x, target.y) < 380) {
            fireShell(g.x, g.y, g.aim);
            burst(g.x + Math.cos(g.aim) * 10, g.y + Math.sin(g.aim) * 10, P, 3, 55, 1.5);
            g.fireCd = 0.58;
          }
        }
      }
    }

    function updateBases(dt) {
      player.healCd = (player.healCd || 0) - dt;
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i];
        b.spin += dt;
        const playerOn = dist(player.x, player.y, b.x, b.y) < b.r + 8;
        let enemyOn = false;
        for (let j = 0; j < enemies.length; j++) if (dist(enemies[j].x, enemies[j].y, b.x, b.y) < b.r + 6) { enemyOn = true; break; }
        if (playerOn) {
          const before = player.hp;
          const rate = b.owner === 1 ? 28 : 20;
          player.hp = clamp(player.hp + rate * dt, 0, player.maxHp);
          if (player.hp > before && player.healCd <= 0) {
            floater(player.x, player.y - 26, "+HULL", P);
            burst(player.x, player.y, P, 3, 40, 1.6);
            player.healCd = 0.35;
          }
        }
        if (playerOn && !enemyOn) {
          b.progress = clamp(b.progress + dt * 28, 0, 100);
          if (b.progress >= 100 && b.owner !== 1) {
            b.owner = 1;
            armNode(b);
            floater(b.x, b.y - 40, "NODE SECURED", P);
            beep(520, 0.2, "sine", 0.07);
          }
        } else if (enemyOn && !playerOn) {
          b.progress = clamp(b.progress - dt * 22, 0, 100);
          if (b.progress <= 0 && b.owner === 1) {
            b.owner = 0;
            disarmNode(b);
            floater(b.x, b.y - 40, "TURRETS DOWN", D);
          }
        } else if (!playerOn && b.owner !== 1) b.progress = clamp(b.progress - dt * 8, 0, 100);
        if (b.owner === 1) {
          if (!b.guns) armNode(b);
          updateNodeGuns(b, dt);
        } else if (b.guns) disarmNode(b);
      }
      if (capturedCount() === 3 && state.capturedBonusArmed) {
        const bonus = Math.round(750 * (CFG.score_mult || 1));
        state.score += bonus; state.cores += 25; state.capturedBonusArmed = false;
        state.banner = "TOTAL DOMINATION  +" + bonus; state.bannerT = 2.6; beep(780, 0.28, "triangle", 0.08);
      }
      if (capturedCount() < 3) state.capturedBonusArmed = true;
    }

    function updateWaves(dt) {
      const cap = Math.min(10, Math.round(state.enemiesAliveTarget * (CFG.spawn_rate_mult || 1)));
      state.spawnTimer -= dt;
      if (enemies.length < cap && state.spawnTimer <= 0) {
        spawnEnemy();
        state.spawnTimer = Math.max(0.4, 1.15 - state.wave * 0.04) / (CFG.spawn_rate_mult || 1);
      }
      if (state.score > state.wave * 220) {
        state.wave += 1; state.enemiesAliveTarget = 4 + state.wave;
        state.banner = "WAVE " + String(state.wave).padStart(2, "0"); state.bannerT = 2; beep(440, 0.16, "square", 0.05);
      }
    }

    function updateFx(dt) {
      state.t += dt; state.shake = Math.max(0, state.shake - dt * 18);
      state.bannerT = Math.max(0, state.bannerT - dt); state.shopNoteT = Math.max(0, state.shopNoteT - dt);
      if (state.comboTimer > 0) { state.comboTimer -= dt; if (state.comboTimer <= 0) state.combo = 0; }
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.96; p.vy *= 0.96; p.life -= dt;
        if (p.life <= 0) particles.splice(i, 1);
      }
      for (let i = floaters.length - 1; i >= 0; i--) { floaters[i].y -= 28 * dt; floaters[i].life -= dt; if (floaters[i].life <= 0) floaters.splice(i, 1); }
    }

    function glow(c, b) { ctx.shadowColor = c; ctx.shadowBlur = b; }
    function noGlow() { ctx.shadowBlur = 0; }
    function roundRect(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }
    function panel(x, y, w, h, stroke, fill) {
      roundRect(x, y, w, h, 8);
      ctx.fillStyle = fill || "rgba(4, 10, 20, 0.86)";
      ctx.fill(); ctx.strokeStyle = stroke; glow(stroke, 7); ctx.stroke(); noGlow();
    }
    function statBar(x, y, w, value, label, col) {
      ctx.fillStyle = "rgba(255,255,255,0.12)"; ctx.fillRect(x, y, w, 5);
      glow(col, 6); ctx.fillStyle = col; ctx.fillRect(x, y, w * clamp(value / 10, 0, 1), 5); noGlow();
      ctx.fillStyle = HUD; ctx.font = "600 10px " + FONT2; ctx.textAlign = "left";
      ctx.fillText(label, x, y - 3);
    }

    function drawWeaponArt(id, x, y, scale, t) {
      ctx.save(); ctx.translate(x, y); ctx.scale(scale, scale); ctx.rotate(t ? Math.sin(t * 2) * 0.05 : 0);
      glow(P, 10);
      if (id === "pulse") {
        ctx.fillStyle = "#0b1a22"; ctx.strokeStyle = "#7ef9ff"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(16, 0); ctx.lineTo(-10, 8); ctx.lineTo(-6, 0); ctx.lineTo(-10, -8); ctx.closePath(); ctx.fill(); ctx.stroke();
        ctx.fillStyle = "#7ef9ff"; ctx.fillRect(6, -3, 12, 2); ctx.fillRect(6, 1, 12, 2);
      } else if (id === "rocket") {
        ctx.fillStyle = "#2a1208"; ctx.strokeStyle = "#ff8a3d"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(18, 0); ctx.lineTo(6, 5); ctx.lineTo(-12, 5); ctx.lineTo(-16, 9); ctx.lineTo(-16, -9); ctx.lineTo(-12, -5); ctx.lineTo(6, -5); ctx.closePath(); ctx.fill(); ctx.stroke();
        ctx.fillStyle = "#ff8a3d"; ctx.beginPath(); ctx.moveTo(18, 0); ctx.lineTo(8, 4); ctx.lineTo(8, -4); ctx.closePath(); ctx.fill();
      } else if (id === "needle") {
        ctx.strokeStyle = "#d4f7ff"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(-16, 0); ctx.lineTo(20, 0); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(20, 0); ctx.lineTo(10, 4); ctx.lineTo(10, -4); ctx.closePath(); ctx.fillStyle = "#d4f7ff"; ctx.fill();
        ctx.strokeRect(-10, -5, 8, 10);
      } else if (id === "scatter") {
        ctx.fillStyle = "#160c24"; ctx.strokeStyle = "#c9a6ff"; ctx.lineWidth = 2;
        ctx.fillRect(-12, -10, 18, 20); ctx.strokeRect(-12, -10, 18, 20);
        for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(6, i * 4); ctx.lineTo(16, i * 5); ctx.stroke(); }
      } else if (id === "lance") {
        ctx.strokeStyle = "#5cffb0"; ctx.fillStyle = "#062016"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(-8, -8); ctx.lineTo(8, 0); ctx.lineTo(-8, 8); ctx.closePath(); ctx.fill(); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(8, 0); ctx.lineTo(22, 0); ctx.stroke();
        ctx.fillStyle = "#5cffb0"; ctx.fillRect(10, -2, 12, 4);
      } else if (id === "seeker") {
        ctx.fillStyle = "#1a0616"; ctx.strokeStyle = "#ff4fd8"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(0, 0, 8, 0, TAU); ctx.fill(); ctx.stroke();
        ctx.beginPath(); ctx.arc(-10, 7, 4, 0, TAU); ctx.stroke();
        ctx.beginPath(); ctx.arc(-10, -7, 4, 0, TAU); ctx.stroke();
        ctx.fillStyle = "#ff4fd8"; ctx.beginPath(); ctx.arc(3, 0, 2, 0, TAU); ctx.fill();
      }
      noGlow(); ctx.restore();
    }

    function drawGrid() {
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "#07101c"); g.addColorStop(1, BG);
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = GRID; ctx.lineWidth = 1;
      const gap = 36, ox = (state.t * 14) % gap;
      ctx.beginPath();
      for (let x = -gap + ox; x < BAR_X; x += gap) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
      for (let y = -gap + (state.t * 10) % gap; y < H; y += gap) { ctx.moveTo(0, y); ctx.lineTo(BAR_X, y); }
      ctx.stroke();
      const fog = ctx.createRadialGradient((W - BAR_W) * 0.5, H * 0.5, 30, (W - BAR_W) * 0.5, H * 0.5, 420);
      fog.addColorStop(0, "rgba(0,0,0,0)"); fog.addColorStop(1, "rgba(0,0,0,.55)");
      ctx.fillStyle = fog; ctx.fillRect(0, 0, BAR_X, H);
    }

    function drawBases() {
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i], col = b.owner === 1 ? P : A;
        ctx.save(); ctx.translate(b.x, b.y);
        glow(col, 20); ctx.strokeStyle = col; ctx.lineWidth = 2.2;
        ctx.beginPath(); ctx.arc(0, 0, b.r, 0, TAU); ctx.stroke();
        ctx.globalAlpha = 0.12; ctx.fillStyle = col; ctx.beginPath(); ctx.arc(0, 0, b.r, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
        ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, b.r - 9, -Math.PI / 2, -Math.PI / 2 + TAU * (b.progress / 100)); ctx.stroke();
        ctx.rotate(b.spin); ctx.lineWidth = 1.4;
        for (let k = 0; k < 6; k++) { ctx.rotate(TAU / 6); ctx.beginPath(); ctx.moveTo(0, 14); ctx.lineTo(0, b.r - 14); ctx.stroke(); }
        noGlow(); ctx.restore();
        ctx.font = "700 11px " + FONT2; ctx.fillStyle = HUD; ctx.textAlign = "center";
        ctx.fillText("NODE " + (i + 1) + (b.owner === 1 ? "  GUNS ONLINE" : ""), b.x, b.y + b.r + 22);
        if (b.guns) {
          for (let g = 0; g < b.guns.length; g++) {
            const gun = b.guns[g];
            ctx.save(); ctx.translate(gun.x, gun.y); ctx.rotate(gun.aim);
            glow(P, 10);
            ctx.fillStyle = "#07141c"; ctx.strokeStyle = P; ctx.lineWidth = 1.6;
            ctx.beginPath(); ctx.arc(0, 0, 6.5, 0, TAU); ctx.fill(); ctx.stroke();
            ctx.fillStyle = P;
            ctx.fillRect(2, -2.4, 14, 4.8);
            ctx.fillStyle = "#fff"; ctx.fillRect(12, -1.4, 5, 2.8);
            noGlow(); ctx.restore();
          }
        }
      }
    }

    function drawDrone(e) {
      const col = e.kind === "tank" ? "#ff7a3c" : e.kind === "hunter" ? D : "#89a8ff";
      ctx.save(); ctx.translate(e.x, e.y); ctx.rotate(e.angle); glow(col, 14);
      const arm = e.kind === "tank" ? 18 : 14;
      for (let i = 0; i < 4; i++) {
        const a = i * Math.PI / 2 + Math.PI / 4;
        const ax = Math.cos(a) * arm, ay = Math.sin(a) * arm * 0.7;
        ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(ax, ay); ctx.stroke();
        ctx.save(); ctx.translate(ax, ay); ctx.rotate(e.spin * 12);
        ctx.globalAlpha = 0.35; ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(0, 0, 8, 3, 0, 0, TAU); ctx.fill();
        ctx.globalAlpha = 1; ctx.strokeStyle = "rgba(255,255,255,.85)"; ctx.beginPath(); ctx.moveTo(-7, 0); ctx.lineTo(7, 0); ctx.stroke();
        ctx.restore();
      }
      ctx.fillStyle = "#070b14"; ctx.strokeStyle = col; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(0, 0, e.kind === "tank" ? 12 : 10, e.kind === "tank" ? 9 : 7, 0, 0, TAU); ctx.fill(); ctx.stroke();
      if (e.kind === "tank") { ctx.fillStyle = col; ctx.fillRect(8, -3, 11, 6); }
      if (e.kind === "hunter") { ctx.beginPath(); ctx.moveTo(12, 0); ctx.lineTo(4, 5); ctx.lineTo(4, -5); ctx.closePath(); ctx.fillStyle = col; ctx.fill(); }
      ctx.fillStyle = "#ffe14a"; glow("#ffe14a", 10); ctx.beginPath(); ctx.arc(5, 0, 2.5, 0, TAU); ctx.fill();
      noGlow(); ctx.restore();
      if (e.hp < e.maxHp) {
        ctx.fillStyle = "rgba(0,0,0,.55)"; ctx.fillRect(e.x - 14, e.y - e.r - 10, 28, 4);
        ctx.fillStyle = col; ctx.fillRect(e.x - 14, e.y - e.r - 10, 28 * (e.hp / e.maxHp), 4);
      }
    }

    function drawProjectiles() {
      for (let i = 0; i < bullets.length; i++) {
        const b = bullets[i];
        glow(b.tint || P, 12);
        if (b.kind === "rocket") {
          const ang = Math.atan2(b.vy, b.vx);
          ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(ang);
          ctx.fillStyle = "#ff8a3d"; ctx.beginPath(); ctx.moveTo(8, 0); ctx.lineTo(-8, 4); ctx.lineTo(-8, -4); ctx.closePath(); ctx.fill();
          ctx.restore();
        } else if (b.kind === "shell") {
          const ang = Math.atan2(b.vy, b.vx);
          ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(ang);
          ctx.fillStyle = P; ctx.beginPath(); ctx.ellipse(0, 0, 8, 3.1, 0, 0, TAU); ctx.fill();
          ctx.fillStyle = "#fff"; ctx.fillRect(-1, -1.6, 5, 3.2);
          ctx.restore();
        } else if (b.kind === "needle") {
          ctx.strokeStyle = "#fff"; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - b.vx * 0.04, b.y - b.vy * 0.04); ctx.stroke();
        } else if (b.kind === "lance") {
          ctx.strokeStyle = "#5cffb0"; ctx.lineWidth = 3;
          ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - b.vx * 0.05, b.y - b.vy * 0.05); ctx.stroke();
        } else {
          ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, TAU); ctx.fill();
        }
        noGlow();
      }
      for (let i = 0; i < hostile.length; i++) {
        const b = hostile[i]; glow(D, 10); ctx.fillStyle = "#ffb4c8";
        ctx.beginPath(); ctx.moveTo(b.x + 5, b.y); ctx.lineTo(b.x, b.y + 4); ctx.lineTo(b.x - 5, b.y); ctx.lineTo(b.x, b.y - 4); ctx.closePath(); ctx.fill(); noGlow();
      }
      for (let i = 0; i < specials.length; i++) {
        const s = specials[i], ang = Math.atan2(s.vy, s.vx);
        ctx.save(); ctx.translate(s.x, s.y); ctx.rotate(ang); glow(A, 20);
        ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.ellipse(0, 0, 14, 6, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = A; ctx.beginPath(); ctx.ellipse(-6, 0, 10, 5, 0, 0, TAU); ctx.fill();
        noGlow(); ctx.restore();
      }
    }

    function drawPlayer() {
      ctx.save(); ctx.translate(player.x, player.y); ctx.rotate(player.angle);
      glow(player.hitT > 0 ? D : P, 18);
      ctx.fillStyle = "#07141c"; ctx.strokeStyle = player.hitT > 0 ? D : P; ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(22, 0); ctx.lineTo(8, 6); ctx.lineTo(-3, 13); ctx.lineTo(-16, 9);
      ctx.lineTo(-11, 3); ctx.lineTo(-19, 0); ctx.lineTo(-11, -3); ctx.lineTo(-16, -9);
      ctx.lineTo(-3, -13); ctx.lineTo(8, -6); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = P; ctx.globalAlpha = 0.8;
      ctx.beginPath(); ctx.moveTo(9, 0); ctx.lineTo(-1, 4); ctx.lineTo(-1, -4); ctx.closePath(); ctx.fill();
      ctx.globalAlpha = 1; ctx.fillStyle = "#031018";
      ctx.beginPath(); ctx.ellipse(5, 0, 4.4, 2.6, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 1; ctx.stroke();
      if (player.dashT > 0 || Math.hypot(player.vx, player.vy) > 40) {
        ctx.fillStyle = A; ctx.globalAlpha = 0.85;
        ctx.beginPath(); ctx.moveTo(-16, 4); ctx.lineTo(-30 - Math.random() * 8, 0); ctx.lineTo(-16, -4); ctx.fill();
      }
      noGlow(); ctx.restore();
      if (player.shields > 0) {
        glow(S, 16); ctx.strokeStyle = S; ctx.globalAlpha = 0.5 + Math.sin(state.t * 6) * 0.15; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(player.x, player.y, player.r + 12, 0, TAU); ctx.stroke(); ctx.globalAlpha = 1; noGlow();
      }
    }

    function drawAvailableBar() {
      panel(BAR_X, 10, BAR_W, H - 20, P, "rgba(3, 8, 16, 0.92)");
      ctx.textAlign = "left";
      ctx.fillStyle = P; ctx.font = "700 10px " + FONT;
      ctx.fillText("ENERGY CORES", BAR_X + 12, 30);
      ctx.font = "900 26px " + FONT; ctx.fillText(String(state.cores), BAR_X + 12, 58);
      ctx.fillStyle = HUD; ctx.font = "600 12px " + FONT2;
      ctx.fillText("SCORE " + state.score, BAR_X + 12, 76);
      ctx.fillText("HI " + state.high, BAR_X + 12, 92);

      ctx.fillStyle = P; ctx.font = "700 10px " + FONT;
      ctx.fillText("AVAILABLE", BAR_X + 12, 116);

      for (let i = 0; i < WEAPONS.length; i++) {
        const w = WEAPONS[i];
        const y = 126 + i * 58;
        const owned = !!player.owned[w.id];
        const on = player.equip === w.id;
        roundRect(BAR_X + 8, y, BAR_W - 16, 52, 6);
        ctx.fillStyle = on ? "rgba(0,240,255,0.16)" : "rgba(255,255,255,0.03)";
        ctx.fill();
        ctx.strokeStyle = on ? P : (owned ? "rgba(0,240,255,0.35)" : "rgba(255,255,255,0.1)");
        ctx.stroke();
        ctx.fillStyle = on ? P : HUD;
        ctx.font = "800 12px " + FONT;
        ctx.fillText(w.slot + "", BAR_X + 14, y + 20);
        if (owned) drawWeaponArt(w.id, BAR_X + 40, y + 26, 0.72, state.t + i);
        else {
          ctx.fillStyle = "rgba(255,255,255,0.2)"; ctx.font = "700 16px " + FONT;
          ctx.fillText("+", BAR_X + 34, y + 32);
        }
        ctx.fillStyle = owned ? HUD : "rgba(200,220,230,0.35)";
        ctx.font = "700 10px " + FONT;
        ctx.fillText(owned ? w.short : "LOCKED", BAR_X + 62, y + 22);
        ctx.font = "600 10px " + FONT2;
        ctx.fillText(owned ? (on ? "EQUIPPED" : "READY") : w.cost + " CR", BAR_X + 62, y + 38);
      }

      const my = H - 86;
      ctx.fillStyle = P; ctx.font = "700 10px " + FONT; ctx.fillText("MODULES", BAR_X + 12, my);
      const mods = [
        { on: player.velocity, lab: "VEL" },
        { on: player.rapid, lab: "COIL" },
        { on: player.shields > 0, lab: "SHD " + player.shields }
      ];
      for (let i = 0; i < mods.length; i++) {
        const x = BAR_X + 10 + i * 52;
        roundRect(x, my + 8, 48, 28, 4);
        ctx.fillStyle = mods[i].on ? "rgba(0,240,255,0.18)" : "rgba(255,255,255,0.04)";
        ctx.fill(); ctx.strokeStyle = mods[i].on ? P : "rgba(255,255,255,0.12)"; ctx.stroke();
        ctx.fillStyle = mods[i].on ? P : "rgba(200,220,230,0.4)";
        ctx.font = "700 9px " + FONT; ctx.textAlign = "center";
        ctx.fillText(mods[i].lab, x + 24, my + 26);
      }
    }

    function drawHud() {
      panel(12, 12, 250, 100, P);
      ctx.fillStyle = HUD; ctx.font = "700 10px " + FONT; ctx.textAlign = "left";
      ctx.fillText("HULL INTEGRITY", 24, 30);
      ctx.fillStyle = "rgba(255,255,255,0.12)"; ctx.fillRect(24, 38, 226, 9);
      const hpPct = player.maxHp ? player.hp / player.maxHp : 0;
      const hpCol = hpPct > 0.45 ? P : D;
      glow(hpCol, 8); ctx.fillStyle = hpCol; ctx.fillRect(24, 38, 226 * clamp(hpPct, 0, 1), 9); noGlow();
      ctx.fillStyle = HUD; ctx.font = "600 12px " + FONT2;
      ctx.fillText(Math.ceil(player.hp) + " / " + player.maxHp + "   SHD " + player.shields + "/3", 24, 64);
      roundRect(24, 72, 226, 28, 4);
      ctx.fillStyle = player.purgeCd > 0 ? "rgba(255,255,255,0.06)" : "rgba(255,43,214,0.22)";
      ctx.fill();
      ctx.strokeStyle = A; ctx.stroke();
      ctx.fillStyle = player.purgeCd > 0 ? HUD : A;
      ctx.font = "700 11px " + FONT;
      ctx.fillText(player.purgeCd > 0 ? ("R  PURGE  " + Math.ceil(player.purgeCd) + "s") : "R  PURGE  ALL  [READY]", 32, 91);

      panel((BAR_X - 12) * 0.5 - 200, 12, 400, 44, S);
      ctx.textAlign = "center"; ctx.fillStyle = HUD; ctx.font = "700 12px " + FONT;
      const w = equipped();
      ctx.fillText("WAVE " + String(state.wave).padStart(2, "0") + "   NODES " + capturedCount() + "/3   x" + captureMult().toFixed(2) + "   " + w.short + "   " + (state.combo > 1 ? "COMBO x" + state.combo : ""), (BAR_X - 12) * 0.5, 40);

      if (specials.length > 0) {
        ctx.fillStyle = A; ctx.font = "700 12px " + FONT;
        ctx.fillText("STEER PLASMA WITH ARROWS", (BAR_X - 12) * 0.5, H - 16);
      }
      if (state.bannerT > 0) {
        ctx.globalAlpha = Math.min(1, state.bannerT);
        ctx.font = "900 26px " + FONT; ctx.fillStyle = P; glow(P, 16);
        ctx.fillText(state.banner, (BAR_X - 12) * 0.5, H * 0.3); noGlow(); ctx.globalAlpha = 1;
      }
      ctx.textAlign = "left";
      for (let i = 0; i < floaters.length; i++) {
        const f = floaters[i]; ctx.globalAlpha = clamp(f.life, 0, 1); ctx.fillStyle = f.color;
        ctx.font = "700 13px " + FONT; ctx.fillText(f.text, f.x, f.y); ctx.globalAlpha = 1;
      }
    }

    function drawParticles() {
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]; ctx.globalAlpha = clamp(p.life / 0.7, 0, 1);
        glow(p.color, 8); ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, TAU); ctx.fill();
        noGlow(); ctx.globalAlpha = 1;
      }
    }

    function drawBoot() {
      drawGrid();
      ctx.textAlign = "center"; ctx.fillStyle = P; glow(P, 22);
      ctx.font = "900 40px " + FONT; ctx.fillText("NEON DOMINATION", (BAR_X) * 0.5, 120);
      ctx.fillStyle = A; ctx.font = "700 16px " + FONT; ctx.fillText("AI ARENA", (BAR_X) * 0.5, 150); noGlow();
      panel(70, 168, BAR_X - 140, 330, P);
      ctx.fillStyle = HUD; ctx.font = "600 14px " + FONT2;
      ctx.fillText("BATTLE CRY", (BAR_X) * 0.5, 210);
      ctx.font = "700 18px " + FONT; ctx.fillStyle = P;
      ctx.fillText("\"" + String(CFG.battle_cry || "").slice(0, 44) + "\"", (BAR_X) * 0.5, 240);
      ctx.font = "700 12px " + FONT;
      ctx.fillStyle = CFG.label === "NEGATIVE" ? D : CFG.label === "POSITIVE" ? P : S;
      ctx.fillText((theme.name || "PROTOCOL") + "  //  " + CFG.label + "  " + Math.round((CFG.confidence || 0) * 100) + "%", (BAR_X) * 0.5, 268);
      ctx.fillStyle = HUD; ctx.font = "600 14px " + FONT2;
      const lines = [
        "WASD flies. 1 is the Pulse Cannon. Buy guns in the shop, then 2-6 to switch.",
        "Shop cards show a weapon image plus DMG / RATE / VEL / AOE bars.",
        "Purchases appear on the AVAILABLE rack to the right.",
        "F steers a plasma bolt. R purges every drone (30s cooldown)."
      ];
      for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], (BAR_X) * 0.5, 304 + i * 22);
      ctx.font = "700 15px " + FONT; ctx.fillStyle = P; glow(P, 10);
      ctx.globalAlpha = 0.65 + Math.sin(state.t * 4) * 0.35;
      ctx.fillText("PRESS  ENTER  /  CLICK  TO  DROP  IN", (BAR_X) * 0.5, 470);
      ctx.globalAlpha = 1; noGlow();
    }

    function drawShop() {
      ctx.fillStyle = "rgba(2, 6, 14, 0.88)"; ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center"; ctx.fillStyle = P; glow(P, 14);
      ctx.font = "900 22px " + FONT; ctx.fillText("ARMORY  //  CLICK A CARD TO RACK IT", W * 0.5, 28);
      noGlow();
      ctx.fillStyle = HUD; ctx.font = "600 13px " + FONT2;
      ctx.fillText("CORES " + state.cores + "     1-6 SWITCH OWNED GUNS     B CLOSES", W * 0.5, 46);

      const hits = shopHits();
      for (let i = 0; i < WEAPONS.length; i++) {
        const w = WEAPONS[i], c = hits[i];
        const hover = mouse.x >= c.x && mouse.x <= c.x + c.w && mouse.y >= c.y && mouse.y <= c.y + c.h;
        const owned = !!player.owned[w.id];
        panel(c.x, c.y, c.w, c.h, hover ? A : (owned ? S : P), hover ? "rgba(16,24,48,0.96)" : "rgba(6,10,24,0.95)");
        roundRect(c.x + 12, c.y + 14, 72, 72, 8);
        ctx.fillStyle = "#04080f"; ctx.fill(); ctx.strokeStyle = w.tint; ctx.stroke();
        drawWeaponArt(w.id, c.x + 48, c.y + 50, 1.15, state.t);
        ctx.textAlign = "left";
        ctx.fillStyle = P; ctx.font = "700 13px " + FONT;
        ctx.fillText(w.slot + "  " + w.name, c.x + 96, c.y + 32);
        ctx.fillStyle = HUD; ctx.font = "600 11px " + FONT2;
        ctx.fillText(w.note, c.x + 96, c.y + 50);
        statBar(c.x + 96, c.y + 68, 70, w.bars.dmg, "DMG", D);
        statBar(c.x + 176, c.y + 68, 70, w.bars.rate, "RATE", P);
        statBar(c.x + 96, c.y + 90, 70, w.bars.vel, "VEL", S);
        statBar(c.x + 176, c.y + 90, 70, w.bars.aoe, "AOE", A);
        ctx.textAlign = "center";
        roundRect(c.x + 16, c.y + 160, c.w - 32, 32, 6);
        ctx.fillStyle = owned ? "rgba(123,97,255,0.35)" : (hover ? A : P);
        ctx.fill();
        ctx.fillStyle = "#041018"; ctx.font = "800 12px " + FONT;
        ctx.fillText(owned ? "IN RACK  ·  PRESS " + w.slot : "BUY  " + w.cost + " CORES", c.x + c.w / 2, c.y + 181);
      }
      for (let i = 0; i < MODULES.length; i++) {
        const m = MODULES[i], c = hits[WEAPONS.length + i];
        const hover = mouse.x >= c.x && mouse.x <= c.x + c.w && mouse.y >= c.y && mouse.y <= c.y + c.h;
        const fitted = (m.id === "velocity" && player.velocity) || (m.id === "rapid" && player.rapid) || (m.id === "shield" && player.shields >= 3);
        panel(c.x, c.y, c.w, c.h, hover ? A : P);
        ctx.textAlign = "left"; ctx.fillStyle = P; ctx.font = "700 12px " + FONT;
        ctx.fillText(m.name, c.x + 14, c.y + 22);
        ctx.fillStyle = HUD; ctx.font = "600 11px " + FONT2; ctx.fillText(m.note, c.x + 14, c.y + 40);
        ctx.textAlign = "right"; ctx.fillStyle = A; ctx.font = "800 12px " + FONT;
        ctx.fillText(fitted ? (m.id === "shield" ? player.shields + "/3" : "FITTED") : m.cost + " CR", c.x + c.w - 14, c.y + 28);
      }
      if (state.shopNoteT > 0) {
        ctx.textAlign = "center"; ctx.fillStyle = P; ctx.font = "700 14px " + FONT;
        ctx.fillText(state.shopNote, W * 0.5, 572);
      }
    }

    function drawOver() {
      ctx.fillStyle = "rgba(4,0,8,0.62)"; ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center"; ctx.fillStyle = D; glow(D, 22);
      ctx.font = "900 40px " + FONT; ctx.fillText("SIGNAL LOST", (BAR_X) * 0.5, 230); noGlow();
      ctx.fillStyle = HUD; ctx.font = "600 16px " + FONT2;
      ctx.fillText("SCORE  " + state.score + "     CORES  " + state.cores + "     WAVE  " + state.wave, (BAR_X) * 0.5, 276);
      ctx.fillStyle = P; ctx.font = "700 15px " + FONT;
      ctx.fillText("PRESS ENTER OR CLICK TO REBOOT", (BAR_X) * 0.5, 330);
    }

    function frame(now) {
      const dt = Math.min(0.033, (now - (frame.last || now)) / 1000);
      frame.last = now; updateFx(dt);
      if (state.mode === "play") {
        updatePlayer(dt); updateEnemies(dt); updateBullets(dt); updateHostile(dt);
        updateSpecials(dt); updateBases(dt); updateWaves(dt);
      } else if (Math.random() < 0.3) burst(rand(0, BAR_X), rand(0, H), Math.random() > 0.5 ? P : A, 1, 8, 1.1);
      ctx.save();
      if (state.shake > 0) ctx.translate((Math.random() - 0.5) * state.shake, (Math.random() - 0.5) * state.shake);
      if (state.mode === "boot") { drawBoot(); drawParticles(); drawAvailableBar(); }
      else {
        drawGrid(); drawBases(); drawParticles(); drawProjectiles();
        for (let i = 0; i < enemies.length; i++) drawDrone(enemies[i]);
        drawPlayer(); drawHud(); drawAvailableBar();
        if (state.mode === "shop") drawShop();
        if (state.mode === "over") drawOver();
      }
      ctx.restore();
      requestAnimationFrame(frame);
    }

    function onKey(e) {
      keys[e.code] = true;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].indexOf(e.code) >= 0) e.preventDefault();
      ensureAudio(); canvas.focus();
      if (e.code === "Enter" && (state.mode === "boot" || state.mode === "over")) resetRun();
      if (e.code === "KeyB" || e.code === "Escape") {
        if (state.mode === "play") state.mode = "shop";
        else if (state.mode === "shop") state.mode = "play";
      }
      if (state.mode === "play" && e.code === "Space" && player.dashCd <= 0) {
        player.dashT = 0.18; player.dashCd = 1.45; player.hitT = 0.18; beep(240, 0.08, "sine", 0.05);
      }
      if (state.mode === "play" && (e.code === "KeyF" || e.code === "KeyQ")) launchSpecial();
      if (state.mode === "play" && (e.code === "KeyR" || e.key === "r" || e.key === "R")) {
        e.preventDefault();
        purgeAll();
      }
      const slotMap = { Digit1: 1, Numpad1: 1, Digit2: 2, Numpad2: 2, Digit3: 3, Numpad3: 3, Digit4: 4, Numpad4: 4, Digit5: 5, Numpad5: 5, Digit6: 6, Numpad6: 6 };
      if (slotMap[e.code] && (state.mode === "play" || state.mode === "shop")) equipSlot(slotMap[e.code]);
    }

    window.addEventListener("keydown", onKey, { passive: false });
    window.addEventListener("keyup", function (e) { keys[e.code] = false; });
    canvas.addEventListener("mousemove", function (e) { const p = canvasPos(e); mouse.x = p.x; mouse.y = p.y; });
    canvas.addEventListener("click", function (e) {
      canvas.focus(); ensureAudio();
      const p = canvasPos(e); mouse.x = p.x; mouse.y = p.y;
      if (state.mode === "boot" || state.mode === "over") { resetRun(); return; }
      if (state.mode === "shop") { tryBuyAt(p.x, p.y); return; }
      if (state.mode === "play" && p.x >= 24 && p.x <= 250 && p.y >= 72 && p.y <= 100) {
        purgeAll();
      }
    });
    canvas.focus();
    requestAnimationFrame(frame);
  })();
  </script>
</body>
</html>
"""
