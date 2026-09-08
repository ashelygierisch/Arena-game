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
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #020208;
      font-family: "Rajdhani", "Segoe UI", sans-serif;
      color: #e8f6ff;
    }

    .shell {
      position: relative;
      width: 1080px;
      height: 700px;
      margin: 0 auto;
      background: #050510;
      border: 2px solid var(--p);
      box-shadow:
        0 0 0 1px rgba(255, 43, 214, 0.35),
        0 0 28px rgba(0, 240, 255, 0.35),
        inset 0 0 40px rgba(0, 240, 255, 0.06);
    }

    .topbar {
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      background: linear-gradient(90deg, #041018, #0a0720 50%, #041018);
      border-bottom: 1px solid var(--p);
    }

    .brand {
      font-family: "Orbitron", "Segoe UI", sans-serif;
      font-size: 13px;
      font-weight: 900;
      color: var(--p);
      text-shadow: 0 0 14px var(--p);
    }
    .brand span { color: var(--a); }

    .chip {
      font-family: "Orbitron", sans-serif;
      font-size: 10px;
      letter-spacing: 0.2em;
      padding: 5px 12px;
      border: 1px solid var(--p);
      color: var(--p);
      background: rgba(0, 240, 255, 0.08);
      text-shadow: 0 0 8px var(--p);
    }

    #arena {
      display: block;
      width: 1080px;
      height: 620px;
      background: #000;
      outline: none;
      cursor: crosshair;
    }

    .hint {
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      font-size: 12px;
      letter-spacing: 0.12em;
      color: #9fd9e8;
      border-top: 1px solid var(--p);
      background: #04040c;
    }
    .hint b { color: var(--p); font-weight: 700; }

    .scan, .vignette {
      pointer-events: none;
      position: absolute;
      inset: 44px 0 36px 0;
    }
    .scan {
      background: repeating-linear-gradient(
        to bottom,
        rgba(255,255,255,0.035) 0px,
        rgba(255,255,255,0.035) 1px,
        transparent 1px,
        transparent 3px
      );
    }
    .vignette { box-shadow: inset 0 0 110px rgba(0, 0, 0, 0.65); }
  </style>
</head>
<body>
  <div class="shell" id="shell">
    <div class="topbar">
      <div class="brand">NEON <span>DOMINATION</span> // AI ARENA</div>
      <div class="chip" id="protocolChip">STANDBY</div>
    </div>
    <canvas id="arena" width="1080" height="620" tabindex="0"></canvas>
    <div class="scan"></div>
    <div class="vignette"></div>
    <div class="hint">
      <span><b>WASD</b> MOVE</span>
      <span><b>F</b> PLASMA BOLT</span>
      <span><b>ARROWS</b> STEER BOLT</span>
      <span><b>SPACE</b> DASH</span>
      <span><b>B</b> SHOP · <b>CLICK</b> TO BUY</span>
    </div>
  </div>

  <script>
  const CFG = %%CONFIG%%;

  (function () {
    "use strict";

    const W = 1080;
    const H = 620;
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
    let uid = 1;
    let audioCtx = null;

    const state = {
      mode: "boot",
      t: 0,
      wave: 1,
      cores: 0,
      score: 0,
      combo: 0,
      comboTimer: 0,
      capturedBonusArmed: true,
      shake: 0,
      banner: "",
      bannerT: 0,
      spawnTimer: 1.2,
      enemiesAliveTarget: 4,
      shopNote: "",
      shopNoteT: 0,
      high: Number(localStorage.getItem("neonDominationHi") || 0)
    };

    const player = {
      x: W * 0.5,
      y: H * 0.55,
      vx: 0,
      vy: 0,
      angle: -Math.PI / 2,
      r: 15,
      hp: CFG.player_max_hp,
      maxHp: CFG.player_max_hp,
      fireCd: 0,
      fireRate: 0.28,
      rapid: 0,
      triple: false,
      shields: 0,
      dashCd: 0,
      dashT: 0,
      hitT: 0,
      specialCd: 0,
      specialMax: 5
    };

    const bullets = [];
    const hostile = [];
    const specials = [];
    const enemies = [];
    const particles = [];
    const floaters = [];
    const bases = [
      { x: 210, y: 175, r: 54, progress: 0, owner: 0, spin: 0 },
      { x: 870, y: 175, r: 54, progress: 0, owner: 0, spin: 1.2 },
      { x: 540, y: 470, r: 54, progress: 0, owner: 0, spin: 2.4 }
    ];

    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function rand(a, b) { return a + Math.random() * (b - a); }
    function dist(ax, ay, bx, by) { return Math.hypot(bx - ax, by - ay); }
    function lerpAngle(a, b, t) {
      const diff = ((b - a + Math.PI) % TAU + TAU) % TAU - Math.PI;
      return a + diff * t;
    }

    function canvasPos(ev) {
      const r = canvas.getBoundingClientRect();
      return {
        x: (ev.clientX - r.left) * (canvas.width / Math.max(r.width, 1)),
        y: (ev.clientY - r.top) * (canvas.height / Math.max(r.height, 1))
      };
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
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = type || "square";
      o.frequency.value = freq;
      g.gain.value = gain || 0.04;
      o.connect(g);
      g.connect(audioCtx.destination);
      o.start();
      g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + dur);
      o.stop(audioCtx.currentTime + dur);
    }

    function burst(x, y, color, n, speed, size) {
      for (let i = 0; i < n; i++) {
        const ang = rand(0, TAU);
        const sp = rand(speed * 0.25, speed);
        particles.push({
          x: x, y: y,
          vx: Math.cos(ang) * sp,
          vy: Math.sin(ang) * sp,
          life: rand(0.22, 0.7),
          color: color,
          size: rand(size * 0.5, size)
        });
      }
    }

    function floater(x, y, text, color) {
      floaters.push({ x: x, y: y, text: text, color: color, life: 1.0 });
    }

    function capturedCount() {
      return bases.filter(function (b) { return b.owner === 1; }).length;
    }
    function captureMult() { return 1 + capturedCount() * 0.35; }
    function weaponLevel() { return 1 + player.rapid + (player.triple ? 1 : 0); }

    function shopCatalog() {
      return [
        {
          id: "rapid",
          title: "RAPID FIRE",
          blurb: "Cycle the cannons faster.",
          blurb2: "Stacks three times.",
          cost: player.rapid >= 3 ? 0 : 60 * (player.rapid + 1),
          tag: player.rapid >= 3 ? "MAXED" : player.rapid + "/3 OWNED",
          locked: player.rapid >= 3,
          key: "1",
          x: 115, y: 178, w: 260, h: 300
        },
        {
          id: "triple",
          title: "TRIPLE SHOT",
          blurb: "Each volley becomes a",
          blurb2: "three-bolt spread.",
          cost: player.triple ? 0 : 140,
          tag: player.triple ? "OWNED" : "LOCKED",
          locked: player.triple,
          key: "2",
          x: 410, y: 178, w: 260, h: 300
        },
        {
          id: "shield",
          title: "SHIELD",
          blurb: "Eat one lethal hit.",
          blurb2: "Carry up to 3 layers.",
          cost: player.shields >= 3 ? 0 : 90,
          tag: player.shields >= 3 ? "MAXED" : player.shields + "/3 LAYERS",
          locked: player.shields >= 3,
          key: "3",
          x: 705, y: 178, w: 260, h: 300
        }
      ];
    }

    function spawnEnemy() {
      const edge = Math.floor(Math.random() * 4);
      let x, y;
      if (edge === 0) { x = rand(40, W - 40); y = -24; }
      else if (edge === 1) { x = rand(40, W - 40); y = H + 24; }
      else if (edge === 2) { x = -24; y = rand(40, H - 40); }
      else { x = W + 24; y = rand(40, H - 40); }

      const kindRoll = Math.random();
      let kind = "drone";
      if (state.wave >= 3 && kindRoll > 0.68) kind = "hunter";
      if (state.wave >= 5 && kindRoll > 0.86) kind = "tank";

      const hpBase = kind === "tank" ? 5 : kind === "hunter" ? 2 : 2;
      const speedBase = kind === "hunter" ? 130 : kind === "tank" ? 62 : 86;

      enemies.push({
        id: uid++,
        x: x, y: y, kind: kind,
        r: kind === "tank" ? 20 : kind === "hunter" ? 14 : 15,
        hp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        maxHp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        speed: speedBase * (CFG.enemy_speed_mult || 1) * (0.92 + state.wave * 0.035),
        angle: 0,
        spin: rand(0, TAU),
        fireCd: rand(0.4, 1.5)
      });
    }

    function nearestEnemy(from) {
      let best = null;
      let bestD = 1e9;
      for (let i = 0; i < enemies.length; i++) {
        const d = dist(from.x, from.y, enemies[i].x, enemies[i].y);
        if (d < bestD) { bestD = d; best = enemies[i]; }
      }
      return best;
    }

    function fireAt(target) {
      if (!target) return;
      const ang = Math.atan2(target.y - player.y, target.x - player.x);
      player.angle = ang;
      const spread = player.triple ? [-0.22, 0, 0.22] : [0];
      for (let i = 0; i < spread.length; i++) {
        const a = ang + spread[i];
        bullets.push({
          x: player.x + Math.cos(a) * 20,
          y: player.y + Math.sin(a) * 20,
          vx: Math.cos(a) * 540,
          vy: Math.sin(a) * 540,
          life: 0.85,
          r: 3.4
        });
      }
      burst(player.x + Math.cos(ang) * 18, player.y + Math.sin(ang) * 18, P, 5, 90, 2);
      beep(680 + player.rapid * 40, 0.05, "square", 0.028);
    }

    function launchSpecial() {
      if (state.mode !== "play") return;
      if (player.specialCd > 0 || specials.length > 0) return;
      const ang = player.angle;
      specials.push({
        x: player.x + Math.cos(ang) * 24,
        y: player.y + Math.sin(ang) * 24,
        vx: Math.cos(ang) * 360,
        vy: Math.sin(ang) * 360,
        r: 9,
        life: 4.2,
        dmg: 3,
        hit: Object.create(null)
      });
      player.specialCd = player.specialMax;
      state.banner = "PLASMA BOLT  ·  STEER WITH ARROWS";
      state.bannerT = 1.4;
      burst(player.x, player.y, A, 16, 180, 3);
      beep(160, 0.22, "sawtooth", 0.07);
    }

    function hurtPlayer(amount) {
      if (player.hitT > 0 || player.dashT > 0) return;
      if (player.shields > 0) {
        player.shields -= 1;
        player.hitT = 0.45;
        burst(player.x, player.y, S, 16, 170, 3);
        floater(player.x, player.y - 22, "SHIELD BROKEN", S);
        beep(300, 0.08, "triangle", 0.05);
        return;
      }
      player.hp -= amount;
      player.hitT = 0.55;
      state.shake = 8;
      burst(player.x, player.y, D, 16, 180, 3);
      beep(90, 0.16, "sawtooth", 0.07);
      if (player.hp <= 0) {
        player.hp = 0;
        state.mode = "over";
        burst(player.x, player.y, P, 42, 300, 4);
      }
    }

    function killEnemy(e, index) {
      enemies.splice(index, 1);
      burst(e.x, e.y, e.kind === "tank" ? A : D, 22, 240, 3.6);
      state.shake = Math.min(10, state.shake + 4);
      state.comboTimer = 1.8;
      state.combo += 1;
      const basePts = (e.kind === "tank" ? 28 : e.kind === "hunter" ? 16 : 10);
      const pts = Math.round(basePts * (CFG.score_mult || 1) * captureMult() * (1 + state.combo * 0.08));
      const cores = Math.round((e.kind === "tank" ? 8 : e.kind === "hunter" ? 5 : 3) * (CFG.score_mult || 1));
      state.score += pts;
      state.cores += cores;
      floater(e.x, e.y - 10, "+" + cores + " CORES", P);
      beep(140, 0.1, "sawtooth", 0.05);
      if (state.score > state.high) {
        state.high = state.score;
        localStorage.setItem("neonDominationHi", String(state.high));
      }
    }

    function resetRun() {
      player.x = W * 0.5;
      player.y = H * 0.55;
      player.vx = 0;
      player.vy = 0;
      player.hp = player.maxHp;
      player.fireCd = 0;
      player.rapid = 0;
      player.triple = false;
      player.shields = 0;
      player.fireRate = 0.28;
      player.dashCd = 0;
      player.dashT = 0;
      player.hitT = 0;
      player.specialCd = 0;
      bullets.length = 0;
      hostile.length = 0;
      specials.length = 0;
      enemies.length = 0;
      particles.length = 0;
      floaters.length = 0;
      bases.forEach(function (b) { b.progress = 0; b.owner = 0; });
      state.wave = 1;
      state.cores = 0;
      state.score = 0;
      state.combo = 0;
      state.comboTimer = 0;
      state.capturedBonusArmed = true;
      state.shake = 0;
      state.spawnTimer = 0.6;
      state.enemiesAliveTarget = 4;
      state.banner = "WAVE 01";
      state.bannerT = 2.2;
      state.mode = "play";
    }

    function buy(id) {
      let ok = false;
      let label = "";
      if (id === "rapid") {
        if (player.rapid >= 3) { state.shopNote = "RAPID FIRE ALREADY MAXED"; state.shopNoteT = 1.4; return false; }
        const cost = 60 * (player.rapid + 1);
        if (state.cores < cost) { state.shopNote = "NEED " + cost + " CORES"; state.shopNoteT = 1.4; beep(90, 0.08, "square", 0.04); return false; }
        state.cores -= cost;
        player.rapid += 1;
        player.fireRate = 0.28 * Math.pow(0.78, player.rapid);
        ok = true; label = "RAPID FIRE L" + player.rapid;
      } else if (id === "triple") {
        if (player.triple) { state.shopNote = "TRIPLE SHOT ALREADY OWNED"; state.shopNoteT = 1.4; return false; }
        if (state.cores < 140) { state.shopNote = "NEED 140 CORES"; state.shopNoteT = 1.4; beep(90, 0.08, "square", 0.04); return false; }
        state.cores -= 140;
        player.triple = true;
        ok = true; label = "TRIPLE SHOT ONLINE";
      } else if (id === "shield") {
        if (player.shields >= 3) { state.shopNote = "SHIELD BANK FULL"; state.shopNoteT = 1.4; return false; }
        if (state.cores < 90) { state.shopNote = "NEED 90 CORES"; state.shopNoteT = 1.4; beep(90, 0.08, "square", 0.04); return false; }
        state.cores -= 90;
        player.shields += 1;
        ok = true; label = "SHIELD LAYER +" + player.shields;
      }
      if (ok) {
        state.shopNote = "PURCHASED  ·  " + label;
        state.shopNoteT = 1.8;
        floater(W * 0.5, 150, label, P);
        beep(880, 0.12, "triangle", 0.07);
      }
      return ok;
    }

    function tryBuyAt(x, y) {
      const cards = shopCatalog();
      for (let i = 0; i < cards.length; i++) {
        const c = cards[i];
        if (x >= c.x && x <= c.x + c.w && y >= c.y && y <= c.y + c.h) {
          buy(c.id);
          return true;
        }
      }
      return false;
    }

    function updatePlayer(dt) {
      const boltLive = specials.length > 0;
      let ax = 0, ay = 0;
      if (keys.KeyW || keys.KeyI) ay -= 1;
      if (keys.KeyS || keys.KeyK) ay += 1;
      if (keys.KeyA || keys.KeyJ) ax -= 1;
      if (keys.KeyD || keys.KeyL) ax += 1;
      if (!boltLive) {
        if (keys.ArrowUp) ay -= 1;
        if (keys.ArrowDown) ay += 1;
        if (keys.ArrowLeft) ax -= 1;
        if (keys.ArrowRight) ax += 1;
      }
      const len = Math.hypot(ax, ay) || 1;
      ax /= len; ay /= len;

      const speed = player.dashT > 0 ? 640 : 275;
      player.vx = lerp(player.vx, ax * speed, 0.18);
      player.vy = lerp(player.vy, ay * speed, 0.18);
      player.x = clamp(player.x + player.vx * dt, 24, W - 24);
      player.y = clamp(player.y + player.vy * dt, 24, H - 24);

      if (player.dashT > 0) {
        player.dashT -= dt;
        burst(player.x, player.y, P, 2, 40, 2);
      }
      player.dashCd = Math.max(0, player.dashCd - dt);
      player.hitT = Math.max(0, player.hitT - dt);
      player.fireCd = Math.max(0, player.fireCd - dt);
      player.specialCd = Math.max(0, player.specialCd - dt);

      const target = nearestEnemy(player);
      if (target) {
        const desired = Math.atan2(target.y - player.y, target.x - player.x);
        player.angle = lerpAngle(player.angle, desired, 0.2);
        if (player.fireCd <= 0) {
          fireAt(target);
          player.fireCd = player.fireRate;
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
        hostile.push({
          x: e.x + Math.cos(a) * 18,
          y: e.y + Math.sin(a) * 18,
          vx: Math.cos(a) * spd,
          vy: Math.sin(a) * spd,
          life: 2.3,
          r: e.kind === "tank" ? 4.6 : 3.3,
          dmg: e.kind === "tank" ? 14 : e.kind === "hunter" ? 10 : 8
        });
      }
      burst(e.x + Math.cos(ang) * 14, e.y + Math.sin(ang) * 14, D, 4, 70, 2);
      beep(210, 0.05, "square", 0.02);
    }

    function updateEnemies(dt) {
      const aggro = CFG.aggro || 1;
      for (let i = enemies.length - 1; i >= 0; i--) {
        const e = enemies[i];
        e.spin += dt * (e.kind === "hunter" ? 5 : 3.2);
        const ang = Math.atan2(player.y - e.y, player.x - e.x);
        e.angle = lerpAngle(e.angle, ang, 0.08);
        const jitter = Math.sin(state.t * 3 + e.spin) * 12;
        e.x += (Math.cos(ang) * e.speed + jitter) * dt;
        e.y += (Math.sin(ang) * e.speed) * dt;

        e.fireCd -= dt;
        const range = e.kind === "hunter" ? 480 : 400;
        if (e.fireCd <= 0 && dist(e.x, e.y, player.x, player.y) < range) {
          enemyFire(e);
          const cd = e.kind === "hunter" ? 1.05 : e.kind === "tank" ? 1.9 : 1.55;
          e.fireCd = cd / Math.max(0.75, aggro);
        }

        if (dist(e.x, e.y, player.x, player.y) < e.r + player.r - 2) {
          hurtPlayer(e.kind === "tank" ? 12 : 7);
        }
      }
    }

    function updateBullets(dt) {
      for (let i = bullets.length - 1; i >= 0; i--) {
        const b = bullets[i];
        b.x += b.vx * dt;
        b.y += b.vy * dt;
        b.life -= dt;
        if (b.life <= 0 || b.x < -20 || b.x > W + 20 || b.y < -20 || b.y > H + 20) {
          bullets.splice(i, 1);
          continue;
        }
        for (let j = enemies.length - 1; j >= 0; j--) {
          const e = enemies[j];
          if (dist(b.x, b.y, e.x, e.y) < e.r + b.r) {
            e.hp -= 1;
            burst(b.x, b.y, P, 6, 90, 2);
            bullets.splice(i, 1);
            if (e.hp <= 0) killEnemy(e, j);
            break;
          }
        }
      }
    }

    function updateHostile(dt) {
      for (let i = hostile.length - 1; i >= 0; i--) {
        const b = hostile[i];
        b.x += b.vx * dt;
        b.y += b.vy * dt;
        b.life -= dt;
        if (b.life <= 0 || b.x < -24 || b.x > W + 24 || b.y < -24 || b.y > H + 24) {
          hostile.splice(i, 1);
          continue;
        }
        if (dist(b.x, b.y, player.x, player.y) < player.r + b.r) {
          hurtPlayer(b.dmg);
          burst(b.x, b.y, D, 8, 110, 2.4);
          hostile.splice(i, 1);
        }
      }
    }

    function updateSpecials(dt) {
      for (let i = specials.length - 1; i >= 0; i--) {
        const s = specials[i];
        let ax = 0, ay = 0;
        if (keys.ArrowLeft) ax -= 1;
        if (keys.ArrowRight) ax += 1;
        if (keys.ArrowUp) ay -= 1;
        if (keys.ArrowDown) ay += 1;
        if (ax || ay) {
          const L = Math.hypot(ax, ay);
          s.vx += (ax / L) * 780 * dt;
          s.vy += (ay / L) * 780 * dt;
        }
        const spd = Math.hypot(s.vx, s.vy) || 1;
        const max = 440;
        const min = 300;
        if (spd > max) { s.vx *= max / spd; s.vy *= max / spd; }
        else if (spd < min) { s.vx *= min / spd; s.vy *= min / spd; }
        s.x += s.vx * dt;
        s.y += s.vy * dt;
        s.life -= dt;
        burst(s.x, s.y, A, 1, 16, 2.2);

        for (let j = enemies.length - 1; j >= 0; j--) {
          const e = enemies[j];
          if (s.hit[e.id]) continue;
          if (dist(s.x, s.y, e.x, e.y) < e.r + s.r) {
            e.hp -= s.dmg;
            s.hit[e.id] = true;
            burst(e.x, e.y, A, 14, 160, 3);
            if (e.hp <= 0) killEnemy(e, j);
          }
        }

        if (s.life <= 0 || s.x < -40 || s.x > W + 40 || s.y < -40 || s.y > H + 40) {
          burst(s.x, s.y, A, 28, 260, 4);
          specials.splice(i, 1);
        }
      }
    }

    function updateBases(dt) {
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i];
        b.spin += dt;
        const playerOn = dist(player.x, player.y, b.x, b.y) < b.r + 8;
        let enemyOn = false;
        for (let j = 0; j < enemies.length; j++) {
          if (dist(enemies[j].x, enemies[j].y, b.x, b.y) < b.r + 6) { enemyOn = true; break; }
        }
        if (playerOn && !enemyOn) {
          b.progress = clamp(b.progress + dt * 28, 0, 100);
          if (b.progress >= 100 && b.owner !== 1) {
            b.owner = 1;
            floater(b.x, b.y - 40, "NODE SECURED", P);
            beep(520, 0.2, "sine", 0.07);
          }
        } else if (enemyOn && !playerOn) {
          b.progress = clamp(b.progress - dt * 22, 0, 100);
          if (b.progress <= 0 && b.owner === 1) {
            b.owner = 0;
            floater(b.x, b.y - 40, "NODE LOST", D);
          }
        } else if (!playerOn && b.owner !== 1) {
          b.progress = clamp(b.progress - dt * 8, 0, 100);
        }
      }
      if (capturedCount() === 3 && state.capturedBonusArmed) {
        const bonus = Math.round(750 * (CFG.score_mult || 1));
        state.score += bonus;
        state.cores += 25;
        state.capturedBonusArmed = false;
        state.banner = "TOTAL DOMINATION  +" + bonus;
        state.bannerT = 2.6;
        beep(780, 0.28, "triangle", 0.08);
      }
      if (capturedCount() < 3) state.capturedBonusArmed = true;
    }

    function updateWaves(dt) {
      const cap = Math.min(16, Math.round(state.enemiesAliveTarget * (CFG.spawn_rate_mult || 1)));
      state.spawnTimer -= dt;
      if (enemies.length < cap && state.spawnTimer <= 0) {
        spawnEnemy();
        state.spawnTimer = Math.max(0.32, 1.2 - state.wave * 0.05) / (CFG.spawn_rate_mult || 1);
      }
      if (state.score > state.wave * 220) {
        state.wave += 1;
        state.enemiesAliveTarget = 4 + state.wave * 2;
        state.banner = "WAVE " + String(state.wave).padStart(2, "0");
        state.bannerT = 2.0;
        beep(440, 0.16, "square", 0.05);
      }
    }

    function updateFx(dt) {
      state.t += dt;
      state.shake = Math.max(0, state.shake - dt * 18);
      state.bannerT = Math.max(0, state.bannerT - dt);
      state.shopNoteT = Math.max(0, state.shopNoteT - dt);
      if (state.comboTimer > 0) {
        state.comboTimer -= dt;
        if (state.comboTimer <= 0) state.combo = 0;
      }
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vx *= 0.96;
        p.vy *= 0.96;
        p.life -= dt;
        if (p.life <= 0) particles.splice(i, 1);
      }
      for (let i = floaters.length - 1; i >= 0; i--) {
        floaters[i].y -= 28 * dt;
        floaters[i].life -= dt;
        if (floaters[i].life <= 0) floaters.splice(i, 1);
      }
    }

    function glow(color, blur) { ctx.shadowColor = color; ctx.shadowBlur = blur; }
    function noGlow() { ctx.shadowBlur = 0; }

    function roundRect(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function drawGrid() {
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, W, H);

      const hex = 26;
      const h = hex * Math.sqrt(3);
      ctx.strokeStyle = GRID;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let row = -1; row < H / h + 2; row++) {
        for (let col = -1; col < W / (hex * 1.5) + 2; col++) {
          const x = col * hex * 1.5 + (state.t * 8) % (hex * 1.5);
          const y = row * h + (col % 2 ? h * 0.5 : 0) + (state.t * 5) % h;
          ctx.moveTo(x + hex, y);
          for (let k = 0; k < 6; k++) {
            const a = k * TAU / 6;
            ctx.lineTo(x + Math.cos(a) * hex, y + Math.sin(a) * hex);
          }
        }
      }
      ctx.stroke();

      const g = ctx.createRadialGradient(W * 0.5, H * 0.5, 40, W * 0.5, H * 0.5, 560);
      g.addColorStop(0, "rgba(0,0,0,0)");
      g.addColorStop(1, "rgba(0,0,0,0.62)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);

      ctx.strokeStyle = P;
      ctx.globalAlpha = 0.18;
      ctx.strokeRect(10, 10, W - 20, H - 20);
      ctx.globalAlpha = 1;
    }

    function drawBases() {
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i];
        const col = b.owner === 1 ? P : A;
        ctx.save();
        ctx.translate(b.x, b.y);
        glow(col, 22);
        ctx.strokeStyle = col;
        ctx.lineWidth = 2.4;
        ctx.beginPath();
        ctx.arc(0, 0, b.r, 0, TAU);
        ctx.stroke();
        ctx.globalAlpha = 0.14;
        ctx.fillStyle = col;
        ctx.beginPath();
        ctx.arc(0, 0, b.r, 0, TAU);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.lineWidth = 7;
        ctx.beginPath();
        ctx.arc(0, 0, b.r - 10, -Math.PI / 2, -Math.PI / 2 + TAU * (b.progress / 100));
        ctx.stroke();
        ctx.rotate(b.spin);
        ctx.lineWidth = 1.5;
        for (let k = 0; k < 6; k++) {
          ctx.rotate(TAU / 6);
          ctx.beginPath();
          ctx.moveTo(0, 12);
          ctx.lineTo(0, b.r - 16);
          ctx.stroke();
        }
        noGlow();
        ctx.restore();
        ctx.font = "700 12px " + FONT2;
        ctx.fillStyle = HUD;
        ctx.textAlign = "center";
        ctx.fillText("NODE " + (i + 1) + (b.owner === 1 ? "  OWNED" : ""), b.x, b.y + b.r + 18);
      }
    }

    function drawDrone(e) {
      const col = e.kind === "tank" ? "#ff7a3c" : e.kind === "hunter" ? D : "#8aa4ff";
      ctx.save();
      ctx.translate(e.x, e.y);
      ctx.rotate(e.angle);
      glow(col, 16);

      const arm = e.kind === "tank" ? 17 : 13;
      for (let i = 0; i < 4; i++) {
        const a = i * Math.PI / 2 + Math.PI / 4;
        const ax = Math.cos(a) * arm;
        const ay = Math.sin(a) * arm * 0.72;
        ctx.strokeStyle = col;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(ax, ay);
        ctx.stroke();
        ctx.save();
        ctx.translate(ax, ay);
        ctx.rotate(e.spin * 10);
        ctx.strokeStyle = "rgba(255,255,255,0.8)";
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(-7, 0); ctx.lineTo(7, 0);
        ctx.moveTo(0, -7); ctx.lineTo(0, 7);
        ctx.stroke();
        ctx.restore();
      }

      ctx.fillStyle = "#070b14";
      ctx.strokeStyle = col;
      ctx.lineWidth = 2;
      if (e.kind === "tank") {
        roundRect(-13, -11, 26, 22, 5);
        ctx.fill(); ctx.stroke();
        ctx.fillStyle = col;
        ctx.fillRect(6, -3, 10, 6);
      } else if (e.kind === "hunter") {
        ctx.beginPath();
        ctx.moveTo(16, 0);
        ctx.lineTo(-9, 8);
        ctx.lineTo(-5, 0);
        ctx.lineTo(-9, -8);
        ctx.closePath();
        ctx.fill(); ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.ellipse(0, 0, 11, 8, 0, 0, TAU);
        ctx.fill(); ctx.stroke();
        ctx.beginPath();
        ctx.ellipse(0, 2, 7, 4, 0, 0, TAU);
        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.stroke();
      }

      ctx.fillStyle = e.kind === "hunter" ? "#ff003c" : "#ffe14a";
      glow("#ffe14a", 12);
      ctx.beginPath();
      ctx.arc(5, 0, 2.6, 0, TAU);
      ctx.fill();
      noGlow();
      ctx.restore();

      if (e.hp < e.maxHp) {
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(e.x - 14, e.y - e.r - 10, 28, 4);
        ctx.fillStyle = col;
        ctx.fillRect(e.x - 14, e.y - e.r - 10, 28 * (e.hp / e.maxHp), 4);
      }
    }

    function drawEnemies() {
      for (let i = 0; i < enemies.length; i++) drawDrone(enemies[i]);
    }

    function drawBullets() {
      for (let i = 0; i < bullets.length; i++) {
        const b = bullets[i];
        glow(P, 12);
        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, TAU);
        ctx.fill();
        ctx.strokeStyle = P;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(b.x, b.y);
        ctx.lineTo(b.x - b.vx * 0.028, b.y - b.vy * 0.028);
        ctx.stroke();
        noGlow();
      }
      for (let i = 0; i < hostile.length; i++) {
        const b = hostile[i];
        glow(D, 12);
        ctx.fillStyle = "#ffb4c8";
        ctx.beginPath();
        ctx.moveTo(b.x + 5, b.y);
        ctx.lineTo(b.x, b.y + 4);
        ctx.lineTo(b.x - 5, b.y);
        ctx.lineTo(b.x, b.y - 4);
        ctx.closePath();
        ctx.fill();
        noGlow();
      }
      for (let i = 0; i < specials.length; i++) {
        const s = specials[i];
        const ang = Math.atan2(s.vy, s.vx);
        ctx.save();
        ctx.translate(s.x, s.y);
        ctx.rotate(ang);
        glow(A, 22);
        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.ellipse(0, 0, 14, 6, 0, 0, TAU);
        ctx.fill();
        ctx.fillStyle = A;
        ctx.beginPath();
        ctx.ellipse(-6, 0, 10, 5, 0, 0, TAU);
        ctx.fill();
        noGlow();
        ctx.restore();
      }
    }

    function drawPlayer() {
      ctx.save();
      ctx.translate(player.x, player.y);
      ctx.rotate(player.angle);
      glow(player.hitT > 0 ? D : P, 20);
      ctx.fillStyle = "#061018";
      ctx.strokeStyle = player.hitT > 0 ? D : P;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(20, 0);
      ctx.lineTo(8, 6);
      ctx.lineTo(-2, 12);
      ctx.lineTo(-15, 9);
      ctx.lineTo(-11, 3);
      ctx.lineTo(-18, 0);
      ctx.lineTo(-11, -3);
      ctx.lineTo(-15, -9);
      ctx.lineTo(-2, -12);
      ctx.lineTo(8, -6);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = P;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      ctx.moveTo(8, 0);
      ctx.lineTo(-2, 4);
      ctx.lineTo(-2, -4);
      ctx.closePath();
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.fillStyle = "#041018";
      ctx.beginPath();
      ctx.ellipse(4, 0, 4.2, 2.6, 0, 0, TAU);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1;
      ctx.stroke();
      if (player.dashT > 0 || Math.hypot(player.vx, player.vy) > 40) {
        ctx.fillStyle = A;
        ctx.globalAlpha = 0.85;
        ctx.beginPath();
        ctx.moveTo(-16, 4);
        ctx.lineTo(-28 - Math.random() * 10, 0);
        ctx.lineTo(-16, -4);
        ctx.fill();
      }
      noGlow();
      ctx.restore();

      if (player.shields > 0) {
        glow(S, 18);
        ctx.strokeStyle = S;
        ctx.globalAlpha = 0.5 + Math.sin(state.t * 6) * 0.15;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(player.x, player.y, player.r + 11, 0, TAU);
        ctx.stroke();
        ctx.globalAlpha = 1;
        noGlow();
      }
    }

    function panel(x, y, w, h, stroke) {
      roundRect(x, y, w, h, 8);
      ctx.fillStyle = "rgba(4, 8, 18, 0.82)";
      ctx.fill();
      ctx.strokeStyle = stroke;
      glow(stroke, 8);
      ctx.stroke();
      noGlow();
    }

    function drawHud() {
      panel(14, 12, 268, 100, P);
      ctx.fillStyle = HUD;
      ctx.font = "700 11px " + FONT;
      ctx.textAlign = "left";
      ctx.fillText("HULL INTEGRITY", 28, 32);
      ctx.fillStyle = "rgba(255,255,255,0.12)";
      ctx.fillRect(28, 40, 236, 10);
      const hpPct = player.maxHp ? player.hp / player.maxHp : 0;
      const hpCol = hpPct > 0.45 ? P : D;
      glow(hpCol, 10);
      ctx.fillStyle = hpCol;
      ctx.fillRect(28, 40, 236 * clamp(hpPct, 0, 1), 10);
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "600 13px " + FONT2;
      ctx.fillText(Math.ceil(player.hp) + " / " + player.maxHp, 28, 68);
      ctx.fillText("SHIELD " + player.shields + "/3", 150, 68);
      const spec = player.specialCd > 0 ? player.specialCd.toFixed(1) + "s" : "READY";
      ctx.fillText("DASH " + (player.dashCd > 0 ? player.dashCd.toFixed(1) + "s" : "RDY") + "   F-BOLT " + spec, 28, 90);

      panel(W - 282, 12, 268, 100, A);
      ctx.fillStyle = HUD;
      ctx.font = "700 11px " + FONT;
      ctx.fillText("ENERGY CORES", W - 266, 32);
      ctx.font = "900 28px " + FONT;
      ctx.fillStyle = P;
      ctx.fillText(String(state.cores), W - 266, 64);
      ctx.font = "600 13px " + FONT2;
      ctx.fillStyle = HUD;
      ctx.fillText("SCORE " + state.score + "   HI " + state.high, W - 266, 90);

      panel(W * 0.5 - 230, 12, 460, 48, S);
      ctx.textAlign = "center";
      ctx.fillStyle = HUD;
      ctx.font = "700 13px " + FONT;
      ctx.fillText(
        "WAVE " + String(state.wave).padStart(2, "0")
        + "   NODES " + capturedCount() + "/3"
        + "   x" + captureMult().toFixed(2)
        + "   WPN L" + weaponLevel()
        + (player.triple ? " TRI" : "")
        + (state.combo > 1 ? "   COMBO x" + state.combo : ""),
        W * 0.5, 42
      );

      if (specials.length > 0) {
        ctx.fillStyle = A;
        ctx.font = "700 12px " + FONT;
        ctx.fillText("STEER PLASMA WITH ARROW KEYS", W * 0.5, H - 18);
      }

      if (state.bannerT > 0) {
        ctx.globalAlpha = Math.min(1, state.bannerT);
        ctx.font = "900 30px " + FONT;
        ctx.fillStyle = P;
        glow(P, 18);
        ctx.fillText(state.banner, W * 0.5, H * 0.28);
        noGlow();
        ctx.globalAlpha = 1;
      }

      ctx.textAlign = "left";
      for (let i = 0; i < floaters.length; i++) {
        const f = floaters[i];
        ctx.globalAlpha = clamp(f.life, 0, 1);
        ctx.fillStyle = f.color;
        ctx.font = "700 14px " + FONT;
        ctx.fillText(f.text, f.x, f.y);
        ctx.globalAlpha = 1;
      }
    }

    function drawParticles() {
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        ctx.globalAlpha = clamp(p.life / 0.7, 0, 1);
        glow(p.color, 10);
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, TAU);
        ctx.fill();
        noGlow();
        ctx.globalAlpha = 1;
      }
    }

    function drawBoot() {
      drawGrid();
      ctx.textAlign = "center";
      ctx.fillStyle = P;
      glow(P, 24);
      ctx.font = "900 42px " + FONT;
      ctx.fillText("NEON DOMINATION", W * 0.5, 130);
      ctx.fillStyle = A;
      ctx.font = "700 18px " + FONT;
      ctx.fillText("AI ARENA", W * 0.5, 162);
      noGlow();

      panel(W * 0.5 - 360, 190, 720, 280, P);
      ctx.fillStyle = HUD;
      ctx.font = "600 15px " + FONT2;
      ctx.fillText("BATTLE CRY", W * 0.5, 220);
      ctx.font = "700 20px " + FONT;
      ctx.fillStyle = P;
      ctx.fillText("\"" + String(CFG.battle_cry || "").slice(0, 46) + "\"", W * 0.5, 252);
      ctx.font = "700 13px " + FONT;
      ctx.fillStyle = CFG.label === "NEGATIVE" ? D : CFG.label === "POSITIVE" ? P : S;
      ctx.fillText((theme.name || "PROTOCOL") + "  //  " + CFG.label + "  " + Math.round((CFG.confidence || 0) * 100) + "%", W * 0.5, 284);
      ctx.fillStyle = HUD;
      ctx.font = "600 15px " + FONT2;
      const lines = [
        "WASD flies the interceptor. Cannons auto-lock the nearest drone.",
        "F launches a plasma bolt you steer with the ARROW KEYS.",
        "Hostile drones now return fire. Dash through their volleys.",
        "Open the shop with B, then CLICK a card or press 1 / 2 / 3 to buy."
      ];
      for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], W * 0.5, 322 + i * 22);

      ctx.font = "700 16px " + FONT;
      ctx.fillStyle = P;
      glow(P, 12);
      ctx.globalAlpha = 0.65 + Math.sin(state.t * 4) * 0.35;
      ctx.fillText("PRESS  ENTER  /  CLICK  TO  DROP  IN", W * 0.5, 560);
      ctx.globalAlpha = 1;
      noGlow();
    }

    function drawShop() {
      ctx.fillStyle = "rgba(2, 4, 14, 0.78)";
      ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center";
      ctx.fillStyle = P;
      glow(P, 16);
      ctx.font = "900 28px " + FONT;
      ctx.fillText("UPGRADE LAB", W * 0.5, 86);
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "600 15px " + FONT2;
      ctx.fillText("CORES  " + state.cores + "     CLICK A CARD TO BUY     1 / 2 / 3  ALSO WORK     B CLOSES", W * 0.5, 118);

      const cards = shopCatalog();
      for (let i = 0; i < cards.length; i++) {
        const c = cards[i];
        const hover = mouse.x >= c.x && mouse.x <= c.x + c.w && mouse.y >= c.y && mouse.y <= c.y + c.h;
        roundRect(c.x, c.y, c.w, c.h, 14);
        ctx.fillStyle = hover ? "rgba(16, 22, 48, 0.96)" : "rgba(8, 10, 28, 0.94)";
        ctx.fill();
        ctx.strokeStyle = c.locked ? S : (hover ? A : P);
        glow(c.locked ? S : P, hover ? 18 : 10);
        ctx.lineWidth = hover ? 2.4 : 1.6;
        ctx.stroke();
        noGlow();
        ctx.fillStyle = P;
        ctx.font = "700 16px " + FONT;
        ctx.fillText(c.title, c.x + c.w / 2, c.y + 48);
        ctx.fillStyle = HUD;
        ctx.font = "600 14px " + FONT2;
        ctx.fillText(c.blurb, c.x + c.w / 2, c.y + 92);
        ctx.fillText(c.blurb2, c.x + c.w / 2, c.y + 112);
        ctx.fillStyle = A;
        ctx.font = "900 20px " + FONT;
        ctx.fillText(c.locked ? c.tag : c.cost + " CORES", c.x + c.w / 2, c.y + 168);
        ctx.fillStyle = HUD;
        ctx.font = "600 13px " + FONT2;
        ctx.fillText(c.tag, c.x + c.w / 2, c.y + 196);

        if (!c.locked) {
          roundRect(c.x + 40, c.y + 220, c.w - 80, 44, 8);
          ctx.fillStyle = hover ? A : P;
          ctx.fill();
          ctx.fillStyle = "#050510";
          ctx.font = "800 14px " + FONT;
          ctx.fillText("BUY  [" + c.key + "]", c.x + c.w / 2, c.y + 248);
        }
      }

      if (state.shopNoteT > 0) {
        ctx.fillStyle = state.shopNote.indexOf("NEED") >= 0 || state.shopNote.indexOf("ALREADY") >= 0 || state.shopNote.indexOf("FULL") >= 0 ? D : P;
        ctx.font = "700 16px " + FONT;
        ctx.fillText(state.shopNote, W * 0.5, 560);
      }
    }

    function drawOver() {
      ctx.fillStyle = "rgba(4, 0, 8, 0.62)";
      ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center";
      ctx.fillStyle = D;
      glow(D, 24);
      ctx.font = "900 42px " + FONT;
      ctx.fillText("SIGNAL LOST", W * 0.5, 220);
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "600 18px " + FONT2;
      ctx.fillText("SCORE  " + state.score + "     CORES  " + state.cores + "     WAVE  " + state.wave, W * 0.5, 270);
      ctx.fillText("HIGH  " + state.high + "     NODES  " + capturedCount() + "/3", W * 0.5, 300);
      ctx.fillStyle = P;
      ctx.font = "700 16px " + FONT;
      ctx.fillText("PRESS ENTER OR CLICK TO REBOOT", W * 0.5, 360);
    }

    function frame(now) {
      const dt = Math.min(0.033, (now - (frame.last || now)) / 1000);
      frame.last = now;
      updateFx(dt);

      if (state.mode === "play") {
        updatePlayer(dt);
        updateEnemies(dt);
        updateBullets(dt);
        updateHostile(dt);
        updateSpecials(dt);
        updateBases(dt);
        updateWaves(dt);
      } else if (state.mode === "boot" || state.mode === "shop" || state.mode === "over") {
        if (Math.random() < 0.35) burst(rand(0, W), rand(0, H), Math.random() > 0.5 ? P : A, 1, 8, 1.2);
      }

      ctx.save();
      if (state.shake > 0) {
        ctx.translate((Math.random() - 0.5) * state.shake, (Math.random() - 0.5) * state.shake);
      }
      if (state.mode === "boot") {
        drawBoot();
        drawParticles();
      } else {
        drawGrid();
        drawBases();
        drawParticles();
        drawBullets();
        drawEnemies();
        drawPlayer();
        drawHud();
        if (state.mode === "shop") drawShop();
        if (state.mode === "over") drawOver();
      }
      ctx.restore();
      requestAnimationFrame(frame);
    }

    function onKey(e) {
      keys[e.code] = true;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].indexOf(e.code) >= 0) {
        e.preventDefault();
      }
      ensureAudio();
      canvas.focus();

      if (e.code === "Enter") {
        if (state.mode === "boot" || state.mode === "over") resetRun();
      }
      if (e.code === "KeyB" || e.code === "Escape") {
        if (state.mode === "play") state.mode = "shop";
        else if (state.mode === "shop") state.mode = "play";
      }
      if (state.mode === "play" && e.code === "Space" && player.dashCd <= 0) {
        player.dashT = 0.18;
        player.dashCd = 1.45;
        player.hitT = 0.18;
        beep(240, 0.08, "sine", 0.05);
      }
      if (state.mode === "play" && (e.code === "KeyF" || e.code === "KeyQ")) {
        launchSpecial();
      }
      if (state.mode === "shop") {
        const k = e.key;
        if (e.code === "Digit1" || e.code === "Numpad1" || k === "1") buy("rapid");
        if (e.code === "Digit2" || e.code === "Numpad2" || k === "2") buy("triple");
        if (e.code === "Digit3" || e.code === "Numpad3" || k === "3") buy("shield");
      }
    }

    window.addEventListener("keydown", onKey, { passive: false });
    window.addEventListener("keyup", function (e) { keys[e.code] = false; });

    canvas.addEventListener("mousemove", function (e) {
      const p = canvasPos(e);
      mouse.x = p.x; mouse.y = p.y;
    });

    canvas.addEventListener("click", function (e) {
      canvas.focus();
      ensureAudio();
      const p = canvasPos(e);
      mouse.x = p.x; mouse.y = p.y;
      if (state.mode === "boot" || state.mode === "over") {
        resetRun();
        return;
      }
      if (state.mode === "shop") {
        tryBuyAt(p.x, p.y);
      }
    });

    canvas.focus();
    requestAnimationFrame(frame);
  })();
  </script>
</body>
</html>
"""
