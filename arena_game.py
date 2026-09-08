"""
NEON DOMINATION: AI Arena — HTML5 Canvas payload.

Streamlit embeds this document through ``components.html``. All realtime
simulation stays in JavaScript so the match can hold 60 FPS without a
Python round-trip each frame. Sentiment modifiers arrive as a JSON blob.
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

    :root {
      --p: #00f0ff;
      --s: #7b61ff;
      --a: #ff2bd6;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #03030a;
      font-family: "Rajdhani", sans-serif;
      color: #e8f6ff;
    }

    .shell {
      position: relative;
      width: 1080px;
      height: 700px;
      margin: 0 auto;
      background:
        radial-gradient(1200px 400px at 50% -10%, color-mix(in srgb, var(--p) 22%, transparent), transparent 60%),
        linear-gradient(180deg, #070714 0%, #03030a 100%);
      border: 1px solid color-mix(in srgb, var(--p) 55%, #111);
      box-shadow:
        0 0 0 1px rgba(255, 255, 255, 0.04) inset,
        0 0 40px color-mix(in srgb, var(--p) 28%, transparent),
        0 0 80px color-mix(in srgb, var(--a) 12%, transparent);
    }

    .topbar {
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      background: linear-gradient(90deg, rgba(0,0,0,0.55), rgba(12,12,28,0.75), rgba(0,0,0,0.55));
      border-bottom: 1px solid color-mix(in srgb, var(--p) 40%, transparent);
      letter-spacing: 0.18em;
    }

    .brand {
      font-family: "Orbitron", sans-serif;
      font-size: 13px;
      font-weight: 900;
      color: var(--p);
      text-shadow: 0 0 12px var(--p);
    }

    .brand span { color: var(--a); }

    .chip {
      font-size: 11px;
      letter-spacing: 0.22em;
      padding: 4px 10px;
      border: 1px solid color-mix(in srgb, var(--p) 50%, transparent);
      color: var(--p);
      background: rgba(0, 0, 0, 0.35);
      animation: pulse 2.4s ease-in-out infinite;
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
      gap: 22px;
      font-size: 13px;
      letter-spacing: 0.16em;
      color: rgba(200, 247, 255, 0.72);
      border-top: 1px solid rgba(0, 240, 255, 0.2);
      background: rgba(0, 0, 0, 0.45);
    }

    .hint b { color: var(--p); font-weight: 700; }

    .scan {
      pointer-events: none;
      position: absolute;
      inset: 44px 0 36px 0;
      background: repeating-linear-gradient(
        to bottom,
        rgba(255,255,255,0.025) 0px,
        rgba(255,255,255,0.025) 1px,
        transparent 1px,
        transparent 3px
      );
      mix-blend-mode: overlay;
      animation: drift 8s linear infinite;
    }

    .vignette {
      pointer-events: none;
      position: absolute;
      inset: 44px 0 36px 0;
      box-shadow: inset 0 0 90px rgba(0, 0, 0, 0.55);
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 0 rgba(0, 240, 255, 0); }
      50% { box-shadow: 0 0 16px color-mix(in srgb, var(--p) 45%, transparent); }
    }
    @keyframes drift {
      from { background-position: 0 0; }
      to { background-position: 0 12px; }
    }
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
      <span><b>WASD / ARROWS</b> MOVE</span>
      <span><b>SPACE</b> DASH</span>
      <span><b>B</b> UPGRADES</span>
      <span><b>AUTO-FIRE</b> NEAREST TARGET</span>
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

    document.documentElement.style.setProperty("--p", P);
    document.documentElement.style.setProperty("--s", S);
    document.documentElement.style.setProperty("--a", A);
    const chip = document.getElementById("protocolChip");
    if (chip) chip.textContent = (theme.name || "ION EQUILIBRIUM") + "  " + CFG.label;

    const keys = Object.create(null);
    const TAU = Math.PI * 2;

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
      high: Number(localStorage.getItem("neonDominationHi") || 0)
    };

    const player = {
      x: W * 0.5,
      y: H * 0.55,
      vx: 0,
      vy: 0,
      angle: -Math.PI / 2,
      r: 13,
      hp: CFG.player_max_hp,
      maxHp: CFG.player_max_hp,
      fireCd: 0,
      fireRate: 0.28,
      rapid: 0,
      triple: false,
      shields: 0,
      dashCd: 0,
      dashT: 0,
      hitT: 0
    };

    const bullets = [];
    const enemies = [];
    const particles = [];
    const floaters = [];
    const bases = [
      { x: 210, y: 175, r: 52, progress: 0, owner: 0, spin: 0 },
      { x: 870, y: 175, r: 52, progress: 0, owner: 0, spin: 1.2 },
      { x: 540, y: 470, r: 52, progress: 0, owner: 0, spin: 2.4 }
    ];

    let audioCtx = null;

    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function rand(a, b) { return a + Math.random() * (b - a); }
    function dist(ax, ay, bx, by) { return Math.hypot(bx - ax, by - ay); }

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
        const sp = rand(speed * 0.3, speed);
        particles.push({
          x, y,
          vx: Math.cos(ang) * sp,
          vy: Math.sin(ang) * sp,
          life: rand(0.25, 0.7),
          max: 0.7,
          color, size: rand(size * 0.5, size)
        });
      }
    }

    function floater(x, y, text, color) {
      floaters.push({ x, y, text, color, life: 0.9 });
    }

    function capturedCount() {
      return bases.filter(function (b) { return b.owner === 1; }).length;
    }

    function captureMult() {
      return 1 + capturedCount() * 0.35;
    }

    function weaponLevel() {
      return 1 + player.rapid + (player.triple ? 1 : 0);
    }

    function spawnEnemy() {
      const edge = Math.floor(Math.random() * 4);
      let x, y;
      if (edge === 0) { x = rand(30, W - 30); y = -18; }
      else if (edge === 1) { x = rand(30, W - 30); y = H + 18; }
      else if (edge === 2) { x = -18; y = rand(30, H - 30); }
      else { x = W + 18; y = rand(30, H - 30); }

      const kindRoll = Math.random();
      let kind = "drone";
      if (state.wave >= 3 && kindRoll > 0.72) kind = "hunter";
      if (state.wave >= 5 && kindRoll > 0.88) kind = "tank";

      const hpBase = kind === "tank" ? 4 : kind === "hunter" ? 2 : 1;
      const speedBase = kind === "hunter" ? 145 : kind === "tank" ? 70 : 95;

      enemies.push({
        x, y, kind,
        r: kind === "tank" ? 16 : 11,
        hp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        maxHp: Math.max(1, Math.round(hpBase * (CFG.enemy_hp_mult || 1))),
        speed: speedBase * (CFG.enemy_speed_mult || 1) * (0.92 + state.wave * 0.04),
        angle: 0,
        spin: rand(0, TAU)
      });
    }

    function nearestEnemy(from) {
      let best = null;
      let bestD = 1e9;
      for (let i = 0; i < enemies.length; i++) {
        const e = enemies[i];
        const d = dist(from.x, from.y, e.x, e.y);
        if (d < bestD) { bestD = d; best = e; }
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
          x: player.x + Math.cos(a) * 18,
          y: player.y + Math.sin(a) * 18,
          vx: Math.cos(a) * 520,
          vy: Math.sin(a) * 520,
          life: 0.9,
          r: 3.2
        });
      }
      burst(player.x + Math.cos(ang) * 16, player.y + Math.sin(ang) * 16, P, 4, 80, 2);
      beep(660 + player.rapid * 40, 0.06, "square", 0.03);
    }

    function killEnemy(e, index) {
      enemies.splice(index, 1);
      burst(e.x, e.y, e.kind === "tank" ? A : D, 18, 220, 3.5);
      state.shake = Math.min(10, state.shake + 4);
      state.comboTimer = 1.8;
      state.combo += 1;
      const basePts = (e.kind === "tank" ? 28 : e.kind === "hunter" ? 16 : 10);
      const pts = Math.round(basePts * (CFG.score_mult || 1) * captureMult() * (1 + state.combo * 0.08));
      const cores = Math.round((e.kind === "tank" ? 8 : e.kind === "hunter" ? 5 : 3) * (CFG.score_mult || 1));
      state.score += pts;
      state.cores += cores;
      floater(e.x, e.y - 10, "+" + cores + " CORES", P);
      beep(140, 0.12, "sawtooth", 0.05);
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
      bullets.length = 0;
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
      if (id === "rapid") {
        if (player.rapid >= 3) return;
        const cost = 60 * (player.rapid + 1);
        if (state.cores < cost) return;
        state.cores -= cost;
        player.rapid += 1;
        player.fireRate = 0.28 * Math.pow(0.78, player.rapid);
        beep(880, 0.1, "triangle", 0.06);
      } else if (id === "triple") {
        if (player.triple) return;
        if (state.cores < 140) return;
        state.cores -= 140;
        player.triple = true;
        beep(920, 0.12, "triangle", 0.06);
      } else if (id === "shield") {
        if (player.shields >= 3) return;
        if (state.cores < 90) return;
        state.cores -= 90;
        player.shields += 1;
        beep(420, 0.16, "sine", 0.07);
      }
    }

    function updatePlayer(dt) {
      let ax = 0, ay = 0;
      if (keys.KeyW || keys.ArrowUp) ay -= 1;
      if (keys.KeyS || keys.ArrowDown) ay += 1;
      if (keys.KeyA || keys.ArrowLeft) ax -= 1;
      if (keys.KeyD || keys.ArrowRight) ax += 1;
      const len = Math.hypot(ax, ay) || 1;
      ax /= len; ay /= len;

      const speed = player.dashT > 0 ? 640 : 275;
      player.vx = lerp(player.vx, ax * speed, 0.18);
      player.vy = lerp(player.vy, ay * speed, 0.18);
      player.x = clamp(player.x + player.vx * dt, 22, W - 22);
      player.y = clamp(player.y + player.vy * dt, 22, H - 22);

      if (player.dashT > 0) {
        player.dashT -= dt;
        burst(player.x, player.y, P, 2, 40, 2);
      }
      player.dashCd = Math.max(0, player.dashCd - dt);
      player.hitT = Math.max(0, player.hitT - dt);
      player.fireCd = Math.max(0, player.fireCd - dt);

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

    function lerpAngle(a, b, t) {
      let diff = ((b - a + Math.PI) % TAU + TAU) % TAU - Math.PI;
      return a + diff * t;
    }

    function updateEnemies(dt) {
      const aggro = CFG.aggro || 1;
      for (let i = enemies.length - 1; i >= 0; i--) {
        const e = enemies[i];
        e.spin += dt * 3;
        let tx = player.x, ty = player.y;
        if (Math.random() < 0.002 * aggro) {
          const b = bases[Math.floor(Math.random() * bases.length)];
          tx = b.x; ty = b.y;
        }
        const ang = Math.atan2(ty - e.y, tx - e.x);
        e.angle = ang;
        const jitter = (Math.sin(state.t * 4 + e.spin) * 18) * (2 - aggro);
        e.x += (Math.cos(ang) * e.speed + jitter) * dt;
        e.y += (Math.sin(ang) * e.speed) * dt;

        if (player.hitT <= 0 && player.dashT <= 0 && dist(e.x, e.y, player.x, player.y) < e.r + player.r) {
          if (player.shields > 0) {
            player.shields -= 1;
            player.hitT = 0.55;
            burst(player.x, player.y, S, 14, 160, 3);
            beep(300, 0.08, "triangle", 0.05);
          } else {
            player.hp -= e.kind === "tank" ? 18 : 12;
            player.hitT = 0.7;
            state.shake = 8;
            burst(player.x, player.y, D, 16, 180, 3);
            beep(90, 0.18, "sawtooth", 0.07);
            if (player.hp <= 0) {
              player.hp = 0;
              state.mode = "over";
              burst(player.x, player.y, P, 40, 280, 4);
            }
          }
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

    function updateBases(dt) {
      let holding = 0;
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i];
        b.spin += dt;
        const playerOn = dist(player.x, player.y, b.x, b.y) < b.r + 8;
        let enemyOn = false;
        for (let j = 0; j < enemies.length; j++) {
          if (dist(enemies[j].x, enemies[j].y, b.x, b.y) < b.r + 6) { enemyOn = true; break; }
        }
        if (playerOn && !enemyOn) {
          holding += 1;
          b.progress = clamp(b.progress + dt * 28, 0, 100);
          if (b.progress >= 100 && b.owner !== 1) {
            b.owner = 1;
            floater(b.x, b.y - 40, "NODE SECURED", P);
            beep(520, 0.2, "sine", 0.07);
            state.shake = 3;
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
        if (playerOn) {
          burst(b.x + rand(-20, 20), b.y + rand(-20, 20), b.owner ? P : A, 1, 20, 1.6);
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
      const cap = Math.min(18, Math.round(state.enemiesAliveTarget * (CFG.spawn_rate_mult || 1)));
      state.spawnTimer -= dt;
      if (enemies.length < cap && state.spawnTimer <= 0) {
        spawnEnemy();
        state.spawnTimer = Math.max(0.28, 1.15 - state.wave * 0.06) / (CFG.spawn_rate_mult || 1);
      }
      if (state.score > state.wave * 220) {
        state.wave += 1;
        state.enemiesAliveTarget = 4 + state.wave * 2;
        state.banner = "WAVE " + String(state.wave).padStart(2, "0");
        state.bannerT = 2.0;
        beep(440, 0.18, "square", 0.05);
      }
    }

    function updateFx(dt) {
      state.t += dt;
      state.shake = Math.max(0, state.shake - dt * 18);
      state.bannerT = Math.max(0, state.bannerT - dt);
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

    function glow(color, blur) {
      ctx.shadowColor = color;
      ctx.shadowBlur = blur;
    }
    function noGlow() { ctx.shadowBlur = 0; }

    function drawGrid() {
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, W, H);

      ctx.save();
      ctx.strokeStyle = GRID;
      ctx.lineWidth = 1;
      const gap = 46;
      const ox = (state.t * 18) % gap;
      const oy = (state.t * 12) % gap;
      ctx.beginPath();
      for (let x = -gap + ox; x < W + gap; x += gap) {
        ctx.moveTo(x, 0); ctx.lineTo(x, H);
      }
      for (let y = -gap + oy; y < H + gap; y += gap) {
        ctx.moveTo(0, y); ctx.lineTo(W, y);
      }
      ctx.stroke();

      ctx.strokeStyle = "rgba(255,255,255,0.03)";
      ctx.beginPath();
      for (let x = 0; x < W; x += 92) {
        ctx.moveTo(x, 0); ctx.lineTo(x * 0.2 + W * 0.4, H);
      }
      ctx.stroke();
      ctx.restore();

      const g = ctx.createRadialGradient(W * 0.5, H * 0.45, 40, W * 0.5, H * 0.45, 520);
      g.addColorStop(0, "rgba(0,0,0,0)");
      g.addColorStop(1, "rgba(0,0,0,0.55)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    function drawBases() {
      for (let i = 0; i < bases.length; i++) {
        const b = bases[i];
        const col = b.owner === 1 ? P : A;
        ctx.save();
        ctx.translate(b.x, b.y);
        glow(col, 18);
        ctx.strokeStyle = col;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, b.r, 0, TAU);
        ctx.stroke();

        ctx.globalAlpha = 0.12;
        ctx.fillStyle = col;
        ctx.beginPath();
        ctx.arc(0, 0, b.r, 0, TAU);
        ctx.fill();
        ctx.globalAlpha = 1;

        ctx.lineWidth = 6;
        ctx.strokeStyle = col;
        ctx.beginPath();
        ctx.arc(0, 0, b.r - 8, -Math.PI / 2, -Math.PI / 2 + TAU * (b.progress / 100));
        ctx.stroke();

        ctx.rotate(b.spin);
        ctx.lineWidth = 1.4;
        for (let k = 0; k < 6; k++) {
          ctx.rotate(TAU / 6);
          ctx.beginPath();
          ctx.moveTo(0, b.r - 16);
          ctx.lineTo(0, b.r - 6);
          ctx.stroke();
        }
        noGlow();
        ctx.restore();

        ctx.font = "700 11px Rajdhani";
        ctx.fillStyle = HUD;
        ctx.textAlign = "center";
        ctx.fillText("NODE " + (i + 1) + (b.owner === 1 ? "  OWNED" : ""), b.x, b.y + b.r + 16);
      }
    }

    function drawHex(x, y, r, rot) {
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = rot + i * TAU / 6;
        const px = x + Math.cos(a) * r;
        const py = y + Math.sin(a) * r;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
    }

    function drawEnemies() {
      for (let i = 0; i < enemies.length; i++) {
        const e = enemies[i];
        const col = e.kind === "tank" ? A : e.kind === "hunter" ? D : S;
        ctx.save();
        glow(col, 16);
        ctx.strokeStyle = col;
        ctx.fillStyle = "rgba(0,0,0,0.4)";
        ctx.lineWidth = 2;
        drawHex(e.x, e.y, e.r, e.spin);
        ctx.fill();
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(e.x, e.y, 3, 0, TAU);
        ctx.fillStyle = col;
        ctx.fill();
        noGlow();
        if (e.hp < e.maxHp) {
          ctx.fillStyle = "rgba(0,0,0,0.5)";
          ctx.fillRect(e.x - 12, e.y - e.r - 8, 24, 3);
          ctx.fillStyle = col;
          ctx.fillRect(e.x - 12, e.y - e.r - 8, 24 * (e.hp / e.maxHp), 3);
        }
        ctx.restore();
      }
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
        ctx.lineTo(b.x - b.vx * 0.03, b.y - b.vy * 0.03);
        ctx.stroke();
        noGlow();
      }
    }

    function drawPlayer() {
      ctx.save();
      ctx.translate(player.x, player.y);
      ctx.rotate(player.angle);
      glow(player.hitT > 0 ? D : P, 22);
      ctx.fillStyle = player.hitT > 0 ? D : P;
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(16, 0);
      ctx.lineTo(-12, 9);
      ctx.lineTo(-7, 0);
      ctx.lineTo(-12, -9);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#041018";
      ctx.beginPath();
      ctx.arc(2, 0, 3.2, 0, TAU);
      ctx.fill();
      if (player.dashT > 0 || Math.hypot(player.vx, player.vy) > 40) {
        ctx.fillStyle = A;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.moveTo(-12, 4);
        ctx.lineTo(-22 - Math.random() * 8, 0);
        ctx.lineTo(-12, -4);
        ctx.fill();
      }
      noGlow();
      ctx.restore();

      if (player.shields > 0) {
        glow(S, 18);
        ctx.strokeStyle = S;
        ctx.globalAlpha = 0.55 + Math.sin(state.t * 6) * 0.15;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(player.x, player.y, player.r + 10, 0, TAU);
        ctx.stroke();
        ctx.globalAlpha = 1;
        noGlow();
      }
    }

    function roundRect(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function drawHud() {
      roundRect(14, 12, 268, 92, 10);
      ctx.fillStyle = "rgba(4, 6, 16, 0.72)";
      ctx.fill();
      ctx.strokeStyle = P;
      glow(P, 8);
      ctx.stroke();
      noGlow();

      ctx.fillStyle = HUD;
      ctx.font = "700 12px Orbitron";
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
      ctx.font = "600 13px Rajdhani";
      ctx.fillText(Math.ceil(player.hp) + " / " + player.maxHp, 28, 66);
      ctx.fillText("SHIELD " + player.shields + "/3", 150, 66);
      ctx.fillText("DASH " + (player.dashCd > 0 ? player.dashCd.toFixed(1) + "s" : "READY"), 28, 86);

      roundRect(W - 282, 12, 268, 92, 10);
      ctx.fillStyle = "rgba(4, 6, 16, 0.72)";
      ctx.fill();
      ctx.strokeStyle = A;
      glow(A, 8);
      ctx.stroke();
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "700 12px Orbitron";
      ctx.textAlign = "left";
      ctx.fillText("ENERGY CORES", W - 266, 32);
      ctx.font = "900 28px Orbitron";
      ctx.fillStyle = P;
      ctx.fillText(String(state.cores), W - 266, 62);
      ctx.font = "600 13px Rajdhani";
      ctx.fillStyle = HUD;
      ctx.fillText("SCORE " + state.score + "   HI " + state.high, W - 266, 84);

      roundRect(W * 0.5 - 210, 12, 420, 52, 10);
      ctx.fillStyle = "rgba(4, 6, 16, 0.72)";
      ctx.fill();
      ctx.strokeStyle = S;
      ctx.stroke();
      ctx.textAlign = "center";
      ctx.fillStyle = HUD;
      ctx.font = "700 13px Orbitron";
      ctx.fillText(
        "WAVE " + String(state.wave).padStart(2, "0")
        + "   NODES " + capturedCount() + "/3"
        + "   x" + captureMult().toFixed(2)
        + "   WPN L" + weaponLevel()
        + (player.triple ? " TRI" : "")
        + (state.combo > 1 ? "   COMBO x" + state.combo : ""),
        W * 0.5, 42
      );

      if (state.bannerT > 0) {
        ctx.globalAlpha = Math.min(1, state.bannerT);
        ctx.font = "900 34px Orbitron";
        ctx.fillStyle = P;
        glow(P, 20);
        ctx.fillText(state.banner, W * 0.5, H * 0.28);
        noGlow();
        ctx.globalAlpha = 1;
      }

      ctx.textAlign = "left";
      for (let i = 0; i < floaters.length; i++) {
        const f = floaters[i];
        ctx.globalAlpha = clamp(f.life, 0, 1);
        ctx.fillStyle = f.color;
        ctx.font = "700 14px Orbitron";
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
      ctx.font = "900 42px Orbitron";
      ctx.fillText("NEON DOMINATION", W * 0.5, 150);
      ctx.fillStyle = A;
      ctx.font = "700 18px Orbitron";
      ctx.fillText("AI ARENA", W * 0.5, 182);
      noGlow();

      roundRect(W * 0.5 - 340, 220, 680, 210, 14);
      ctx.fillStyle = "rgba(4,8,18,0.82)";
      ctx.fill();
      ctx.strokeStyle = P;
      ctx.stroke();

      ctx.fillStyle = HUD;
      ctx.font = "600 16px Rajdhani";
      ctx.fillText("BATTLE CRY", W * 0.5, 250);
      ctx.font = "700 22px Orbitron";
      ctx.fillStyle = P;
      ctx.fillText("“" + String(CFG.battle_cry || "").slice(0, 48) + "”", W * 0.5, 284);

      ctx.font = "700 14px Orbitron";
      ctx.fillStyle = CFG.label === "NEGATIVE" ? D : CFG.label === "POSITIVE" ? P : S;
      ctx.fillText((theme.name || "PROTOCOL") + "   //   " + CFG.label + "  " + Math.round((CFG.confidence || 0) * 100) + "%", W * 0.5, 318);

      ctx.fillStyle = HUD;
      ctx.font = "600 15px Rajdhani";
      const lines = [
        "Glide with WASD. Cannons lock the nearest drone automatically.",
        "Stand on the three Nodes to capture them and raise your multiplier.",
        "Bank Energy Cores, open the lab with B, and rewrite the loadout.",
        "Hold all three Nodes at once for a Total Domination bonus."
      ];
      for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], W * 0.5, 348 + i * 20);

      ctx.font = "700 16px Orbitron";
      ctx.fillStyle = P;
      glow(P, 12);
      const flicker = 0.65 + Math.sin(state.t * 4) * 0.35;
      ctx.globalAlpha = flicker;
      ctx.fillText("PRESS  ENTER  /  CLICK  TO  DROP  IN", W * 0.5, 560);
      ctx.globalAlpha = 1;
      noGlow();
    }

    function drawShop() {
      ctx.fillStyle = "rgba(2, 4, 12, 0.72)";
      ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center";
      ctx.fillStyle = P;
      glow(P, 16);
      ctx.font = "900 28px Orbitron";
      ctx.fillText("UPGRADE LAB", W * 0.5, 120);
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "600 14px Rajdhani";
      ctx.fillText("CORES AVAILABLE  " + state.cores + "     [B] OR [ESC] CLOSE", W * 0.5, 148);

      const cards = [
        { id: "rapid", title: "01  RAPID FIRE", desc: "Cycle the cannons faster.\nStacks 3 times.", cost: player.rapid >= 3 ? "MAX" : String(60 * (player.rapid + 1)), key: "1", locked: player.rapid >= 3 },
        { id: "triple", title: "02  TRIPLE SHOT", desc: "Split each volley into a\nthree-bolt spread.", cost: player.triple ? "OWNED" : "140", key: "2", locked: player.triple },
        { id: "shield", title: "03  SHIELD", desc: "Absorb one lethal hit.\nYou can carry 3 layers.", cost: player.shields >= 3 ? "MAX" : "90", key: "3", locked: player.shields >= 3 }
      ];
      for (let i = 0; i < cards.length; i++) {
        const c = cards[i];
        const x = 150 + i * 270;
        const y = 200;
        roundRect(x, y, 240, 250, 14);
        ctx.fillStyle = "rgba(8, 10, 28, 0.92)";
        ctx.fill();
        ctx.strokeStyle = c.locked ? S : P;
        glow(c.locked ? S : P, 12);
        ctx.stroke();
        noGlow();
        ctx.fillStyle = P;
        ctx.font = "700 14px Orbitron";
        ctx.fillText(c.title, x + 120, y + 40);
        ctx.fillStyle = HUD;
        ctx.font = "600 15px Rajdhani";
        const bits = c.desc.split("\n");
        ctx.fillText(bits[0], x + 120, y + 90);
        ctx.fillText(bits[1], x + 120, y + 112);
        ctx.font = "900 22px Orbitron";
        ctx.fillStyle = A;
        ctx.fillText(c.cost === "MAX" || c.cost === "OWNED" ? c.cost : c.cost + " CORES", x + 120, y + 170);
        ctx.font = "700 13px Orbitron";
        ctx.fillStyle = P;
        ctx.fillText("PRESS  " + c.key, x + 120, y + 214);
      }
    }

    function drawOver() {
      ctx.fillStyle = "rgba(4, 0, 8, 0.55)";
      ctx.fillRect(0, 0, W, H);
      ctx.textAlign = "center";
      ctx.fillStyle = D;
      glow(D, 24);
      ctx.font = "900 42px Orbitron";
      ctx.fillText("SIGNAL LOST", W * 0.5, 220);
      noGlow();
      ctx.fillStyle = HUD;
      ctx.font = "600 18px Rajdhani";
      ctx.fillText("SCORE  " + state.score + "     CORES  " + state.cores + "     WAVE  " + state.wave, W * 0.5, 270);
      ctx.fillText("HIGH  " + state.high + "     NODES  " + capturedCount() + "/3", W * 0.5, 300);
      ctx.fillStyle = P;
      ctx.font = "700 16px Orbitron";
      ctx.fillText("PRESS ENTER TO REBOOT THE ARENA", W * 0.5, 360);
    }

    function frame(now) {
      const dt = Math.min(0.033, (now - (frame.last || now)) / 1000);
      frame.last = now;
      updateFx(dt);

      if (state.mode === "play") {
        updatePlayer(dt);
        updateEnemies(dt);
        updateBullets(dt);
        updateBases(dt);
        updateWaves(dt);
      } else if (state.mode === "boot" || state.mode === "shop" || state.mode === "over") {
        if (Math.random() < 0.4) burst(rand(0, W), rand(0, H), Math.random() > 0.5 ? P : A, 1, 8, 1.2);
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

    window.addEventListener("keydown", function (e) {
      keys[e.code] = true;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].indexOf(e.code) >= 0) {
        e.preventDefault();
      }
      ensureAudio();

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
      if (state.mode === "shop") {
        if (e.code === "Digit1" || e.code === "Numpad1") buy("rapid");
        if (e.code === "Digit2" || e.code === "Numpad2") buy("triple");
        if (e.code === "Digit3" || e.code === "Numpad3") buy("shield");
      }
    }, { passive: false });

    window.addEventListener("keyup", function (e) { keys[e.code] = false; });

    canvas.addEventListener("click", function () {
      canvas.focus();
      ensureAudio();
      if (state.mode === "boot") resetRun();
    });

    canvas.focus();
    requestAnimationFrame(frame);
  })();
  </script>
</body>
</html>
"""
