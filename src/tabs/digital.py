# ============================================================
# NSIA ASSURANCE — EXPÉRIENCE CLIENT
# ONGLET DIGITAL
# ============================================================
#
# Version premium :
# - Granularité → Année → Période → Agence
# - KPI de pilotage
# - Variations en %
# - Évolution temporelle
# - Contre-performances analysées comme commentaires
# - Initiatives analysées comme actions
# - Performance par agence
# - Analyse décisionnelle
#
# Compatible avec :
#   src/tabs/digital.py
#
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# HTML RENDER HELPER
# ============================================================
#
# Streamlit runs every st.markdown() string through a Markdown
# parser BEFORE rendering it as HTML. Markdown treats any line
# indented by 4+ spaces as a literal/code block, so the heavily
# indented HTML strings below (indented to match Python's own
# code style) were being displayed as raw text instead of being
# rendered as actual HTML elements. Stripping the leading
# whitespace from every line avoids that trap while keeping the
# HTML readable in the source.
# ============================================================

def _html(s: str) -> str:
    return "\n".join(line.strip() for line in s.strip("\n").splitlines())



# ============================================================
# PALETTE NSIA
# ============================================================

NAVY_DEEP = "#081426"
NAVY_DARK = "#0D1D35"
NAVY_MID = "#162A50"
NAVY_CARD = "#182C50"

GOLD = "#D4AF37"
GOLD_LIGHT = "#F5E6B8"

WHITE = "#FFFFFF"
TEXT = "#F4F7FB"
TEXT_SOFT = "rgba(255,255,255,0.68)"
TEXT_MUTED = "rgba(255,255,255,0.42)"

BLUE = "#4C8DFF"
CYAN = "#38D9E8"
GREEN = "#22C55E"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
PINK = "#F472B6"

GRID = "rgba(255,255,255,0.07)"


# ============================================================
# CONFIGURATION
# ============================================================

OBJECTIF_DIGITALISATION = 0.30


# ============================================================
# CSS
# ============================================================

def inject_digital_css():

    st.markdown(_html(f"""
        <style>

        /* ==================================================
           CONTENEUR PRINCIPAL
        ================================================== */

        .digital-page {{
            width: 100%;
        }}

        /* ==================================================
           HEADER
        ================================================== */

        .digital-hero {{
            position: relative;
            overflow: hidden;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.25rem;
            border-radius: 22px;

            background:
                linear-gradient(
                    135deg,
                    rgba(24,44,80,0.96),
                    rgba(10,22,40,0.96)
                );

            border: 1px solid rgba(212,175,55,0.16);

            box-shadow:
                0 12px 45px rgba(0,0,0,0.28);
        }}

        .digital-hero::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;

            background:
                linear-gradient(
                    180deg,
                    {GOLD},
                    {GOLD_LIGHT},
                    {GOLD}
                );

            box-shadow:
                0 0 28px rgba(212,175,55,0.35);
        }}

        .digital-hero::after {{
            content: "";
            position: absolute;
            width: 420px;
            height: 420px;
            right: -160px;
            top: -250px;

            background:
                radial-gradient(
                    circle,
                    rgba(76,141,255,0.13),
                    transparent 65%
                );

            pointer-events: none;
        }}

        .digital-title {{
            position: relative;
            z-index: 2;

            font-size: 1.55rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            color: {WHITE};

            margin: 0;
        }}

        .digital-subtitle {{
            position: relative;
            z-index: 2;

            margin-top: 0.35rem;

            color: {TEXT_SOFT};
            font-size: 0.82rem;
            font-weight: 500;
        }}

        .digital-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;

            margin-top: 0.85rem;
            padding: 0.35rem 0.75rem;

            border-radius: 999px;

            background: rgba(212,175,55,0.10);
            border: 1px solid rgba(212,175,55,0.18);

            color: {GOLD_LIGHT};

            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}


        /* ==================================================
           FILTRES
        ================================================== */

        .filter-container {{
            position: relative;

            padding: 1rem 1.15rem 0.45rem;
            margin-bottom: 1.2rem;

            border-radius: 18px;

            background:
                rgba(255,255,255,0.035);

            border:
                1px solid rgba(255,255,255,0.07);

            box-shadow:
                0 7px 28px rgba(0,0,0,0.16);
        }}

        .filter-title {{
            color: {TEXT_SOFT};

            font-size: 0.67rem;
            font-weight: 800;

            letter-spacing: 0.08em;
            text-transform: uppercase;

            margin-bottom: 0.65rem;
        }}

        div[data-baseweb="select"] > div {{
            background: rgba(255,255,255,0.055) !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            border-radius: 12px !important;

            min-height: 42px;

            transition: all 0.25s ease;
        }}

        div[data-baseweb="select"] > div:hover {{
            border-color: rgba(212,175,55,0.65) !important;

            box-shadow:
                0 0 20px rgba(212,175,55,0.10);
        }}

        /* ==================================================
           SECTION
        ================================================== */

        .digital-section {{
            display: flex;
            align-items: center;

            gap: 0.75rem;

            margin:
                1.55rem 0
                0.95rem;

            padding:
                0.72rem
                1rem;

            background:
                rgba(255,255,255,0.028);

            border-left:
                4px solid {GOLD};

            border-radius:
                0 14px 14px 0;

            color: {WHITE};

            font-size: 0.74rem;
            font-weight: 900;

            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .digital-section-line {{
            flex: 1;

            height: 1px;

            background:
                linear-gradient(
                    90deg,
                    rgba(255,255,255,0.09),
                    transparent
                );
        }}


        /* ==================================================
           KPI
        ================================================== */

        .digital-kpi {{
            position: relative;
            overflow: hidden;

            min-height: 157px;

            padding:
                1.05rem
                1.2rem;

            border-radius: 19px;

            background:
                linear-gradient(
                    145deg,
                    rgba(38,62,103,0.88),
                    rgba(19,37,67,0.94)
                );

            border:
                1px solid rgba(255,255,255,0.07);

            box-shadow:
                0 8px 30px rgba(0,0,0,0.22);

            transition:
                transform 0.25s ease,
                border-color 0.25s ease,
                box-shadow 0.25s ease;
        }}

        .digital-kpi::before {{
            content: "";

            position: absolute;

            left: 0;
            right: 0;
            top: 0;

            height: 3px;

            background:
                linear-gradient(
                    90deg,
                    {GOLD},
                    {GOLD_LIGHT},
                    {GOLD}
                );

            opacity: 0.72;
        }}

        .digital-kpi:hover {{
            transform: translateY(-3px);

            border-color:
                rgba(212,175,55,0.25);

            box-shadow:
                0 15px 40px rgba(0,0,0,0.30),
                0 0 30px rgba(212,175,55,0.07);
        }}

        .digital-kpi-icon {{
            width: 38px;
            height: 38px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 11px;

            background:
                rgba(212,175,55,0.11);

            border:
                1px solid rgba(212,175,55,0.10);

            font-size: 1rem;

            margin-bottom: 0.55rem;
        }}

        .digital-kpi-label {{
            color: rgba(255,255,255,0.46);

            font-size: 0.62rem;
            font-weight: 800;

            letter-spacing: 0.075em;
            text-transform: uppercase;

            line-height: 1.25;
        }}

        .digital-kpi-value {{
            margin-top: 0.25rem;

            color: {WHITE};

            font-size: 1.82rem;
            font-weight: 900;

            letter-spacing: -0.035em;

            line-height: 1.1;
        }}

        .digital-kpi-value.good {{
            color: {GREEN};
        }}

        .digital-kpi-value.warn {{
            color: {AMBER};
        }}

        .digital-kpi-value.bad {{
            color: {RED};
        }}

        .digital-kpi-sub {{
            margin-top: 0.45rem;

            color:
                rgba(255,255,255,0.37);

            font-size: 0.65rem;
            font-weight: 500;
        }}

        .variation-up {{
            color: {GREEN} !important;
            font-weight: 800;
        }}

        .variation-down {{
            color: {RED} !important;
            font-weight: 800;
        }}

        .variation-neutral {{
            color: {TEXT_MUTED} !important;
        }}


        /* ==================================================
           PANNEAU
        ================================================== */

        .digital-panel {{
            padding: 1rem;

            border-radius: 19px;

            background:
                rgba(255,255,255,0.035);

            border:
                1px solid rgba(255,255,255,0.065);

            box-shadow:
                0 8px 28px rgba(0,0,0,0.16);
        }}

        .digital-panel-title {{
            color: {WHITE};

            font-size: 0.78rem;
            font-weight: 850;

            margin-bottom: 0.1rem;
        }}

        .digital-panel-subtitle {{
            color: {TEXT_MUTED};

            font-size: 0.63rem;
            font-weight: 500;

            margin-bottom: 0.4rem;
        }}


        /* ==================================================
           TABLEAU
        ================================================== */

        .agency-table {{
            border-radius: 16px;
            overflow: hidden;

            border:
                1px solid rgba(255,255,255,0.06);
        }}

        .agency-table-header {{
            display: grid;

            grid-template-columns:
                2.4fr
                1fr
                1fr
                1fr
                1fr;

            padding: 0.75rem 0.9rem;

            background:
                rgba(212,175,55,0.08);

            color:
                rgba(255,255,255,0.55);

            font-size: 0.61rem;
            font-weight: 800;

            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .agency-table-row {{
            display: grid;

            grid-template-columns:
                2.4fr
                1fr
                1fr
                1fr
                1fr;

            padding: 0.72rem 0.9rem;

            background:
                rgba(255,255,255,0.025);

            border-top:
                1px solid rgba(255,255,255,0.045);

            color:
                rgba(255,255,255,0.82);

            font-size: 0.66rem;
        }}

        .agency-name {{
            font-weight: 750;
            color: {WHITE};
        }}

        .agency-good {{
            color: {GREEN};
            font-weight: 800;
        }}

        .agency-warn {{
            color: {AMBER};
            font-weight: 800;
        }}

        .agency-bad {{
            color: {RED};
            font-weight: 800;
        }}


        /* ==================================================
           MESSAGE D'ANALYSE
        ================================================== */

        .insight-card {{
            padding: 1rem 1.15rem;

            border-radius: 17px;

            background:
                linear-gradient(
                    135deg,
                    rgba(212,175,55,0.07),
                    rgba(255,255,255,0.025)
                );

            border:
                1px solid rgba(212,175,55,0.12);

            margin-top: 0.75rem;
        }}

        .insight-title {{
            color: {GOLD_LIGHT};

            font-size: 0.68rem;
            font-weight: 900;

            text-transform: uppercase;
            letter-spacing: 0.07em;
        }}

        .insight-text {{
            margin-top: 0.35rem;

            color:
                rgba(255,255,255,0.72);

            font-size: 0.72rem;
            line-height: 1.55;
        }}

        </style>
        """), unsafe_allow_html=True)


# ============================================================
# UTILITAIRES
# ============================================================

def fmt_nombre(value) -> str:

    if value is None or pd.isna(value):
        return "—"

    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except Exception:
        return "—"


def fmt_pct(value, decimals=1) -> str:

    if value is None or pd.isna(value):
        return "—"

    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except Exception:
        return "—"


def variation_pct(current, previous):

    if previous is None or pd.isna(previous):
        return None

    if current is None or pd.isna(current):
        return None

    try:

        previous = float(previous)
        current = float(current)

        if previous == 0:
            return None

        return (current - previous) / abs(previous)

    except Exception:

        return None


def variation_html(value):

    if value is None or pd.isna(value):

        return (
            '<span class="variation-neutral">'
            'Pas de comparaison disponible'
            '</span>'
        )

    if value > 0:

        return (
            f'<span class="variation-up">'
            f'▲ +{value * 100:.1f}%'
            f'</span>'
        )

    if value < 0:

        return (
            f'<span class="variation-down">'
            f'▼ {value * 100:.1f}%'
            f'</span>'
        )

    return (
        '<span class="variation-neutral">'
        '→ 0,0%'
        '</span>'
    )


def safe_numeric(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)


def clean_text_series(series):

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


# ============================================================
# RECHERCHE AUTOMATIQUE DU DATAFRAME DIGITAL
# ============================================================

def _is_digital_dataframe(obj) -> bool:

    if not isinstance(obj, pd.DataFrame):
        return False

    required = {
        "Prestations Digital",
        "Total Prestations",
    }

    return required.issubset(set(obj.columns))


def _find_dataframe_in_object(obj):

    if isinstance(obj, pd.DataFrame):

        if _is_digital_dataframe(obj):
            return obj

        return None

    if isinstance(obj, dict):

        # priorité aux clés évidentes
        for key, value in obj.items():

            key_str = str(key).lower()

            if any(
                word in key_str
                for word in [
                    "digital",
                    "base digital",
                    "df_digital",
                ]
            ):

                found = _find_dataframe_in_object(value)

                if found is not None:
                    return found

        # recherche générale
        for value in obj.values():

            found = _find_dataframe_in_object(value)

            if found is not None:
                return found

    return None


def get_digital_dataframe(df: Optional[pd.DataFrame] = None):

    # 1 — DataFrame directement fourni
    if _is_digital_dataframe(df):

        return df.copy()

    # 2 — session_state
    for key, value in st.session_state.items():

        found = _find_dataframe_in_object(value)

        if found is not None:
            return found.copy()

    return None


# ============================================================
# NORMALISATION
# ============================================================

def prepare_dataframe(df: pd.DataFrame):

    df = df.copy()

    # ------------------------------
    # Colonnes obligatoires
    # ------------------------------

    required = [
        "Date",
        "Agence",
        "Prestations Digital",
        "Total Prestations",
    ]

    for col in required:

        if col not in df.columns:

            if col == "Date":

                df[col] = pd.NaT

            elif col in [
                "Prestations Digital",
                "Total Prestations",
            ]:

                df[col] = 0

            else:

                df[col] = "Non renseigné"

    # ------------------------------
    # Date
    # ------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce",
    )

    df = df.dropna(
        subset=["Date"]
    ).copy()

    # ------------------------------
    # Numériques
    # ------------------------------

    df["Prestations Digital"] = safe_numeric(
        df["Prestations Digital"]
    )

    df["Total Prestations"] = safe_numeric(
        df["Total Prestations"]
    )

    # ------------------------------
    # Texte
    # ------------------------------

    df["Agence"] = (
        df["Agence"]
        .fillna("Agence non renseignée")
        .astype(str)
        .str.strip()
    )

    if "Contre Performance" not in df.columns:
        df["Contre Performance"] = ""

    if "Initiative" not in df.columns:
        df["Initiative"] = ""

    df["Contre Performance"] = clean_text_series(
        df["Contre Performance"]
    )

    df["Initiative"] = clean_text_series(
        df["Initiative"]
    )

    # ------------------------------
    # Calendrier
    # ------------------------------

    df["Année"] = df["Date"].dt.year

    df["Mois_Num"] = df["Date"].dt.month

    df["Mois"] = df["Date"].dt.month_name(
        locale="fr_FR"
    ) if False else df["Date"].dt.month.map({
        1: "Janvier",
        2: "Février",
        3: "Mars",
        4: "Avril",
        5: "Mai",
        6: "Juin",
        7: "Juillet",
        8: "Août",
        9: "Septembre",
        10: "Octobre",
        11: "Novembre",
        12: "Décembre",
    })

    df["Trimestre"] = (
        "T"
        + df["Date"].dt.quarter.astype(str)
    )

    iso = df["Date"].dt.isocalendar()

    df["Semaine_Num"] = (
        iso.week
        .astype(int)
    )

    df["Période_Mensuelle"] = (
        df["Date"]
        .dt.to_period("M")
        .astype(str)
    )

    return df


# ============================================================
# FILTRES
# ============================================================

def render_filters(df):

    st.markdown(
        '<div class="filter-container">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="filter-title">'
        'PARAMÈTRES D’ANALYSE'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(
        [1.05, 0.9, 1.45, 1.55]
    )

    # ========================================================
    # GRANULARITÉ
    # ========================================================

    with c1:

        granularite = st.selectbox(
            "Granularité",
            [
        
                "Mensuelle",
                "Hebdomadaire",
                "Journalière",
                "Trimestrielle",
            ],
            index=0,
            key="digital_granularite",
        )

    # ========================================================
    # ANNÉE
    # ========================================================

    annees = sorted(
        df["Année"].dropna().unique(),
        reverse=True,
    )

    with c2:

        annee = st.selectbox(
            "Année",
            annees,
            key="digital_annee",
        )

    df_annee = df[
        df["Année"] == annee
    ].copy()

    # ========================================================
    # PÉRIODE
    # ========================================================

    with c3:

        if granularite == "Mensuelle":

            periodes = sorted(
                df_annee["Mois_Num"]
                .dropna()
                .unique()
            )

            options = ["Toutes les périodes"] + [
                {
                    1: "Janvier",
                    2: "Février",
                    3: "Mars",
                    4: "Avril",
                    5: "Mai",
                    6: "Juin",
                    7: "Juillet",
                    8: "Août",
                    9: "Septembre",
                    10: "Octobre",
                    11: "Novembre",
                    12: "Décembre",
                }[int(m)]
                for m in periodes
            ]

        elif granularite == "Hebdomadaire":

            semaines = sorted(
                df_annee["Semaine_Num"]
                .dropna()
                .unique()
            )

            options = ["Toutes les périodes"] + [
                f"Semaine {int(s)}"
                for s in semaines
            ]

        elif granularite == "Trimestrielle":

            trimestres = sorted(
                df_annee["Date"]
                .dt.quarter
                .dropna()
                .unique()
            )

            options = ["Toutes les périodes"] + [
                f"Trimestre {int(t)}"
                for t in trimestres
            ]

        else:

            dates = sorted(
                df_annee["Date"]
                .dt.date
                .dropna()
                .unique()
            )

            options = ["Toutes les périodes"] + [
                pd.Timestamp(d).strftime("%d/%m/%Y")
                for d in dates
            ]

        periode = st.selectbox(
            "Période",
            options,
            key="digital_periode",
        )

    # ========================================================
    # AGENCE
    # ========================================================

    agences = sorted(
        df_annee["Agence"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    with c4:

        agence = st.selectbox(
            "Agence",
            ["Toutes les agences"] + agences,
            key="digital_agence",
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    return (
        granularite,
        int(annee),
        periode,
        agence,
    )


# ============================================================
# APPLICATION DES FILTRES
# ============================================================

def apply_filters(
    df,
    granularite,
    annee,
    periode,
    agence,
):

    filtered = df[
        df["Année"] == annee
    ].copy()

    # ------------------------------
    # Agence
    # ------------------------------

    if agence != "Toutes les agences":

        filtered = filtered[
            filtered["Agence"] == agence
        ]

    # ------------------------------
    # Période
    # ------------------------------

    if periode != "Toutes les périodes":

        if granularite == "Mensuelle":

            month_map = {
                "Janvier": 1,
                "Février": 2,
                "Mars": 3,
                "Avril": 4,
                "Mai": 5,
                "Juin": 6,
                "Juillet": 7,
                "Août": 8,
                "Septembre": 9,
                "Octobre": 10,
                "Novembre": 11,
                "Décembre": 12,
            }

            mois = month_map.get(
                periode
            )

            if mois is not None:

                filtered = filtered[
                    filtered["Mois_Num"] == mois
                ]

        elif granularite == "Hebdomadaire":

            semaine = int(
                periode.replace(
                    "Semaine ",
                    ""
                )
            )

            filtered = filtered[
                filtered["Semaine_Num"] == semaine
            ]

        elif granularite == "Trimestrielle":

            trimestre = int(
                periode.replace(
                    "Trimestre ",
                    ""
                )
            )

            filtered = filtered[
                filtered["Date"]
                .dt.quarter == trimestre
            ]

        elif granularite == "Journalière":

            date_value = pd.to_datetime(
                periode,
                dayfirst=True,
                errors="coerce"
            )

            if not pd.isna(date_value):

                filtered = filtered[
                    filtered["Date"].dt.date
                    == date_value.date()
                ]

    return filtered


# ============================================================
# CLÉ DE PÉRIODE
# ============================================================

def get_period_key(
    granularite,
    row_dates,
):

    if len(row_dates) == 0:
        return None

    d = pd.to_datetime(row_dates)

    if granularite == "Mensuelle":

        return d.min().to_period("M")

    if granularite == "Hebdomadaire":

        return d.min().to_period("W")

    if granularite == "Trimestrielle":

        return d.min().to_period("Q")

    if granularite == "Journalière":

        return d.min().normalize()

    return None


# ============================================================
# DATA PÉRIODE PRÉCÉDENTE
# ============================================================

def get_previous_period_df(
    df,
    filtered,
    granularite,
    annee,
    periode,
    agence,
):

    # --------------------------------------------------------
    # TOUTES LES PÉRIODES
    # => comparaison avec l'année précédente
    # --------------------------------------------------------

    if periode == "Toutes les périodes":

        previous_year = annee - 1

        previous = df[
            df["Année"] == previous_year
        ].copy()

        if agence != "Toutes les agences":

            previous = previous[
                previous["Agence"] == agence
            ]

        return previous

    # --------------------------------------------------------
    # MENSUEL
    # --------------------------------------------------------

    if granularite == "Mensuelle":

        month_map = {
            "Janvier": 1,
            "Février": 2,
            "Mars": 3,
            "Avril": 4,
            "Mai": 5,
            "Juin": 6,
            "Juillet": 7,
            "Août": 8,
            "Septembre": 9,
            "Octobre": 10,
            "Novembre": 11,
            "Décembre": 12,
        }

        mois = month_map.get(
            periode
        )

        if mois is None:
            return pd.DataFrame()

        date_ref = pd.Timestamp(
            year=annee,
            month=mois,
            day=1
        )

        previous_month = (
            date_ref
            - pd.offsets.MonthBegin(1)
        )

        previous = df[
            (
                df["Date"].dt.to_period("M")
                == previous_month.to_period("M")
            )
        ].copy()

    # --------------------------------------------------------
    # HEBDOMADAIRE
    # --------------------------------------------------------

    elif granularite == "Hebdomadaire":

        semaine = int(
            periode.replace(
                "Semaine ",
                ""
            )
        )

        current = df[
            (
                df["Année"] == annee
            )
            &
            (
                df["Semaine_Num"] == semaine
            )
        ]

        if current.empty:
            return pd.DataFrame()

        current_date = current["Date"].min()

        previous_start = (
            current_date
            - pd.Timedelta(days=7)
        )

        previous_end = (
            previous_start
            + pd.Timedelta(days=6)
        )

        previous = df[
            (
                df["Date"] >= previous_start
            )
            &
            (
                df["Date"] <= previous_end
            )
        ].copy()

    # --------------------------------------------------------
    # TRIMESTRIEL
    # --------------------------------------------------------

    elif granularite == "Trimestrielle":

        trimestre = int(
            periode.replace(
                "Trimestre ",
                ""
            )
        )

        current_period = pd.Period(
            f"{annee}Q{trimestre}",
            freq="Q"
        )

        previous_period = (
            current_period - 1
        )

        previous = df[
            df["Date"]
            .dt.to_period("Q")
            == previous_period
        ].copy()

    # --------------------------------------------------------
    # JOURNALIER
    # --------------------------------------------------------

    else:

        date_value = pd.to_datetime(
            periode,
            dayfirst=True,
            errors="coerce"
        )

        if pd.isna(date_value):
            return pd.DataFrame()

        previous_date = (
            date_value
            - pd.Timedelta(days=1)
        )

        previous = df[
            df["Date"].dt.normalize()
            == previous_date.normalize()
        ].copy()

    if agence != "Toutes les agences":

        previous = previous[
            previous["Agence"] == agence
        ]

    return previous


# ============================================================
# CALCUL DES INDICATEURS
# ============================================================

def calculate_metrics(df):

    if df.empty:

        return {
            "digital": 0,
            "total": 0,
            "taux": np.nan,
            "cp": 0,
            "initiatives": 0,
        }

    digital = df[
        "Prestations Digital"
    ].sum()

    total = df[
        "Total Prestations"
    ].sum()

    taux = (
        digital / total
        if total > 0
        else np.nan
    )

    cp = (
        df["Contre Performance"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    initiatives = (
        df["Initiative"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    return {
        "digital": digital,
        "total": total,
        "taux": taux,
        "cp": cp,
        "initiatives": initiatives,
    }


# ============================================================
# KPI CARD
# ============================================================

def render_kpi(
    icon,
    label,
    value,
    variation=None,
    status="neutral",
    subtitle="",
):

    variation_text = variation_html(
        variation
    )

    st.markdown(_html(f"""
        <div class="digital-kpi">

            <div class="digital-kpi-icon">
                {icon}
            </div>

            <div class="digital-kpi-label">
                {label}
            </div>

            <div class="digital-kpi-value {status}">
                {value}
            </div>

            <div class="digital-kpi-sub">
                {variation_text}
                {" · " + subtitle if subtitle else ""}
            </div>

        </div>
        """), unsafe_allow_html=True)


# ============================================================
# SECTION
# ============================================================

def section(title):

    st.markdown(_html(f"""
        <div class="digital-section">

            <span>{title}</span>

            <span class="digital-section-line"></span>

        </div>
        """), unsafe_allow_html=True)


# ============================================================
# GRAPHIQUE — ÉVOLUTION TAUX DIGITAL
# ============================================================

def chart_evolution_taux(
    df,
    granularite,
):

    if df.empty:
        return

    temp = df.copy()

    if granularite == "Mensuelle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        label_format = "%b %Y"

    elif granularite == "Hebdomadaire":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("W")
            .apply(lambda x: x.start_time)
        )

        label_format = "S%V"

    elif granularite == "Trimestrielle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("Q")
            .dt.to_timestamp()
        )

        label_format = "T%q"

    else:

        temp["Période"] = (
            temp["Date"]
            .dt.normalize()
        )

        label_format = "%d/%m"

    grouped = (
        temp
        .groupby("Période", as_index=False)
        .agg(
            digital=(
                "Prestations Digital",
                "sum"
            ),
            total=(
                "Total Prestations",
                "sum"
            ),
        )
    )

    grouped["taux"] = np.where(
        grouped["total"] > 0,
        grouped["digital"]
        / grouped["total"],
        np.nan,
    )

    grouped = grouped.sort_values(
        "Période"
    )

    fig = go.Figure()

    # zone sous la courbe
    fig.add_trace(
        go.Scatter(
            x=grouped["Période"],
            y=grouped["taux"] * 100,
            mode="lines",
            line=dict(
                color=GOLD,
                width=4,
            ),
            fill="tozeroy",
            fillcolor="rgba(212,175,55,0.08)",
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Taux de digitalisation : "
                "%{y:.1f}%"
                "<extra></extra>"
            ),
            name="Taux de digitalisation",
        )
    )

    # objectif
    fig.add_hline(
        y=OBJECTIF_DIGITALISATION * 100,
        line_dash="dash",
        line_width=1.5,
        line_color="rgba(34,197,94,0.65)",
        annotation_text="Objectif",
        annotation_position="top left",
        annotation_font_color=GREEN,
    )

    fig.update_layout(
        height=370,

        margin=dict(
            l=10,
            r=10,
            t=25,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            color=TEXT_SOFT,
            family="Inter",
        ),

        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(
                color=TEXT_MUTED,
                size=10,
            ),
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            ticksuffix="%",
            tickfont=dict(
                color=TEXT_MUTED,
                size=10,
            ),
        ),

        hoverlabel=dict(
            bgcolor=NAVY_DARK,
            bordercolor=GOLD,
            font_color=WHITE,
        ),

        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# GRAPHIQUE — VOLUMES
# ============================================================

def chart_evolution_volumes(
    df,
    granularite,
):

    if df.empty:
        return

    temp = df.copy()

    if granularite == "Mensuelle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

    elif granularite == "Hebdomadaire":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("W")
            .apply(lambda x: x.start_time)
        )

    elif granularite == "Trimestrielle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("Q")
            .dt.to_timestamp()
        )

    else:

        temp["Période"] = (
            temp["Date"]
            .dt.normalize()
        )

    grouped = (
        temp
        .groupby("Période", as_index=False)
        .agg(
            digitales=(
                "Prestations Digital",
                "sum"
            ),
            total=(
                "Total Prestations",
                "sum"
            ),
        )
        .sort_values("Période")
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période"],
            y=grouped["digitales"],
            mode="lines+markers",
            name="Prestations digitales",
            line=dict(
                color=CYAN,
                width=3,
            ),
            marker=dict(
                size=6,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Digital : %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période"],
            y=grouped["total"],
            mode="lines+markers",
            name="Prestations totales",
            line=dict(
                color=BLUE,
                width=3,
            ),
            marker=dict(
                size=6,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Total : %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=370,

        margin=dict(
            l=10,
            r=10,
            t=25,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            color=TEXT_SOFT,
            family="Inter",
        ),

        xaxis=dict(
            showgrid=False,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            tickfont=dict(
                color=TEXT_MUTED
            ),
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            font=dict(
                color=TEXT_SOFT,
                size=10,
            ),
        ),

        hoverlabel=dict(
            bgcolor=NAVY_DARK,
            bordercolor=GOLD,
            font_color=WHITE,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# GRAPHIQUE — CONTRE-PERFORMANCES
# ============================================================

def chart_contre_performances(df):

    if df.empty:
        return

    cp = (
        df["Contre Performance"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .reset_index()
    )

    cp.columns = [
        "Motif",
        "Nombre"
    ]

    cp = cp.sort_values(
        "Nombre",
        ascending=True
    )

    if cp.empty:

        st.info(
            "Aucune contre-performance "
            "renseignée sur la période sélectionnée."
        )

        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=cp["Nombre"],
            y=cp["Motif"],
            orientation="h",

            marker=dict(
                color=RED,
                opacity=0.82,
            ),

            text=cp["Nombre"],
            textposition="outside",

            textfont=dict(
                color=TEXT_SOFT,
                size=10,
            ),

            hovertemplate=(
                "<b>%{y}</b>"
                "<br>Nombre : %{x}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=max(
            260,
            len(cp) * 58
        ),

        margin=dict(
            l=10,
            r=35,
            t=10,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter",
            color=TEXT_SOFT,
        ),

        xaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(
                size=10,
                color=TEXT_SOFT,
            ),
        ),

        showlegend=False,

        hoverlabel=dict(
            bgcolor=NAVY_DARK,
            bordercolor=RED,
            font_color=WHITE,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# ÉVOLUTION DES CONTRE-PERFORMANCES
# ============================================================

def chart_evolution_cp(
    df,
    granularite,
):

    if df.empty:
        return

    temp = df.copy()

    if granularite == "Mensuelle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

    elif granularite == "Hebdomadaire":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("W")
            .apply(
                lambda x: x.start_time
            )
        )

    elif granularite == "Trimestrielle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("Q")
            .dt.to_timestamp()
        )

    else:

        temp["Période"] = (
            temp["Date"]
            .dt.normalize()
        )

    temp["CP"] = (
        temp["Contre Performance"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    grouped = (
        temp
        .groupby("Période", as_index=False)
        .agg(
            contre_performances=(
                "CP",
                "sum"
            )
        )
        .sort_values("Période")
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période"],
            y=grouped["contre_performances"],
            mode="lines+markers",

            line=dict(
                color=RED,
                width=3,
            ),

            marker=dict(
                size=6,
            ),

            fill="tozeroy",
            fillcolor="rgba(239,68,68,0.06)",

            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Contre-performances : %{y}"
                "<extra></extra>"
            ),

            name="Contre-performances",
        )
    )

    fig.update_layout(
        height=320,

        margin=dict(
            l=10,
            r=10,
            t=15,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        xaxis=dict(
            showgrid=False,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# INITIATIVES PAR TYPE
# ============================================================

def chart_initiatives(df):

    if df.empty:
        return

    initiatives = (
        df["Initiative"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .reset_index()
    )

    initiatives.columns = [
        "Initiative",
        "Nombre"
    ]

    initiatives = initiatives.sort_values(
        "Nombre",
        ascending=True
    )

    if initiatives.empty:

        st.info(
            "Aucune initiative renseignée "
            "sur la période sélectionnée."
        )

        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=initiatives["Nombre"],
            y=initiatives["Initiative"],
            orientation="h",

            marker=dict(
                color=GOLD,
                opacity=0.86,
            ),

            text=initiatives["Nombre"],
            textposition="outside",

            hovertemplate=(
                "<b>%{y}</b>"
                "<br>Nombre : %{x}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=max(
            250,
            len(initiatives) * 55
        ),

        margin=dict(
            l=10,
            r=35,
            t=10,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        xaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=False,
            zeroline=False,
        ),

        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# ÉVOLUTION INITIATIVES
# ============================================================

def chart_evolution_initiatives(
    df,
    granularite,
):

    if df.empty:
        return

    temp = df.copy()

    if granularite == "Mensuelle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

    elif granularite == "Hebdomadaire":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("W")
            .apply(
                lambda x: x.start_time
            )
        )

    elif granularite == "Trimestrielle":

        temp["Période"] = (
            temp["Date"]
            .dt.to_period("Q")
            .dt.to_timestamp()
        )

    else:

        temp["Période"] = (
            temp["Date"]
            .dt.normalize()
        )

    temp["Initiative_OK"] = (
        temp["Initiative"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    grouped = (
        temp
        .groupby("Période", as_index=False)
        .agg(
            initiatives=(
                "Initiative_OK",
                "sum"
            )
        )
        .sort_values("Période")
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période"],
            y=grouped["initiatives"],
            mode="lines+markers",

            line=dict(
                color=GOLD,
                width=3,
            ),

            marker=dict(
                size=6,
            ),

            fill="tozeroy",
            fillcolor="rgba(212,175,55,0.06)",

            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Initiatives : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=320,

        margin=dict(
            l=10,
            r=10,
            t=15,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        xaxis=dict(
            showgrid=False,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# PERFORMANCE PAR AGENCE
# ============================================================

def agency_performance(df):

    if df.empty:
        return pd.DataFrame()

    temp = df.copy()

    grouped = (
        temp
        .groupby(
            ["Agence"],
            as_index=False
        )
        .agg(
            digital=(
                "Prestations Digital",
                "sum"
            ),

            total=(
                "Total Prestations",
                "sum"
            ),

            cp=(
                "Contre Performance",
                lambda x:
                x.replace(
                    "",
                    np.nan
                ).notna().sum()
            ),

            initiatives=(
                "Initiative",
                lambda x:
                x.replace(
                    "",
                    np.nan
                ).notna().sum()
            ),
        )
    )

    grouped["taux"] = np.where(
        grouped["total"] > 0,
        grouped["digital"]
        / grouped["total"],
        np.nan,
    )

    grouped = grouped.sort_values(
        "taux",
        ascending=False
    )

    return grouped


# ============================================================
# GRAPHIQUE PERFORMANCE AGENCES
# ============================================================

def chart_agences(df):

    agency = agency_performance(df)

    if agency.empty:
        return

    agency = agency.head(15).copy()

    agency = agency.sort_values(
        "taux",
        ascending=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=agency["taux"] * 100,
            y=agency["Agence"],
            orientation="h",

            marker=dict(
                color=[
                    GREEN
                    if x >= OBJECTIF_DIGITALISATION
                    else AMBER
                    for x in agency["taux"]
                ],
                opacity=0.85,
            ),

            text=[
                f"{x * 100:.1f}%"
                for x in agency["taux"]
            ],

            textposition="outside",

            hovertemplate=(
                "<b>%{y}</b>"
                "<br>Taux de digitalisation : %{x:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=OBJECTIF_DIGITALISATION * 100,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.5,
    )

    fig.update_layout(
        height=max(
            330,
            len(agency) * 34
        ),

        margin=dict(
            l=10,
            r=45,
            t=15,
            b=15,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        xaxis=dict(
            ticksuffix="%",
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(
                size=9
            ),
        ),

        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# TABLEAU AGENCES
# ============================================================

def render_agency_table(df):

    agency = agency_performance(df)

    if agency.empty:

        st.info(
            "Aucune donnée agence disponible."
        )

        return

    agency = agency.head(12)

    html = """
    <div class="agency-table">

        <div class="agency-table-header">
            <div>Agence</div>
            <div>Digital</div>
            <div>Taux</div>
            <div>CP</div>
            <div>Initiatives</div>
        </div>
    """

    for _, row in agency.iterrows():

        taux = row["taux"]

        if pd.isna(taux):

            status_class = ""

        elif taux >= OBJECTIF_DIGITALISATION:

            status_class = "agency-good"

        elif taux >= OBJECTIF_DIGITALISATION * 0.8:

            status_class = "agency-warn"

        else:

            status_class = "agency-bad"

        html += f"""
        <div class="agency-table-row">

            <div class="agency-name">
                {row["Agence"]}
            </div>

            <div>
                {fmt_nombre(row["digital"])}
            </div>

            <div class="{status_class}">
                {fmt_pct(taux)}
            </div>

            <div>
                {fmt_nombre(row["cp"])}
            </div>

            <div>
                {fmt_nombre(row["initiatives"])}
            </div>

        </div>
        """

    html += "</div>"

    st.markdown(
        _html(html),
        unsafe_allow_html=True
    )


# ============================================================
# ANALYSE DÉCISIONNELLE
# ============================================================

def render_decision_analysis(df):

    agency = agency_performance(df)

    if agency.empty:
        return

    agency_valid = agency.dropna(
        subset=["taux"]
    ).copy()

    if agency_valid.empty:
        return

    meilleur = agency_valid.iloc[0]

    plus_cp = (
        agency_valid
        .sort_values(
            "cp",
            ascending=False
        )
        .iloc[0]
    )

    plus_initiatives = (
        agency_valid
        .sort_values(
            "initiatives",
            ascending=False
        )
        .iloc[0]
    )

    texte = (
        f"<b>{meilleur['Agence']}</b> présente "
        f"le meilleur taux de digitalisation "
        f"avec <b>{fmt_pct(meilleur['taux'])}</b>. "
        f"L'agence enregistrant le plus de "
        f"contre-performances est "
        f"<b>{plus_cp['Agence']}</b> "
        f"({fmt_nombre(plus_cp['cp'])} signalements). "
        f"L'agence ayant renseigné le plus "
        f"d'initiatives est "
        f"<b>{plus_initiatives['Agence']}</b> "
        f"({fmt_nombre(plus_initiatives['initiatives'])} actions)."
    )

    st.markdown(_html(f"""
        <div class="insight-card">

            <div class="insight-title">
                ANALYSE DÉCISIONNELLE
            </div>

            <div class="insight-text">
                {texte}
            </div>

        </div>
        """), unsafe_allow_html=True)


# ============================================================
# SCATTER DIGITALISATION × CP
# ============================================================

def chart_scatter(df):

    agency = agency_performance(df)

    if agency.empty:
        return

    agency = agency.dropna(
        subset=["taux"]
    ).copy()

    if agency.empty:
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=agency["taux"] * 100,
            y=agency["cp"],

            mode="markers",

            marker=dict(
                size=np.maximum(
                    12,
                    np.sqrt(
                        agency["total"].clip(
                            lower=1
                        )
                    ) * 1.8
                ),

                color=agency["initiatives"],

                colorscale=[
                    [0, "#31476B"],
                    [0.5, GOLD],
                    [1, CYAN],
                ],

                showscale=True,

                colorbar=dict(
                    title=dict(
                        text="Initiatives",
                        font=dict(
                        color=TEXT_SOFT,
                        size=12,
                    ),

                    ),
                    
                    tickfont=dict(
                        color=TEXT_SOFT,
                        size=10,
                    ),
                ),

                line=dict(
                    color="rgba(255,255,255,0.22)",
                    width=1,
                ),
            ),

            text=agency["Agence"],

            customdata=np.stack(
                [
                    agency["Agence"],
                    agency["total"],
                    agency["initiatives"],
                ],
                axis=-1
            ),

            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br>Taux digital : %{x:.1f}%"
                "<br>Contre-performances : %{y}"
                "<br>Prestations totales : %{customdata[1]:,.0f}"
                "<br>Initiatives : %{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=OBJECTIF_DIGITALISATION * 100,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.5,
    )

    fig.update_layout(
        height=410,

        margin=dict(
            l=10,
            r=10,
            t=15,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        xaxis=dict(
            title="Taux de digitalisation",
            ticksuffix="%",
            showgrid=True,
            gridcolor=GRID,
        ),

        yaxis=dict(
            title="Contre-performances signalées",
            showgrid=True,
            gridcolor=GRID,
        ),

        font=dict(
            family="Inter",
            color=TEXT_SOFT,
        ),

        hoverlabel=dict(
            bgcolor=NAVY_DARK,
            bordercolor=GOLD,
            font_color=WHITE,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def render(df: Optional[pd.DataFrame] = None):

    inject_digital_css()

    # ========================================================
    # RÉCUPÉRATION DATA
    # ========================================================

    data = get_digital_dataframe(df)

    if data is None:

        st.error(
            "Impossible de récupérer la base DIGITAL. "
            "Vérifie que l'ingestion Excel charge bien "
            "la feuille DIGITAL."
        )

        return

    data = prepare_dataframe(
        data
    )

    if data.empty:

        st.warning(
            "La base DIGITAL ne contient aucune donnée exploitable."
        )

        return

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(_html("""
        <div class="digital-hero">

            <div class="digital-title">
                DIGITAL
            </div>

            <div class="digital-subtitle">
                Pilotage de l'activité digitale
                et suivi de la performance des agences
            </div>

            <div class="digital-badge">
                ◈ PILOTAGE DIGITAL
            </div>

        </div>
        """), unsafe_allow_html=True)

    # ========================================================
    # FILTRES
    # ========================================================

    (
        granularite,
        annee,
        periode,
        agence,
    ) = render_filters(data)

    # ========================================================
    # DONNÉES FILTRÉES
    # ========================================================

    filtered = apply_filters(
        data,
        granularite,
        annee,
        periode,
        agence,
    )

    previous = get_previous_period_df(
        data,
        filtered,
        granularite,
        annee,
        periode,
        agence,
    )

    current_metrics = calculate_metrics(
        filtered
    )

    previous_metrics = calculate_metrics(
        previous
    )

    # ========================================================
    # CONTEXTE
    # ========================================================

    if periode == "Toutes les périodes":

        contexte = (
            f"{annee} · "
            f"{agence}"
        )

    else:

        contexte = (
            f"{periode} {annee} · "
            f"{agence}"
        )

    st.markdown(_html(f"""
        <div style="
            margin:
                0.2rem 0
                1rem;

            color:
                rgba(255,255,255,0.42);

            font-size:
                0.68rem;

            font-weight:
                700;

            letter-spacing:
                0.04em;
        ">
            FILTRE ACTIF · {contexte.upper()}
        </div>
        """), unsafe_allow_html=True)

    # ========================================================
    # KPI
    # ========================================================

    section(
        "INDICATEURS CLÉS"
    )

    v_digital = variation_pct(
        current_metrics["digital"],
        previous_metrics["digital"]
    )

    v_total = variation_pct(
        current_metrics["total"],
        previous_metrics["total"]
    )

    v_taux = variation_pct(
        current_metrics["taux"],
        previous_metrics["taux"]
    )

    v_cp = variation_pct(
        current_metrics["cp"],
        previous_metrics["cp"]
    )

    v_init = variation_pct(
        current_metrics["initiatives"],
        previous_metrics["initiatives"]
    )

    taux = current_metrics["taux"]

    if pd.isna(taux):

        taux_status = "neutral"

    elif taux >= OBJECTIF_DIGITALISATION:

        taux_status = "good"

    elif taux >= OBJECTIF_DIGITALISATION * 0.8:

        taux_status = "warn"

    else:

        taux_status = "bad"

    k1, k2, k3, k4, k5 = st.columns(
        5,
        gap="medium"
    )

    with k1:

        render_kpi(
            "📱",
            "Prestations digitales",
            fmt_nombre(
                current_metrics["digital"]
            ),
            v_digital,
            "neutral",
        )

    with k2:

        render_kpi(
            "📊",
            "Prestations totales",
            fmt_nombre(
                current_metrics["total"]
            ),
            v_total,
            "neutral",
        )

    with k3:

        render_kpi(
            "🎯",
            "Taux de digitalisation",
            fmt_pct(
                current_metrics["taux"]
            ),
            v_taux,
            taux_status,
            f"Objectif {fmt_pct(OBJECTIF_DIGITALISATION)}",
        )

    with k4:

        render_kpi(
            "⚠️",
            "Contre-performances",
            fmt_nombre(
                current_metrics["cp"]
            ),
            v_cp,
            "bad"
            if current_metrics["cp"] > 0
            else "good",
            "Commentaires renseignés",
        )

    with k5:

        render_kpi(
            "🚀",
            "Initiatives",
            fmt_nombre(
                current_metrics["initiatives"]
            ),
            v_init,
            "neutral",
            "Actions renseignées",
        )

    # ========================================================
    # NOTE MÉTHODOLOGIQUE
    # ========================================================

    st.markdown(_html(f"""
        <div style="
            margin-top:0.65rem;
            color:rgba(255,255,255,0.38);
            font-size:0.64rem;
        ">
            Le taux de digitalisation correspond au ratio
            des prestations digitales sur l'ensemble des
            prestations enregistrées.
            Les contre-performances et initiatives sont
            comptabilisées à partir des commentaires renseignés.
        </div>
        """), unsafe_allow_html=True)

    # ========================================================
    # ÉVOLUTION
    # ========================================================

    section(
        "ÉVOLUTION DE LA PERFORMANCE"
    )

    c1, c2 = st.columns(
        2,
        gap="large"
    )

    with c1:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Évolution du taux de digitalisation
                </div>

                <div class="digital-panel-subtitle">
                    Suivi de la pénétration du digital dans les prestations
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_evolution_taux(
            filtered
            if periode != "Toutes les périodes"
            else data[
                data["Année"] == annee
            ],
            granularite,
        )

    with c2:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Évolution des prestations
                </div>

                <div class="digital-panel-subtitle">
                    Comparaison du volume digital avec le volume total
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_evolution_volumes(
            filtered
            if periode != "Toutes les périodes"
            else data[
                data["Année"] == annee
            ],
            granularite,
        )

    # ========================================================
    # CONTRE-PERFORMANCES
    # ========================================================

    section(
        "CONTRE-PERFORMANCES — ANALYSE DES MOTIFS"
    )

    cp1, cp2 = st.columns(
        2,
        gap="large"
    )

    with cp1:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Motifs des contre-performances
                </div>

                <div class="digital-panel-subtitle">
                    Analyse des commentaires renseignés
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_contre_performances(
            filtered
        )

    with cp2:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Évolution des contre-performances
                </div>

                <div class="digital-panel-subtitle">
                    Nombre de signalements dans le temps
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_evolution_cp(
            filtered
            if periode != "Toutes les périodes"
            else data[
                data["Année"] == annee
            ],
            granularite,
        )

    # ========================================================
    # INITIATIVES
    # ========================================================

    section(
        "INITIATIVES — ACTIONS MENÉES"
    )

    i1, i2 = st.columns(
        2,
        gap="large"
    )

    with i1:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Répartition des initiatives
                </div>

                <div class="digital-panel-subtitle">
                    Actions renseignées dans la base
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_initiatives(
            filtered
        )

    with i2:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Évolution des initiatives
                </div>

                <div class="digital-panel-subtitle">
                    Dynamique des actions dans le temps
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_evolution_initiatives(
            filtered
            if periode != "Toutes les périodes"
            else data[
                data["Année"] == annee
            ],
            granularite,
        )

    # ========================================================
    # AGENCES
    # ========================================================

    section(
        "PERFORMANCE PAR AGENCE"
    )

    a1, a2 = st.columns(
        [1.45, 1],
        gap="large"
    )

    agency_data = agency_performance(
        filtered
    )

    with a1:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Taux de digitalisation par agence
                </div>

                <div class="digital-panel-subtitle">
                    Classement des agences selon leur performance
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_agences(
            filtered
        )

    with a2:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Tableau de pilotage
                </div>

                <div class="digital-panel-subtitle">
                    Principaux indicateurs par agence
                </div>

            </div>
            """), unsafe_allow_html=True)

        render_agency_table(
            filtered
        )

    # ========================================================
    # ANALYSE DÉCISIONNELLE
    # ========================================================

    section(
        "ANALYSE DÉCISIONNELLE"
    )

    d1, d2 = st.columns(
        [1.3, 1],
        gap="large"
    )

    with d1:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Digitalisation × contre-performances
                </div>

                <div class="digital-panel-subtitle">
                    Lecture croisée de la performance des agences
                </div>

            </div>
            """), unsafe_allow_html=True)

        chart_scatter(
            filtered
        )

    with d2:

        st.markdown(_html("""
            <div class="digital-panel">

                <div class="digital-panel-title">
                    Lecture managériale
                </div>

                <div class="digital-panel-subtitle">
                    Points d'attention issus des données
                </div>

            </div>
            """), unsafe_allow_html=True)

        render_decision_analysis(
            filtered
        )

    # ========================================================
    # RÉSUMÉ FINAL
    # ========================================================

    section(
        "SYNTHÈSE DE LA PÉRIODE"
    )

    taux = current_metrics["taux"]

    if pd.isna(taux):

        commentaire_taux = (
            "Le taux de digitalisation ne peut pas être calculé "
            "sur la période sélectionnée."
        )

    elif taux >= OBJECTIF_DIGITALISATION:

        commentaire_taux = (
            f"Le taux de digitalisation est de "
            f"<b>{fmt_pct(taux)}</b>, soit un niveau "
            f"au-dessus de l'objectif fixé à "
            f"<b>{fmt_pct(OBJECTIF_DIGITALISATION)}</b>."
        )

    else:

        commentaire_taux = (
            f"Le taux de digitalisation est de "
            f"<b>{fmt_pct(taux)}</b>, soit un niveau "
            f"inférieur à l'objectif de "
            f"<b>{fmt_pct(OBJECTIF_DIGITALISATION)}</b>. "
            f"Une attention particulière doit être portée "
            f"à l'adoption des parcours digitaux."
        )

    st.markdown(_html(f"""
        <div class="insight-card">

            <div class="insight-title">
                SYNTHÈSE
            </div>

            <div class="insight-text">

                {commentaire_taux}

                <br><br>

                La période compte
                <b>{fmt_nombre(current_metrics["digital"])}</b>
                prestations digitales sur
                <b>{fmt_nombre(current_metrics["total"])}</b>
                prestations au total.

                <br><br>

                <b>
                {fmt_nombre(current_metrics["cp"])}
                </b>
                contre-performances ont été
                signalées sous forme de commentaires,
                tandis que
                <b>
                {fmt_nombre(current_metrics["initiatives"])}
                </b>
                initiatives ont été renseignées.

            </div>

        </div>
        """), unsafe_allow_html=True)


# ============================================================
# ALIAS
# ============================================================

main = render
show = render
display = render


# ============================================================
# EXÉCUTION DIRECTE
# ============================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="NSIA — Digital",
        page_icon="📱",
        layout="wide",
    )

    render()