"""
NEON DOMINATION: AI Arena — Streamlit command deck.

Python owns the chrome, the battle-cry analysis, and the one-shot inject of
sentiment modifiers into the HTML5 Canvas arena. The match itself never
round-trips back to Streamlit; that keeps the gunplay at 60 FPS.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from arena_game import build_arena_html
from sentiment_engine import analyze_battle_cry, load_sentiment_pipeline


st.set_page_config(
    page_title="NEON DOMINATION: AI Arena",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_chrome() -> None:
    """Hide stock Streamlit chrome and paint a cyberpunk frame."""
    st.markdown(
        """
        <style>
          @import url("https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap");

          html, body, [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(900px 420px at 10% -10%, rgba(0, 240, 255, 0.12), transparent 55%),
              radial-gradient(800px 380px at 90% 0%, rgba(255, 43, 214, 0.10), transparent 50%),
              linear-gradient(180deg, #050510 0%, #070714 40%, #030308 100%);
            color: #e8f6ff;
          }
          header, footer, [data-testid="stToolbar"], #MainMenu { visibility: hidden; height: 0; }
          .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.4rem;
            max-width: 1180px;
          }
          h1, h2, h3, .stMarkdown p, .stCaption, label {
            font-family: "Rajdhani", sans-serif;
          }
          .hero-wrap {
            border: 1px solid rgba(0, 240, 255, 0.35);
            background:
              linear-gradient(90deg, rgba(0, 240, 255, 0.08), rgba(123, 97, 255, 0.08) 50%, rgba(255, 43, 214, 0.08)),
              rgba(6, 8, 20, 0.75);
            box-shadow: 0 0 40px rgba(0, 240, 255, 0.12), inset 0 0 40px rgba(123, 97, 255, 0.08);
            padding: 22px 28px 18px;
            margin-bottom: 12px;
            position: relative;
            overflow: hidden;
          }
          .hero-wrap::after {
            content: "";
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(
              to bottom,
              rgba(255,255,255,0.03) 0px,
              rgba(255,255,255,0.03) 1px,
              transparent 1px,
              transparent 4px
            );
            pointer-events: none;
          }
          .hero-kicker {
            font-family: "Orbitron", sans-serif;
            letter-spacing: 0.42em;
            font-size: 11px;
            color: #00f0ff;
            margin-bottom: 6px;
          }
          .hero-title {
            font-family: "Orbitron", sans-serif;
            font-weight: 900;
            font-size: 34px;
            letter-spacing: 0.08em;
            color: #f4fbff;
            text-shadow: 0 0 18px rgba(0, 240, 255, 0.55);
            margin: 0;
          }
          .hero-title span { color: #ff2bd6; }
          .hero-sub {
            margin-top: 8px;
            color: #9fd9e8;
            font-size: 16px;
            letter-spacing: 0.04em;
          }
          .stTextInput input {
            background: #070714 !important;
            color: #e8f6ff !important;
            border: 1px solid rgba(0, 240, 255, 0.45) !important;
            border-radius: 0 !important;
            font-family: "Orbitron", sans-serif !important;
            letter-spacing: 0.04em;
          }
          .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #00f0ff, #7b61ff 55%, #ff2bd6);
            color: #050510;
            border: 0;
            font-family: "Orbitron", sans-serif;
            font-weight: 800;
            letter-spacing: 0.18em;
            padding: 0.7rem 1rem;
            box-shadow: 0 0 22px rgba(0, 240, 255, 0.35);
          }
          .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 28px rgba(255, 43, 214, 0.4);
          }
          div[data-testid="stMetric"] {
            background: rgba(8, 10, 28, 0.7);
            border: 1px solid rgba(0, 240, 255, 0.25);
            padding: 8px 12px;
          }
          .intel-card {
            border: 1px solid rgba(0, 240, 255, 0.28);
            background: rgba(8, 10, 24, 0.72);
            padding: 16px 18px;
            height: 100%;
          }
          .intel-card h3 {
            font-family: "Orbitron", sans-serif;
            color: #00f0ff;
            font-size: 15px;
            letter-spacing: 0.14em;
            margin-bottom: 8px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_nlp():
    """Load DistilBERT once per server process. Returns None on failure."""
    try:
        return load_sentiment_pipeline()
    except Exception:
        return None


def nav_choice() -> str:
    """Horizontal command menu with a graceful fallback if the extra package is missing."""
    try:
        from streamlit_option_menu import option_menu

        return option_menu(
            menu_title=None,
            options=["Arena", "Intel Brief", "Loadout"],
            icons=["cpu", "info-circle", "lightning-charge"],
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {
                    "background-color": "rgba(6, 8, 20, 0.9)",
                    "padding": "4px",
                    "border": "1px solid rgba(0, 240, 255, 0.25)",
                },
                "icon": {"color": "#00f0ff", "font-size": "16px"},
                "nav-link": {
                    "color": "#c8f7ff",
                    "font-family": "Orbitron, sans-serif",
                    "font-size": "13px",
                    "letter-spacing": "0.12em",
                    "--hover-color": "rgba(0, 240, 255, 0.12)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, #ff2a6d, #7b61ff)",
                    "color": "#fff",
                },
            },
        )
    except Exception:
        return st.radio("Command deck", ["Arena", "Intel Brief", "Loadout"], horizontal=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
          <div class="hero-kicker">REWORKD  //  SECTOR 09  //  LIVE FEED</div>
          <p class="hero-title">NEON <span>DOMINATION</span></p>
          <div class="hero-sub">Twin-stick arena warfare driven by a DistilBERT battle-cry classifier.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intel() -> None:
    st.markdown("### Combat Doctrine")
    c1, c2, c3 = st.columns(3)
    cards = [
        (
            "01  MOVEMENT",
            "Pilot with WASD or the arrow keys. Space triggers a short invulnerable dash. "
            "The hull auto-locks the nearest drone and fires without a trigger pull.",
        ),
        (
            "02  NODE CONTROL",
            "Three capture nodes sit on the grid. Stand inside a ring to claim it. "
            "Each owned node raises your score multiplier. Own all three for a Total Domination bonus.",
        ),
        (
            "03  ENERGY ECONOMY",
            "Destroyed drones drop Energy Cores. Open the Upgrade Lab with B and spend cores on "
            "Rapid Fire, Triple Shot, or Shield layers mid-match.",
        ),
    ]
    for col, (title, body) in zip((c1, c2, c3), cards):
        col.markdown(f'<div class="intel-card"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)

    st.markdown("### Sentiment Protocols")
    p1, p2, p3 = st.columns(3)
    p1.success("**POSITIVE / AURORA** — +hull integrity, moderate drone speed, emerald neon.")
    p2.error("**NEGATIVE / CRIMSON** — faster, hungrier drones, **2× cores**, red neon.")
    p3.info("**NEUTRAL / ION** — balanced numbers, cyan / violet neon.")


def render_loadout() -> None:
    st.markdown("### Upgrade Lab")
    a, b, c = st.columns(3)
    a.markdown(
        '<div class="intel-card"><h3>01  RAPID FIRE</h3>'
        "<p>Shortens cannon cooldown. Stacks three times. Cost scales 60 / 120 / 180 cores.</p></div>",
        unsafe_allow_html=True,
    )
    b.markdown(
        '<div class="intel-card"><h3>02  TRIPLE SHOT</h3>'
        "<p>Each volley becomes a three-bolt spread. Single purchase, 140 cores.</p></div>",
        unsafe_allow_html=True,
    )
    c.markdown(
        '<div class="intel-card"><h3>03  SHIELD</h3>'
        "<p>Each layer eats one lethal contact. Carry up to three. 90 cores per layer.</p></div>",
        unsafe_allow_html=True,
    )
    st.caption("Weapon Level on the HUD equals 1 + Rapid Fire ranks + Triple Shot unlock.")


def deploy_arena(payload: dict) -> None:
    """Paint protocol telemetry, then drop the player into the Canvas match."""
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Protocol", payload["theme"]["name"])
    m2.metric("Sentiment", payload["label"])
    m3.metric("Confidence", f"{payload['confidence'] * 100:.1f}%")
    m4.metric("Score Mult", f"{payload['score_mult']:.1f}×")
    st.caption(
        f"Analyzer: `{payload['source']}`  ·  Hull {payload['player_max_hp']} HP  ·  "
        f"Enemy speed ×{payload['enemy_speed_mult']:.2f}  ·  Click the arena to capture keyboard."
    )
    html = build_arena_html(payload)
    # Streamlit 1.50+ replaced components.html with st.iframe for srcdoc embeds.
    if hasattr(st, "iframe"):
        st.iframe(html, height=720, width="stretch")
    else:
        components.html(html, height=720, scrolling=False)


def main() -> None:
    inject_chrome()
    render_hero()

    if "payload" not in st.session_state:
        st.session_state.payload = None

    selected = nav_choice()
    if selected == "Intel Brief":
        render_intel()
        return
    if selected == "Loadout":
        render_loadout()
        return

    st.markdown("#### Enter your Battle Cry")
    # A form keeps keystrokes from rerunning Streamlit (which would remount the iframe).
    with st.form("battle_cry_form", clear_on_submit=False):
        cry = st.text_input(
            "Battle Cry",
            value="We rise in the neon and we do not fall.",
            max_chars=160,
            label_visibility="collapsed",
            placeholder="Enter your Battle Cry:",
        )
        go = st.form_submit_button("DEPLOY TO ARENA", type="primary")
    if go:
        with st.spinner("DistilBERT is reading the battle cry…"):
            nlp = get_nlp()
            st.session_state.payload = analyze_battle_cry(cry, nlp=nlp)
            if nlp is None:
                st.warning(
                    "Transformers model was unavailable, so the lexicon fallback classified this cry. "
                    "Install torch + transformers for the full DistilBERT path."
                )

    if st.session_state.payload:
        deploy_arena(st.session_state.payload)
    else:
        render_intel()


if __name__ == "__main__":
    main()
