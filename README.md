# NEON DOMINATION: AI Arena

A twin-stick / top-down arena shooter built as a **Streamlit** command deck around a **60 FPS HTML5 Canvas** match. Before you drop in, a Hugging Face **DistilBERT** sentiment model reads your battle cry and rewrites the rules of the night: hull strength, drone aggression, score payout, and the entire neon palette.

## What you are flying

You pilot a glowing interceptor across a cyberpunk grid. Cannons **auto-lock the nearest drone**. Three capture nodes sit on the map. Stand on a node to claim it. Each owned node raises your score multiplier. Hold all three at once and the arena pays a **Total Domination** bonus.

Energy Cores drop from every kill. Open the **Upgrade Lab** with `B` and spend them mid-fight.

| Control | Action |
| --- | --- |
| `WASD` | Move the interceptor |
| `1` | Equip Pulse Cannon (starter) |
| `2` `3` `4` `5` `6` | Switch to a purchased weapon |
| `F` or `Q` | Launch a plasma bolt |
| Arrow keys | Steer the plasma bolt |
| `Space` | Dash (brief i-frames) |
| Auto | Equipped gun lock-fires the nearest drone |
| `B` / `Esc` | Open / close the armory |
| Click a shop card | Buy a weapon or module |
| `Enter` | Start or reboot the run |

## AI sentiment logic

The start screen asks for a **Battle Cry**. Streamlit runs:

`distilbert-base-uncased-finetuned-sst-2-english`

SST-2 only emits positive or negative. Confidence below **0.72** is treated as **Neutral**, so hesitant or mixed lines do not overclock the match.

| Sentiment | Protocol | Player | Enemies | Scoring | Theme |
| --- | --- | --- | --- | --- | --- |
| Positive | Aurora Protocol | 160 HP | Moderate speed | 1× | Emerald / cyan |
| Negative | Crimson Overclock | 110 HP | Faster, more aggressive, extra HP | **2× cores and points** | Crimson / amber |
| Neutral | Ion Equilibrium | 125 HP | Baseline | 1× | Cyan / violet |

If `torch` / `transformers` cannot load (no weights, no network on first download), a compact lexicon classifier keeps the arena playable. The HUD chip still reports which analyzer fired.

Gameplay modifiers are computed **once in Python**, then injected into the Canvas document as JSON. The simulation never talks back to Streamlit during a frame — that is how the gunplay stays at 60 FPS.

## Armory

Shop cards show a drawn weapon image plus **DMG / RATE / VEL / AOE** bars. A purchase lights up on the right-hand **AVAILABLE** rack. Key `1` is always the Pulse Cannon; keys `2`–`6` switch only after you buy that gun.

| Slot | Weapon | Role | Cost |
| --- | --- | --- | --- |
| `1` | Pulse Cannon | Starter lock-fire | Free |
| `2` | Rocket Pod | Slow blast warhead | 160 |
| `3` | Velocity Needle | Bullet-speed booster pins | 150 |
| `4` | Scatter Volt | Five-bolt cone | 140 |
| `5` | Ion Lance | Piercing beam | 180 |
| `6` | Seeker Swarm | Twin homing mites | 200 |

Modules (also in the shop, shown at the bottom of the rack): Velocity Booster (+35% projectile speed), Rapid Coil (+30% fire rate), Shield Cell (absorb one hit, up to 3).

## Architecture

```
app.py                 Streamlit UI, option menu, model cache
sentiment_engine.py    DistilBERT pipeline + lexicon fallback + modifiers
arena_game.py          Self-contained HTML/CSS/JS Canvas arena
requirements.txt       Python dependencies
.streamlit/config.toml Dark neon Streamlit theme
```

- **Python / Streamlit** — battle cry, sentiment, chrome, `components.html`.
- **JavaScript / Canvas** — movement, auto-fire, waves, nodes, particles, shop, HUD.
- **streamlit-option-menu** — Arena / Intel Brief / Loadout. Falls back to a radio control if the package is missing.

## Run it

Python 3.10+ recommended. First launch downloads DistilBERT weights (on the order of 250 MB).

```bash
cd My-game
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

Type a battle cry, hit **DEPLOY TO ARENA**, click the canvas once so it owns the keyboard, and press **Enter**.

### CPU vs GPU

The pipeline uses CUDA when PyTorch can see a GPU, otherwise CPU. Sentiment inference is a single short sequence, so CPU is fine.

## Design notes

The outer deck uses Orbitron / Rajdhani, glowing borders, and a scanline overlay. Inside the Canvas: animated grid, hexagonal drones, capture rings, hull bar, cores, node count, weapon level, and a local high score in `localStorage`.

This project is a self-contained demo of **AI-conditioned game design**: language in, systemic rules out, no generative text during combat.

## License

This project is released under the [MIT License](LICENSE).
