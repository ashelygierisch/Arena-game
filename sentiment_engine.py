"""
NEON DOMINATION: AI Arena — Battle Cry sentiment analysis.

Uses Hugging Face Transformers (DistilBERT SST-2) when available, then
maps the model output onto gameplay modifiers (health, aggression, score).
A lightweight lexicon fallback keeps the arena playable if the model
cannot be downloaded or imported.
"""

from __future__ import annotations

import re
from typing import Any


# SST-2 only emits POSITIVE / NEGATIVE. Treat low-confidence outputs as Neutral
# so middling battle cries do not swing the entire match.
NEUTRAL_CONFIDENCE_THRESHOLD = 0.72

MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"

# Compact lexicon used only when Transformers is unavailable.
_POSITIVE_LEXICON = {
    "win", "victory", "glory", "legend", "legendary", "awesome", "love",
    "hope", "shine", "bright", "hero", "courage", "brave", "peace", "good",
    "great", "amazing", "excellent", "dominate", "champion", "rise", "light",
    "protect", "honor", "together", "unstoppable", "epic", "beautiful",
    "yes", "wow", "fire", "lets", "go", "neon",
}
_NEGATIVE_LEXICON = {
    "destroy", "hate", "kill", "rage", "death", "dark", "revenge", "pain",
    "fear", "doom", "crash", "burn", "blood", "war", "annihilate", "crush",
    "die", "dead", "evil", "anger", "angry", "fury", "ruin", "never", "no",
    "lose", "lost", "void", "shadow", "obliterate", "suffer", "nightmare",
}


def load_sentiment_pipeline():
    """
    Load and return a cached-friendly Transformers sentiment pipeline.

    Call this from Streamlit via ``@st.cache_resource`` so the weights are
    downloaded once per process. Raises ImportError / OSError on failure
    so the caller can fall back to the lexicon analyzer.
    """
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        task="sentiment-analysis",
        model=MODEL_ID,
        device=device,
        truncation=True,
    )


def _lexicon_analyze(text: str) -> dict[str, Any]:
    """Heuristic POSITIVE / NEGATIVE / NEUTRAL scoring from word hits."""
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return {"label": "NEUTRAL", "confidence": 0.5, "source": "fallback"}

    pos = sum(1 for t in tokens if t in _POSITIVE_LEXICON)
    neg = sum(1 for t in tokens if t in _NEGATIVE_LEXICON)
    total = pos + neg

    if total == 0 or pos == neg:
        return {"label": "NEUTRAL", "confidence": 0.55, "source": "fallback"}

    if pos > neg:
        confidence = min(0.95, 0.62 + (pos - neg) / max(len(tokens), 1) * 0.8)
        return {"label": "POSITIVE", "confidence": round(confidence, 3), "source": "fallback"}

    confidence = min(0.95, 0.62 + (neg - pos) / max(len(tokens), 1) * 0.8)
    return {"label": "NEGATIVE", "confidence": round(confidence, 3), "source": "fallback"}


def _model_to_label(raw_label: str, score: float) -> tuple[str, float]:
    """Map SST-2 output onto POSITIVE / NEGATIVE / NEUTRAL."""
    normalized = (raw_label or "").upper()
    if "POS" in normalized:
        family = "POSITIVE"
    elif "NEG" in normalized:
        family = "NEGATIVE"
    else:
        family = "NEUTRAL"

    if family != "NEUTRAL" and score < NEUTRAL_CONFIDENCE_THRESHOLD:
        return "NEUTRAL", score
    return family, score


def build_modifiers(label: str) -> dict[str, Any]:
    """
    Translate sentiment into arena rules and a neon palette.

    Positive  — tankier ship, moderate drone speed, emerald theme.
    Negative  — faster / hungrier drones, 2x cores, crimson theme.
    Neutral   — baseline numbers, cyan / violet theme.
    """
    label = (label or "NEUTRAL").upper()

    if label == "POSITIVE":
        return {
            "player_max_hp": 160,
            "enemy_speed_mult": 1.12,
            "enemy_hp_mult": 1.0,
            "spawn_rate_mult": 1.0,
            "score_mult": 1.0,
            "aggro": 0.85,
            "theme": {
                "name": "AURORA PROTOCOL",
                "primary": "#00ff9c",
                "secondary": "#39ff14",
                "accent": "#00e5ff",
                "danger": "#ff2a6d",
                "bg": "#02080a",
                "grid": "rgba(0, 255, 156, 0.10)",
                "hud": "#9affd4",
            },
        }

    if label == "NEGATIVE":
        return {
            "player_max_hp": 110,
            "enemy_speed_mult": 1.55,
            "enemy_hp_mult": 1.15,
            "spawn_rate_mult": 1.25,
            "score_mult": 2.0,
            "aggro": 1.35,
            "theme": {
                "name": "CRIMSON OVERCLOCK",
                "primary": "#ff2a6d",
                "secondary": "#ff003c",
                "accent": "#ffb703",
                "danger": "#ff003c",
                "bg": "#0a0206",
                "grid": "rgba(255, 42, 109, 0.12)",
                "hud": "#ffc2d4",
            },
        }

    return {
        "player_max_hp": 125,
        "enemy_speed_mult": 1.0,
        "enemy_hp_mult": 1.0,
        "spawn_rate_mult": 1.0,
        "score_mult": 1.0,
        "aggro": 1.0,
        "theme": {
            "name": "ION EQUILIBRIUM",
            "primary": "#00f0ff",
            "secondary": "#7b61ff",
            "accent": "#ff2bd6",
            "danger": "#ff2a6d",
            "bg": "#050510",
            "grid": "rgba(0, 240, 255, 0.10)",
            "hud": "#c8f7ff",
        },
    }


def analyze_battle_cry(text: str, nlp=None) -> dict[str, Any]:
    """
    Analyze a battle cry and return a gameplay payload.

    Parameters
    ----------
    text:
        Player-authored rally text from the start screen.
    nlp:
        Optional Transformers pipeline. When omitted or when inference
        fails, the lexicon fallback is used.
    """
    cry = (text or "").strip()
    if not cry:
        label, confidence, source, raw = "NEUTRAL", 0.5, "empty", "NEUTRAL"
    elif nlp is not None:
        try:
            result = nlp(cry[:512])[0]
            raw = str(result.get("label", "NEUTRAL"))
            score = float(result.get("score", 0.5))
            label, confidence = _model_to_label(raw, score)
            source = "transformers"
        except Exception:
            fallback = _lexicon_analyze(cry)
            label = fallback["label"]
            confidence = fallback["confidence"]
            source = "fallback"
            raw = label
    else:
        fallback = _lexicon_analyze(cry)
        label = fallback["label"]
        confidence = fallback["confidence"]
        source = "fallback"
        raw = label

    modifiers = build_modifiers(label)
    return {
        "battle_cry": cry or "SILENCE IS A WEAPON",
        "label": label,
        "confidence": round(float(confidence), 3),
        "raw_label": raw,
        "source": source,
        **modifiers,
    }
