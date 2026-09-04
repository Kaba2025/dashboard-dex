# ============================================================
# NSIA ASSURANCE — EXPÉRIENCE CLIENT
# ONGLET PHYSIQUE
# ============================================================
#
# VERSION PILOTAGE — FRANÇAIS
#
# Structure :
#   Granularité → Année → Période → Agence
#
# Indicateurs :
#   - Clients reçus
#   - Taux de respect du délai d'attente
#   - Taux de prise en charge < 15 minutes
#   - Temps d'attente moyen
#   - Temps moyen de prise en charge
#   - Taux de parcours rapide
#   - Signalements liés à l'attente
#   - Signalements liés à la prise en charge
#   - Initiatives engagées
#
# Graphiques :
#   - Évolution des taux
#   - Évolution des délais
#   - Évolution de l'activité
#   - Motifs des contre-performances
#   - Évolution des contre-performances
#   - Répartition des initiatives
#   - Évolution des initiatives
#   - Classement des agences
#   - Matrice activité / performance
#
# IMPORTANT :
#   - Interface entièrement en français
#   - Variations en %
#   - Aucun "titlefont"
#   - Aucun colorbar Plotly fragile
#   - Compatible avec l'appel actuel de app.py :
#
#     physique.render(
#         df_sat,
#         freq,
#         df_recla,
#         rec_by_agency,
#         periode,
#         agence_filtre,
#         agences_toutes
#     )
#
# ============================================================

from __future__ import annotations

from typing import Optional, Any
import html
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


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
# OBJECTIFS
# ============================================================

OBJECTIF_RESPECT_DELAI = 0.80
OBJECTIF_MOINS_15 = 0.80

# Pour les temps, plus bas = meilleur.
OBJECTIF_ATTENTE_MINUTES = 15.0
OBJECTIF_PRISE_EN_CHARGE_MINUTES = 30.0


# ============================================================
# HTML
# ============================================================

def _html(s: str) -> str:
    """
    Nettoie l'indentation HTML avant envoi à Streamlit.

    Cela évite que Markdown transforme le HTML indenté
    en bloc de code visible.
    """
    return "\n".join(
        line.strip()
        for line in s.strip("\n").splitlines()
    )


# ============================================================
# FORMATTAGE
# ============================================================

def fmt_nombre(value: Any) -> str:
    try:
        if pd.isna(value):
            return "—"

        value = float(value)

        if abs(value - round(value)) < 1e-9:
            return f"{int(round(value)):,}".replace(",", " ")

        return f"{value:,.1f}".replace(",", " ")
    except Exception:
        return "—"


def fmt_pct(value: Any, decimals: int = 1) -> str:
    try:
        if pd.isna(value):
            return "—"

        return f"{float(value) * 100:.{decimals}f}%"
    except Exception:
        return "—"


def fmt_minutes(value: Any) -> str:
    try:
        if pd.isna(value):
            return "—"

        return f"{float(value):.1f} min"
    except Exception:
        return "—"


def fmt_variation(value: Any) -> str:
    """
    Variation absolue exprimée en pourcentage.
    """
    if value is None or pd.isna(value):
        return (
            '<span class="physique-variation neutral">'
            'Pas de comparaison disponible'
            '</span>'
        )

    try:
        value = float(value)
    except Exception:
        return (
            '<span class="physique-variation neutral">'
            'Pas de comparaison disponible'
            '</span>'
        )

    if abs(value) < 1e-9:
        return (
            '<span class="physique-variation neutral">'
            '→ 0,0%'
            '</span>'
        )

    if value > 0:
        return (
            f'<span class="physique-variation hausse">'
            f'▲ +{value * 100:.1f}%'
            f'</span>'
        )

    return (
        f'<span class="physique-variation baisse">'
        f'▼ {value * 100:.1f}%'
        f'</span>'
    )


def variation_pct(current: Any, previous: Any) -> Optional[float]:
    """
    Variation relative :
        (actuel - précédent) / précédent

    Retourne None si comparaison impossible.
    """
    try:
        if current is None or previous is None:
            return None

        if pd.isna(current) or pd.isna(previous):
            return None

        current = float(current)
        previous = float(previous)

        if abs(previous) < 1e-12:
            return None

        return (current - previous) / abs(previous)

    except Exception:
        return None


# ============================================================
# CSS
# ============================================================

def inject_physique_css():

    st.markdown(
        _html(
            """
            <style>

            .physique-page {
                width: 100%;
            }

            /* ==================================================
               EN-TÊTE
            ================================================== */

            .physique-hero {
                position: relative;
                overflow: hidden;
                padding: 1.55rem 1.8rem;
                margin-bottom: 1.2rem;
                border-radius: 22px;

                background:
                    linear-gradient(
                        135deg,
                        rgba(24,44,80,0.97),
                        rgba(10,22,40,0.97)
                    );

                border:
                    1px solid rgba(212,175,55,0.18);

                box-shadow:
                    0 12px 45px rgba(0,0,0,0.28);
            }

            .physique-hero::after {
                content: "";
                position: absolute;
                width: 260px;
                height: 260px;
                right: -90px;
                top: -120px;
                border-radius: 50%;
                background: rgba(212,175,55,0.055);
                pointer-events: none;
            }

            .physique-title {
                color: #FFFFFF;
                font-size: 1.55rem;
                font-weight: 900;
                letter-spacing: 0.03em;
                margin-bottom: 0.25rem;
            }

            .physique-subtitle {
                color: rgba(255,255,255,0.62);
                font-size: 0.86rem;
                line-height: 1.5;
                max-width: 700px;
            }

            .physique-badge {
                display: inline-block;
                margin-top: 0.8rem;
                padding: 0.38rem 0.72rem;
                border-radius: 999px;

                background: rgba(212,175,55,0.10);
                border: 1px solid rgba(212,175,55,0.20);

                color: #F5E6B8;
                font-size: 0.64rem;
                font-weight: 800;
                letter-spacing: 0.08em;
            }

            /* ==================================================
               FILTRES
            ================================================== */

            .physique-filter-title {
                margin-top: 0.3rem;
                margin-bottom: 0.45rem;

                color: rgba(255,255,255,0.45);
                font-size: 0.68rem;
                font-weight: 800;
                letter-spacing: 0.08em;
            }

            .physique-context {
                margin-top: 0.55rem;
                margin-bottom: 1rem;

                padding: 0.65rem 0.9rem;

                border-left:
                    3px solid #D4AF37;

                background:
                    rgba(212,175,55,0.055);

                color:
                    rgba(255,255,255,0.58);

                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.03em;
            }

            /* ==================================================
               SECTIONS
            ================================================== */

            .physique-section {
                display: flex;
                align-items: center;
                gap: 0.75rem;

                margin-top: 1.5rem;
                margin-bottom: 0.85rem;

                color: #FFFFFF;
                font-size: 0.73rem;
                font-weight: 900;
                letter-spacing: 0.08em;
            }

            .physique-section-line {
                flex: 1;
                height: 1px;

                background:
                    linear-gradient(
                        90deg,
                        rgba(212,175,55,0.32),
                        rgba(255,255,255,0.04)
                    );
            }

            /* ==================================================
               KPI
            ================================================== */

            .physique-kpi {
                min-height: 152px;

                padding: 1.05rem;

                border-radius: 18px;

                background:
                    linear-gradient(
                        145deg,
                        rgba(31,55,96,0.97),
                        rgba(20,38,68,0.97)
                    );

                border:
                    1px solid rgba(255,255,255,0.07);

                border-top:
                    2px solid rgba(212,175,55,0.72);

                box-shadow:
                    0 10px 30px rgba(0,0,0,0.18);
            }

            .physique-kpi-icon {
                width: 38px;
                height: 38px;

                display: flex;
                align-items: center;
                justify-content: center;

                margin-bottom: 0.75rem;

                border-radius: 11px;

                background:
                    rgba(255,255,255,0.08);

                border:
                    1px solid rgba(255,255,255,0.08);

                font-size: 1.05rem;
            }

            .physique-kpi-label {
                color:
                    rgba(255,255,255,0.48);

                font-size:
                    0.63rem;

                font-weight:
                    800;

                letter-spacing:
                    0.055em;

                text-transform:
                    uppercase;

                min-height: 28px;
            }

            .physique-kpi-value {
                margin-top: 0.1rem;

                font-size:
                    1.55rem;

                line-height:
                    1.15;

                font-weight:
                    900;
            }

            .physique-kpi-value.good {
                color: #22C55E;
            }

            .physique-kpi-value.warn {
                color: #F59E0B;
            }

            .physique-kpi-value.bad {
                color: #EF4444;
            }

            .physique-kpi-value.neutral {
                color: #FFFFFF;
            }

            .physique-kpi-sub {
                margin-top: 0.48rem;

                color:
                    rgba(255,255,255,0.42);

                font-size:
                    0.62rem;

                line-height:
                    1.35;
            }

            .physique-variation {
                font-weight: 800;
            }

            .physique-variation.hausse {
                color: #F59E0B;
            }

            .physique-variation.baisse {
                color: #EF4444;
            }

            .physique-variation.neutral {
                color: rgba(255,255,255,0.38);
            }

            /* ==================================================
               PANNEAUX
            ================================================== */

            .physique-panel {
                padding: 1rem 1.1rem 0.55rem 1.1rem;

                border-radius: 18px;

                background:
                    linear-gradient(
                        145deg,
                        rgba(24,44,80,0.78),
                        rgba(13,29,53,0.74)
                    );

                border:
                    1px solid rgba(255,255,255,0.06);

                box-shadow:
                    0 8px 28px rgba(0,0,0,0.12);
            }

            .physique-panel-title {
                color: #FFFFFF;
                font-size: 0.86rem;
                font-weight: 850;
            }

            .physique-panel-subtitle {
                margin-top: 0.2rem;
                margin-bottom: 0.55rem;

                color:
                    rgba(255,255,255,0.42);

                font-size:
                    0.65rem;
            }

            /* ==================================================
               ALERTES
            ================================================== */

            .physique-alert-card {
                padding: 1rem;

                border-radius: 16px;

                background:
                    rgba(239,68,68,0.055);

                border:
                    1px solid rgba(239,68,68,0.15);

                border-left:
                    3px solid rgba(239,68,68,0.75);
            }

            .physique-action-card {
                padding: 1rem;

                border-radius: 16px;

                background:
                    rgba(212,175,55,0.045);

                border:
                    1px solid rgba(212,175,55,0.13);

                border-left:
                    3px solid rgba(212,175,55,0.75);
            }

            .physique-mini-title {
                color:
                    rgba(255,255,255,0.52);

                font-size:
                    0.62rem;

                font-weight:
                    800;

                letter-spacing:
                    0.06em;

                text-transform:
                    uppercase;
            }

            .physique-mini-value {
                color:
                    #FFFFFF;

                font-size:
                    1.45rem;

                font-weight:
                    900;

                margin-top:
                    0.2rem;
            }

            /* ==================================================
               TABLEAU AGENCES
            ================================================== */

            .physique-table {
                width: 100%;
                overflow: hidden;

                border-radius: 16px;

                border:
                    1px solid rgba(255,255,255,0.06);

                background:
                    rgba(10,22,40,0.55);
            }

            .physique-table-row {
                display: grid;

                grid-template-columns:
                    2.25fr
                    0.9fr
                    0.9fr
                    0.9fr
                    0.95fr
                    0.95fr
                    0.75fr
                    0.85fr;

                gap: 0.4rem;

                align-items: center;

                padding:
                    0.68rem 0.75rem;

                border-bottom:
                    1px solid rgba(255,255,255,0.045);

                color:
                    rgba(255,255,255,0.70);

                font-size:
                    0.62rem;
            }

            .physique-table-row.header {
                background:
                    rgba(255,255,255,0.035);

                color:
                    rgba(255,255,255,0.43);

                font-size:
                    0.57rem;

                font-weight:
                    900;

                text-transform:
                    uppercase;

                letter-spacing:
                    0.035em;
            }

            .physique-table-row:last-child {
                border-bottom: none;
            }

            .physique-agence {
                color: #FFFFFF;
                font-weight: 750;
            }

            .physique-good {
                color: #22C55E;
                font-weight: 850;
            }

            .physique-warn {
                color: #F59E0B;
                font-weight: 850;
            }

            .physique-bad {
                color: #EF4444;
                font-weight: 850;
            }

            /* ==================================================
               MATRICE
            ================================================== */

            .physique-matrix {
                padding:
                    1rem;

                border-radius:
                    16px;

                background:
                    rgba(255,255,255,0.025);

                border:
                    1px solid rgba(255,255,255,0.06);
            }

            .physique-matrix-title {
                color: #FFFFFF;
                font-weight: 850;
                font-size: 0.78rem;
                margin-bottom: 0.5rem;
            }

            /* ==================================================
               ANALYSE
            ================================================== */

            .physique-insight {
                padding:
                    1.15rem;

                border-radius:
                    18px;

                background:
                    linear-gradient(
                        135deg,
                        rgba(212,175,55,0.075),
                        rgba(255,255,255,0.025)
                    );

                border:
                    1px solid rgba(212,175,55,0.14);
            }

            .physique-insight-title {
                color:
                    #F5E6B8;

                font-size:
                    0.69rem;

                font-weight:
                    900;

                letter-spacing:
                    0.08em;

                margin-bottom:
                    0.6rem;
            }

            .physique-insight-text {
                color:
                    rgba(255,255,255,0.67);

                font-size:
                    0.76rem;

                line-height:
                    1.65;
            }

            /* ==================================================
               RESPONSIVE
            ================================================== */

            @media (max-width: 1100px) {
                .physique-table-row {
                    grid-template-columns:
                        2fr
                        0.8fr
                        0.8fr
                        0.8fr
                        0.9fr
                        0.9fr
                        0.7fr
                        0.8fr;
                }
            }

            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# RECHERCHE DU DATAFRAME PHYSIQUE
# ============================================================

COLONNES_PHYSIQUES = {
    "Date",
    "Agence",
    "Clients reçus",
    "Clients ON TIME",
    "Temps d'attente",
    "Temps de prise en charge",
}


def _is_physique_dataframe(obj: Any) -> bool:

    if not isinstance(obj, pd.DataFrame):
        return False

    return COLONNES_PHYSIQUES.issubset(
        set(obj.columns)
    )


def _find_dataframe(obj: Any) -> Optional[pd.DataFrame]:

    if isinstance(obj, pd.DataFrame):

        if _is_physique_dataframe(obj):
            return obj

        return None

    if isinstance(obj, dict):

        # Priorité aux clés explicites.
        for key, value in obj.items():

            key_text = str(key).lower()

            if any(
                terme in key_text
                for terme in [
                    "physique",
                    "base physique",
                    "df_physique",
                    "reception",
                ]
            ):

                found = _find_dataframe(value)

                if found is not None:
                    return found

        # Recherche générale.
        for value in obj.values():

            found = _find_dataframe(value)

            if found is not None:
                return found

    elif isinstance(obj, (list, tuple)):

        for value in obj:

            found = _find_dataframe(value)

            if found is not None:
                return found

    return None


def get_physique_dataframe(
    *objects,
) -> Optional[pd.DataFrame]:

    # 1. Objets passés directement.
    for obj in objects:

        found = _find_dataframe(obj)

        if found is not None:
            return found.copy()

    # 2. Session Streamlit.
    for _, value in st.session_state.items():

        found = _find_dataframe(value)

        if found is not None:
            return found.copy()

    # 3. Base DEX centrale.
    try:

        from ingestion_dex import get_dex_data

        datasets = get_dex_data()

        found = _find_dataframe(datasets)

        if found is not None:
            return found.copy()

    except Exception:
        pass

    return None


# ============================================================
# NORMALISATION
# ============================================================

def prepare_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    # --------------------------------------------------------
    # Colonnes manquantes
    # --------------------------------------------------------

    numeric_columns = [
        "Temps de présence",
        "Clients ON TIME",
        "Clients reçus",
        "Temps d'attente",
        "Temps de prise en charge",
        "Nombre de clients attendus en moins de 15 minutes",
        "Nombre de clients pris en charge en moins de 15 minutes",
    ]

    text_columns = [
        "TIME OK",
        "CP ATTENTE",
        "INITIATIVE ATTENTE",
        "CP PRISE EN CHARGE",
        "INITIATIVE PRISE EN CHARGE",
        "QUICK",
        "Agence",
    ]

    for col in numeric_columns:

        if col not in df.columns:
            df[col] = 0

    for col in text_columns:

        if col not in df.columns:
            df[col] = ""

    if "Date" not in df.columns:
        df["Date"] = pd.NaT

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce",
    )

    df = df.dropna(
        subset=["Date"]
    ).copy()

    # --------------------------------------------------------
    # Numériques
    # --------------------------------------------------------

    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        ).fillna(0)

        df[col] = df[col].clip(
            lower=0
        )

    # --------------------------------------------------------
    # Textes
    # --------------------------------------------------------

    for col in text_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------
    # Année
    # --------------------------------------------------------

    df["Année"] = (
        df["Date"]
        .dt.year
        .astype(int)
    )

    # --------------------------------------------------------
    # Mois numérique
    # --------------------------------------------------------

    df["Mois numérique"] = (
        df["Date"]
        .dt.month
    )

    # --------------------------------------------------------
    # Nettoyage des doublons exacts
    # --------------------------------------------------------

    df = df.drop_duplicates().copy()

    return df


# ============================================================
# PÉRIODES
# ============================================================

MOIS_FR = {
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
}


def get_period_options(
    df: pd.DataFrame,
    granularite: str,
    annee: int,
):

    temp = df[
        df["Année"] == annee
    ].copy()

    if temp.empty:
        return ["Toutes les périodes"]

    if granularite == "Mensuelle":

        mois = sorted(
            temp["Mois numérique"]
            .dropna()
            .astype(int)
            .unique()
        )

        return (
            ["Toutes les périodes"]
            + [
                MOIS_FR[m]
                for m in mois
            ]
        )

    if granularite == "Hebdomadaire":

        semaines = sorted(
            temp["Date"]
            .dt.isocalendar()
            .week
            .dropna()
            .astype(int)
            .unique()
        )

        return (
            ["Toutes les périodes"]
            + [
                f"Semaine {s:02d}"
                for s in semaines
            ]
        )

    if granularite == "Trimestrielle":

        trimestres = sorted(
            temp["Date"]
            .dt.quarter
            .dropna()
            .astype(int)
            .unique()
        )

        return (
            ["Toutes les périodes"]
            + [
                f"Trimestre {q}"
                for q in trimestres
            ]
        )

    dates = sorted(
        temp["Date"]
        .dt.normalize()
        .dropna()
        .unique()
    )

    return (
        ["Toutes les périodes"]
        + [
            pd.Timestamp(d).strftime("%d/%m/%Y")
            for d in dates
        ]
    )


def filter_period(
    df: pd.DataFrame,
    granularite: str,
    annee: int,
    periode: str,
    agence: str,
) -> pd.DataFrame:

    temp = df[
        df["Année"] == annee
    ].copy()

    if periode != "Toutes les périodes":

        if granularite == "Mensuelle":

            mois_num = {
                nom: numero
                for numero, nom in MOIS_FR.items()
            }

            mois = mois_num.get(
                periode
            )

            if mois is not None:
                temp = temp[
                    temp["Mois numérique"] == mois
                ]

        elif granularite == "Hebdomadaire":

            try:
                semaine = int(
                    periode.replace(
                        "Semaine ",
                        "",
                    )
                )

                temp = temp[
                    temp["Date"]
                    .dt.isocalendar()
                    .week
                    == semaine
                ]

            except Exception:
                pass

        elif granularite == "Trimestrielle":

            try:
                trimestre = int(
                    periode.replace(
                        "Trimestre ",
                        "",
                    )
                )

                temp = temp[
                    temp["Date"]
                    .dt.quarter
                    == trimestre
                ]

            except Exception:
                pass

        else:

            date_value = pd.to_datetime(
                periode,
                dayfirst=True,
                errors="coerce",
            )

            if not pd.isna(date_value):

                temp = temp[
                    temp["Date"].dt.normalize()
                    == date_value.normalize()
                ]

    if agence != "Toutes les agences":

        temp = temp[
            temp["Agence"] == agence
        ]

    return temp


# ============================================================
# PÉRIODE PRÉCÉDENTE
# ============================================================

def previous_period_dataframe(
    df: pd.DataFrame,
    granularite: str,
    annee: int,
    periode: str,
    agence: str,
) -> pd.DataFrame:

    # Aucun choix précis = comparaison annuelle impossible
    # si l'année précédente n'existe pas.
    if periode == "Toutes les périodes":

        previous_year = annee - 1

        temp = df[
            df["Année"] == previous_year
        ].copy()

        if agence != "Toutes les agences":
            temp = temp[
                temp["Agence"] == agence
            ]

        return temp

    if granularite == "Mensuelle":

        mois_num = {
            nom: numero
            for numero, nom in MOIS_FR.items()
        }

        mois = mois_num.get(
            periode
        )

        if mois is None:
            return pd.DataFrame()

        current = pd.Period(
            f"{annee}-{mois:02d}",
            freq="M",
        )

        previous = current - 1

        temp = df[
            df["Date"].dt.to_period("M")
            == previous
        ].copy()

    elif granularite == "Hebdomadaire":

        try:
            semaine = int(
                periode.replace(
                    "Semaine ",
                    "",
                )
            )
        except Exception:
            return pd.DataFrame()

        # ISO : création de la période depuis année + semaine.
        try:
            current_start = pd.Timestamp.fromisocalendar(
                annee,
                semaine,
                1,
            )

            previous_start = (
                current_start
                - pd.Timedelta(days=7)
            )

            previous_end = (
                previous_start
                + pd.Timedelta(days=6)
            )

            temp = df[
                (df["Date"] >= previous_start)
                &
                (df["Date"] <= previous_end)
            ].copy()

        except Exception:
            return pd.DataFrame()

    elif granularite == "Trimestrielle":

        try:
            trimestre = int(
                periode.replace(
                    "Trimestre ",
                    "",
                )
            )

            current = pd.Period(
                f"{annee}Q{trimestre}",
                freq="Q",
            )

            previous = current - 1

            temp = df[
                df["Date"].dt.to_period("Q")
                == previous
            ].copy()

        except Exception:
            return pd.DataFrame()

    else:

        date_value = pd.to_datetime(
            periode,
            dayfirst=True,
            errors="coerce",
        )

        if pd.isna(date_value):
            return pd.DataFrame()

        previous_date = (
            date_value
            - pd.Timedelta(days=1)
        )

        temp = df[
            df["Date"].dt.normalize()
            == previous_date.normalize()
        ].copy()

    if agence != "Toutes les agences":

        temp = temp[
            temp["Agence"] == agence
        ]

    return temp


# ============================================================
# CALCUL DES INDICATEURS
# ============================================================

def calculate_metrics(
    df: pd.DataFrame,
) -> dict:

    if df.empty:

        return {
            "clients": 0,
            "clients_ontime": 0,
            "taux_ontime": np.nan,
            "attendus_15": 0,
            "pris_15": 0,
            "taux_moins_15": np.nan,
            "temps_attente": np.nan,
            "temps_prise": np.nan,
            "taux_rapide": np.nan,
            "cp_attente": 0,
            "cp_prise": 0,
            "cp_total": 0,
            "init_attente": 0,
            "init_prise": 0,
            "init_total": 0,
            "temps_presence": np.nan,
            "taux_time_ok": np.nan,
        }

    clients = df[
        "Clients reçus"
    ].sum()

    clients_ontime = df[
        "Clients ON TIME"
    ].sum()

    attendus_15 = df[
        "Nombre de clients attendus en moins de 15 minutes"
    ].sum()

    pris_15 = df[
        "Nombre de clients pris en charge en moins de 15 minutes"
    ].sum()

    # --------------------------------------------------------
    # Taux de respect du délai d'attente
    # --------------------------------------------------------

    taux_ontime = (
        clients_ontime / clients
        if clients > 0
        else np.nan
    )

    # --------------------------------------------------------
    # Taux de prise en charge <15 min
    #
    # On utilise les clients reçus comme dénominateur.
    # Cela garantit un taux borné à 100 % et évite les
    # incohérences présentes dans certaines lignes sources
    # où "pris <15" peut dépasser "attendus <15".
    # --------------------------------------------------------

    taux_moins_15 = (
        pris_15 / clients
        if clients > 0
        else np.nan
    )

    # --------------------------------------------------------
    # Moyennes pondérées par le volume de clients
    # --------------------------------------------------------

    if clients > 0:

        temps_attente = (
            (
                df["Temps d'attente"]
                * df["Clients reçus"]
            ).sum()
            / clients
        )

        temps_prise = (
            (
                df["Temps de prise en charge"]
                * df["Clients reçus"]
            ).sum()
            / clients
        )

    else:

        temps_attente = np.nan
        temps_prise = np.nan

    # --------------------------------------------------------
    # Parcours rapide
    # --------------------------------------------------------

    quick = (
        df["QUICK"]
        .str.lower()
        .eq("oui")
        .sum()
    )

    taux_rapide = (
        quick / len(df)
        if len(df) > 0
        else np.nan
    )

    # --------------------------------------------------------
    # Contre-performances
    # --------------------------------------------------------

    cp_attente = (
        df["CP ATTENTE"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    cp_prise = (
        df["CP PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    cp_total = (
        cp_attente
        + cp_prise
    )

    # --------------------------------------------------------
    # Initiatives
    # --------------------------------------------------------

    init_attente = (
        df["INITIATIVE ATTENTE"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    init_prise = (
        df["INITIATIVE PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .sum()
    )

    init_total = (
        init_attente
        + init_prise
    )

    # --------------------------------------------------------
    # Temps de présence
    # --------------------------------------------------------

    temps_presence = (
        df["Temps de présence"]
        .mean()
        if not df.empty
        else np.nan
    )

    # --------------------------------------------------------
    # TIME OK
    # --------------------------------------------------------

    taux_time_ok = (
        df["TIME OK"]
        .str.lower()
        .eq("oui")
        .mean()
        if not df.empty
        else np.nan
    )

    return {
        "clients": clients,
        "clients_ontime": clients_ontime,
        "taux_ontime": taux_ontime,
        "attendus_15": attendus_15,
        "pris_15": pris_15,
        "taux_moins_15": taux_moins_15,
        "temps_attente": temps_attente,
        "temps_prise": temps_prise,
        "taux_rapide": taux_rapide,
        "cp_attente": cp_attente,
        "cp_prise": cp_prise,
        "cp_total": cp_total,
        "init_attente": init_attente,
        "init_prise": init_prise,
        "init_total": init_total,
        "temps_presence": temps_presence,
        "taux_time_ok": taux_time_ok,
    }


# ============================================================
# STATUT DES KPI
# ============================================================

def status_taux(
    value: float,
    objectif: float,
) -> str:

    if value is None or pd.isna(value):
        return "neutral"

    if value >= objectif:
        return "good"

    if value >= objectif * 0.90:
        return "warn"

    return "bad"


def status_temps(
    value: float,
    objectif: float,
) -> str:

    if value is None or pd.isna(value):
        return "neutral"

    if value <= objectif:
        return "good"

    if value <= objectif * 1.15:
        return "warn"

    return "bad"


# ============================================================
# KPI
# ============================================================

def render_kpi(
    icon: str,
    label: str,
    value: str,
    variation: Optional[float] = None,
    status: str = "neutral",
    subtitle: str = "",
):

    variation_text = fmt_variation(
        variation
    )

    st.markdown(
        _html(
            f"""
            <div class="physique-kpi">

                <div class="physique-kpi-icon">
                    {icon}
                </div>

                <div class="physique-kpi-label">
                    {html.escape(label)}
                </div>

                <div class="physique-kpi-value {status}">
                    {value}
                </div>

                <div class="physique-kpi-sub">
                    {variation_text}
                    {" · " + html.escape(subtitle) if subtitle else ""}
                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# SECTION
# ============================================================

def section(title: str):

    st.markdown(
        _html(
            f"""
            <div class="physique-section">
                <span>{html.escape(title)}</span>
                <span class="physique-section-line"></span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# PANNEAU TITRE
# ============================================================

def panel_header(
    title: str,
    subtitle: str,
):

    st.markdown(
        _html(
            f"""
            <div class="physique-panel">

                <div class="physique-panel-title">
                    {html.escape(title)}
                </div>

                <div class="physique-panel-subtitle">
                    {html.escape(subtitle)}
                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# GRAPHIQUE COMMUN
# ============================================================

def base_layout(
    fig: go.Figure,
    height: int = 330,
):

    fig.update_layout(
        height=height,

        margin=dict(
            l=12,
            r=18,
            t=18,
            b=10,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter, Arial",
            color=TEXT_SOFT,
            size=11,
        ),

        xaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            linecolor="rgba(255,255,255,0.08)",
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            linecolor="rgba(255,255,255,0.08)",
        ),

        hoverlabel=dict(
            bgcolor=NAVY_DARK,
            bordercolor=GOLD,
            font_color=WHITE,
        ),

        showlegend=True,

        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                color=TEXT_SOFT,
                size=10,
            ),
        ),
    )

    return fig


def show_chart(fig):

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# ============================================================
# PRÉPARATION DES PÉRIODES POUR LES GRAPHIQUES
# ============================================================

def add_period_column(
    df: pd.DataFrame,
    granularite: str,
) -> pd.DataFrame:

    temp = df.copy()

    if temp.empty:
        return temp

    if granularite == "Mensuelle":

        temp["Période graphique"] = (
            temp["Date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

    elif granularite == "Hebdomadaire":

        temp["Période graphique"] = (
            temp["Date"]
            .dt.to_period("W-MON")
            .apply(lambda p: p.start_time)
        )

    elif granularite == "Trimestrielle":

        temp["Période graphique"] = (
            temp["Date"]
            .dt.to_period("Q")
            .dt.to_timestamp()
        )

    else:

        temp["Période graphique"] = (
            temp["Date"]
            .dt.normalize()
        )

    return temp


# ============================================================
# ÉVOLUTION DES TAUX
# ============================================================

def chart_evolution_taux(
    df: pd.DataFrame,
    granularite: str,
):

    if df.empty:
        st.info(
            "Aucune donnée disponible pour afficher l'évolution."
        )
        return

    temp = add_period_column(
        df,
        granularite,
    )

    grouped = (
        temp
        .groupby(
            "Période graphique",
            as_index=False,
        )
        .agg(
            clients=(
                "Clients reçus",
                "sum",
            ),
            clients_ontime=(
                "Clients ON TIME",
                "sum",
            ),
            pris_15=(
                "Nombre de clients pris en charge en moins de 15 minutes",
                "sum",
            ),
        )
        .sort_values(
            "Période graphique"
        )
    )

    grouped["taux_ontime"] = np.where(
        grouped["clients"] > 0,
        grouped["clients_ontime"]
        / grouped["clients"],
        np.nan,
    )

    grouped["taux_moins_15"] = np.where(
        grouped["clients"] > 0,
        grouped["pris_15"]
        / grouped["clients"],
        np.nan,
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["taux_ontime"] * 100,
            mode="lines+markers",
            name="Respect du délai",
            line=dict(
                color=BLUE,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Respect du délai : %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["taux_moins_15"] * 100,
            mode="lines+markers",
            name="Prise en charge < 15 min",
            line=dict(
                color=CYAN,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Prise en charge < 15 min : %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=OBJECTIF_RESPECT_DELAI * 100,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.4,
        annotation_text="Objectif respect du délai",
        annotation_position="top left",
    )

    fig.add_hline(
        y=OBJECTIF_MOINS_15 * 100,
        line_dash="dot",
        line_color=GREEN,
        line_width=1.3,
        annotation_text="Objectif < 15 min",
        annotation_position="bottom left",
    )

    fig.update_yaxes(
        ticksuffix="%",
        rangemode="tozero",
        title="Taux",
    )

    fig.update_xaxes(
        title="Période",
    )

    fig = base_layout(
        fig,
        height=350,
    )

    show_chart(fig)


# ============================================================
# ÉVOLUTION DES DÉLAIS
# ============================================================

def chart_evolution_delais(
    df: pd.DataFrame,
    granularite: str,
):

    if df.empty:
        return

    temp = add_period_column(
        df,
        granularite,
    )

    # Moyennes pondérées par le volume de clients.
    temp["_poids_attente"] = (
        temp["Temps d'attente"]
        * temp["Clients reçus"]
    )

    temp["_poids_prise"] = (
        temp["Temps de prise en charge"]
        * temp["Clients reçus"]
    )

    grouped = (
        temp
        .groupby(
            "Période graphique",
            as_index=False,
        )
        .agg(
            clients=(
                "Clients reçus",
                "sum",
            ),
            poids_attente=(
                "_poids_attente",
                "sum",
            ),
            poids_prise=(
                "_poids_prise",
                "sum",
            ),
        )
        .sort_values(
            "Période graphique"
        )
    )

    grouped["attente"] = np.where(
        grouped["clients"] > 0,
        grouped["poids_attente"]
        / grouped["clients"],
        np.nan,
    )

    grouped["prise"] = np.where(
        grouped["clients"] > 0,
        grouped["poids_prise"]
        / grouped["clients"],
        np.nan,
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["attente"],
            mode="lines+markers",
            name="Temps d'attente",
            line=dict(
                color=AMBER,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Temps d'attente : %{y:.1f} min"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["prise"],
            mode="lines+markers",
            name="Temps de prise en charge",
            line=dict(
                color=PINK,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Temps de prise en charge : %{y:.1f} min"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=OBJECTIF_ATTENTE_MINUTES,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.3,
        annotation_text="Repère attente : 15 min",
    )

    fig.update_yaxes(
        title="Minutes",
        rangemode="tozero",
    )

    fig.update_xaxes(
        title="Période",
    )

    fig = base_layout(
        fig,
        height=350,
    )

    show_chart(fig)


# ============================================================
# ÉVOLUTION DE L'ACTIVITÉ
# ============================================================

def chart_evolution_activite(
    df: pd.DataFrame,
    granularite: str,
):

    if df.empty:
        return

    temp = add_period_column(
        df,
        granularite,
    )

    grouped = (
        temp
        .groupby(
            "Période graphique",
            as_index=False,
        )
        .agg(
            clients=(
                "Clients reçus",
                "sum",
            ),
            clients_ontime=(
                "Clients ON TIME",
                "sum",
            ),
        )
        .sort_values(
            "Période graphique"
        )
    )

    grouped["taux"] = np.where(
        grouped["clients"] > 0,
        grouped["clients_ontime"]
        / grouped["clients"],
        np.nan,
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=grouped["Période graphique"],
            y=grouped["clients"],
            name="Clients reçus",
            marker=dict(
                color="rgba(76,141,255,0.70)",
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Clients reçus : %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["taux"] * 100,
            mode="lines+markers",
            name="Respect du délai",
            yaxis="y2",
            line=dict(
                color=GOLD,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Respect du délai : %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        yaxis=dict(
            title="Clients",
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
        ),

        yaxis2=dict(
            title="Respect du délai",
            overlaying="y",
            side="right",
            ticksuffix="%",
            showgrid=False,
            range=[0, 100],
        ),
    )

    fig = base_layout(
        fig,
        height=350,
    )

    show_chart(fig)


# ============================================================
# CONTRE-PERFORMANCES — MOTIFS
# ============================================================

def chart_motifs_cp(
    df: pd.DataFrame,
):

    if df.empty:
        return

    attente = (
        df["CP ATTENTE"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .rename_axis("Motif")
        .reset_index(
            name="Nombre"
        )
    )

    prise = (
        df["CP PRISE EN CHARGE"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .rename_axis("Motif")
        .reset_index(
            name="Nombre"
        )
    )

    motifs = pd.concat(
        [
            attente.assign(
                Type="Attente"
            ),
            prise.assign(
                Type="Prise en charge"
            ),
        ],
        ignore_index=True,
    )

    if motifs.empty:

        st.info(
            "Aucun signalement renseigné sur la période sélectionnée."
        )

        return

    motifs["Libellé"] = (
        motifs["Type"]
        + " — "
        + motifs["Motif"]
    )

    motifs = motifs.sort_values(
        "Nombre",
        ascending=True,
    )

    fig = go.Figure()

    for type_cp, couleur in [
        ("Attente", RED),
        ("Prise en charge", PINK),
    ]:

        subset = motifs[
            motifs["Type"] == type_cp
        ]

        if subset.empty:
            continue

        fig.add_trace(
            go.Bar(
                x=subset["Nombre"],
                y=subset["Motif"],
                orientation="h",
                name=type_cp,
                marker=dict(
                    color=couleur,
                    opacity=0.82,
                ),
                text=subset["Nombre"],
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b>"
                    f"<br>{type_cp} : "
                    "%{x}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_xaxes(
        title="Nombre de signalements",
        rangemode="tozero",
    )

    fig.update_yaxes(
        title="Motif",
    )

    fig = base_layout(
        fig,
        height=max(
            320,
            len(motifs) * 52,
        ),
    )

    show_chart(fig)


# ============================================================
# ÉVOLUTION DES CONTRE-PERFORMANCES
# ============================================================

def chart_evolution_cp(
    df: pd.DataFrame,
    granularite: str,
):

    if df.empty:
        return

    temp = add_period_column(
        df,
        granularite,
    )

    temp["CP attente"] = (
        temp["CP ATTENTE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    temp["CP prise"] = (
        temp["CP PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    grouped = (
        temp
        .groupby(
            "Période graphique",
            as_index=False,
        )
        .agg(
            attente=(
                "CP attente",
                "sum",
            ),
            prise=(
                "CP prise",
                "sum",
            ),
        )
        .sort_values(
            "Période graphique"
        )
    )

    grouped["total"] = (
        grouped["attente"]
        + grouped["prise"]
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["attente"],
            mode="lines+markers",
            name="Signalements d'attente",
            line=dict(
                color=RED,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Attente : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["prise"],
            mode="lines+markers",
            name="Signalements de prise en charge",
            line=dict(
                color=PINK,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Prise en charge : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["total"],
            mode="lines",
            name="Total des signalements",
            line=dict(
                color=GOLD,
                width=2,
                dash="dot",
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Total : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_yaxes(
        title="Nombre de signalements",
        rangemode="tozero",
    )

    fig = base_layout(
        fig,
        height=350,
    )

    show_chart(fig)


# ============================================================
# INITIATIVES
# ============================================================

def chart_initiatives(
    df: pd.DataFrame,
):

    if df.empty:
        return

    attente = (
        df["INITIATIVE ATTENTE"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .rename_axis("Initiative")
        .reset_index(
            name="Nombre"
        )
    )

    prise = (
        df["INITIATIVE PRISE EN CHARGE"]
        .replace("", np.nan)
        .dropna()
        .value_counts()
        .rename_axis("Initiative")
        .reset_index(
            name="Nombre"
        )
    )

    initiatives = pd.concat(
        [
            attente.assign(
                Type="Attente"
            ),
            prise.assign(
                Type="Prise en charge"
            ),
        ],
        ignore_index=True,
    )

    if initiatives.empty:

        st.info(
            "Aucune initiative renseignée sur la période sélectionnée."
        )

        return

    initiatives = initiatives.sort_values(
        "Nombre",
        ascending=True,
    )

    fig = go.Figure()

    for type_init, couleur in [
        ("Attente", GOLD),
        ("Prise en charge", CYAN),
    ]:

        subset = initiatives[
            initiatives["Type"] == type_init
        ]

        if subset.empty:
            continue

        fig.add_trace(
            go.Bar(
                x=subset["Nombre"],
                y=subset["Initiative"],
                orientation="h",
                name=type_init,
                marker=dict(
                    color=couleur,
                    opacity=0.84,
                ),
                text=subset["Nombre"],
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b>"
                    f"<br>{type_init} : "
                    "%{x}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_xaxes(
        title="Nombre d'actions",
        rangemode="tozero",
    )

    fig.update_yaxes(
        title="Initiative",
    )

    fig = base_layout(
        fig,
        height=max(
            320,
            len(initiatives) * 52,
        ),
    )

    show_chart(fig)


# ============================================================
# ÉVOLUTION DES INITIATIVES
# ============================================================

def chart_evolution_initiatives(
    df: pd.DataFrame,
    granularite: str,
):

    if df.empty:
        return

    temp = add_period_column(
        df,
        granularite,
    )

    temp["Initiative attente"] = (
        temp["INITIATIVE ATTENTE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    temp["Initiative prise"] = (
        temp["INITIATIVE PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    grouped = (
        temp
        .groupby(
            "Période graphique",
            as_index=False,
        )
        .agg(
            attente=(
                "Initiative attente",
                "sum",
            ),
            prise=(
                "Initiative prise",
                "sum",
            ),
        )
        .sort_values(
            "Période graphique"
        )
    )

    grouped["total"] = (
        grouped["attente"]
        + grouped["prise"]
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["attente"],
            mode="lines+markers",
            name="Actions liées à l'attente",
            line=dict(
                color=GOLD,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Actions attente : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["prise"],
            mode="lines+markers",
            name="Actions liées à la prise en charge",
            line=dict(
                color=CYAN,
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Actions prise en charge : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["Période graphique"],
            y=grouped["total"],
            mode="lines",
            name="Total des actions",
            line=dict(
                color=WHITE,
                width=2,
                dash="dot",
            ),
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b>"
                "<br>Total actions : %{y}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_yaxes(
        title="Nombre d'actions",
        rangemode="tozero",
    )

    fig = base_layout(
        fig,
        height=350,
    )

    show_chart(fig)


# ============================================================
# PERFORMANCE PAR AGENCE
# ============================================================

def agency_performance(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    temp = df.copy()

    temp["_cp_att"] = (
        temp["CP ATTENTE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    temp["_cp_prise"] = (
        temp["CP PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    temp["_init_att"] = (
        temp["INITIATIVE ATTENTE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    temp["_init_prise"] = (
        temp["INITIATIVE PRISE EN CHARGE"]
        .replace("", np.nan)
        .notna()
        .astype(int)
    )

    grouped = (
        temp
        .groupby(
            "Agence",
            as_index=False,
        )
        .agg(
            clients=(
                "Clients reçus",
                "sum",
            ),
            clients_ontime=(
                "Clients ON TIME",
                "sum",
            ),
            pris_15=(
                "Nombre de clients pris en charge en moins de 15 minutes",
                "sum",
            ),
            attente_ponderee=(
                "Temps d'attente",
                lambda s: 0,
            ),
            prise_ponderee=(
                "Temps de prise en charge",
                lambda s: 0,
            ),
            cp_attente=(
                "_cp_att",
                "sum",
            ),
            cp_prise=(
                "_cp_prise",
                "sum",
            ),
            init_attente=(
                "_init_att",
                "sum",
            ),
            init_prise=(
                "_init_prise",
                "sum",
            ),
        )
    )

    # Recalcul des moyennes pondérées agence.
    attente_weighted = (
        temp.assign(
            _poids_attente=
            temp["Temps d'attente"]
            * temp["Clients reçus"]
        )
        .groupby("Agence")["_poids_attente"]
        .sum()
    )

    prise_weighted = (
        temp.assign(
            _poids_prise=
            temp["Temps de prise en charge"]
            * temp["Clients reçus"]
        )
        .groupby("Agence")["_poids_prise"]
        .sum()
    )

    grouped["temps_attente"] = (
        grouped["Agence"]
        .map(attente_weighted)
        / grouped["clients"].replace(
            0,
            np.nan,
        )
    )

    grouped["temps_prise"] = (
        grouped["Agence"]
        .map(prise_weighted)
        / grouped["clients"].replace(
            0,
            np.nan,
        )
    )

    grouped["taux_ontime"] = np.where(
        grouped["clients"] > 0,
        grouped["clients_ontime"]
        / grouped["clients"],
        np.nan,
    )

    grouped["taux_moins_15"] = np.where(
        grouped["clients"] > 0,
        grouped["pris_15"]
        / grouped["clients"],
        np.nan,
    )

    grouped["cp_total"] = (
        grouped["cp_attente"]
        + grouped["cp_prise"]
    )

    grouped["init_total"] = (
        grouped["init_attente"]
        + grouped["init_prise"]
    )

    grouped["intensite_actions"] = np.where(
        grouped["cp_total"] > 0,
        grouped["init_total"]
        / grouped["cp_total"],
        np.nan,
    )

    return grouped.sort_values(
        "taux_ontime",
        ascending=False,
    ).reset_index(
        drop=True
    )


# ============================================================
# GRAPHIQUE AGENCES
# ============================================================

def chart_agences(
    df: pd.DataFrame,
):

    agency = agency_performance(
        df
    )

    if agency.empty:
        return

    agency = agency.dropna(
        subset=["taux_ontime"]
    )

    if agency.empty:
        return

    # On limite l'affichage à 15 agences
    # pour garder une lecture propre.
    agency = agency.head(
        15
    ).sort_values(
        "taux_ontime",
        ascending=True,
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=agency["taux_ontime"] * 100,
            y=agency["Agence"],
            orientation="h",
            marker=dict(
                color=[
                    GREEN
                    if value >= OBJECTIF_RESPECT_DELAI * 100
                    else AMBER
                    if value >= OBJECTIF_RESPECT_DELAI * 90
                    else RED
                    for value in agency["taux_ontime"] * 100
                ],
                opacity=0.86,
            ),
            text=[
                f"{v:.1f}%"
                for v in agency["taux_ontime"] * 100
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>Respect du délai : %{x:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=OBJECTIF_RESPECT_DELAI * 100,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.5,
    )

    fig.update_xaxes(
        title="Taux de respect du délai",
        ticksuffix="%",
        range=[
            0,
            max(
                100,
                float(
                    agency["taux_ontime"].max()
                    * 100
                ) + 8,
            ),
        ],
    )

    fig.update_yaxes(
        title="Agence",
    )

    fig = base_layout(
        fig,
        height=max(
            360,
            len(agency) * 42,
        ),
    )

    fig.update_layout(
        showlegend=False
    )

    show_chart(fig)


# ============================================================
# MATRICE ACTIVITÉ × PERFORMANCE
# ============================================================

def chart_matrice_agences(
    df: pd.DataFrame,
):

    agency = agency_performance(
        df
    )

    if agency.empty:
        return

    agency = agency.dropna(
        subset=[
            "taux_ontime",
            "clients",
        ]
    ).copy()

    if agency.empty:
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=agency["clients"],
            y=agency["taux_ontime"] * 100,
            mode="markers+text",
            text=agency["Agence"].str.replace(
                "NSIA VIE ASSURANCE ",
                "",
                regex=False,
            ),
            textposition="top center",

            marker=dict(
                size=np.maximum(
                    12,
                    np.sqrt(
                        agency["clients"]
                        .clip(lower=1)
                    ) / 2.3,
                ),
                color=agency["cp_total"],
                colorscale=[
                    [0, "#22C55E"],
                    [0.5, "#F59E0B"],
                    [1, "#EF4444"],
                ],
                showscale=False,
                line=dict(
                    color="rgba(255,255,255,0.22)",
                    width=1,
                ),
            ),

            customdata=np.stack(
                [
                    agency["Agence"],
                    agency["clients"],
                    agency["cp_total"],
                    agency["init_total"],
                ],
                axis=-1,
            ),

            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br>Clients reçus : %{customdata[1]:,.0f}"
                "<br>Respect du délai : %{y:.1f}%"
                "<br>Signalements : %{customdata[2]}"
                "<br>Actions : %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=OBJECTIF_RESPECT_DELAI * 100,
        line_dash="dash",
        line_color=GOLD,
        line_width=1.5,
    )

    fig.update_xaxes(
        title="Volume de clients reçus",
        rangemode="tozero",
    )

    fig.update_yaxes(
        title="Respect du délai",
        ticksuffix="%",
        range=[
            0,
            100,
        ],
    )

    fig = base_layout(
        fig,
        height=410,
    )

    fig.update_layout(
        showlegend=False
    )

    show_chart(fig)


# ============================================================
# TABLEAU AGENCES
# ============================================================

def render_agency_table(
    df: pd.DataFrame,
):

    agency = agency_performance(
        df
    )

    if agency.empty:

        st.info(
            "Aucune agence disponible pour la période sélectionnée."
        )

        return

    # --------------------------------------------------------
    # En-tête
    # --------------------------------------------------------

    html_table = """
    <div class="physique-table">

        <div class="physique-table-row header">
            <div>Agence</div>
            <div>Clients</div>
            <div>Délai</div>
            <div>&lt; 15 min</div>
            <div>Attente</div>
            <div>Prise en charge</div>
            <div>Signalements</div>
            <div>Actions</div>
        </div>
    """

    for _, row in agency.iterrows():

        taux = row["taux_ontime"]

        if pd.isna(taux):
            taux_class = "physique-warn"
        elif taux >= OBJECTIF_RESPECT_DELAI:
            taux_class = "physique-good"
        elif taux >= OBJECTIF_RESPECT_DELAI * 0.90:
            taux_class = "physique-warn"
        else:
            taux_class = "physique-bad"

        html_table += f"""
        <div class="physique-table-row">

            <div class="physique-agence">
                {html.escape(str(row["Agence"]))}
            </div>

            <div>
                {fmt_nombre(row["clients"])}
            </div>

            <div class="{taux_class}">
                {fmt_pct(row["taux_ontime"])}
            </div>

            <div>
                {fmt_pct(row["taux_moins_15"])}
            </div>

            <div>
                {fmt_minutes(row["temps_attente"])}
            </div>

            <div>
                {fmt_minutes(row["temps_prise"])}
            </div>

            <div class="physique-bad">
                {fmt_nombre(row["cp_total"])}
            </div>

            <div class="physique-good">
                {fmt_nombre(row["init_total"])}
            </div>

        </div>
        """

    html_table += "</div>"

    st.markdown(
        _html(html_table),
        unsafe_allow_html=True,
    )


# ============================================================
# TOP AGENCES
# ============================================================

def render_top_agences(
    df: pd.DataFrame,
):

    agency = agency_performance(
        df
    )

    if agency.empty:
        return

    agency = agency.dropna(
        subset=["taux_ontime"]
    ).copy()

    if agency.empty:
        return

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    # --------------------------------------------------------
    # TOP PERFORMANCES
    # --------------------------------------------------------

    with col1:

        top = agency.sort_values(
            [
                "taux_ontime",
                "clients",
            ],
            ascending=[
                False,
                False,
            ],
        ).head(3)

        html_block = """
        <div class="physique-action-card">
            <div class="physique-mini-title">
                TOP 3 — MEILLEURES PERFORMANCES
            </div>
        """

        for i, (_, row) in enumerate(
            top.iterrows(),
            start=1,
        ):

            html_block += f"""
            <div style="
                margin-top:0.7rem;
                color:#FFFFFF;
                font-size:0.72rem;
            ">
                <b>{i}. {html.escape(str(row["Agence"]))}</b>
                <br>
                <span style="
                    color:#22C55E;
                    font-weight:800;
                ">
                    {fmt_pct(row["taux_ontime"])}
                </span>
                <span style="
                    color:rgba(255,255,255,0.40);
                ">
                    · {fmt_nombre(row["clients"])} clients
                </span>
            </div>
            """

        html_block += "</div>"

        st.markdown(
            _html(html_block),
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # À SURVEILLER
    # --------------------------------------------------------

    with col2:

        # Score de vigilance :
        # faible respect du délai + volume important
        agency["score_vigilance"] = (
            (1 - agency["taux_ontime"].fillna(0))
            * np.log1p(
                agency["clients"].clip(lower=0)
            )
        )

        top = agency.sort_values(
            "score_vigilance",
            ascending=False,
        ).head(3)

        html_block = """
        <div class="physique-alert-card">
            <div class="physique-mini-title">
                TOP 3 — AGENCES À SURVEILLER
            </div>
        """

        for i, (_, row) in enumerate(
            top.iterrows(),
            start=1,
        ):

            html_block += f"""
            <div style="
                margin-top:0.7rem;
                color:#FFFFFF;
                font-size:0.72rem;
            ">
                <b>{i}. {html.escape(str(row["Agence"]))}</b>
                <br>
                <span style="
                    color:#EF4444;
                    font-weight:800;
                ">
                    {fmt_pct(row["taux_ontime"])}
                </span>
                <span style="
                    color:rgba(255,255,255,0.40);
                ">
                    · {fmt_nombre(row["cp_total"])} signalements
                </span>
            </div>
            """

        html_block += "</div>"

        st.markdown(
            _html(html_block),
            unsafe_allow_html=True,
        )


# ============================================================
# ANALYSE DÉCISIONNELLE
# ============================================================

def render_decision_analysis(
    current: dict,
    previous: dict,
    agency: pd.DataFrame,
):

    # --------------------------------------------------------
    # Evolution du respect du délai
    # --------------------------------------------------------

    v_ontime = variation_pct(
        current["taux_ontime"],
        previous["taux_ontime"],
    )

    v_attente = variation_pct(
        current["temps_attente"],
        previous["temps_attente"],
    )

    v_cp = variation_pct(
        current["cp_total"],
        previous["cp_total"],
    )

    # --------------------------------------------------------
    # Meilleure agence
    # --------------------------------------------------------

    meilleure = None
    plus_cp = None
    plus_init = None

    if not agency.empty:

        valid = agency.dropna(
            subset=["taux_ontime"]
        )

        if not valid.empty:

            meilleure = valid.sort_values(
                "taux_ontime",
                ascending=False,
            ).iloc[0]

            plus_cp = valid.sort_values(
                "cp_total",
                ascending=False,
            ).iloc[0]

            plus_init = valid.sort_values(
                "init_total",
                ascending=False,
            ).iloc[0]

    # --------------------------------------------------------
    # Texte
    # --------------------------------------------------------

    paragraphs = []

    if not pd.isna(
        current["taux_ontime"]
    ):

        if current["taux_ontime"] >= OBJECTIF_RESPECT_DELAI:

            paragraphs.append(
                f"Le taux de respect du délai atteint "
                f"<b>{fmt_pct(current['taux_ontime'])}</b>, "
                f"au-dessus de l'objectif de "
                f"<b>{fmt_pct(OBJECTIF_RESPECT_DELAI)}</b>."
            )

        else:

            paragraphs.append(
                f"Le taux de respect du délai est de "
                f"<b>{fmt_pct(current['taux_ontime'])}</b>, "
                f"inférieur à l'objectif de "
                f"<b>{fmt_pct(OBJECTIF_RESPECT_DELAI)}</b>. "
                f"Une vigilance est nécessaire sur la fluidité "
                f"de l'accueil."
            )

    if not pd.isna(
        current["temps_attente"]
    ):

        if current["temps_attente"] > OBJECTIF_ATTENTE_MINUTES:

            paragraphs.append(
                f"Le temps d'attente moyen atteint "
                f"<b>{fmt_minutes(current['temps_attente'])}</b>. "
                f"Le niveau dépasse le repère de "
                f"<b>{OBJECTIF_ATTENTE_MINUTES:.0f} minutes</b>."
            )

        else:

            paragraphs.append(
                f"Le temps d'attente moyen est contenu à "
                f"<b>{fmt_minutes(current['temps_attente'])}</b>."
            )

    if current["cp_total"] > 0:

        paragraphs.append(
            f"<b>{fmt_nombre(current['cp_total'])}</b> "
            f"signalements ont été renseignés, dont "
            f"<b>{fmt_nombre(current['cp_attente'])}</b> "
            f"liés à l'attente et "
            f"<b>{fmt_nombre(current['cp_prise'])}</b> "
            f"liés à la prise en charge."
        )

    if current["init_total"] > 0:

        paragraphs.append(
            f"<b>{fmt_nombre(current['init_total'])}</b> "
            f"actions ont été renseignées sur la période."
        )

    if meilleure is not None:

        paragraphs.append(
            f"L'agence présentant le meilleur taux de respect "
            f"du délai est "
            f"<b>{html.escape(str(meilleure['Agence']))}</b> "
            f"avec <b>{fmt_pct(meilleure['taux_ontime'])}</b>."
        )

    if plus_cp is not None:

        paragraphs.append(
            f"L'agence comptabilisant le plus de signalements "
            f"est <b>{html.escape(str(plus_cp['Agence']))}</b> "
            f"avec <b>{fmt_nombre(plus_cp['cp_total'])}</b> "
            f"signalements."
        )

    if plus_init is not None:

        paragraphs.append(
            f"L'agence ayant engagé le plus d'actions est "
            f"<b>{html.escape(str(plus_init['Agence']))}</b> "
            f"avec <b>{fmt_nombre(plus_init['init_total'])}</b> "
            f"actions renseignées."
        )

    texte = "<br><br>".join(
        paragraphs
    )

    if not texte:

        texte = (
            "Les données disponibles ne permettent pas "
            "de produire une analyse décisionnelle."
        )

    st.markdown(
        _html(
            f"""
            <div class="physique-insight">

                <div class="physique-insight-title">
                    ANALYSE DÉCISIONNELLE
                </div>

                <div class="physique-insight-text">
                    {texte}
                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# SYNTHÈSE
# ============================================================

def render_summary(
    metrics: dict,
    previous: dict,
):

    v_clients = variation_pct(
        metrics["clients"],
        previous["clients"],
    )

    v_ontime = variation_pct(
        metrics["taux_ontime"],
        previous["taux_ontime"],
    )

    v_attente = variation_pct(
        metrics["temps_attente"],
        previous["temps_attente"],
    )

    v_cp = variation_pct(
        metrics["cp_total"],
        previous["cp_total"],
    )

    phrases = []

    # Activité
    phrases.append(
        f"La période compte "
        f"<b>{fmt_nombre(metrics['clients'])}</b> "
        f"clients reçus."
    )

    # Respect délai
    if not pd.isna(
        metrics["taux_ontime"]
    ):

        phrases.append(
            f"Le taux de respect du délai est de "
            f"<b>{fmt_pct(metrics['taux_ontime'])}</b>."
        )

    # Délais
    if not pd.isna(
        metrics["temps_attente"]
    ):

        phrases.append(
            f"Le temps d'attente moyen est de "
            f"<b>{fmt_minutes(metrics['temps_attente'])}</b> "
            f"et le temps moyen de prise en charge est de "
            f"<b>{fmt_minutes(metrics['temps_prise'])}</b>."
        )

    # Signalements
    phrases.append(
        f"<b>{fmt_nombre(metrics['cp_total'])}</b> "
        f"signalements ont été renseignés."
    )

    # Actions
    phrases.append(
        f"<b>{fmt_nombre(metrics['init_total'])}</b> "
        f"actions ont été renseignées."
    )

    # Variation
    variations = []

    if v_clients is not None:
        variations.append(
            f"activité : {v_clients * 100:+.1f}%"
        )

    if v_ontime is not None:
        variations.append(
            f"respect du délai : {v_ontime * 100:+.1f}%"
        )

    if v_attente is not None:
        variations.append(
            f"temps d'attente : {v_attente * 100:+.1f}%"
        )

    if v_cp is not None:
        variations.append(
            f"signalements : {v_cp * 100:+.1f}%"
        )

    if variations:

        phrases.append(
            "Évolution par rapport à la période précédente : "
            + " · ".join(variations)
            + "."
        )

    texte = " ".join(
        phrases
    )

    st.markdown(
        _html(
            f"""
            <div class="physique-insight">

                <div class="physique-insight-title">
                    SYNTHÈSE DE LA PÉRIODE
                </div>

                <div class="physique-insight-text">
                    {texte}
                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def render(
    *args,
    **kwargs,
):

    inject_physique_css()

    # ========================================================
    # DONNÉES
    # ========================================================

    data = get_physique_dataframe(
        *args
    )

    if data is None or data.empty:

        st.warning(
            "Aucune donnée de la base PHYSIQUE n'est disponible. "
            "Vérifiez que la base DEX contenant la feuille PHYSIQUE "
            "est bien chargée."
        )

        return

    data = prepare_dataframe(
        data
    )

    if data.empty:

        st.warning(
            "La base PHYSIQUE ne contient aucune donnée exploitable."
        )

        return

    # ========================================================
    # PAGE
    # ========================================================

    st.markdown(
        _html(
            """
            <div class="physique-page">

                <div class="physique-hero">

                    <div class="physique-title">
                        RÉCEPTION PHYSIQUE
                    </div>

                    <div class="physique-subtitle">
                        Pilotage de l'accueil physique,
                        des délais d'attente et de la qualité
                        de prise en charge des clients.
                    </div>

                    <div class="physique-badge">
                        ◈ PILOTAGE DE L'ACCUEIL PHYSIQUE
                    </div>

                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # PARAMÈTRES
    # ========================================================

    st.markdown(
        _html(
            """
            <div class="physique-filter-title">
                PARAMÈTRES D'ANALYSE
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(
        4,
        gap="medium",
    )

    # --------------------------------------------------------
    # GRANULARITÉ
    # --------------------------------------------------------

    with col1:

        granularite = st.selectbox(
            "Granularité",
            [
                "Mensuelle",
                "Hebdomadaire",
                "Trimestrielle",
                "Journalière",
            ],
            key="physique_granularite",
        )

    # --------------------------------------------------------
    # ANNÉE
    # --------------------------------------------------------

    annees = sorted(
        data["Année"]
        .dropna()
        .astype(int)
        .unique(),
        reverse=True,
    )

    with col2:

        annee = st.selectbox(
            "Année",
            annees,
            key="physique_annee",
        )

    # --------------------------------------------------------
    # PÉRIODE
    # --------------------------------------------------------

    periodes = get_period_options(
        data,
        granularite,
        int(annee),
    )

    with col3:

        periode = st.selectbox(
            "Période",
            periodes,
            key="physique_periode",
        )

    # --------------------------------------------------------
    # AGENCE
    # --------------------------------------------------------

    agences = sorted(
        data["Agence"]
        .dropna()
        .astype(str)
        .unique()
    )

    agences = [
        a
        for a in agences
        if a.strip()
    ]

    agences_options = [
        "Toutes les agences"
    ] + agences

    with col4:

        agence = st.selectbox(
            "Agence",
            agences_options,
            key="physique_agence",
        )

    # ========================================================
    # DONNÉES FILTRÉES
    # ========================================================

    filtered = filter_period(
        data,
        granularite,
        int(annee),
        periode,
        agence,
    )

    previous = previous_period_dataframe(
        data,
        granularite,
        int(annee),
        periode,
        agence,
    )

    current_metrics = calculate_metrics(
        filtered
    )

    previous_metrics = calculate_metrics(
        previous
    )

    contexte = (
        f"{granularite} · "
        f"{annee} · "
        f"{periode} · "
        f"{agence}"
    )

    st.markdown(
        _html(
            f"""
            <div class="physique-context">
                FILTRE ACTIF · {html.escape(contexte.upper())}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # SI AUCUNE DONNÉE
    # ========================================================

    if filtered.empty:

        st.info(
            "Aucune donnée disponible pour les filtres sélectionnés."
        )

        return

    # ========================================================
    # KPI
    # ========================================================

    section(
        "INDICATEURS CLÉS"
    )

    v_clients = variation_pct(
        current_metrics["clients"],
        previous_metrics["clients"],
    )

    v_ontime = variation_pct(
        current_metrics["taux_ontime"],
        previous_metrics["taux_ontime"],
    )

    v_moins_15 = variation_pct(
        current_metrics["taux_moins_15"],
        previous_metrics["taux_moins_15"],
    )

    v_attente = variation_pct(
        current_metrics["temps_attente"],
        previous_metrics["temps_attente"],
    )

    v_prise = variation_pct(
        current_metrics["temps_prise"],
        previous_metrics["temps_prise"],
    )

    v_rapide = variation_pct(
        current_metrics["taux_rapide"],
        previous_metrics["taux_rapide"],
    )

    v_cp = variation_pct(
        current_metrics["cp_total"],
        previous_metrics["cp_total"],
    )

    v_init = variation_pct(
        current_metrics["init_total"],
        previous_metrics["init_total"],
    )

    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )

    with k1:

        render_kpi(
            "👥",
            "Clients reçus",
            fmt_nombre(
                current_metrics["clients"]
            ),
            v_clients,
            "neutral",
        )

    with k2:

        render_kpi(
            "⏱️",
            "Respect du délai d'attente",
            fmt_pct(
                current_metrics["taux_ontime"]
            ),
            v_ontime,
            status_taux(
                current_metrics["taux_ontime"],
                OBJECTIF_RESPECT_DELAI,
            ),
            "Objectif 80%",
        )

    with k3:

        render_kpi(
            "🟢",
            "Prise en charge < 15 min",
            fmt_pct(
                current_metrics["taux_moins_15"]
            ),
            v_moins_15,
            status_taux(
                current_metrics["taux_moins_15"],
                OBJECTIF_MOINS_15,
            ),
            "Objectif 80%",
        )

    with k4:

        render_kpi(
            "⌛",
            "Temps d'attente moyen",
            fmt_minutes(
                current_metrics["temps_attente"]
            ),
            v_attente,
            status_temps(
                current_metrics["temps_attente"],
                OBJECTIF_ATTENTE_MINUTES,
            ),
            "Repère 15 min",
        )

    k5, k6, k7, k8 = st.columns(
        4,
        gap="medium",
    )

    with k5:

        render_kpi(
            "🤝",
            "Temps moyen de prise en charge",
            fmt_minutes(
                current_metrics["temps_prise"]
            ),
            v_prise,
            status_temps(
                current_metrics["temps_prise"],
                OBJECTIF_PRISE_EN_CHARGE_MINUTES,
            ),
            "Repère 30 min",
        )

    with k6:

        render_kpi(
            "⚡",
            "Taux de parcours rapide",
            fmt_pct(
                current_metrics["taux_rapide"]
            ),
            v_rapide,
            "neutral",
            "Parcours identifié comme rapide",
        )

    with k7:

        render_kpi(
            "⚠️",
            "Signalements",
            fmt_nombre(
                current_metrics["cp_total"]
            ),
            v_cp,
            "bad"
            if current_metrics["cp_total"] > 0
            else "good",
            (
                f"{fmt_nombre(current_metrics['cp_attente'])} attente"
                f" · "
                f"{fmt_nombre(current_metrics['cp_prise'])} prise en charge"
            ),
        )

    with k8:

        render_kpi(
            "🚀",
            "Actions engagées",
            fmt_nombre(
                current_metrics["init_total"]
            ),
            v_init,
            "neutral",
            (
                f"{fmt_nombre(current_metrics['init_attente'])} attente"
                f" · "
                f"{fmt_nombre(current_metrics['init_prise'])} prise en charge"
            ),
        )

    # ========================================================
    # ÉVOLUTION
    # ========================================================

    section(
        "ÉVOLUTION DE LA PERFORMANCE"
    )

    # Pour afficher l'évolution, on utilise toute l'année
    # sélectionnée, tout en conservant l'agence.
    evolution_data = data[
        data["Année"] == int(annee)
    ].copy()

    if agence != "Toutes les agences":

        evolution_data = evolution_data[
            evolution_data["Agence"] == agence
        ]

    c1, c2 = st.columns(
        2,
        gap="large",
    )

    with c1:

        panel_header(
            "Évolution des indicateurs de qualité",
            "Suivi du respect du délai et de la prise en charge en moins de 15 minutes",
        )

        chart_evolution_taux(
            evolution_data,
            granularite,
        )

    with c2:

        panel_header(
            "Évolution des délais",
            "Temps d'attente et temps moyen de prise en charge",
        )

        chart_evolution_delais(
            evolution_data,
            granularite,
        )

    c3, c4 = st.columns(
        2,
        gap="large",
    )

    with c3:

        panel_header(
            "Évolution de l'activité",
            "Volume de clients reçus et niveau de respect du délai",
        )

        chart_evolution_activite(
            evolution_data,
            granularite,
        )

    with c4:

        # Carte de lecture rapide.
        st.markdown(
            _html(
                f"""
                <div class="physique-panel">

                    <div class="physique-panel-title">
                        Lecture de la période
                    </div>

                    <div class="physique-panel-subtitle">
                        Comparaison avec la période précédente
                    </div>

                    <div style="
                        display:grid;
                        grid-template-columns:1fr 1fr;
                        gap:0.7rem;
                        margin-top:0.7rem;
                    ">

                        <div class="physique-action-card">
                            <div class="physique-mini-title">
                                Activité
                            </div>
                            <div class="physique-mini-value">
                                {fmt_nombre(current_metrics["clients"])}
                            </div>
                            <div style="
                                margin-top:0.25rem;
                                font-size:0.62rem;
                            ">
                                {fmt_variation(v_clients)}
                            </div>
                        </div>

                        <div class="physique-action-card">
                            <div class="physique-mini-title">
                                Respect du délai
                            </div>
                            <div class="physique-mini-value">
                                {fmt_pct(current_metrics["taux_ontime"])}
                            </div>
                            <div style="
                                margin-top:0.25rem;
                                font-size:0.62rem;
                            ">
                                {fmt_variation(v_ontime)}
                            </div>
                        </div>

                        <div class="physique-alert-card">
                            <div class="physique-mini-title">
                                Temps d'attente
                            </div>
                            <div class="physique-mini-value">
                                {fmt_minutes(current_metrics["temps_attente"])}
                            </div>
                            <div style="
                                margin-top:0.25rem;
                                font-size:0.62rem;
                            ">
                                {fmt_variation(v_attente)}
                            </div>
                        </div>

                        <div class="physique-alert-card">
                            <div class="physique-mini-title">
                                Signalements
                            </div>
                            <div class="physique-mini-value">
                                {fmt_nombre(current_metrics["cp_total"])}
                            </div>
                            <div style="
                                margin-top:0.25rem;
                                font-size:0.62rem;
                            ">
                                {fmt_variation(v_cp)}
                            </div>
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # CONTRE-PERFORMANCES
    # ========================================================

    section(
        "CONTRE-PERFORMANCES — ANALYSE DES MOTIFS"
    )

    cp1, cp2 = st.columns(
        2,
        gap="large",
    )

    with cp1:

        panel_header(
            "Motifs des signalements",
            "Analyse des problèmes liés à l'attente et à la prise en charge",
        )

        chart_motifs_cp(
            filtered
        )

    with cp2:

        panel_header(
            "Évolution des signalements",
            "Dynamique des difficultés rencontrées au cours de l'année",
        )

        chart_evolution_cp(
            evolution_data,
            granularite,
        )

    # ========================================================
    # ACTIONS
    # ========================================================

    section(
        "ACTIONS ENGAGÉES"
    )

    a1, a2 = st.columns(
        2,
        gap="large",
    )

    with a1:

        panel_header(
            "Répartition des actions",
            "Actions renseignées pour améliorer l'accueil",
        )

        chart_initiatives(
            filtered
        )

    with a2:

        panel_header(
            "Évolution des actions",
            "Dynamique des initiatives engagées",
        )

        chart_evolution_initiatives(
            evolution_data,
            granularite,
        )

    # ========================================================
    # AGENCES
    # ========================================================

    section(
        "PERFORMANCE PAR AGENCE"
    )

    agency_data = agency_performance(
        filtered
    )

    ag1, ag2 = st.columns(
        [1.25, 1],
        gap="large",
    )

    with ag1:

        panel_header(
            "Classement des agences",
            "Taux de respect du délai par agence",
        )

        chart_agences(
            filtered
        )

    with ag2:

        panel_header(
            "Activité et performance",
            "Lecture croisée du volume de clients et de la qualité de service",
        )

        chart_matrice_agences(
            filtered
        )

    # ========================================================
    # TABLEAU
    # ========================================================

    panel_header(
        "Tableau de pilotage",
        "Principaux indicateurs opérationnels par agence",
    )

    render_agency_table(
        filtered
    )

    # ========================================================
    # TOP AGENCES
    # ========================================================

    render_top_agences(
        filtered
    )

    # ========================================================
    # ANALYSE DÉCISIONNELLE
    # ========================================================

    section(
        "ANALYSE DÉCISIONNELLE"
    )

    render_decision_analysis(
        current_metrics,
        previous_metrics,
        agency_data,
    )

    # ========================================================
    # SYNTHÈSE
    # ========================================================

    section(
        "SYNTHÈSE DE PILOTAGE"
    )

    render_summary(
        current_metrics,
        previous_metrics,
    )

    # ========================================================
    # DONNÉES SOURCES
    # ========================================================

    with st.expander(
        "Voir les données sources de la période"
    ):

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )