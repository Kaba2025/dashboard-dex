import sys
from pathlib import Path

import streamlit as st


# ============================================================
# CHEMINS
# ============================================================

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
TABS = SRC / "tabs"

sys.path.append(str(SRC))
sys.path.append(str(TABS))


# ============================================================
# IMPORTS
# ============================================================

from ingestion_dex import (
    save_uploaded_dex,
    validate_workbook,
    get_dex_data,
    quality_report as dex_quality_report,
)

from theme import (
    inject_css,
    footer_brand,
    asset_html,
)

from point_global import render_point_global

import accueil
import digital
import physique
import satisfaction
import reclamation
import messagerie
import callcenter
import desherence


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NSIA — Expérience Client",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ============================================================
# STYLE APP
# ============================================================

st.markdown(
    """
<style>

.app-sidebar-title {
    text-align: center;
    padding: 0.5rem 0 1.2rem 0;
}

.app-sidebar-title .brand {
    font-size: 1.45rem;
    font-weight: 900;
    letter-spacing: 0.02em;
    color: #FFFFFF;
}

.app-sidebar-title .brand span {
    background: linear-gradient(135deg, #D4AF37, #F5E6B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.app-sidebar-title .subtitle {
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.3);
    margin-top: 0.2rem;
    font-weight: 600;
}

.sidebar-section {
    margin-top: 0.8rem;
    margin-bottom: 0.45rem;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.25);
}

.sidebar-status {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin: 0.3rem 0;
    font-size: 0.72rem;
    color: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(8px);
    transition: all 0.3s ease;
}

.sidebar-status:hover {
    border-color: rgba(212, 175, 55, 0.2);
    background: rgba(255, 255, 255, 0.06);
}

/* ==========================================================
   PAGE D'ACCUEIL — Bannière premium
   ========================================================== */

.welcome-hero {
    text-align: center;
    padding: 3rem 2rem;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 28px;
    margin: 0.5rem 0 1.5rem;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
    position: relative;
    overflow: hidden;
}

.welcome-hero::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse at 70% 30%, rgba(212, 175, 55, 0.05), transparent 70%);
    pointer-events: none;
}

.welcome-hero .icon {
    font-size: 3.5rem;
    margin-bottom: 0.5rem;
    display: block;
}

.welcome-hero h1 {
    font-size: 2.2rem;
    font-weight: 900;
    color: #FFFFFF;
    margin: 0.3rem 0 0.2rem;
    letter-spacing: -0.02em;
}

.welcome-hero h1 .highlight {
    background: linear-gradient(135deg, #D4AF37, #F5E6B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.welcome-hero p {
    color: rgba(255, 255, 255, 0.5);
    font-size: 1.05rem;
    max-width: 520px;
    margin: 0.5rem auto;
    line-height: 1.6;
}

.welcome-hero .divider {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.3), transparent);
    margin: 0.8rem auto;
}

.welcome-hero .badge-gold {
    display: inline-block;
    padding: 0.3rem 1.2rem;
    border-radius: 999px;
    background: rgba(212, 175, 55, 0.08);
    border: 1px solid rgba(212, 175, 55, 0.12);
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

.welcome-hero .badge-gold + .badge-gold {
    margin-left: 0.5rem;
}

.welcome-cta {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin-top: 0.8rem;
    text-align: center;
}

.welcome-cta .arrow {
    display: inline-block;
    color: rgba(212, 175, 55, 0.6);
    font-size: 1.2rem;
    margin-right: 0.5rem;
}

.welcome-cta .text {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.9rem;
}

.welcome-cta .text strong {
    color: rgba(255, 255, 255, 0.8);
    font-weight: 700;
}

/* ==========================================================
   NAVIGATION — Onglets premium
   ========================================================== */

section.main div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 0.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
    margin-bottom: 1.4rem;
}

section.main div[data-testid="stRadio"] label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 0.5rem 1.1rem !important;
    margin: 0 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}

section.main div[data-testid="stRadio"] label:hover {
    background: rgba(255, 255, 255, 0.04);
}

section.main div[data-testid="stRadio"] label p {
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    color: rgba(255, 255, 255, 0.5) !important;
    margin: 0 !important;
    transition: color 0.3s ease;
}

section.main div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #D4AF37, #B8960F);
    border-color: #D4AF37;
    box-shadow: 0 4px 20px rgba(212, 175, 55, 0.25);
}

section.main div[data-testid="stRadio"] label:has(input:checked) p {
    color: #0A1628 !important;
    font-weight: 800 !important;
}

section.main div[data-testid="stRadio"] label [data-baseweb="radio"] > div:first-child {
    width: 0;
    height: 0;
    margin: 0;
    opacity: 0;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR — IDENTITÉ
# ============================================================

with st.sidebar:

    logo_vie_assurance = asset_html(
        ["vie-assurance", "nsia-vie", "vie assurance"],
        size=64,
    )

    if logo_vie_assurance:

        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:.6rem;">
                {logo_vie_assurance}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="app-sidebar-title">
            <div class="brand">NSIA <span>ASSURANCE</span></div>
            <div class="subtitle">EXPÉRIENCE CLIENT</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR — IMPORT DEX
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-section">📥 Données</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Importez la base DEX centrale contenant "
        "les 6 métiers."
    )

    uf_dex = st.file_uploader(
        "Importer la base DEX",
        type=["xlsx", "xlsm", "xls"],
        key="up_dex",
        help=(
            "DIGITAL, MESSAGERIE, RC & SATISFACTION, "
            "PHYSIQUE, CALLCENTER et DESHERENCE."
        ),
        label_visibility="collapsed",
    )

    if uf_dex is not None:

        try:

            dex_path = save_uploaded_dex(uf_dex)

            validation = validate_workbook(dex_path)

            if validation.ok:

                st.success(
                    "Base DEX prête",
                    icon="✅",
                )

                with st.expander(
                    "Contrôle qualité",
                    expanded=False,
                ):

                    for canonical, actual in (
                        validation.sheet_map.items()
                    ):

                        st.write(
                            f"✓ **{canonical}** ← `{actual}`"
                        )

                    datasets = get_dex_data()

                    issues = dex_quality_report(datasets)

                    if issues:

                        st.warning(
                            f"{len(issues)} anomalie(s) détectée(s)"
                        )

                        for issue in issues:
                            st.caption(f"• {issue}")

                    else:

                        st.success(
                            "Aucune anomalie détectée."
                        )

                st.session_state["dex_ready"] = True
                st.session_state["dex_path"] = str(dex_path)

            else:

                st.error(
                    "La base DEX n'est pas conforme."
                )

                with st.expander(
                    "Voir les problèmes",
                    expanded=True,
                ):

                    for issue in validation.issues:
                        st.caption(f"• {issue}")

                st.session_state["dex_ready"] = False

        except Exception as exc:

            st.error(
                f"Erreur lors de l'importation : {exc}"
            )

            st.session_state["dex_ready"] = False


# ============================================================
# ATTENTE BASE DEX — PAGE D'ACCUEIL PREMIUM
# ============================================================

if not st.session_state.get("dex_ready", False):

    st.markdown(
        """
        <div class="welcome-hero">
            <span class="icon">📊</span>
            <h1>Bienvenue sur <span class="highlight">votre espace NSIA</span></h1>
            <div class="divider"></div>
            <p>
                Tableau de pilotage de l'expérience client.<br>
                Importez votre base DEX pour commencer l'analyse.
            </p>
            <div style="margin-top: 0.8rem;">
                <span class="badge-gold">● 6 métiers intégrés</span>
                <span class="badge-gold">● KPIs en temps réel</span>
                <span class="badge-gold">● IA intégrée</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    banniere_etudes = asset_html(
        ["etude"],
        style="width:100%;max-width:640px;border-radius:16px;display:block;margin:0 auto;object-fit:cover;",
    )

    if banniere_etudes:

        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; margin: 1.4rem 0;">
                {banniere_etudes}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="welcome-cta">
            <span class="arrow">⬅️</span>
            <span class="text">
                <strong>Pour démarrer :</strong> importez la base DEX depuis le menu à gauche
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

try:

    dex = get_dex_data()

except Exception as exc:

    st.error(
        f"Impossible de charger la base DEX : {exc}"
    )

    st.stop()


# ============================================================
# VÉRIFICATION DES BASES
# ============================================================

bases_attendues = [
    "DIGITAL",
    "MESSAGERIE",
    "RC & SATISFACTION",
    "PHYSIQUE",
    "CALLCENTER",
    "DESHERENCE",
]

bases_manquantes = [
    base
    for base in bases_attendues
    if base not in dex
]

if bases_manquantes:

    st.error(
        "Bases manquantes : "
        + ", ".join(bases_manquantes)
    )

    st.stop()


# ============================================================
# DATAFRAMES
# ============================================================

df_digital = dex["DIGITAL"]
df_msg = dex["MESSAGERIE"]
df_rc_sat = dex["RC & SATISFACTION"]
df_physique = dex["PHYSIQUE"]
df_cc = dex["CALLCENTER"]
df_desherence = dex["DESHERENCE"]


# ============================================================
# SIDEBAR — ÉTAT DES BASES
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-section">📊 Données chargées</div>',
        unsafe_allow_html=True,
    )

    bases_ui = [
        ("🟦", "Digital", df_digital),
        ("🏢", "Physique", df_physique),
        ("😊", "Satisfaction", df_rc_sat),
        ("💬", "Messagerie", df_msg),
        ("🎧", "Call Center", df_cc),
        ("📉", "Déshérence", df_desherence),
    ]

    for icon, name, dataframe in bases_ui:

        volume = f"{len(dataframe):,}".replace(",", " ")

        st.markdown(
            f"""
            <div class="sidebar-status">
                {icon} <b>{name}</b>
                <span style="float:right; opacity:.5;">
                    {volume}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# INDICATEUR DE CONNEXION (sidebar)
# ============================================================

with st.sidebar:

    st.markdown("---")

    st.markdown(
        """
        <div style="
            text-align: center;
            font-size: .6rem;
            color: rgba(255,255,255,0.15);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        ">
            ● Système opérationnel
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# NAVIGATION — ONGLETS HORIZONTAUX
# ============================================================

NAV_ITEMS = [
    "🏠 Accueil",
    "📊 Point Global",
    "🟦 Digital",
    "🏢 Physique",
    "😊 Satisfaction",
    "⚠️ Réclamations",
    "💬 Messagerie",
    "🎧 Call Center",
    "📉 Déshérence",
]

page = st.radio(
    "Navigation",
    NAV_ITEMS,
    key="navigation",
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# ROUTAGE DES PAGES
# ============================================================

if page == "🏠 Accueil":

    accueil.render(dex)


elif page == "📊 Point Global":

    render_point_global(dex)


elif page == "🟦 Digital":

    digital.render(df_digital)


elif page == "🏢 Physique":

    physique.render(df_physique)


elif page == "😊 Satisfaction":

    satisfaction.render(df_rc_sat)


elif page == "⚠️ Réclamations":

    reclamation.render(df_rc_sat)


elif page == "💬 Messagerie":

    messagerie.render(df_msg)


elif page == "🎧 Call Center":

    callcenter.render(df_cc)


elif page == "📉 Déshérence":

    desherence.render(df_desherence)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

footer_brand()