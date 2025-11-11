import base64
import hashlib
import io
import json
import os
import random
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

import db
import notifications
from security import (
    create_password_record,
    decrypt_text,
    derive_encryption_key,
    encrypt_text,
    verify_password,
)

APP_NAME = "Heartline Care Companion"
SCHEDULES = ["Day", "Night", "Mixed"]
HOME_SECTIONS = ["Planner", "Widget shelf", "Deep care"]
DEFAULT_THEME = "coquette"
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
:root {
  --sand: #D8CFC4;
  --olive: #7C8663;
  --warm-charcoal: #2F2F32;
  --sage: #AEBFA7;
  --off-white: #F7F6F3;
  --header-font: "Inter", sans-serif;
  --body-font: "Inter", sans-serif;
  --ease-soft: cubic-bezier(.16,.84,.44,1);
  --transition-soft: 0.3s var(--ease-soft);

  --heart-bg: linear-gradient(180deg, rgba(247,246,243,1) 0%, rgba(216,207,196,0.6) 60%, #FFFFFF 100%);
  --heart-text: var(--warm-charcoal);
  --heart-hero-gradient: linear-gradient(120deg, rgba(247,246,243,0.95), rgba(174,191,167,0.45));
  --heart-hero-shadow: 0 22px 46px rgba(47,47,50,0.15);
  --heart-card-bg: var(--off-white);
  --heart-card-border: rgba(47,47,50,0.08);
  --heart-card-shadow: 0 15px 32px rgba(47,47,50,0.11);
  --heart-button-bg: var(--sage);
  --heart-button-hover: #8ea182;
  --heart-button-text: #1f1f21;
  --heart-button-radius: 16px;
  --heart-button-shadow: 0 12px 24px rgba(47,47,50,0.12);
  --heart-checkbox: var(--olive);
  --heart-illustration-border: rgba(47,47,50,0.08);
  --heart-illustration-bg: linear-gradient(120deg, rgba(174,191,167,0.25), rgba(247,246,243,0.7));
}
*::-webkit-scrollbar { width: 6px; }
*::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 6px; }
.stApp {
  background: var(--heart-bg);
  color: var(--heart-text);
  font-family: var(--body-font);
  transition: background 0.7s ease, color 0.4s ease;
  filter: saturate(var(--vibe-saturation));
}
.theme-micro {
  margin-top: -10px;
  margin-bottom: 18px;
  font-style: italic;
  color: rgba(90,74,74,0.75);
}
.heart-hero {
  border-radius: 26px;
  padding: 32px;
  background: var(--heart-hero-gradient);
  box-shadow: var(--heart-hero-shadow);
  border: 1px solid var(--heart-hero-border);
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  transition: all 0.45s ease;
  font-family: var(--header-font);
}
.heart-hero h1 {
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.heart-hero p {
  margin: 0;
  font-size: 1.02rem;
  font-family: var(--body-font);
  color: rgba(90,74,74,0.85);
}
.heart-hero .hero-emoji {
  font-size: 2.6rem;
  background: rgba(255,255,255,0.7);
  border-radius: 18px;
  padding: 12px 16px;
  box-shadow: 0 10px 20px rgba(47,47,50,0.12);
}
.heart-card {
  background: var(--heart-card-bg);
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--heart-card-shadow);
  border: 1.5px solid var(--heart-card-border);
  margin-bottom: 18px;
}
.task-card {
  background: transparent;
  border-radius: 0;
  padding: 0;
  border: none;
  box-shadow: none;
  transition: none;
}
.task-cutout {
  border-radius: 0;
  clip-path: none;
  position: relative;
  overflow: visible;
  animation: none;
}
.task-cutout::before {
  display: none;
}
.task-cutout.completed {
  opacity: 0.92;
}
.task-cutout.completed::after {
  content: "✓";
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 1rem;
  color: rgba(31,35,39,0.85);
  animation: bow-pop 1.2s ease forwards;
}
.widget-card {
  background: var(--off-white);
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(47,47,50,0.08);
  box-shadow: 0 12px 26px rgba(47,47,50,0.08);
  margin-bottom: 16px;
  position: relative;
}
.widget-card h4 {
  margin-top: 0;
  margin-bottom: 6px;
  font-family: var(--header-font);
  font-size: 1.05rem;
}
.sparkle-burst {
  display: inline-block;
  animation: sparkle-pop 0.8s ease forwards;
  color: var(--highlight-gold);
  margin-left: 6px;
}
.slider-glow { box-shadow: none; }
.widget-shelf {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
  padding: 10px 0 16px;
}
.widget-shelf-item {
  min-width: 0;
}
.widget-card-wrapper {
  width: 100%;
}
.profile-card {
  background: rgba(255,255,255,0.85);
  border: 1px solid rgba(31,35,39,0.08);
  border-radius: 18px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.profile-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-family: var(--header-font);
  color: rgba(0,0,0,0.65);
}
.profile-meta h4 {
  font-size: 1rem;
  margin: 0;
  font-family: var(--header-font);
}
.profile-meta span {
  font-size: 0.85rem;
  color: rgba(0,0,0,0.55);
}
.widget-energy .widget-card {
  background-image: radial-gradient(circle at 10% 10%, rgba(247,199,217,0.3), transparent);
}
.widget-hydration .widget-card::after {
  content: "";
  position: absolute;
  top: -6px;
  left: 14px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(31,35,39,0.2);
}
.widget-screen .widget-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(247,199,217,0.45));
  box-shadow: inset 0 0 20px rgba(255,255,255,0.7);
}
.widget-reflect .widget-card::after {
  content: "";
  position: absolute;
  top: 8px;
  right: 12px;
  width: 14px;
  height: 2px;
  background: rgba(31,35,39,0.25);
}
.desk-header {
  text-align: center;
  margin: -10px auto 10px;
}
.desk-header h2 {
  font-family: var(--header-font);
  font-size: 2.4rem;
  margin-bottom: 0;
}
.desk-header p {
  margin-top: 2px;
  color: rgba(90,74,74,0.85);
  font-size: 1.1rem;
}
.mood-icons {
  display: flex;
  justify-content: space-between;
  font-size: 0.86rem;
  color: rgba(90,74,74,0.75);
  margin-bottom: 4px;
  padding: 0 4px;
}
.heart-illustration {
  width: 100%;
  border-radius: 24px;
  padding: 18px;
  margin-top: -8px;
  margin-bottom: 18px;
  border: 1px solid var(--heart-illustration-border);
  box-shadow: inset 0 0 30px rgb(255 255 255 / 60%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95rem;
  color: rgba(90,74,74,0.9);
  background: var(--heart-illustration-bg);
}
.illustration-home { background: linear-gradient(120deg, rgba(247,199,217,0.45), rgba(248,233,238,0.6)); }
.illustration-health { background: linear-gradient(120deg, rgba(248,233,238,0.45), rgba(255,253,252,0.7)); }
.illustration-shift { background: linear-gradient(120deg, rgba(169,195,168,0.35), rgba(247,199,217,0.45)); }
.stButton button {
  background: var(--heart-button-bg);
  color: var(--heart-button-text);
  border-radius: var(--heart-button-radius);
  border: none;
  padding: 0.55rem 1.4rem;
  font-weight: 600;
  box-shadow: var(--heart-button-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.3s ease;
}
.stButton button:hover {
  transform: translateY(-1px);
  background: var(--heart-button-hover);
}
div[data-testid="stMetricValue"] {
  font-weight: 700;
  color: var(--heart-text);
}
div[data-testid="stMetricLabel"] {
  font-size: 0.85rem;
  color: rgba(90,74,74,0.65);
}
div[data-testid="stCheckbox"] {
  position: relative;
}
div[data-testid="stCheckbox"] label {
  border-radius: 18px;
  padding: 6px 14px;
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(0,0,0,0.04);
  gap: 8px;
  transition: background 0.2s ease, border 0.2s ease, transform 0.2s ease;
}
div[data-testid="stCheckbox"] label:hover {
  border-color: var(--heart-checkbox);
  background: rgba(255,255,255,0.92);
  transform: translateY(-1px);
}
div[data-testid="stCheckbox"] div[role="checkbox"] {
  background: rgba(255,255,255,0.9);
  border: 1.5px solid rgba(90,74,74,0.2);
  border-radius: 12px;
  width: 22px;
  height: 22px;
  position: relative;
}
div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
  border-color: var(--cotton-candy);
  background: rgba(247,199,217,0.25);
  box-shadow: 0 0 10px rgba(247,199,217,0.6);
}
div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
  content: "❤";
  color: var(--cotton-candy);
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: sparkle-pop 0.6s ease forwards;
  font-size: 0.85rem;
}
div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::before {
  content: "";
  position: absolute;
  inset: -6px;
  border-radius: 16px;
  border: 1px solid rgba(252,228,168,0.65);
  animation: sparkle-pop 0.7s ease;
}
@keyframes sparkle-pop {
  0% { transform: scale(0.7); opacity: 0.2; }
  50% { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}
@keyframes slider-sparkle {
  0% { opacity: 0; transform: translateY(-4px); }
  50% { opacity: 1; }
  100% { opacity: 1; }
}
@keyframes gentle-wobble {
  0% { transform: rotate(-0.6deg); }
  50% { transform: rotate(0.6deg); }
  100% { transform: rotate(-0.6deg); }
}
@keyframes bow-pop {
  0% { transform: scale(0.5); opacity: 0; }
  60% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes cloud-bob {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-4px); }
  100% { transform: translateY(0px); }
}
</style>
"""

LAYOUT_CSS = """
<style>
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 1.6rem !important;
    }
    input[type="text"], textarea, .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 8px 10px;
    }
    .stCheckbox {
        margin-top: -6px;
    }
</style>
"""
THEME_PRESETS = {
    "coquette": {
        "label": "Notebook focus",
        "micro_message": "“Stay present with what matters right now.”",
        "css": """
        <style>
        :root {
          --heart-bg: linear-gradient(180deg, rgba(248,233,238,0.95) 0%, rgba(250,220,225,0.8) 45%, var(--cream-paper) 100%), url('https://www.transparenttextures.com/patterns/paper-fibers.png');
          --heart-hero-gradient: linear-gradient(125deg, rgba(247,199,217,0.95), rgba(255,253,252,0.9));
          --heart-hero-shadow: 0 30px 70px rgb(247 199 217 / 45%);
          --heart-card-shadow: 0 28px 55px rgb(247 199 217 / 32%);
          --heart-button-bg: linear-gradient(130deg, #F7C6D5, #FADCE1);
          --heart-button-hover: linear-gradient(130deg, #F5B1C8, #F7C7D9);
          --heart-button-radius: 28px 10px 28px 10px;
          --heart-button-shadow: 0 22px 48px rgb(247 155 194 / 45%);
          --heart-illustration-bg: rgba(250,220,225,0.65);
        }
        .stApp {
          background-size: cover, 420px;
          background-attachment: fixed;
        }
        .stButton button {
          border: 1px solid rgba(255,255,255,0.65);
        }
        .stButton button:after {
          content: "";
        }
        </style>
        """,
    },
    "cloud": {
        "label": "Cloud gradient",
        "micro_message": "“Pause, breathe, and reset your focus.”",
        "css": """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600&display=swap');
        :root {
          --heart-bg: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.95) 0%, rgba(233,229,255,0.9) 45%, rgba(214,244,255,0.95) 100%);
          --heart-text: #2C2C3A;
          --heart-body-font: 'DM Sans', sans-serif;
          --heart-display-font: 'Playfair Display', serif;
          --heart-hero-gradient: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(202, 214, 255, 0.85), rgba(214,244,255,0.75));
          --heart-hero-shadow: 0 30px 70px rgb(186 199 255 / 45%);
          --heart-hero-border: rgba(255,255,255,0.9);
          --heart-card-bg: rgba(255,255,255,0.85);
          --heart-card-border: rgba(186,199,255,0.45);
          --heart-card-shadow: 0 20px 55px rgb(173 196 255 / 40%);
          --heart-button-bg: linear-gradient(120deg, #E4E3FF, #D8F1FF);
          --heart-button-hover: linear-gradient(120deg, #D6D4FF, #C3EBFF);
          --heart-button-text: #2C2C3A;
          --heart-button-radius: 999px;
          --heart-button-shadow: 0 18px 40px rgb(171 196 255 / 45%);
          --heart-checkbox: #B6C8FF;
          --heart-illustration-bg: linear-gradient(135deg, rgba(228,227,255,0.5), rgba(216,241,255,0.65));
        }
        .heart-card {
          animation: cloud-bob 9s ease-in-out infinite;
        }
        .stButton button {
          border: 1px solid rgba(255,255,255,0.7);
        }
        .stButton button::after {
          content: "✨";
          font-size: 0.85rem;
          margin-left: 10px;
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
          content: "✨";
          color: #B6C8FF;
        }
        </style>
        """,
    },
    "matcha": {
        "label": "Matcha studio",
        "micro_message": "“Consistent steady work beats intensity.”",
        "css": """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        :root {
          --heart-bg: linear-gradient(180deg, #FAF5EE 0%, #FDFBF7 55%, #EEF3EC 100%);
          --heart-text: #2F2B25;
          --heart-body-font: 'Inter', sans-serif;
          --heart-display-font: 'Inter', sans-serif;
          --heart-hero-gradient: linear-gradient(120deg, rgba(253,251,247,0.95), rgba(201,219,198,0.8));
          --heart-hero-shadow: 0 25px 50px rgb(169 195 168 / 35%);
          --heart-hero-border: rgba(255,255,255,0.85);
          --heart-card-bg: rgba(253,251,247,0.95);
          --heart-card-border: rgba(169,195,168,0.8);
          --heart-card-shadow: 0 18px 45px rgb(169 195 168 / 35%);
          --heart-button-bg: #A9C3A8;
          --heart-button-hover: #97B894;
          --heart-button-text: #1F241F;
          --heart-button-radius: 16px;
          --heart-button-shadow: 0 15px 28px rgb(169 195 168 / 35%);
          --heart-checkbox: #8DAF8A;
          --heart-illustration-bg: linear-gradient(120deg, rgba(169,195,168,0.4), rgba(253,251,247,0.8));
        }
        .heart-card {
          border: 1px dashed rgba(131, 155, 129, 0.7);
        }
        div[data-testid="stCheckbox"] label {
          border-style: dashed;
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
          content: "🍃";
          color: #5f7d5c;
        }
        </style>
        """,
    },
    "calm": {
        "label": "Calm studio",
        "micro_message": "“Steady progress, no pressure.”",
        "css": """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Space+Grotesk:wght@500&display=swap');
        :root {
          --heart-bg: linear-gradient(180deg, #E9EEF3 0%, #F6F8FA 55%, #FFFFFF 100%);
          --heart-text: #1F2327;
          --heart-body-font: 'Inter', sans-serif;
          --heart-display-font: 'Space Grotesk', sans-serif;
          --heart-hero-gradient: linear-gradient(120deg, rgba(44,82,130,0.08), rgba(255,255,255,0.9));
          --heart-hero-shadow: 0 25px 55px rgb(45 64 89 / 20%);
          --heart-card-bg: rgba(255,255,255,0.95);
          --heart-card-border: rgba(44,82,130,0.12);
          --heart-card-shadow: 0 15px 35px rgb(31 35 39 / 12%);
          --heart-button-bg: #ffffff;
          --heart-button-hover: #e4e9ef;
          --heart-button-text: #1f2327;
          --heart-checkbox: #4D9DE0;
          --heart-illustration-bg: linear-gradient(120deg, rgba(77,157,224,0.08), rgba(255,255,255,0.85));
        }
        .heart-hero, .heart-card {
          border: 1px solid rgba(31,35,39,0.08);
        }
        .stButton button {
          border: 1px solid rgba(31,35,39,0.08);
        }
        div[data-testid="stCheckbox"] label::before {
          content: "";
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
          content: "◆";
          color: #4D9DE0;
        }
        </style>
        """,
    },
}

AUDIO_LIBRARY = {
    "Lo-fi Bloom": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_0d3c3c4ba0.mp3?filename=lofi-study-112191.mp3",
    "Soft Chimes": "https://cdn.pixabay.com/download/audio/2021/12/23/audio_58e8cd5e0f.mp3?filename=calm-meditation-110517.mp3",
    "Night Shift Waves": "https://cdn.pixabay.com/download/audio/2022/11/02/audio_29a25de403.mp3?filename=soft-ambient-124841.mp3",
}
SOUND_EFFECTS = {
    "page": "https://cdn.pixabay.com/download/audio/2022/03/14/audio_2905ddbfda.mp3?filename=book-page-flip-10555.mp3",
    "glitter": "https://cdn.pixabay.com/download/audio/2021/09/30/audio_9fda986996.mp3?filename=magic-wand-6296.mp3",
}

TASK_SIZES = ["Tiny", "Medium", "Big"]
ENERGY_TASK_LIBRARY = {
    "low": [
        "Sip warm water with lemon",
        "Put away one item",
        "Send a 'thinking of you' emoji",
    ],
    "medium": [
        "Reply to one email",
        "Prep a simple meal",
        "Walk outside for 10 minutes",
    ],
    "high": [
        "Deep clean a surface",
        "Study sprint (45 min)",
        "Move your body with music",
    ],
}
SELF_CARE_PROMPTS = [
    "Have you sipped water yet? 🍵",
    "Three slow breaths: in 4… hold… out…",
    "Shoulders down, jaw unclenched, gentle stretch?",
    "Snack time? Protein + something cozy.",
]
EMOTION_SUPPORT = {
    "Scary": "Break it into micro steps and phone a friend if you can.",
    "Overwhelming": "Body double or set a 5-minute starter timer.",
    "Confusing": "Write the next question you need answered first.",
    "Boring": "Pair it with a sweet playlist or a treat afterwards.",
}
AFFIRMATIONS = [
    "Let’s take this at your own pace today.",
    "That’s a meaningful step. Good work.",
    "Steady effort counts, even on quiet days.",
    "Thanks for checking in with yourself.",
]


def current_theme_key() -> str:
    key = st.session_state.get("theme_key", DEFAULT_THEME)
    return key if key in THEME_PRESETS else DEFAULT_THEME


def current_theme() -> Dict[str, str]:
    return THEME_PRESETS.get(current_theme_key(), THEME_PRESETS[DEFAULT_THEME])


def inject_theme_css() -> None:
    """Inject the base style plus the active preset so the UI recolors together."""
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    theme = current_theme()
    st.markdown(theme["css"], unsafe_allow_html=True)
    st.session_state["theme_micro"] = theme["micro_message"]


def theme_microcopy() -> str:
    return st.session_state.get("theme_micro", current_theme()["micro_message"])


def theme_micro_badge() -> None:
    st.markdown(f"<p class='theme-micro'>{theme_microcopy()}</p>", unsafe_allow_html=True)


def render_profile_card(user: Dict) -> None:
    name = user.get("name") or "Account"
    email = user.get("email", "")
    initials = "".join([part[0] for part in name.split() if part][:2]).upper() or (email[:2].upper() if email else "HF")
    st.sidebar.markdown(
        f"""
        <div class="profile-card">
            <div class="profile-avatar">{initials}</div>
            <div class="profile-meta">
                <h4>{name}</h4>
                <span>{email}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def persist_theme_choice(theme_key: str) -> None:
    if theme_key not in THEME_PRESETS:
        return
    user = st.session_state.get("user")
    if user:
        db.update_user_theme(user["id"], theme_key)
        st.session_state.user["theme"] = theme_key


def apply_vibe_saturation(energy: int) -> None:
    saturation = round(0.8 + (energy / 10) * 0.4, 2)
    st.markdown(f"<style>:root {{ --vibe-saturation: {saturation}; }}</style>", unsafe_allow_html=True)


def inject_soundscape() -> None:
    st.markdown(
        f"""
        <audio id="pageFlipSound" src="{SOUND_EFFECTS['page']}" preload="auto"></audio>
        <audio id="glitterSound" src="{SOUND_EFFECTS['glitter']}" preload="auto"></audio>
        <script>
        (function(){{
            const sliderLabel = "Mood slider";
            function bindSlider(){{
                const sliders = Array.from(document.querySelectorAll('div[data-testid="stSlider"] input'));
                const slider = sliders.find(el => el.getAttribute('aria-label') === sliderLabel);
                if (!slider) {{
                    setTimeout(bindSlider, 1000);
                    return;
                }}
                if (slider.dataset.bound) return;
                slider.dataset.bound = "true";
                slider.addEventListener('input', () => {{
                    const sparkle = document.getElementById('glitterSound');
                    if (sparkle) {{
                        sparkle.currentTime = 0;
                        sparkle.play().catch(() => {{}});
                    }}
                    slider.classList.add('slider-glow');
                    setTimeout(() => slider.classList.remove('slider-glow'), 800);
                }}, {{ passive: true }});
            }}
            bindSlider();
            document.addEventListener('change', (event) => {{
                const target = event.target;
                if (!target || target.type !== 'checkbox') return;
                if (!target.closest('.task-card')) return;
                const page = document.getElementById('pageFlipSound');
                if (page) {{
                    page.currentTime = 0;
                    page.play().catch(() => {{}});
                }}
                setTimeout(() => {{
                    const sparkle = document.getElementById('glitterSound');
                    if (sparkle) {{
                        sparkle.currentTime = 0;
                        sparkle.play().catch(() => {{}});
                    }}
                }}, 200);
            }}, true);
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def hero_section(title: str, subtitle: str, emoji: str) -> None:
    st.markdown(
        f"""
        <div class="heart-hero">
            <div class="hero-emoji">{emoji}</div>
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pastel_illustration(view_key: str) -> None:
    classes = {
        "home": "illustration-home",
        "health": "illustration-health",
        "shift": "illustration-shift",
    }
    captions = {
        "home": "Mood clouds shift — Heartline follows.",
        "health": "Admin tasks + compassion can coexist.",
        "shift": "Night lights, day naps, all valid rhythms.",
    }
    css_class = classes.get(view_key, "illustration-home")
    caption = captions.get(view_key, "Starry planner energy.")
    st.markdown(
        f"""
        <div class="heart-illustration {css_class}">
            <span>{caption}</span>
            <div class="illustration-dots"><span></span><span></span><span></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def heart_card_container():
    st.markdown('<div class="heart-card">', unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def task_card(variant: str = "standard", completed: bool = False):
    variant_class = ""
    if variant == "cutout":
        variant_class = " task-cutout"
        if completed:
            variant_class += " completed"
        st.markdown('<div class="task-card task-cutout">', unsafe_allow_html=True)
    else:
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def widget_card(title: str, emoji: str = "", wrapper_class: str = ""):
    heading = f"{emoji} {title}".strip()
    outer_class = f"widget-card-wrapper {wrapper_class}".strip()
    if wrapper_class:
        st.markdown(f'<div class="{outer_class}">', unsafe_allow_html=True)
    st.markdown('<div class="widget-card">', unsafe_allow_html=True)
    st.markdown(f"<h4>{heading}</h4>", unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)
    if wrapper_class:
        st.markdown("</div>", unsafe_allow_html=True)


def routine_prescription(mood: int, energy: int, schedule: str) -> Dict[str, List[str]]:
    tone = "slo-mo" if energy <= 3 else "steady" if energy <= 7 else "glow"
    base = {
        "body": ["Sip warm lemon water", "Stretch shoulders + jaw", "Take meds / vitamins"],
        "mind": ["Name one feeling (no fixing needed)", "Note 3 sensations in your body", "Play 5-min calming audio"],
        "logistics": ["Scan calendar for next 3 days", "Flag one admin task to delegate", "Check refill status"],
    }
    if tone == "slo-mo":
        base["body"] = ["Eat a nourishing meal", "Lay down with legs up", "Choose comfy clothes"]
        base["logistics"] = ["Mark day as Rest-ish", "Send quick status to team", "Move non-urgent tasks"]
    elif tone == "glow":
        base["body"].append("Walk outside for 10 min")
        base["logistics"].extend(["Plan one proactive appointment", "Prep call questions"])
    by_schedule = {
        "Day": "Anchor lunch + sunlight between 10a-2p",
        "Night": "Dim lights early, hydrate before shift",
        "Mixed": "Protect 4-hr core sleep block",
    }
    base["logistics"].insert(0, by_schedule.get(schedule, "Honor the rhythm you have"))
    return base


def appointment_reminders(appointments: List[Dict]) -> List[str]:
    templates = {"Dental Cleaning": 180, "Therapy": 7, "Annual Physical": 365}
    reminders = []
    now = datetime.now().date()
    for label, cadence in templates.items():
        last = max(
            [appt["date"].date() for appt in appointments if appt["category"] == label],
            default=None,
        )
        if not last:
            reminders.append(f"You haven't logged a {label.lower()} yet — want to pick a date?")
        else:
            due = last + timedelta(days=cadence)
            if due <= now:
                reminders.append(f"{label} is ready to be scheduled again. You're allowed to take your time.")
            else:
                reminders.append(f"Next {label.lower()} feels good around {due.strftime('%b %d')}. Soft nudge only ✨")
    return reminders


def generate_script(data: Dict) -> str:
    greeting = random.choice(["Hi there!", "Hello, thanks for taking my call.", "Good day!"])
    insurance_line = f"My insurance is {data['insurance']}" if data.get("insurance") else "I would like to confirm what insurance you accept."
    energy_note = "I'm feeling a bit anxious about calling, so thank you for patience." if data.get("call_support") else ""
    script = f"""{greeting} My name is {data['name'] or '_____'} and I'd like to schedule {data['need']}.
{insurance_line}
My availability is {data['availability'] or 'flexible'}.
Could you please let me know what information you need from me?
{data['notes']}
{energy_note}
Thank you so much for your help today!"""
    return script.strip()


def shift_plan(schedule: str, energy: int) -> Dict[str, List[str]]:
    plans = {
        "Day": {
            "sleep": ["Aim for 7 hrs between 11p-7a", "Light stretch before bed"],
            "meals": ["Protein breakfast", "12p daylight lunch", "6p grounded dinner"],
            "movement": ["Morning sunlight lap", "Afternoon posture reset"],
        },
        "Night": {
            "sleep": ["Core sleep 8a-1p", "1 hr wind-down pre-shift"],
            "meals": ["Fuel-up meal 5p", "Warm bowl at 1a", "Hydrate every break"],
            "movement": ["Pre-shift mobility", "Gentle decompression after"],
        },
        "Mixed": {
            "sleep": ["Protect a 4-hr anchor block", "20-min nap before late shift"],
            "meals": ["Set alarms for meals", "Carry stable snacks", "Magnesium-rich dinner"],
            "movement": ["Stack micro stretches", "2-min breath after calls"],
        },
    }
    focus = "Call it a bare-minimum day" if energy <= 3 else "Steady + kind pace" if energy <= 7 else "Try one energizing habit"
    plans[schedule]["focus"] = [focus]
    return plans[schedule]


def compassion_prompt(mood: int) -> str:
    if mood <= 3:
        return "Today is heavy. Permission to cancel and cocoon."
    return random.choice(
        [
            "It's okay to pause. Rest is part of the care plan.",
            "One small step still counts as momentum.",
            "You're doing brave admin work for Future You.",
            "Slow breaths, soft shoulders, no apologies needed.",
        ]
    )


def render_home():
    if "latest_energy" not in st.session_state:
        init_state()
    ensure_data_loaded()
    run_personal_check_prompt()
    hero_section(
        "Your day check-in <3",
        "tiny steps • gentle wins • soft progress",
        "🌸",
    )
    pastel_illustration("home")
    theme_micro_badge()

    st.markdown(
        """
        <div class="desk-header">
            <h2>Welcome back!!</h2>
            <p>How are you feeling today?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # --- Energy Check Slider ---
    st.subheader("Energy Check ✨")

    if "latest_energy" not in st.session_state:
        st.session_state.latest_energy = 6  # comfy default

    latest_energy = st.slider(
        "How’s your energy feeling right now?",
        min_value=1,
        max_value=10,
        value=st.session_state.latest_energy,
        step=1,
    )

    st.session_state.latest_energy = latest_energy
    apply_vibe_saturation(latest_energy)

    # mood text output
    if latest_energy <= 3:
        mood_label = "Let’s keep things calm and cozy 🌙"
    elif latest_energy <= 7:
        mood_label = "Balanced, focused, and steady 🪄"
    else:
        mood_label = "You’re glowing with momentum!! ⚡️"

    st.caption(mood_label)

    st.subheader("Daily reflection")
    mood_choice = st.radio(
        "How did today feel?",
        ["😣", "😕", "🙂", "😊", "🤩"],
        horizontal=True,
        label_visibility="collapsed",
        key="reflection_mood",
    )
    reflection_note = st.text_input(
        "One sentence to capture the day (optional)",
        placeholder="e.g., Felt steadier after lunch walk.",
        key="reflection_note",
    )
    if st.button("Save reflection", key="save_reflection"):
        st.session_state.daily_reflections.append(
            {
                "timestamp": datetime.now(),
                "mood": ["😣", "😕", "🙂", "😊", "🤩"].index(mood_choice) + 1,
                "emoji": mood_choice,
                "note": reflection_note.strip(),
            }
        )
        st.success("Reflection saved.")
    if st.session_state.daily_reflections:
        df_reflect = pd.DataFrame(
            [
                {"Time": entry["timestamp"], "Mood": entry["mood"]}
                for entry in st.session_state.daily_reflections
            ]
        )
        st.line_chart(df_reflect.set_index("Time"))

    st.divider()

    apply_energy_aura(latest_energy)
    with st.expander("mini self check-in 🫧", expanded=False):
        st.text_area(
            "What does your body need right now?",
            placeholder="water? music? stretch? warmth? a tiny snack? silence?",
            height=60,
            key="home_self_check",
        )


def apply_energy_aura(energy):
    # map energy → soft hue gradient
    if energy <= 3:
        color = "#A3B8FF"  # cool lavender / calming
    elif energy <= 7:
        color = "#9DD9C8"  # soft eucalyptus / balanced
    else:
        color = "#F7B3D2"  # warm rose / energized

    st.markdown(
        f"""
        <style>
            .stSlider > div > div > div {{
                background: linear-gradient(90deg, {color}33, {color});
                height: 8px;
                border-radius: 8px;
            }}
            .stSlider > div > div > div > div {{
                background-color: {color} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("mini self check-in 🫧", expanded=False):
        st.text_area(
            "What does your body need right now?",
            placeholder="water? music? stretch? warmth? a tiny snack? silence?",
            height=60,
            key="aura_self_check",
        )

    section = st.radio(
        "Desk view",
        HOME_SECTIONS,
        horizontal=True,
        index=HOME_SECTIONS.index(st.session_state.home_section),
        key="home_section_radio",
    )
    if section != st.session_state.home_section:
        st.session_state.home_section = section
        st.session_state.sidebar_home_links = section
    else:
        if "sidebar_home_links" in st.session_state and st.session_state.sidebar_home_links != section:
            st.session_state.sidebar_home_links = section

    if section == "Planner":
        st.markdown("### Today’s plan")
        plan_specs = [
            {
                "title": "PRIMARY FOCUS",
                "hint": "Something big and spectacular!!",
                "input_key": "primary_task",
                "checkbox_key": "primary_done",
                "placeholder": "Submit lab report draft",
            },
            {
                "title": "SUPPORT TASK",
                "hint": "Something great and amazing!!.",
                "input_key": "support_task",
                "checkbox_key": "support_done",
                "placeholder": "Email advisor / prep ingredients",
            },
            {
                "title": "QUICK ACTION",
                "hint": "Something small but mighty!!",
                "input_key": "quick_task",
                "checkbox_key": "quick_done",
                "placeholder": "Text back / reset nightstand",
            },
        ]
        for col, spec in zip(st.columns(3), plan_specs):
            with col:
                st.markdown(f"**{spec['title']}**")
                st.caption(spec["hint"])
                st.text_input(
                    "Task",
                    key=spec["input_key"],
                    label_visibility="collapsed",
                    placeholder=spec["placeholder"],
                )
                st.checkbox("mark done", key=spec["checkbox_key"])

        st.subheader("Add a task to the cloud ☁️")
        new_task = st.text_input("Task", placeholder="email Dr. Kim...")
        size = st.selectbox("Size", ["Small", "Medium", "Large"], index=1)
        if st.button("Save task ✨"):
            if new_task.strip():
                add_personal_task(new_task.strip(), size)
                st.success("Task tucked into the cloud.")
            else:
                st.error("Give the task a tiny name first.")

    elif section == "Widget shelf":
        st.markdown("### Widget shelf 🧺")
        st.markdown('<div class="widget-shelf">', unsafe_allow_html=True)
        with widget_card("Energy tracker", "💧"):
            history = st.session_state.check_ins[-7:]
            if history:
                df = pd.DataFrame(
                    {
                        "Mood": [entry["mood"] for entry in history],
                        "Energy": [entry["energy"] for entry in history],
                    },
                    index=[entry["timestamp"] for entry in history],
                )
                st.area_chart(df["Energy"])
            else:
                st.caption("Log a check-in to start spotting your energy waves.")
        with widget_card("Hydration buddy", "💧"):
            goal = st.session_state.hydration_goal
            current = st.session_state.hydration_oz
            st.progress(min(1.0, current / goal))
            st.caption(f"{current} oz / {goal} oz")
            sip_col, reset_col = st.columns(2)
            if sip_col.button("sip +8 oz", key="sip_plus"):
                st.session_state.hydration_oz = min(goal, current + 8)
            if reset_col.button("reset", key="sip_reset"):
                st.session_state.hydration_oz = 0
        with widget_card("Screen time bubble", "📱"):
            new_hours = st.slider(
                "Hours today",
                0.0,
                10.0,
                float(st.session_state.screen_time_hours),
                0.5,
                label_visibility="collapsed",
                key="bubble_hours",
            )
            if new_hours != st.session_state.screen_time_hours:
                st.session_state.screen_time_hours = new_hours
            bubble = "Low load" if new_hours <= 2 else "Balanced" if new_hours <= 5 else "Time to unplug soon"
            st.caption(f"{new_hours:.1f}h • {bubble}")
        with widget_card("Reflection notebook", "📝"):
            snippet = st.text_area(
                "whisper to future you",
                st.session_state.widget_reflection,
                height=90,
                label_visibility="collapsed",
            )
            if st.button("Save snippet", key="snippet_save"):
                st.session_state.widget_reflection = snippet.strip()
                if snippet.strip():
                    store_reflection(f"{snippet.strip()}  \n\n_(soft desk snippet)_")
                st.success("saved gently.")
        with widget_card("Focus timer", "⏱"):
            render_focus_timer()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        if needs_no_shame_screen():
            st.success("It’s okay if you needed time away. Start with what feels manageable today.")
            tiny, regular, challenge = st.columns(3)
            if tiny.button("tiny step", key="reentry_tiny"):
                mark_reentry_acknowledged()
                st.toast("Tiny is perfect. Maybe brush teeth or sip water.")
            if regular.button("regular step", key="reentry_regular"):
                mark_reentry_acknowledged()
                st.toast("Steady step logged. Maybe one admin thing or short walk.")
            if challenge.button("challenge step", key="reentry_challenge"):
                mark_reentry_acknowledged()
                st.toast("Spicy! Pick one bold move and we'll cheer for you.")

        tab_checkin, tab_care, tab_journal = st.tabs(
            ["Check-in", "Care & digest", "Journal"]
        )

        with tab_checkin:
            st.subheader("Energy check-in")
            with st.form("check_in_home"):
                mood = st.slider("Heart vibe", 0, 10, st.session_state.latest_energy)
                energy = st.slider("Body battery", 0, 10, st.session_state.latest_energy)
                schedule = st.select_slider("Current rhythm", options=SCHEDULES, value=st.session_state.selected_schedule)
                highlight = st.text_area(
                    "Tiny note for Future You",
                    placeholder="E.g. 'Neck sore after double' or 'Win: queued dentist call'",
                    height=90,
                )
                submitted = st.form_submit_button("Save check-in")
            if submitted:
                entry = {
                    "timestamp": datetime.now(),
                    "mood": mood,
                    "energy": energy,
                    "schedule": schedule,
                    "note": highlight,
                }
                store_check_in(entry)
                st.success("Logged with care.")

            current_energy = st.session_state.latest_energy
            routine = routine_prescription(mood if submitted else current_energy, current_energy, st.session_state.selected_schedule)
            st.markdown("#### Today’s gentle recipe")
            cols = st.columns(3)
            for idx, cat in enumerate(["body", "mind", "logistics"]):
                with cols[idx]:
                    st.markdown(f"**{cat.title()}**")
                    for item in routine[cat]:
                        st.write(f"• {item}")

            st.markdown("#### Energy-based suggestions")
            for idea in energy_task_suggestions(current_energy):
                st.write(f"• {idea}")

        if current_energy <= 3:
            st.warning("Keep today light—one simple task, one check-in, one pause is enough.")

            with st.expander("Why is this task heavy?", expanded=False):
                feeling = st.radio(
                    "Name the vibe (no fixing needed)",
                    list(EMOTION_SUPPORT.keys()),
                    horizontal=True,
                    key="feeling_radio_home",
                )
                st.info(emotion_support_message(feeling))

        with tab_care:
            st.subheader("Care & digest")
            digest_text = weekly_digest_summary(st.session_state.check_ins, st.session_state.symptoms)
            st.write(digest_text)
            digest_pdf = create_digest_pdf(digest_text)
            digest_png = create_digest_png(digest_text)
            st.download_button("Download digest PDF", data=digest_pdf, file_name="heartline-digest.pdf", mime="application/pdf")
            st.download_button("Download digest PNG", data=digest_png, file_name="heartline-digest.png", mime="image/png")
            with st.form("digest_delivery"):
                digest_email = st.text_input("Email digest to", placeholder="heartline.notes@gmail.com")
                send_digest = st.form_submit_button("Send digest (staged)")
            if send_digest:
                if digest_email:
                    st.success(f"We'll email {digest_email}. Attach the PDF/PNG above once your provider is wired up.")
                else:
                    st.error("Add an email first.")

            st.markdown("#### Self-care prompt")
            if st.button("Send me a gentle nudge", key="selfcare_btn"):
                st.success(random_self_care_prompt())
            elif st.session_state.self_care_prompt:
                st.success(st.session_state.self_care_prompt)
            st.markdown("#### Affirmation")
            if any(task.get("done") for task in st.session_state.tasks):
                reset_affirmation()
            st.info(current_affirmation())

        with tab_journal:
            st.subheader("Reflection journal")
            with st.form("reflection_form"):
                reflection = st.text_area("what’s on your heart today?", height=120)
                save_reflection = st.form_submit_button("Save reflection")
            if save_reflection and reflection.strip():
                closing = "thank you for trying. you are growing beautifully."
                store_reflection(f"{reflection.strip()}\n\n_{closing}_")
                st.success("Reflection saved with a soft affirmation.")
            if st.session_state.reflections:
                with st.expander("Recent reflections", expanded=False):
                    for entry in st.session_state.reflections[-3:][::-1]:
                        st.markdown(f"**{entry['timestamp'].strftime('%b %d %I:%M %p')}**\n\n{entry['text']}") 

        st.info(compassion_prompt(st.session_state.latest_energy))

    inject_soundscape()


def render_health_planner():
    ensure_data_loaded()
    hero_section(
        "Pastel health planner",
        "Appointments, scripts, and symptom notes live in one calm, blush-toned hub.",
        "📒",
    )
    pastel_illustration("health")
    theme_micro_badge()
    st.subheader("Gentle appointment hub")
    with st.form("appointment_form"):
        title = st.text_input("Appointment title", placeholder="Dentist, therapy, labs...")
        category = st.selectbox("Category", ["Dental Cleaning", "Therapy", "Annual Physical", "Other"], index=1)
        provider = st.text_input("Provider or office")
        date = st.date_input("Appointment date", value=datetime.now())
        notes = st.text_area("Notes / prep items")
        submitted = st.form_submit_button("Add to planner")
    if submitted and title:
        add_appointment(
            {
                "title": title,
                "category": category,
                "provider": provider,
                "date": datetime.combine(date, datetime.min.time()),
                "notes": notes,
            }
        )
        st.success("Added. Future you sends a hug.")
    if st.session_state.appointments:
        st.markdown("#### Upcoming")
        df = pd.DataFrame(
            [
                {
                    "Title": appt["title"],
                    "Category": appt["category"],
                    "Provider": appt["provider"],
                    "Date": appt["date"].strftime("%b %d, %Y"),
                    "Prep": appt["notes"],
                }
                for appt in sorted(st.session_state.appointments, key=lambda a: a["date"])
            ]
        )
        with heart_card_container():
            st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("No penalties if something moves. This planner flexes with you.")

    st.divider()
    st.subheader("Call script whisperer")
    with st.form("script_form"):
        name = st.text_input("Your name")
        need = st.text_input("What are you calling about?", placeholder="new patient appointment for pelvic pain...")
        insurance = st.text_input("Insurance details (optional)")
        availability = st.text_input("Preferred times")
        notes = st.text_area("Anything else to mention?", placeholder="I have referrals, I need translator, etc.")
        call_support = st.checkbox("Add anxiety-friendly reassurance line")
        generated = st.form_submit_button("Generate script")
    if generated:
        st.session_state.generated_script = generate_script(
            {
                "name": name,
                "need": need,
                "insurance": insurance,
                "availability": availability,
                "notes": notes,
                "call_support": call_support,
            }
        )
    if st.session_state.generated_script:
        st.text_area("Soft script", st.session_state.generated_script, height=200)
        st.caption("Copy, paste, or tweak. Take breaths between lines.")

    st.divider()
    st.subheader("Symptom & note tracker")
    with st.form("symptom_form"):
        symptom = st.text_input("Symptom / event")
        severity = st.slider("Intensity", 0, 10, 5)
        detail = st.text_area("Notes for your care team")
        symptom_date = st.date_input("Date", value=datetime.now())
        added = st.form_submit_button("Log entry")
    if added and symptom:
        add_symptom(
            {
                "symptom": symptom,
                "severity": severity,
                "notes": detail,
                "date": datetime.combine(symptom_date, datetime.min.time()),
            }
        )
        st.success("Saved. Proud of you for tracking the messy stuff.")
    if st.session_state.symptoms:
        symp_df = pd.DataFrame(
            [
                {
                    "Date": entry["date"].strftime("%b %d"),
                    "Symptom": entry["symptom"],
                    "Severity": entry["severity"],
                    "Notes": entry["notes"],
                }
                for entry in sorted(st.session_state.symptoms, key=lambda e: e["date"], reverse=True)
            ]
        )
        with heart_card_container():
            st.dataframe(symp_df, use_container_width=True, hide_index=True)
        pdf_bytes = create_symptom_pdf(st.session_state.symptoms)
        st.download_button("Download cute PDF for doctor", data=pdf_bytes, file_name="heartline-notes.pdf", mime="application/pdf")

    st.divider()
    st.markdown("#### Gentle reminders")
    for reminder in appointment_reminders(st.session_state.appointments):
        st.write(f"💌 {reminder}")


def render_shift_support():
    ensure_data_loaded()
    hero_section(
        "Shift rhythm cocoon",
        "Night owls, day shifters, and float teams all get a pastel plan that forgives everything.",
        "🌙",
    )
    pastel_illustration("shift")
    theme_micro_badge()
    schedule = st.select_slider("Current rhythm", options=SCHEDULES, value=st.session_state.selected_schedule)
    energy = st.slider("How charged do you feel?", 0, 10, st.session_state.latest_energy)
    st.session_state.selected_schedule = schedule
    st.session_state.latest_energy = energy
    plan = shift_plan(schedule, energy)
    cols = st.columns(3)
    for idx, key in enumerate(["sleep", "meals", "movement"]):
        with cols[idx]:
            st.markdown(f"**{key.title()}**")
            for item in plan[key]:
                st.write(f"• {item}")
    st.success(plan["focus"][0])
    st.markdown("### Hydration + alarms")
    st.write("Set gentle chimes every 90 minutes. Avoid harsh alarms; think lo-fi windchimes.")
    st.write("Pre-fill two bottles before the shift starts. Future You will be thrilled.")
    st.markdown("### Tiny doable wins")
    micro_wins = [
        "Drink a full glass of water",
        "Step outside and take 60 steady breaths",
        "Play one song that matches your mood",
        "Tidy one small surface",
        "Reply to one message you’ve delayed",
    ]
    if energy <= 3:
        micro_wins = [
            "Sit somewhere quiet and breathe for 60 seconds",
            "Drink water or warm tea",
            "Write down one thought to release it",
        ]
    for win in micro_wins:
        st.write(f"• {win}")
    st.info(compassion_prompt(energy))


def render_notification_settings() -> None:
    st.subheader("Reminder dispatch")
    st.caption("Register Expo push tokens or send yourself a soft email ping right from Heartline.")
    form_key = "device_form_sidebar" if st.sidebar else "device_form_main"
    with st.form(form_key):
        label = st.text_input("Device label", placeholder="My iPhone")
        token = st.text_input("Expo push token", placeholder="ExponentPushToken[xxxxxxx]")
        save_token = st.form_submit_button("Save device")
    if save_token and token:
        add_device(label, token)
        st.success("Device saved.")
    if st.session_state.devices:
        st.markdown("##### Registered devices")
        st.table({"Label": [d["label"] for d in st.session_state.devices], "Token": [d["token"] for d in st.session_state.devices]})

    st.markdown("##### Send gentle reminder")
    with st.form("send_notification"):
        channel = st.selectbox("Channel", ["In-app toast", "Expo push", "Email"])
        title = st.text_input("Title", value="Heartline reminder")
        body = st.text_area("Body", value="Hydrate + take three soft breaths.")
        device_labels = [f"{d['label']} ({d['token'][:8]}...)" for d in st.session_state.devices]
        target_token = None
        if channel == "Expo push" and device_labels:
            selected = st.selectbox("Device", device_labels)
            target_token = st.session_state.devices[device_labels.index(selected)]["token"]
        digest_email = st.text_input("Email (for email/backup)", placeholder="heartline.reminders@gmail.com")
        send_now = st.form_submit_button("Send now")
    if send_now:
        try:
            if channel == "In-app toast":
                st.toast(body)
            elif channel == "Expo push":
                if not target_token:
                    raise ValueError("Add an Expo token first.")
                notifications.send_expo_notification(target_token, title, body)
                st.success("Expo push dispatched.")
            else:
                notifications.send_email_notification(digest_email, title, body)
                st.success("Email sent.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Notification failed: {exc}")


def render_calendar_tools() -> None:
    st.subheader("Calendar & automation lab")
    st.caption("Export appointments as ICS or prep a Google sync request.")
    if st.session_state.appointments:
        ics_data = create_ics_calendar(st.session_state.appointments)
        st.download_button("Download calendar (.ics)", data=ics_data, file_name="heartline-appointments.ics", mime="text/calendar")
    else:
        st.info("Add an appointment to unlock calendar exports.")
    with st.form("google_sync_form"):
        google_email = st.text_input("Google Workspace / Gmail", placeholder="heartlineplanner@gmail.com")
        scopes = st.multiselect(
            "Requested permissions",
            ["Calendar events", "Reminders read/write", "Contacts (support circle)"],
            default=["Calendar events", "Reminders read/write"],
        )
        prep_sync = st.form_submit_button("Prep Google sync")
    if prep_sync:
        if google_email:
            st.success(
                f"Great! We'll request offline access for {google_email}. Add these scopes when you create OAuth credentials: {', '.join(scopes)}."
            )
        else:
            st.error("Add an email so we know which account to prep.")


def render_team_support_panel() -> None:
    st.subheader("Support circle sharing")
    st.caption("Loop in a trusted person or mentor without oversharing everything.")
    st.download_button(
        "Download shareable care packet (JSON)",
        data=build_share_packet(),
        file_name="heartline-share.json",
        mime="application/json",
    )
    with st.form("support_invite"):
        support_email = st.text_input("Support person email", placeholder="heartlinebuddy@gmail.com")
        scope = st.selectbox("What can they see?", ["Digest only", "Appointments + digest", "Everything in share packet"])
        invite = st.form_submit_button("Send support invite (staged)")
    if invite:
        if support_email:
            st.info(f"Invite drafted for {support_email}. Once email delivery is wired up they'll receive {scope.lower()} updates.")
        else:
            st.error("Add an email before sending.")


def render_audio_studio() -> None:
    st.markdown("### Ambient cue studio")
    track = st.selectbox("Choose a vibe", list(AUDIO_LIBRARY.keys()))
    st.audio(AUDIO_LIBRARY[track])
    st.caption("Tip: download the MP3 for offline shifts, then set it as a gentle alarm.")


def run_body_check_prompt() -> None:
    freq = st.session_state.get("body_check_frequency", "Never")
    if freq == "Never":
        return
    now = datetime.now()
    last = st.session_state.get("body_check_last_prompt")
    due = False
    if freq == "Once per day":
        due = not last or last.date() < now.date()
    elif freq == "Every 3 hours":
        due = not last or (now - last).total_seconds() >= 3 * 3600
    if not due:
        return
    prompt = random.choice(
        [
            "Have you eaten in the last few hours?",
            "Would a stretch or posture reset help right now?",
            "Could water or tea make the next block easier?",
        ]
    )
    st.info(prompt)
    st.session_state.body_check_last_prompt = now


def run_personal_check_prompt() -> None:
    """Backwards-compatible alias."""
    run_body_check_prompt()


def render_focus_timer() -> None:
    if "focus_timer_state" not in st.session_state:
        st.session_state.focus_timer_state = "ready"
        st.session_state.focus_timer_message = ""
    latest_energy = st.session_state.get("latest_energy", 6)
    if latest_energy <= 3:
        work, rest, preset_label = 10, 5, "Low energy • 10 / 5"
    elif latest_energy <= 7:
        work, rest, preset_label = 25, 5, "Steady focus • 25 / 5"
    else:
        work, rest, preset_label = 45, 15, "High focus • 45 / 15"
    st.caption(preset_label)
    state = st.session_state.focus_timer_state
    if state == "ready":
        if st.button(f"Start {work} min focus", key="focus_start"):
            st.session_state.focus_timer_state = "work"
            st.session_state.focus_timer_message = f"Working for {work} minutes..."
            st.toast(st.session_state.focus_timer_message)
    elif state == "work":
        if st.button("End work block", key="focus_end_work"):
            st.session_state.focus_timer_state = "break"
            st.session_state.focus_timer_message = f"Break for {rest} minutes."
            st.toast(st.session_state.focus_timer_message)
    elif state == "break":
        if st.button("End break", key="focus_end_break"):
            st.session_state.focus_timer_state = "ready"
            st.session_state.focus_timer_message = "Cycle complete. Start again whenever you're ready."
            st.toast(st.session_state.focus_timer_message)
    st.caption(st.session_state.focus_timer_message or "Ready when you are.")


def render_sidebar_tools() -> None:
    st.sidebar.subheader("Companion toolbox")
    with st.sidebar.expander("Quick links", expanded=True):
        quick_idx = HOME_SECTIONS.index(st.session_state.get("home_section", HOME_SECTIONS[0]))
        quick_choice = st.radio(
            "Jump to desk view",
            HOME_SECTIONS,
            index=quick_idx,
            key="sidebar_home_links",
        )
        if quick_choice != st.session_state.home_section:
            st.session_state.home_section = quick_choice
            st.session_state["home_section_radio"] = quick_choice
            st.experimental_rerun()
    with st.sidebar.expander("Personal check reminder", expanded=False):
        freq_options = ["Never", "Once per day", "Every 3 hours"]
        current_freq = st.session_state.get("body_check_frequency", "Never")
        freq_choice = st.radio(
            "Prompt me",
            freq_options,
            index=freq_options.index(current_freq) if current_freq in freq_options else 0,
            key="personal_check_freq_radio",
        )
        if freq_choice != current_freq:
            st.session_state.body_check_frequency = freq_choice
            st.session_state.body_check_last_prompt = None
    with st.sidebar.expander("Theme studio", expanded=True):
        st.caption("Choose the interface that fits today.")
        theme_ids = list(THEME_PRESETS.keys())
        current = current_theme_key()
        choice = st.radio(
            "Select a theme",
            theme_ids,
            index=theme_ids.index(current),
            format_func=lambda key: THEME_PRESETS[key]["label"],
            key="theme_picker_radio",
        )
        if choice != current:
            st.session_state.theme_key = choice
            st.session_state.theme_micro = THEME_PRESETS[choice]["micro_message"]
            st.session_state.theme_just_switched = True
            persist_theme_choice(choice)
        st.caption(theme_microcopy())
        if st.session_state.get("theme_just_switched"):
            st.success("your world has been redecorated ✨")
            st.session_state.theme_just_switched = False
    with st.sidebar.expander("Heartline vibe", expanded=False):
        st.markdown("**productivity that doesn’t hurt**")
        st.write("no guilt. no streak shame. no “do more.” just gentle structure, supportive routines, and tiny steps that feel doable.")
        st.markdown("**some days we’re ✨ on ✨ and some days… no.**")
        st.write("heartline adjusts tasks to your energy. low-energy mode suggests gentle, cozy wins so you still feel proud of yourself.")
        st.markdown("**you’re not “lazy.” tasks can just feel heavy.**")
        st.write("mark why something feels hard — scary, overwhelming, unclear — heartline helps you break it down with soft support.")
        st.markdown("**clarity brings calm**")
        st.write("we pick one big, one medium, one tiny — enough to grow without drowning.")
    with st.sidebar.expander("Reminder dispatch"):
        render_notification_settings()
    with st.sidebar.expander("Calendar & automations"):
        render_calendar_tools()
    with st.sidebar.expander("Support circle"):
        render_team_support_panel()
    with st.sidebar.expander("Ambient cue studio"):
        render_audio_studio()


def auth_panel() -> bool:
    logo_path = Path("png/Cloud Sticker.gif")
    if logo_path.exists():
        cols = st.sidebar.columns([1, 2, 1])
        with cols[1]:
            st.image(str(logo_path), width=120)
    st.sidebar.title(APP_NAME)
    auto_login_from_token()
    user = st.session_state.get("user")
    if user:
        render_profile_card(user)
        if st.sidebar.button("Sign out", use_container_width=True):
            clear_persistent_session()
            reset_user_state()
            st.experimental_rerun()
        return True

    st.sidebar.markdown("### Sign in")
    with st.sidebar.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Keep me signed in for 7 days", value=True)
        submitted = st.form_submit_button("Sign in")
    if submitted:
        email_normalized = email.strip().lower()
        record = db.get_user_by_email(email_normalized)
        if record and verify_password(password, record["password_hash"], record["password_salt"]):
            key = derive_encryption_key(password, record["encryption_salt"])
            theme_pref = record["theme_preference"] or DEFAULT_THEME
            if theme_pref not in THEME_PRESETS:
                theme_pref = DEFAULT_THEME
            st.session_state.user = {"id": record["id"], "email": record["email"], "name": record["full_name"], "theme": theme_pref}
            st.session_state.theme_key = theme_pref
            st.session_state.theme_micro = THEME_PRESETS[theme_pref]["micro_message"]
            st.session_state.crypto_key = key
            st.session_state.data_loaded = False
            if remember_me:
                clear_persistent_session()
                remember_user_session(record["id"], key)
            else:
                clear_persistent_session()
            load_user_data()
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid credentials.")

    st.sidebar.markdown("### Create account")
    with st.sidebar.form("register_form"):
        name = st.text_input("Full name", key="register_name")
        email_reg = st.text_input("Email", key="register_email")
        password_reg = st.text_input("Password", type="password", key="register_pass")
        confirm = st.text_input("Confirm password", type="password", key="register_confirm")
        remember_new = st.checkbox("Keep me signed in here", value=True)
        create = st.form_submit_button("Create account")
    if create:
        errors = []
        email_norm = email_reg.strip().lower()
        if not email_norm:
            errors.append("Email is required.")
        if password_reg != confirm:
            errors.append("Passwords do not match.")
        if len(password_reg) < 8:
            errors.append("Password must be at least 8 characters.")
        if db.get_user_by_email(email_norm):
            errors.append("Account already exists.")
        if errors:
            for err in errors:
                st.sidebar.error(err)
        else:
            password_hash, password_salt = create_password_record(password_reg)
            encryption_salt = base64.b64encode(os.urandom(16)).decode("utf-8")
            user_id = db.create_user(email_norm, name, password_hash, password_salt, encryption_salt)
            db.update_user_theme(user_id, DEFAULT_THEME)
            key = derive_encryption_key(password_reg, encryption_salt)
            st.session_state.user = {"id": user_id, "email": email_norm, "name": name, "theme": DEFAULT_THEME}
            st.session_state.theme_key = DEFAULT_THEME
            st.session_state.theme_micro = THEME_PRESETS[DEFAULT_THEME]["micro_message"]
            st.session_state.crypto_key = key
            st.session_state.data_loaded = False
            clear_persistent_session()
            if remember_new:
                remember_user_session(user_id, key)
            load_user_data()
            st.experimental_rerun()
    return False

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="☁️", layout="wide")
    init_state()
    inject_theme_css()
    st.markdown(LAYOUT_CSS, unsafe_allow_html=True)
    is_authed = auth_panel()
    if not is_authed:
        st.header("Welcome to Heartline Care Companion")
        st.write("Create an account or sign in from the sidebar to unlock your encrypted planner.")
        st.stop()

    view = st.sidebar.radio("Navigate", ["Home", "Health Planner", "Shift Support"], index=0)
    if view == "Home":
        render_home()
    elif view == "Health Planner":
        render_health_planner()
    else:
        render_shift_support()

    render_sidebar_tools()


def init_state() -> None:
    db.init_db()
defaults = {
        "check_ins": [],
        "appointments": [],
        "symptoms": [],
        "devices": [],
        "generated_script": "",
        "selected_schedule": "Day",
        "latest_energy": 5,
        "user": None,
        "crypto_key": None,
        "data_loaded": False,
        "persistent_token": None,
        "tasks": [],
        "reentry_acknowledged": False,
        "self_care_prompt": "",
        "last_affirmation": "",
        "reflections": [],
        "theme_key": DEFAULT_THEME,
        "theme_micro": THEME_PRESETS[DEFAULT_THEME]["micro_message"],
        "theme_just_switched": False,
        "hydration_oz": 0,
        "hydration_goal": 64,
        "screen_time_hours": 0,
        "widget_reflection": "",
        "home_section": HOME_SECTIONS[0],
        "daily_reflections": [],
        "body_check_frequency": "Never",
        "body_check_last_prompt": None,
    }
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_user_state() -> None:
    st.session_state.check_ins = []
    st.session_state.appointments = []
    st.session_state.symptoms = []
    st.session_state.devices = []
    st.session_state.generated_script = ""
    st.session_state.user = None
    st.session_state.crypto_key = None
    st.session_state.data_loaded = False
    st.session_state.persistent_token = None
    st.session_state.selected_schedule = "Day"
    st.session_state.latest_energy = 5
    st.session_state.tasks = []
    st.session_state.self_care_prompt = ""
    st.session_state.last_affirmation = ""
    st.session_state.hydration_oz = 0
    st.session_state.screen_time_hours = 0
    st.session_state.widget_reflection = ""
    st.session_state.theme_key = DEFAULT_THEME
    st.session_state.theme_micro = THEME_PRESETS[DEFAULT_THEME]["micro_message"]
    st.session_state.theme_just_switched = False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def derive_persistent_key(token: str) -> bytes:
    digest = hashlib.sha256(f"remember::{token}".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_query_param_token() -> str | None:
    try:
        params = st.query_params
    except AttributeError:
        params = st.experimental_get_query_params()
    value = params.get("session")
    if isinstance(value, list):
        return value[0]
    return value


def set_query_param_token(token: str | None) -> None:
    try:
        params = st.query_params
        if token:
            params["session"] = token
        elif "session" in params:
            del params["session"]
    except AttributeError:
        if token:
            st.experimental_set_query_params(session=token)
        else:
            st.experimental_set_query_params()


def ensure_data_loaded() -> None:
    if st.session_state.get("user") and not st.session_state.data_loaded:
        load_user_data()


def load_user_data() -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        return
    uid = user["id"]
    st.session_state.check_ins = [
        {
            "timestamp": datetime.fromisoformat(row["timestamp"]),
            "mood": row["mood"],
            "energy": row["energy"],
            "schedule": row["schedule"],
            "note": decrypt_text(row["note_encrypted"], key),
        }
        for row in db.fetch_check_ins(uid)
    ]
    st.session_state.appointments = [
        {
            "title": decrypt_text(row["title_encrypted"], key),
            "category": row["category"],
            "provider": decrypt_text(row["provider_encrypted"], key),
            "date": datetime.fromisoformat(row["date"]),
            "notes": decrypt_text(row["notes_encrypted"], key),
        }
        for row in db.fetch_appointments(uid)
    ]
    st.session_state.symptoms = [
        {
            "symptom": decrypt_text(row["symptom_encrypted"], key),
            "severity": row["severity"],
            "notes": decrypt_text(row["notes_encrypted"], key),
            "date": datetime.fromisoformat(row["date"]),
        }
        for row in db.fetch_symptoms(uid)
    ]
    st.session_state.devices = [
        {"id": row["id"], "label": row["label"] or "Unnamed device", "token": row["expo_token"]}
        for row in db.fetch_devices(uid)
    ]
    if st.session_state.check_ins:
        latest = st.session_state.check_ins[-1]
        st.session_state.selected_schedule = latest["schedule"]
        st.session_state.latest_energy = latest["energy"]
    theme_pref = st.session_state.user.get("theme") if st.session_state.user else None
    if theme_pref and theme_pref in THEME_PRESETS:
        st.session_state.theme_key = theme_pref
        st.session_state.theme_micro = THEME_PRESETS[theme_pref]["micro_message"]
    st.session_state.data_loaded = True


def store_check_in(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to log check-ins.")
        return
    payload = {
        "timestamp": entry["timestamp"].isoformat(),
        "mood": entry["mood"],
        "energy": entry["energy"],
        "schedule": entry["schedule"],
        "note_encrypted": encrypt_text(entry["note"], key),
    }
    db.insert_check_in(user["id"], payload)
    st.session_state.selected_schedule = entry["schedule"]
    st.session_state.latest_energy = entry["energy"]
    st.session_state.reentry_acknowledged = True
    st.session_state.data_loaded = False
    load_user_data()


def add_appointment(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to save appointments.")
        return
    payload = {
        "title_encrypted": encrypt_text(entry["title"], key),
        "category": entry["category"],
        "provider_encrypted": encrypt_text(entry["provider"], key),
        "date": entry["date"].isoformat(),
        "notes_encrypted": encrypt_text(entry["notes"], key),
    }
    db.insert_appointment(user["id"], payload)
    st.session_state.data_loaded = False
    load_user_data()


def add_symptom(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to track symptoms.")
        return
    payload = {
        "symptom_encrypted": encrypt_text(entry["symptom"], key),
        "severity": entry["severity"],
        "notes_encrypted": encrypt_text(entry["notes"], key),
        "date": entry["date"].isoformat(),
    }
    db.insert_symptom(user["id"], payload)
    st.session_state.data_loaded = False
    load_user_data()


def add_device(label: str, token: str) -> None:
    user = st.session_state.user
    if not user:
        return
    db.insert_device(user["id"], label, token)
    st.session_state.data_loaded = False
    load_user_data()


def create_symptom_pdf(entries: List[Dict]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Heartline Symptom & Note Log", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=12)
    if not entries:
        pdf.multi_cell(0, 8, "No entries recorded yet. Sending you gentle encouragement to check in when you're ready.")
    else:
        for item in entries:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, f"{item['date'].strftime('%b %d, %Y')} — {item['symptom']}", ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 6, f"Severity: {item['severity']}/10")
            note_text = item["notes"] or "Notes: (none)"
            if not note_text.startswith("Notes"):
                note_text = f"Notes: {note_text}"
            pdf.multi_cell(0, 6, note_text)
            pdf.ln(4)
    data = pdf.output(dest="S")
    return data.encode("latin1") if isinstance(data, str) else bytes(data)


def create_digest_pdf(digest_text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Heartline Weekly Digest", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, digest_text)
    data = pdf.output(dest="S")
    return data.encode("latin1") if isinstance(data, str) else bytes(data)


def create_digest_png(digest_text: str) -> bytes:
    width, height = 900, 400
    image = Image.new("RGB", (width, height), "#FDFBF7")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    draw.text((40, 30), "Heartline Weekly Digest", fill="#3A3A3A", font=font_title)
    draw.multiline_text((40, 90), digest_text, fill="#3A3A3A", font=font_body, spacing=8)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_ics_calendar(appointments: List[Dict]) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Heartline Care Companion//EN"]
    for appt in appointments:
        dt_start = appt["date"].strftime("%Y%m%dT090000")
        uid = f"{uuid.uuid4()}@heartline"
        summary = appt["title"] or appt["category"]
        description = appt["notes"] or "Gentle reminder from Heartline."
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{dt_start}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines).encode("utf-8")


def weekly_digest_summary(check_ins: List[Dict], symptoms: List[Dict]) -> str:
    window = datetime.now() - timedelta(days=7)
    recent_checks = [c for c in check_ins if c["timestamp"] >= window]
    if not recent_checks:
        return "No check-ins this week. Maybe jot one down so Future You has breadcrumbs."
    avg_mood = sum(c["mood"] for c in recent_checks) / len(recent_checks)
    avg_energy = sum(c["energy"] for c in recent_checks) / len(recent_checks)
    counts = {label: sum(1 for c in recent_checks if c["schedule"] == label) for label in SCHEDULES}
    dominant = max(counts, key=counts.get)
    recent_symptoms = [s for s in symptoms if s["date"] >= window]
    symptom_line = (
        f"You logged {len(recent_symptoms)} symptom notes — maybe bring them to your care team."
        if recent_symptoms
        else "No symptom logs this week. Rest is welcome."
    )
    return (
        f"Average mood {avg_mood:.1f}/10, energy {avg_energy:.1f}/10. "
        f"You lived mostly in {dominant.lower()} rhythm. {symptom_line}"
    )


def build_share_packet() -> bytes:
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "check_ins": st.session_state.check_ins,
        "appointments": [
            {**appt, "date": appt["date"].isoformat()} for appt in st.session_state.appointments
        ],
        "symptoms": [
            {**entry, "date": entry["date"].isoformat()} for entry in st.session_state.symptoms
        ],
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def energy_task_suggestions(energy: int) -> List[str]:
    if energy <= 3:
        return ENERGY_TASK_LIBRARY["low"]
    if energy <= 7:
        return ENERGY_TASK_LIBRARY["medium"]
    return ENERGY_TASK_LIBRARY["high"]


def latest_check_in_timestamp() -> datetime | None:
    if not st.session_state.check_ins:
        return None
    return st.session_state.check_ins[-1]["timestamp"]


def needs_no_shame_screen() -> bool:
    if st.session_state.reentry_acknowledged:
        return False
    last = latest_check_in_timestamp()
    if not last:
        return True
    return datetime.now() - last > timedelta(days=3)


def mark_reentry_acknowledged() -> None:
    st.session_state.reentry_acknowledged = True


def add_personal_task(title: str, size: str) -> None:
    st.session_state.tasks.append(
        {"id": str(uuid.uuid4()), "title": title, "size": size, "done": False, "created_at": datetime.utcnow().isoformat()}
    )


def toggle_task_completion(task_id: str, done: bool) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = done
            break


def today_three_tasks() -> List[Dict]:
    slots = {"Big": None, "Medium": None, "Tiny": None}
    for task in st.session_state.tasks:
        if not task["done"] and slots.get(task["size"]) is None:
            slots[task["size"]] = task
    guidance = {
        "Big": "Choose one bold move (project chunk, call, study sprint).",
        "Medium": "Handle an admin task or prep a meal.",
        "Tiny": "Send one message or tidy one corner.",
    }
    trio = []
    for size in ["Big", "Medium", "Tiny"]:
        if slots[size]:
            trio.append(slots[size])
        else:
            trio.append({"id": f"placeholder-{size}", "size": size, "title": guidance[size], "done": False})
    return trio


def random_self_care_prompt() -> str:
    prompt = random.choice(SELF_CARE_PROMPTS)
    st.session_state.self_care_prompt = prompt
    return prompt


def current_affirmation() -> str:
    if not st.session_state.last_affirmation:
        st.session_state.last_affirmation = random.choice(AFFIRMATIONS)
    return st.session_state.last_affirmation


def reset_affirmation() -> None:
    st.session_state.last_affirmation = random.choice(AFFIRMATIONS)


def emotion_support_message(feeling: str) -> str:
    return EMOTION_SUPPORT.get(feeling, "You get to do this at your own pace.")


def store_reflection(entry: str) -> None:
    st.session_state.reflections.append({"timestamp": datetime.now(), "text": entry})


def remember_user_session(user_id: int, crypto_key: bytes) -> None:
    token = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
    db_token = hash_token(token)
    fernet_key = derive_persistent_key(token)
    encrypted_key = encrypt_text(base64.b64encode(crypto_key).decode("utf-8"), fernet_key)
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    db.store_session_token(user_id, db_token, encrypted_key, expires_at)
    st.session_state.persistent_token = token
    set_query_param_token(token)


def clear_persistent_session() -> None:
    token = st.session_state.get("persistent_token") or get_query_param_token()
    if token:
        db.delete_session_token(hash_token(token))
    st.session_state.persistent_token = None
    set_query_param_token(None)


def auto_login_from_token() -> None:
    if st.session_state.get("user"):
        return
    token = st.session_state.get("persistent_token") or get_query_param_token()
    if not token:
        return
    record = db.fetch_session_token(hash_token(token))
    if not record:
        set_query_param_token(None)
        return
    if datetime.fromisoformat(record["expires_at"]) < datetime.utcnow():
        db.delete_session_token(record["token_hash"])
        set_query_param_token(None)
        return
    user_row = db.get_user_by_id(record["user_id"])
    if not user_row:
        clear_persistent_session()
        return
    try:
        key_string = decrypt_text(record["encrypted_key"], derive_persistent_key(token))
        crypto_key = base64.b64decode(key_string.encode("utf-8"))
    except Exception:
        clear_persistent_session()
        return
    theme_pref = user_row["theme_preference"] or DEFAULT_THEME
    if theme_pref not in THEME_PRESETS:
        theme_pref = DEFAULT_THEME
    st.session_state.user = {"id": user_row["id"], "email": user_row["email"], "name": user_row["full_name"], "theme": theme_pref}
    st.session_state.theme_key = theme_pref
    st.session_state.theme_micro = THEME_PRESETS[theme_pref]["micro_message"]
    st.session_state.crypto_key = crypto_key
    st.session_state.persistent_token = token
    st.session_state.data_loaded = False
    load_user_data()


def set_query_param_token(token: str | None) -> None:
    try:
        params = st.query_params
        if token:
            params["session"] = token
        elif "session" in params:
            del params["session"]
    except AttributeError:
        if token:
            st.experimental_set_query_params(session=token)
        else:
            st.experimental_set_query_params()

if __name__ == "__main__":
    main()
