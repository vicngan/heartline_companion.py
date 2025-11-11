import streamlit as st

DEFAULT_THEME = "coquette"
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
          content: "";
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
        "micro_message": "“Consistent slow growth >>> burnout.”",
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
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
          --heart-button-text: #1f1f21;
          --heart-button-radius: 16px;
          --heart-button-shadow: 0 12px 24px rgba(31,35,39,0.12);
          --heart-checkbox: #4D9DE0;
          --heart-illustration-bg: linear-gradient(120deg, rgba(77,157,224,0.08), rgba(255,255,255,0.85));
        }
        .heart-card,
        .heart-hero {
          border: 1px solid rgba(31,35,39,0.08);
        }
        .stButton button {
          border: 1px solid rgba(31,35,39,0.08);
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
          content: "◆";
          color: #4D9DE0;
        }
        </style>
        """,
    },
}


def current_theme_key() -> str:
    key = st.session_state.get("theme_key", DEFAULT_THEME)
    return key if key in THEME_PRESETS else DEFAULT_THEME


def current_theme() -> dict:
    return THEME_PRESETS.get(current_theme_key(), THEME_PRESETS[DEFAULT_THEME])


def inject_theme_css() -> None:
    st.markdown(current_theme()["css"], unsafe_allow_html=True)


def theme_microcopy() -> str:
    return st.session_state.get("theme_micro", current_theme()["micro_message"])


def theme_micro_badge() -> None:
    st.markdown(f"<p class='theme-micro'>{theme_microcopy()}</p>", unsafe_allow_html=True)


def persist_theme_choice(theme_key: str) -> None:
    if theme_key not in THEME_PRESETS:
        return
    user = st.session_state.get("user")
    if user:
        db.update_user_theme(user["id"], theme_key)
        st.session_state.user["theme"] = theme_key

