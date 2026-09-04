"""
THEME NSIA — Édition Prestige
Design ultra-premium : Bleu nuit profond, or, verre dépoli, animations fluides.
"""

import base64
from datetime import datetime
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

LOGO_EXTENSIONS = {
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": None,
}


# ============================================================
# PALETTE NSIA — ÉDITION PRESTIGE
# ============================================================

NAVY_DEEP = "#0A1628"
NAVY_DARK = "#0F1F3A"
NAVY_MID = "#162A50"
NAVY_BG = "#F0F3F8"

GOLD = "#D4AF37"
GOLD_LIGHT = "#F5E6B8"
GOLD_GLOW = "rgba(212, 175, 55, 0.25)"

SILVER = "#C0C0C0"
SILVER_LIGHT = "#E8E8E8"

WHITE = "#FFFFFF"
TEXT = "#0A1628"
TEXT_SECONDARY = "#4A5A7A"
TEXT_MUTED = "#7A8AA8"
CARD_BG = "rgba(255, 255, 255, 0.92)"
CARD_BORDER = "rgba(255, 255, 255, 0.18)"

BLUE_ACCENT = "#3B82F6"
GREEN_ACCENT = "#22C55E"
AMBER_ACCENT = "#F59E0B"
ROSE_ACCENT = "#EF4444"
PURPLE_ACCENT = "#8B5CF6"

GLASS_BG = "rgba(255, 255, 255, 0.12)"
GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
GLASS_SHADOW = "0 8px 32px rgba(0, 0, 0, 0.25)"


# ============================================================
# EMBLÈME DE SECOURS — Version Or
# ============================================================

_PLACEHOLDER_EMBLEM_SVG = """
<svg width="{size}" height="{size}" viewBox="0 0 100 100"
xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#D4AF37"/>
            <stop offset="100%" style="stop-color:#F5E6B8"/>
        </linearGradient>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#0F1F3A"/>
            <stop offset="100%" style="stop-color:#0A1628"/>
        </linearGradient>
    </defs>
    <circle cx="50" cy="50" r="46" fill="url(#bgGrad)" stroke="url(#goldGrad)" stroke-width="2.5"/>
    <path d="M50 18 L62 40 L86 44 L69 60 L73 84 L50 72 L27 84 L31 60 L14 44 L38 40 Z" 
          fill="url(#goldGrad)" opacity="0.9"/>
    <text x="50" y="68" text-anchor="middle" font-family="Inter, Arial" font-size="16" 
          font-weight="900" fill="#0A1628">NSIA</text>
</svg>
"""


# ============================================================
# LOGO
# ============================================================

def _find_logo_file():
    if not ASSETS_DIR.exists():
        return None
    fichiers = [p for p in ASSETS_DIR.iterdir() if p.suffix.lower() in LOGO_EXTENSIONS]
    if not fichiers:
        return None
    priorite = ["logo_nsia", "logo-nsia", "nsia_logo", "logo"]
    for mot in priorite:
        for fichier in fichiers:
            if mot in fichier.stem.lower():
                return fichier
    return fichiers[0]


def _logo_html(size: int = 52) -> str:
    logo_file = _find_logo_file()
    if logo_file is None:
        return _PLACEHOLDER_EMBLEM_SVG.format(size=size)
    if logo_file.suffix.lower() == ".svg":
        try:
            return logo_file.read_text(encoding="utf-8")
        except Exception:
            return _PLACEHOLDER_EMBLEM_SVG.format(size=size)
    try:
        b64 = base64.b64encode(logo_file.read_bytes()).decode()
        mime = LOGO_EXTENSIONS.get(logo_file.suffix.lower(), "image/png")
        return f'<img src="data:{mime};base64,{b64}" style="height:{size}px;width:auto;object-fit:contain;display:block;">'
    except Exception:
        return _PLACEHOLDER_EMBLEM_SVG.format(size=size)


# ============================================================
# ASSETS NOMMÉS — Logo NSIA Vie Assurance (sidebar),
# bannière NSIA Etudes (accueil), etc.
# ============================================================
# Contrairement à _logo_html() (un seul logo générique), asset_html()
# retrouve un visuel précis par mot-clé dans son nom de fichier.
# Placer les fichiers dans assets/, ex. "Logo-NSIA-Vie-Assurances.webp",
# "Logo-NSIA-Etude.png" : le mot-clé "vie-assurance" / "etude" suffit
# à les retrouver, peu importe l'extension (png, webp, jpg).

def _find_asset_by_keywords(keywords: list[str]):
    if not ASSETS_DIR.exists():
        return None
    fichiers = [p for p in ASSETS_DIR.iterdir() if p.suffix.lower() in LOGO_EXTENSIONS]
    if not fichiers:
        return None
    for mot in keywords:
        mot_low = mot.lower()
        for fichier in fichiers:
            if mot_low in fichier.stem.lower().replace("_", "-").replace(" ", "-"):
                return fichier
    return None


def asset_html(keywords: list[str], size: int = 52, style: str | None = None, fallback: str = "") -> str:
    """
    Retourne le HTML <img> (base64) du premier fichier de assets/ dont le nom
    contient l'un des mots-clés donnés. Retourne `fallback` si rien n'est trouvé
    (aucun placeholder forcé : contrairement au logo générique, une bannière
    absente ne doit pas afficher un emblème de secours à sa place).
    """
    fichier = _find_asset_by_keywords(keywords)

    if fichier is None:
        return fallback

    if fichier.suffix.lower() == ".svg":
        try:
            return fichier.read_text(encoding="utf-8")
        except Exception:
            return fallback

    try:
        b64 = base64.b64encode(fichier.read_bytes()).decode()
        mime = LOGO_EXTENSIONS.get(fichier.suffix.lower(), "image/png")
        css = style or f"height:{size}px;width:auto;object-fit:contain;display:block;"
        return f'<img src="data:{mime};base64,{b64}" style="{css}">'
    except Exception:
        return fallback


# ============================================================
# HTML
# ============================================================

def render_html(html: str):
    cleaned = "\n".join(line.strip() for line in html.strip("\n").split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)


# ============================================================
# CSS GLOBAL
# ============================================================

def inject_css():
    st.markdown(
        f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

.stApp {{
    background:
        radial-gradient(
            ellipse at 20% 20%,
            #1A2A5A 0%,
            #0F1F3A 40%,
            #0A1628 100%
        );
}}

.stApp::before {{
    content: "";
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background:
        radial-gradient(
            circle at 70% 30%,
            rgba(212, 175, 55, 0.03) 0%,
            transparent 60%
        );
    pointer-events: none;
    z-index: 0;
}}

.block-container {{
    max-width: 1500px;
    padding-top: 1.8rem;
    padding-bottom: 2.5rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    position: relative;
    z-index: 1;
}}

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #FFFFFF;
}}

h1, h2, h3, h4, h5, h6 {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}}

p, label, span, .stMarkdown {{
    color: rgba(255, 255, 255, 0.85);
}}

.stCaption, [data-testid="stCaptionContainer"] {{
    color: rgba(255, 255, 255, 0.5) !important;
    font-weight: 400 !important;
    letter-spacing: 0.03em;
}}

section[data-testid="stSidebar"] {{
    background:
        linear-gradient(
            180deg,
            rgba(10, 22, 40, 0.95) 0%,
            rgba(15, 31, 58, 0.92) 60%,
            rgba(10, 22, 40, 0.95) 100%
        );
    backdrop-filter: blur(20px) saturate(1.2);
    -webkit-backdrop-filter: blur(20px) saturate(1.2);
    border-right: 1px solid rgba(212, 175, 55, 0.15);
    box-shadow: 4px 0 40px rgba(0, 0, 0, 0.4);
    min-width: 280px;
}}

section[data-testid="stSidebar"] > div {{
    padding-top: 1.5rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
}}

section[data-testid="stSidebar"] * {{
    color: rgba(255, 255, 255, 0.9) !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px);
    transition: all 0.3s ease;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {{
    border-color: {GOLD} !important;
    box-shadow: 0 0 20px {GOLD_GLOW};
}}

section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px dashed rgba(212, 175, 55, 0.3);
    border-radius: 14px;
    backdrop-filter: blur(8px);
    transition: all 0.4s ease;
}}

section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {GOLD};
    background: rgba(212, 175, 55, 0.05);
    box-shadow: 0 0 30px {GOLD_GLOW};
}}

.nsia-header {{
    position: relative;
    display: grid;
    grid-template-columns: 1fr 1.8fr 1fr;
    align-items: center;
    min-height: 100px;
    padding: 1.2rem 2rem;
    margin-bottom: 1.8rem;
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(16px) saturate(1.3);
    -webkit-backdrop-filter: blur(16px) saturate(1.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 24px;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
    overflow: hidden;
}}

.nsia-header::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, {GOLD}, #F5E6B8, {GOLD});
    box-shadow: 0 0 30px {GOLD_GLOW};
}}

.nsia-header::after {{
    content: "";
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse at 70% 30%, rgba(212, 175, 55, 0.03), transparent 70%);
    pointer-events: none;
}}

.nsia-brand {{
    display: flex;
    align-items: center;
    gap: 1rem;
    z-index: 1;
}}

.nsia-logo {{
    font-size: 1.5rem;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1.1;
    letter-spacing: -0.02em;
}}

.nsia-logo .accent {{
    background: linear-gradient(135deg, {GOLD}, #F5E6B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.nsia-logo-sub {{
    margin-top: 0.2rem;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    font-weight: 600;
}}

.nsia-title {{
    margin: 0;
    text-align: center;
    font-size: 1.65rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    z-index: 1;
}}

.nsia-title .highlight {{
    background: linear-gradient(135deg, {GOLD}, #F5E6B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.nsia-context {{
    margin: 0.3rem 0 0;
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.82rem;
    font-weight: 400;
    z-index: 1;
}}

.nsia-datetime {{
    text-align: right;
    font-size: 0.72rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.35);
    font-weight: 300;
    z-index: 1;
}}

.kpi-card {{
    position: relative;
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px) saturate(1.4);
    -webkit-backdrop-filter: blur(12px) saturate(1.4);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 1.2rem 1.4rem;
    min-height: 155px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    cursor: default;
}}

.kpi-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, {GOLD}, #F5E6B8, {GOLD});
    opacity: 0.6;
    transition: opacity 0.4s ease;
}}

.kpi-card:hover {{
    transform: translateY(-4px);
    background: rgba(255, 255, 255, 0.07);
    border-color: rgba(212, 175, 55, 0.2);
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.35), 0 0 40px {GOLD_GLOW};
}}

.kpi-card:hover::before {{
    opacity: 1;
}}

.kpi-icon {{
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: rgba(212, 175, 55, 0.12);
    font-size: 1.1rem;
    margin-bottom: 0.6rem;
    border: 1px solid rgba(212, 175, 55, 0.08);
}}

.kpi-label {{
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    font-weight: 700;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    line-height: 1.3;
}}

.kpi-value {{
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 900;
    margin-top: 0.35rem;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #FFFFFF, rgba(255,255,255,0.7));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.kpi-sub {{
    margin-top: 0.4rem;
    font-size: 0.68rem;
    color: rgba(255, 255, 255, 0.35);
    font-weight: 400;
}}

.v-good {{
    background: linear-gradient(135deg, {GREEN_ACCENT}, #16A34A) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}

.v-warn {{
    background: linear-gradient(135deg, {AMBER_ACCENT}, #D97706) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}

.v-bad {{
    background: linear-gradient(135deg, {ROSE_ACCENT}, #DC2626) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}

.v-neutral {{
    color: rgba(255, 255, 255, 0.8) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.8) !important;
}}

.section-title {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 2rem 0 1.2rem;
    padding: 0.8rem 1.2rem;
    background: rgba(255, 255, 255, 0.03);
    border-left: 4px solid {GOLD};
    border-radius: 0 14px 14px 0;
    color: #FFFFFF;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    backdrop-filter: blur(8px);
}}

.section-title::after {{
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.06), transparent);
}}

.profile-card {{
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
}}

.profile-card:hover {{
    border-color: rgba(212, 175, 55, 0.15);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}}

.nsia-panel {{
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 1.4rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
}}

div[data-testid="stMetric"] {{
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}}

div[data-testid="stMetricLabel"] {{
    color: rgba(255, 255, 255, 0.4) !important;
    font-weight: 600 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

div[data-testid="stMetricValue"] {{
    color: #FFFFFF !important;
    font-weight: 900 !important;
    font-size: 1.6rem !important;
}}

div[data-testid="stMetricDelta"] {{
    font-weight: 700;
}}

div[data-baseweb="select"] > div {{
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    min-height: 44px;
    transition: all 0.3s ease;
}}

div[data-baseweb="select"] > div:hover {{
    border-color: {GOLD} !important;
    box-shadow: 0 0 20px {GOLD_GLOW};
}}

div[data-baseweb="input"] > div {{
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
}}

.stButton > button {{
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.04);
    color: #FFFFFF;
    font-weight: 700;
    min-height: 44px;
    backdrop-filter: blur(8px);
    transition: all 0.3s ease;
}}

.stButton > button:hover {{
    border-color: {GOLD};
    background: rgba(212, 175, 55, 0.08);
    box-shadow: 0 0 30px {GOLD_GLOW};
    transform: translateY(-2px);
}}

div[data-testid="stAlert"] {{
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 14px !important;
    color: #FFFFFF !important;
}}

div[data-testid="stExpander"] {{
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    overflow: hidden;
}}

div[data-testid="stDataFrame"] {{
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}}

.chat-bubble-user {{
    background: rgba(212, 175, 55, 0.12);
    border: 1px solid rgba(212, 175, 55, 0.1);
    border-radius: 16px 16px 4px 16px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: #FFFFFF;
    backdrop-filter: blur(8px);
}}

.chat-bubble-bot {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px 16px 16px 4px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(8px);
}}

.nsia-footer-brand {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 1.2rem 2rem;
    margin-top: 2.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}}

.nsia-footer-brand .nsia-logo {{
    color: #FFFFFF;
    font-size: 1.4rem;
}}

.nsia-tagline-band {{
    display: flex;
    justify-content: space-around;
    gap: 1rem;
    margin-top: 0.8rem;
    padding: 0.8rem 1.2rem;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.04);
    color: rgba(255, 255, 255, 0.4);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

div[data-testid="stRadio"] > div[role="radiogroup"] {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 0.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    margin-bottom: 1.4rem;
}}

div[data-testid="stRadio"] label {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 0.5rem 1.1rem !important;
    margin: 0 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}}

div[data-testid="stRadio"] label:hover {{
    background: rgba(255, 255, 255, 0.04);
}}

div[data-testid="stRadio"] label p {{
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    color: rgba(255, 255, 255, 0.5) !important;
    margin: 0 !important;
    transition: color 0.3s ease;
}}

div[data-testid="stRadio"] label:has(input:checked) {{
    background: linear-gradient(135deg, {GOLD}, #B8960F);
    border-color: {GOLD};
    box-shadow: 0 4px 20px {GOLD_GLOW};
}}

div[data-testid="stRadio"] label:has(input:checked) p {{
    color: #0A1628 !important;
    font-weight: 800 !important;
}}

div[data-testid="stRadio"] label [data-baseweb="radio"] > div:first-child {{
    width: 0;
    height: 0;
    margin: 0;
    opacity: 0;
}}

@media (max-width: 1100px) {{
    .block-container {{
        padding-left: 1.2rem;
        padding-right: 1.2rem;
    }}
    .nsia-header {{
        grid-template-columns: 1fr;
        gap: 0.8rem;
        text-align: center;
    }}
    .nsia-brand {{ justify-content: center; }}
    .nsia-datetime {{ text-align: center; }}
}}

@media (max-width: 700px) {{
    .block-container {{
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }}
    .kpi-card {{
        min-height: 130px;
        padding: 1rem;
    }}
    .kpi-value {{
        font-size: 1.6rem;
    }}
    .nsia-tagline-band {{
        flex-direction: column;
        text-align: center;
        gap: 0.5rem;
    }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# KPI CARD
# ============================================================

def kpi_card(
    icon: str,
    label: str,
    value: str,
    sub: str = "",
    status: str = "neutral",
):
    color_class = {
        "good": "v-good",
        "warn": "v-warn",
        "bad": "v-bad",
        "neutral": "v-neutral",
    }.get(status, "v-neutral")

    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {color_class}">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """
    )


# ============================================================
# SECTION
# ============================================================

def section(title: str):
    render_html(f'<div class="section-title">{title}</div>')


# ============================================================
# STATUT
# ============================================================

def status_for(value: float, objectif: float) -> str:
    if value >= objectif:
        return "good"
    if value >= objectif - 0.05:
        return "warn"
    return "bad"


# ============================================================
# PAGE HEADER
# ============================================================

def page_header(page_name: str, contexte: str = ""):
    now = datetime.now()
    date_text = now.strftime("%d/%m/%Y")
    heure_text = now.strftime("%H:%M")
    contexte_html = f'<div class="nsia-context">{contexte}</div>' if contexte else ""

    render_html(
        f"""
        <div class="nsia-header">
            <div class="nsia-brand">
                {_logo_html(52)}
                <div>
                    <div class="nsia-logo">
                        NSIA <span class="accent">ASSURANCE</span>
                    </div>
                    <div class="nsia-logo-sub">EXPÉRIENCE CLIENT</div>
                </div>
            </div>
            <div>
                <div class="nsia-title">{page_name}</div>
                {contexte_html}
            </div>
            <div class="nsia-datetime">
                <span>📅</span> {date_text}<br>
                <span>🕐</span> {heure_text}
            </div>
        </div>
        """
    )


# ============================================================
# FOOTER
# ============================================================

def footer_brand():
    render_html(
        f"""
        <div class="nsia-footer-brand">
            {_logo_html(48)}
            <div class="nsia-logo">NSIA <span class="accent">ASSURANCE</span></div>
        </div>
        <div class="nsia-tagline-band">
            <div>🌍 INNOVER POUR VOUS</div>
            <div>🤝 VOUS ACCOMPAGNER</div>
            <div>🛡️ GARANTIR L'AVENIR</div>
        </div>
        """
    )