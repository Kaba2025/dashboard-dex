from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from periods import (
    GRANULARITES,
    Periode,
    filtrer_periode,
    periode_depuis_date,
    periode_precedente,
)

from kpi_dex import (
    digital_kpis,
    physique_kpis,
    satisfaction_kpis,
    reclamation_kpis,
    callcenter_kpis,
)

from kpi_extra import satisfaction_globale_officielle

from settings import (
    get_csat_barometre,
    set_csat_barometre,
)

from theme import (
    kpi_card,
    section,
)


# ============================================================
# COULEURS
# ============================================================

COULEURS = {
    "bleu": "#3B82F6",
    "or": "#D4AF37",
    "vert": "#22C55E",
    "rouge": "#EF4444",
    "violet": "#8B5CF6",
    "cyan": "#06B6D4",
    "rose": "#EC4899",
    "ambre": "#F59E0B",
}


# ============================================================
# OUTILS GÉNÉRAUX
# ============================================================

def _normaliser_date_colonnes(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df is None or df.empty:
        return df

    out = df.copy()

    for col in [
        "Date",
        "Date_parsed",
        "Date_reception",
        "Date2",
    ]:

        if col in out.columns:

            out[col] = pd.to_datetime(
                out[col],
                dayfirst=True,
                errors="coerce",
            ).dt.normalize()

    if (
        "Date" not in out.columns
        and "Date2" in out.columns
    ):

        out["Date"] = out["Date2"]

    return out


def _num(
    df: pd.DataFrame,
    column: str,
) -> float:

    if (
        df is None
        or df.empty
        or column not in df.columns
    ):
        return 0.0

    return float(
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


def _mean(
    df: pd.DataFrame,
    column: str,
) -> float | None:

    if (
        df is None
        or df.empty
        or column not in df.columns
    ):
        return None

    valeurs = (
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .dropna()
    )

    if valeurs.empty:
        return None

    return float(valeurs.mean())


def _count_text(
    df: pd.DataFrame,
    column: str,
) -> int | None:

    if (
        df is None
        or df.empty
        or column not in df.columns
    ):
        return None

    valeurs = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    valeurs = valeurs[
        (valeurs != "")
        & (valeurs.str.lower() != "nan")
    ]

    return int(len(valeurs))


def _pct(
    numerateur: float,
    denominateur: float,
) -> float | None:

    if denominateur == 0:
        return None

    return (
        numerateur
        / denominateur
        * 100.0
    )


def _format_valeur(
    valeur,
    unite: str,
) -> str:

    if (
        valeur is None
        or pd.isna(valeur)
    ):
        return "—"

    valeur = float(valeur)

    if unite == "%":
        return f"{valeur:.1f}%"

    if unite == "min":
        return f"{valeur:.2f} min"

    if unite == "FCFA":
        return (
            f"{valeur:,.0f} FCFA"
            .replace(",", " ")
        )

    if unite:
        return (
            f"{valeur:,.0f} {unite}"
            .replace(",", " ")
        )

    return (
        f"{valeur:,.0f}"
        .replace(",", " ")
    )


# ============================================================
# VARIATION
# ============================================================

def _variation_relative(
    actuel,
    precedent,
) -> tuple[str, str]:

    """
    Variation toujours exprimée en pourcentage
    par rapport à la période précédente.

    Exemple :
        80 -> 88 = +10.0%
        80 -> 72 = -10.0%
    """

    if (
        actuel is None
        or precedent is None
        or pd.isna(actuel)
        or pd.isna(precedent)
    ):
        return "—", "neutral"

    actuel = float(actuel)
    precedent = float(precedent)

    if abs(precedent) < 1e-12:

        if abs(actuel) < 1e-12:
            return "→ Stable", "neutral"

        return "▲ Nouveau", "neutral"

    variation = (
        (actuel - precedent)
        / abs(precedent)
        * 100.0
    )

    if abs(variation) < 0.5:
        return "→ Stable", "neutral"

    if variation > 0:

        return (
            f"▲ {variation:+.1f}%",
            "good",
        )

    return (
        f"▼ {variation:+.1f}%",
        "bad",
    )


# ============================================================
# STATUT KPI
# ============================================================

def _statut(
    valeur,
    objectif,
    direction="higher",
) -> str:

    if (
        valeur is None
        or objectif is None
        or pd.isna(valeur)
    ):
        return "neutral"

    valeur = float(valeur)
    objectif = float(objectif)

    if direction == "lower":

        if valeur <= objectif:
            return "good"

        if valeur <= objectif * 1.10:
            return "warn"

        return "bad"

    if valeur >= objectif:
        return "good"

    if valeur >= objectif * 0.90:
        return "warn"

    return "bad"


def _get_valeur(
    kpis: list[dict],
    nom: str,
):

    for kpi in kpis:

        if kpi.get("name") == nom:
            return kpi.get("value")

    return None


def _get_kpi(
    kpis: list[dict],
    nom: str,
):

    for kpi in kpis:

        if kpi.get("name") == nom:
            return kpi

    return None


# ============================================================
# AGENCES
# ============================================================

def _obtenir_agences(
    dex: dict,
) -> list[str]:

    agences = set()

    for cle in [
        "DIGITAL",
        "PHYSIQUE",
    ]:

        df = dex.get(cle)

        if (
            df is not None
            and "Agence" in df.columns
        ):

            valeurs = (
                df["Agence"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
            )

            agences.update(valeurs)

    return sorted(
        agence
        for agence in agences
        if agence
    )


# ============================================================
# ANNÉES DISPONIBLES
# ============================================================

def _annees_disponibles(
    dex: dict,
) -> list[int]:

    annees = set()

    for df in dex.values():

        if (
            df is None
            or df.empty
            or "Date" not in df.columns
        ):
            continue

        dates = (
            pd.to_datetime(
                df["Date"],
                dayfirst=True,
                errors="coerce",
            )
            .dropna()
        )

        if not dates.empty:

            annees.update(
                dates.dt.year
                .astype(int)
                .tolist()
            )

    return sorted(annees)


# ============================================================
# PÉRIODES D'UNE ANNÉE
# ============================================================

def _construire_periodes_annee(
    granularite: str,
    annee: int,
) -> list[Periode]:

    debut_annee = pd.Timestamp(
        year=annee,
        month=1,
        day=1,
    )

    fin_annee = pd.Timestamp(
        year=annee,
        month=12,
        day=31,
    )

    periode = periode_depuis_date(
        debut_annee,
        granularite,
    )

    resultat = []

    while periode.debut <= fin_annee:

        debut = max(
            periode.debut,
            debut_annee,
        )

        fin = min(
            periode.fin,
            fin_annee,
        )

        resultat.append(
            Periode(
                periode.granularite,
                debut,
                fin,
                periode.label,
                periode.cle,
            )
        )

        if granularite == "Journalier":

            suivante = (
                periode.debut
                + pd.Timedelta(days=1)
            )

        elif granularite == "Hebdomadaire":

            suivante = (
                periode.debut
                + pd.Timedelta(days=7)
            )

        elif granularite == "Mensuel":

            suivante = (
                periode.debut
                + pd.DateOffset(months=1)
            )

        elif granularite == "Bimestriel":

            suivante = (
                periode.debut
                + pd.DateOffset(months=2)
            )

        elif granularite == "Trimestriel":

            suivante = (
                periode.debut
                + pd.DateOffset(months=3)
            )

        elif granularite == "Semestriel":

            suivante = (
                periode.debut
                + pd.DateOffset(months=6)
            )

        else:

            suivante = (
                periode.debut
                + pd.DateOffset(years=1)
            )

        periode = periode_depuis_date(
            suivante,
            granularite,
        )

    return resultat


# ============================================================
# FILTRAGE
# ============================================================

def _filtrer(
    df,
    periode,
    agence=None,
):

    if (
        df is None
        or df.empty
        or "Date" not in df.columns
    ):
        return pd.DataFrame()

    resultat = filtrer_periode(
        df,
        periode,
    )

    if (
        agence
        and "Agence" in resultat.columns
    ):

        resultat = resultat[
            resultat["Agence"]
            .astype(str)
            .str.strip()
            == agence
        ]

    return resultat


# ============================================================
# KPI NUMÉRIQUE
# ============================================================

def _kpis_numerique(
    df: pd.DataFrame,
) -> list[dict]:

    prestations_digitales = _num(
        df,
        "Prestations Digital",
    )

    total_prestations = _num(
        df,
        "Total Prestations",
    )

    contre_performances = _count_text(
        df,
        "Contre Performance",
    )

    initiatives = _count_text(
        df,
        "Initiative",
    )

    return [

        {
            "name":
                "Prestations digitales",
            "value":
                prestations_digitales,
            "unit":
                "prestations",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Total prestations",
            "value":
                total_prestations,
            "unit":
                "prestations",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Part digitale",
            "value":
                _pct(
                    prestations_digitales,
                    total_prestations,
                ),
            "unit":
                "%",
            "objective":
                50,
            "direction":
                "higher",
        },

        {
            "name":
                "Contre-performances signalées",
            "value":
                contre_performances,
            "unit":
                "signalements",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Initiatives signalées",
            "value":
                initiatives,
            "unit":
                "initiatives",
            "objective":
                None,
            "direction":
                "higher",
        },
    ]


# ============================================================
# KPI PHYSIQUE
# ============================================================

def _kpis_physique(
    df: pd.DataFrame,
) -> list[dict]:

    clients = _num(
        df,
        "Clients reçus",
    )

    clients_on_time = _num(
        df,
        "Clients ON TIME",
    )

    clients_attendus_15 = _num(
        df,
        "Nombre de clients attendus en moins de 15 minutes",
    )

    clients_pris_15 = _num(
        df,
        "Nombre de clients pris en charge en moins de 15 minutes",
    )

    cp_attente = _count_text(
        df,
        "CP ATTENTE",
    )

    cp_prise_en_charge = _count_text(
        df,
        "CP PRISE EN CHARGE",
    )

    return [

        {
            "name":
                "Clients reçus",
            "value":
                clients,
            "unit":
                "clients",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de prise en charge à temps",
            "value":
                _pct(
                    clients_on_time,
                    clients,
                ),
            "unit":
                "%",
            "objective":
                80,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de prise en charge < 15 min",
            "value":
                _pct(
                    clients_pris_15,
                    clients_attendus_15,
                ),
            "unit":
                "%",
            "objective":
                80,
            "direction":
                "higher",
        },

        {
            "name":
                "Temps d'attente moyen",
            "value":
                _mean(
                    df,
                    "Temps d'attente",
                ),
            "unit":
                "min",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Temps de prise en charge moyen",
            "value":
                _mean(
                    df,
                    "Temps de prise en charge",
                ),
            "unit":
                "min",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Contre-performances d'attente signalées",
            "value":
                cp_attente,
            "unit":
                "signalements",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Contre-performances de prise en charge signalées",
            "value":
                cp_prise_en_charge,
            "unit":
                "signalements",
            "objective":
                None,
            "direction":
                "lower",
        },
    ]


# ============================================================
# KPI SATISFACTION
# ============================================================

def _kpis_satisfaction(
    df: pd.DataFrame,
) -> list[dict]:

    clients_recus = _num(
        df,
        "Total clients reçus",
    )

    clients_satisfaits = _num(
        df,
        "Clients satisfaits",
    )

    reponses = _num(
        df,
        "Recueil de satisfaction",
    )

    reclamations_recues = _num(
        df,
        "Réclamations MOIS reçues",
    )

    reclamations_traitees = _num(
        df,
        "Réclamations MOIS traitées dans les délais",
    )

    return [

        {
            "name":
                "Taux de satisfaction",
            "value":
                _pct(
                    clients_satisfaits,
                    clients_recus,
                ),
            "unit":
                "%",
            "objective":
                75,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de recueil de satisfaction",
            "value":
                _pct(
                    reponses,
                    clients_recus,
                ),
            "unit":
                "%",
            "objective":
                80,
            "direction":
                "higher",
        },

        {
            "name":
                "Réponses recueillies",
            "value":
                reponses,
            "unit":
                "réponses",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Réclamations reçues",
            "value":
                reclamations_recues,
            "unit":
                "réclamations",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Réclamations traitées dans les délais",
            "value":
                reclamations_traitees,
            "unit":
                "réclamations",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de réclamations traitées dans les délais",
            "value":
                _pct(
                    reclamations_traitees,
                    reclamations_recues,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },
    ]


# ============================================================
# KPI MESSAGERIE
# ============================================================

def _kpis_messagerie(
    df: pd.DataFrame,
) -> list[dict]:

    whatsapp_recus = _num(
        df,
        "WhatsApp reçues",
    )

    whatsapp_clotures = _num(
        df,
        "WhatsApp clôturées",
    )

    mails_recus = _num(
        df,
        "Mail reçus",
    )

    mails_clotures = _num(
        df,
        "Mail clôturés",
    )

    return [

        {
            "name":
                "WhatsApp reçus",
            "value":
                whatsapp_recus,
            "unit":
                "messages",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "WhatsApp clôturés",
            "value":
                whatsapp_clotures,
            "unit":
                "messages",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de clôture WhatsApp",
            "value":
                _pct(
                    whatsapp_clotures,
                    whatsapp_recus,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },

        {
            "name":
                "Mails reçus",
            "value":
                mails_recus,
            "unit":
                "mails",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Mails clôturés",
            "value":
                mails_clotures,
            "unit":
                "mails",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de clôture Mail",
            "value":
                _pct(
                    mails_clotures,
                    mails_recus,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },
    ]


# ============================================================
# KPI CENTRE DE CONTACTS
# ============================================================

def _kpis_centre_contacts(
    df: pd.DataFrame,
) -> list[dict]:

    appels_recus = _num(
        df,
        "Appels reçus",
    )

    appels_decroches = _num(
        df,
        "Appels décrochés",
    )

    appels_dans_delai = _num(
        df,
        "Appels reçus dans le délai",
    )

    appels_emis = _num(
        df,
        "Appels émis",
    )

    objectif_emis = _num(
        df,
        "Objectif appels émis",
    )

    clients_joints = _num(
        df,
        "Clients joints",
    )

    rdv = _num(
        df,
        "RDV pris",
    )

    appels_pour_rdv = _num(
        df,
        "Appels pour RDV",
    )

    return [

        {
            "name":
                "Appels reçus",
            "value":
                appels_recus,
            "unit":
                "appels",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de décroché",
            "value":
                _pct(
                    appels_decroches,
                    appels_recus,
                ),
            "unit":
                "%",
            "objective":
                80,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux d'appels dans le délai",
            "value":
                _pct(
                    appels_dans_delai,
                    appels_recus,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },

        {
            "name":
                "Temps moyen de communication",
            "value":
                _mean(
                    df,
                    "Temps moyen de communication",
                ),
            "unit":
                "min",
            "objective":
                None,
            "direction":
                "lower",
        },

        {
            "name":
                "Appels émis",
            "value":
                appels_emis,
            "unit":
                "appels",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux d'atteinte des appels émis",
            "value":
                _pct(
                    appels_emis,
                    objectif_emis,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de joignabilité",
            "value":
                _pct(
                    clients_joints,
                    appels_emis,
                ),
            "unit":
                "%",
            "objective":
                50,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de rendez-vous",
            "value":
                _pct(
                    rdv,
                    appels_pour_rdv,
                ),
            "unit":
                "%",
            "objective":
                50,
            "direction":
                "higher",
        },
    ]


# ============================================================
# KPI DÉSHÉRENCE
# ============================================================

def _kpis_desherence(
    df: pd.DataFrame,
) -> list[dict]:

    dossiers_ouverts = _num(
        df,
        "Dossiers ouverts",
    )

    dossiers_traites = _num(
        df,
        "Dossiers traités",
    )

    montant_recupere = _num(
        df,
        "Montant récupéré (FCFA)",
    )

    contacts_reussis = _num(
        df,
        "Contacts réussis",
    )

    return [

        {
            "name":
                "Dossiers ouverts",
            "value":
                dossiers_ouverts,
            "unit":
                "dossiers",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Dossiers traités",
            "value":
                dossiers_traites,
            "unit":
                "dossiers",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Taux de traitement des dossiers",
            "value":
                _pct(
                    dossiers_traites,
                    dossiers_ouverts,
                ),
            "unit":
                "%",
            "objective":
                100,
            "direction":
                "higher",
        },

        {
            "name":
                "Montant récupéré",
            "value":
                montant_recupere,
            "unit":
                "FCFA",
            "objective":
                None,
            "direction":
                "higher",
        },

        {
            "name":
                "Contacts réussis",
            "value":
                contacts_reussis,
            "unit":
                "contacts",
            "objective":
                None,
            "direction":
                "higher",
        },
    ]


# ============================================================
# CONFIGURATION DES POINTS
# ============================================================

DOMAINES_DETAIL = [

    {
        "cle":
            "DIGITAL",

        "label":
            "🟦 Numérique",

        "couleur":
            COULEURS["bleu"],

        "builder":
            _kpis_numerique,

        "agence":
            True,

        "evolution":
            [
                (
                    "Part digitale",
                    "%",
                ),
                (
                    "Contre-performances signalées",
                    "signalements",
                ),
            ],
    },

    {
        "cle":
            "PHYSIQUE",

        "label":
            "🏢 Réception physique",

        "couleur":
            COULEURS["vert"],

        "builder":
            _kpis_physique,

        "agence":
            True,

        "evolution":
            [
                (
                    "Taux de prise en charge à temps",
                    "%",
                ),
                (
                    "Contre-performances d'attente signalées",
                    "signalements",
                ),
            ],
    },

    {
        "cle":
            "RC & SATISFACTION",

        "label":
            "😊 Satisfaction et réclamations",

        "couleur":
            COULEURS["or"],

        "builder":
            _kpis_satisfaction,

        "agence":
            False,

        "evolution":
            [
                (
                    "Taux de satisfaction",
                    "%",
                ),
                (
                    "Taux de réclamations traitées dans les délais",
                    "%",
                ),
            ],
    },

    {
        "cle":
            "MESSAGERIE",

        "label":
            "💬 Messagerie",

        "couleur":
            COULEURS["violet"],

        "builder":
            _kpis_messagerie,

        "agence":
            False,

        "evolution":
            [
                (
                    "Taux de clôture WhatsApp",
                    "%",
                ),
                (
                    "Taux de clôture Mail",
                    "%",
                ),
            ],
    },

    {
        "cle":
            "CALLCENTER",

        "label":
            "🎧 Centre de contacts",

        "couleur":
            COULEURS["cyan"],

        "builder":
            _kpis_centre_contacts,

        "agence":
            False,

        "evolution":
            [
                (
                    "Taux de décroché",
                    "%",
                ),
                (
                    "Temps moyen de communication",
                    "min",
                ),
            ],
    },

    {
        "cle":
            "DESHERENCE",

        "label":
            "📉 Déshérence",

        "couleur":
            COULEURS["rose"],

        "builder":
            _kpis_desherence,

        "agence":
            False,

        "evolution":
            [
                (
                    "Dossiers traités",
                    "dossiers",
                ),
                (
                    "Montant récupéré",
                    "FCFA",
                ),
            ],
    },
]


# ============================================================
# SÉRIE D'ÉVOLUTION
# ============================================================

def _serie_evolution(
    df,
    granularite,
    annee,
    agence,
    borne_fin,
    builder,
    nom,
):

    periodes = [
        periode
        for periode in _construire_periodes_annee(
            granularite,
            annee,
        )
        if periode.debut <= borne_fin
    ]

    # On garde les 12 dernières périodes.
    periodes = periodes[-12:]

    labels = []
    valeurs = []

    for periode in periodes:

        df_periode = _filtrer(
            df,
            periode,
            agence,
        )

        kpis = builder(
            df_periode
        )

        valeur = _get_valeur(
            kpis,
            nom,
        )

        if valeur is not None:

            labels.append(
                periode.label
            )

            valeurs.append(
                float(valeur)
            )

    return labels, valeurs


# ============================================================
# GRAPHIQUE
# ============================================================

def _rgba(
    couleur: str,
    alpha: float = 0.15,
):

    couleur = couleur.lstrip("#")

    r = int(
        couleur[0:2],
        16,
    )

    g = int(
        couleur[2:4],
        16,
    )

    b = int(
        couleur[4:6],
        16,
    )

    return (
        f"rgba("
        f"{r},{g},{b},{alpha}"
        f")"
    )


def _graphique_evolution(
    labels,
    valeurs,
    titre,
    couleur,
    unite,
    objectif=None,
    type_graphique="ligne",
):

    fig = go.Figure()

    suffixe = (
        "%"
        if unite == "%"
        else ""
    )

    if type_graphique == "ligne":

        fig.add_trace(
            go.Scatter(
                x=labels,
                y=valeurs,
                mode="lines+markers",
                name=titre,
                fill="tozeroy",
                fillcolor=_rgba(
                    couleur,
                    0.13,
                ),
                line=dict(
                    color=couleur,
                    width=3,
                    shape="spline",
                ),
                marker=dict(
                    size=7,
                    color=couleur,
                    line=dict(
                        color="#FFFFFF",
                        width=1,
                    ),
                ),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + titre
                    + " : "
                    + "%{y:.1f}"
                    + suffixe
                    + "<extra></extra>"
                ),
            )
        )

    else:

        fig.add_trace(
            go.Bar(
                x=labels,
                y=valeurs,
                name=titre,
                marker_color=couleur,
                opacity=0.88,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + titre
                    + " : "
                    + "%{y:.1f}"
                    + suffixe
                    + "<extra></extra>"
                ),
            )
        )

    if objectif is not None:

        texte_objectif = (
            f"Objectif {objectif:g}%"
            if unite == "%"
            else f"Objectif {objectif:g}"
        )

        fig.add_hline(
            y=objectif,
            line_dash="dash",
            line_width=1.5,
            line_color=COULEURS["or"],
            annotation_text=texte_objectif,
            annotation_position="top left",
        )

    fig.update_layout(

        height=300,

        margin=dict(
            l=15,
            r=15,
            t=50,
            b=25,
        ),

        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),

        plot_bgcolor=(
            "rgba(255,255,255,0.025)"
        ),

        font=dict(
            family="Inter, Arial",
            color="#EAF0FA",
        ),

        title=dict(
            text=f"<b>{titre}</b>",
            font=dict(
                size=13,
                color="#FFFFFF",
            ),
            x=0.02,
        ),

        showlegend=False,

        hovermode="x unified",

        xaxis=dict(
            showgrid=False,
            tickfont=dict(
                size=9,
                color="#EAF0FA",
            ),
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=(
                "rgba(255,255,255,0.06)"
            ),
            zeroline=False,
            tickfont=dict(
                size=9,
                color="#EAF0FA",
            ),
        ),
    )

    return fig


# ============================================================
# OBSERVATIONS TEXTUELLES
# ============================================================

def _render_observations(
    cle,
    df,
):

    colonnes = {

        "DIGITAL": [
            "Contre Performance",
            "Initiative",
        ],

        "PHYSIQUE": [
            "CP ATTENTE",
            "CP PRISE EN CHARGE",
            "INITIATIVE ATTENTE",
            "INITIATIVE PRISE EN CHARGE",
        ],
    }.get(
        cle,
        [],
    )

    observations = []

    for colonne in colonnes:

        if colonne not in df.columns:
            continue

        valeurs = (
            df[colonne]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        valeurs = valeurs[
            (valeurs != "")
            & (
                valeurs.str.lower()
                != "nan"
            )
        ]

        for texte, nombre in (
            valeurs.value_counts()
            .items()
        ):

            observations.append(
                (
                    colonne,
                    texte,
                    int(nombre),
                )
            )

    if not observations:
        return

    st.markdown(
        """
        <div style="
            margin-top:1rem;
            margin-bottom:.5rem;
            font-size:.72rem;
            font-weight:800;
            color:rgba(255,255,255,.55);
            letter-spacing:.08em;
            text-transform:uppercase;
        ">
            OBSERVATIONS
        </div>
        """,
        unsafe_allow_html=True,
    )

    observations.sort(
        key=lambda x: -x[2]
    )

    for colonne, texte, nombre in observations[:8]:

        st.caption(
            f"{colonne} : "
            f"{texte} · "
            f"{nombre} signalement(s)"
        )


# ============================================================
# DÉTAIL PAR POINT
# ============================================================

def _render_point_detail(
    cfg,
    df_original,
    periode,
    periode_avant,
    agence,
    granularite,
    annee,
):

    if (
        df_original is None
        or df_original.empty
    ):
        return

    agence_active = (
        agence
        if cfg["agence"]
        else None
    )

    df_periode = _filtrer(
        df_original,
        periode,
        agence_active,
    )

    df_precedente = _filtrer(
        df_original,
        periode_avant,
        agence_active,
    )

    kpis = cfg["builder"](
        df_periode
    )

    kpis_precedents = cfg["builder"](
        df_precedente
    )

    # --------------------------------------------------------
    # SUPPRESSION DES KPI VIDES
    # --------------------------------------------------------

    kpis = [
        kpi
        for kpi in kpis
        if kpi.get("value") is not None
    ]

    if not kpis:
        return

    nombre_lignes = len(
        df_periode
    )

    sous_titre = (
        f"{nombre_lignes} ligne(s)"
        f" · {periode.label}"
    )

    if cfg["agence"]:

        sous_titre += (
            f" · "
            f"{agence or 'Toutes les agences'}"
        )

    else:

        sous_titre += (
            " · données nationales"
        )

    with st.expander(
        f"{cfg['label']} — {sous_titre}",
        expanded=False,
    ):

        # ====================================================
        # KPI
        # ====================================================

        colonnes = st.columns(4)

        for index, kpi in enumerate(kpis):

            valeur = kpi["value"]

            precedent = _get_valeur(
                kpis_precedents,
                kpi["name"],
            )

            variation, statut_variation = (
                _variation_relative(
                    valeur,
                    precedent,
                )
            )

            if precedent is None:

                statut = _statut(
                    valeur,
                    kpi.get("objective"),
                    kpi.get(
                        "direction",
                        "higher",
                    ),
                )

            else:

                statut = statut_variation

            if variation != "—":

                sous = (
                    f"{variation} "
                    "vs période précédente"
                )

            else:

                sous = (
                    "Pas de comparaison disponible"
                )

            if (
                kpi.get("objective")
                is not None
                and kpi.get("unit") == "%"
            ):

                sous += (
                    f" · cible "
                    f"{kpi['objective']:.0f}%"
                )

            with colonnes[
                index % 4
            ]:

                kpi_card(
                    "•",
                    kpi["name"],
                    _format_valeur(
                        valeur,
                        kpi.get(
                            "unit",
                            "",
                        ),
                    ),
                    sous,
                    statut,
                )

        # ====================================================
        # ÉVOLUTION
        # ====================================================

        st.markdown(
            f"""
            <div style="
                margin:1rem 0 .5rem;
                font-size:.75rem;
                font-weight:800;
                color:{cfg['couleur']};
                letter-spacing:.08em;
                text-transform:uppercase;
            ">
                📈 ÉVOLUTION — {granularite} {annee}
            </div>
            """,
            unsafe_allow_html=True,
        )

        for index, (
            nom_indicateur,
            unite,
        ) in enumerate(
            cfg["evolution"]
        ):

            kpi = _get_kpi(
                kpis,
                nom_indicateur,
            )

            if kpi is None:
                continue

            labels, valeurs = (
                _serie_evolution(
                    df_original,
                    granularite,
                    annee,
                    agence_active,
                    periode.fin,
                    cfg["builder"],
                    nom_indicateur,
                )
            )

            if len(valeurs) < 2:
                continue

            graphique = (
                _graphique_evolution(
                    labels,
                    valeurs,
                    nom_indicateur,
                    cfg["couleur"],
                    unite,
                    kpi.get(
                        "objective"
                    ),
                    (
                        "ligne"
                        if index == 0
                        else "barres"
                    ),
                )
            )

            st.plotly_chart(
                graphique,
                use_container_width=True,
                config={
                    "displayModeBar":
                        False,
                },
                key=(
                    "point_global_"
                    f"{cfg['cle']}_"
                    f"{nom_indicateur}_"
                    f"{annee}_"
                    f"{granularite}"
                ),
            )

        # ====================================================
        # OBSERVATIONS
        # ====================================================

        _render_observations(
            cfg["cle"],
            df_periode,
        )


# ============================================================
# VUE D'ENSEMBLE
# ============================================================

def _render_vue_ensemble(
    df_rc_sat,
    df_digital,
    df_physique,
    df_cc,
    periode,
    periode_avant,
    agence,
):

    # ========================================================
    # SATISFACTION
    # ========================================================

    df_sat = _filtrer(
        df_rc_sat,
        periode,
    )

    df_sat_precedent = _filtrer(
        df_rc_sat,
        periode_avant,
    )

    kpis_sat = satisfaction_kpis(
        df_sat
    )

    kpis_sat_precedents = satisfaction_kpis(
        df_sat_precedent
    )

    taux_satisfaction = _get_valeur(
        kpis_sat,
        "Taux de satisfaction",
    )

    taux_satisfaction_precedent = _get_valeur(
        kpis_sat_precedents,
        "Taux de satisfaction",
    )

    taux_recueil = _get_valeur(
        kpis_sat,
        "Taux de recueil de satisfaction",
    )

    taux_recueil_precedent = _get_valeur(
        kpis_sat_precedents,
        "Taux de recueil de satisfaction",
    )

    clients_recus = _get_valeur(
        kpis_sat,
        "Clients reçus",
    ) or 0

    clients_recus_precedent = _get_valeur(
        kpis_sat_precedents,
        "Clients reçus",
    )

    # ========================================================
    # RÉCLAMATIONS
    # ========================================================

    kpis_reclamations = reclamation_kpis(
        df_sat
    )

    kpis_reclamations_precedents = (
        reclamation_kpis(
            df_sat_precedent
        )
    )

    taux_reclamations = _get_valeur(
        kpis_reclamations,
        "Taux réclamations traitées dans le délai",
    )

    taux_reclamations_precedent = _get_valeur(
        kpis_reclamations_precedents,
        "Taux réclamations traitées dans le délai",
    )

    # ========================================================
    # SATISFACTION GLOBALE
    # ========================================================

    satisfaction_globale = (
        satisfaction_globale_officielle(
            (
                taux_satisfaction or 0
            ) / 100,
            (
                taux_reclamations or 0
            ) / 100,
        )
    )

    satisfaction_globale_precedente = (
        satisfaction_globale_officielle(
            (
                taux_satisfaction_precedent
                or 0
            ) / 100,
            (
                taux_reclamations_precedent
                or 0
            ) / 100,
        )
    )

    # ========================================================
    # NUMÉRIQUE
    # ========================================================

    df_numerique = _filtrer(
        df_digital,
        periode,
        agence,
    )

    df_numerique_precedent = _filtrer(
        df_digital,
        periode_avant,
        agence,
    )

    kpis_numerique = _kpis_numerique(
        df_numerique
    )

    kpis_numerique_precedents = (
        _kpis_numerique(
            df_numerique_precedent
        )
    )

    # ========================================================
    # PHYSIQUE
    # ========================================================

    df_physique_periode = _filtrer(
        df_physique,
        periode,
        agence,
    )

    df_physique_precedent = _filtrer(
        df_physique,
        periode_avant,
        agence,
    )

    kpis_physique = _kpis_physique(
        df_physique_periode
    )

    kpis_physique_precedents = (
        _kpis_physique(
            df_physique_precedent
        )
    )

    # ========================================================
    # CENTRE DE CONTACTS
    # ========================================================

    df_cc_periode = _filtrer(
        df_cc,
        periode,
    )

    df_cc_precedent = _filtrer(
        df_cc,
        periode_avant,
    )

    kpis_cc = _kpis_centre_contacts(
        df_cc_periode
    )

    kpis_cc_precedents = (
        _kpis_centre_contacts(
            df_cc_precedent
        )
    )

    # ========================================================
    # VUE
    # ========================================================

    with st.expander(
        "🏅 Vue d'ensemble — "
        "satisfaction globale et réception",
        expanded=True,
    ):

        # ====================================================
        # SATISFACTION GLOBALE
        # ====================================================

        section(
            "SATISFACTION GLOBALE"
        )

        c1, c2, c3, c4, c5 = (
            st.columns(5)
        )

        cartes = [

            (
                c1,
                "🏅",
                "Satisfaction globale",
                satisfaction_globale * 100,
                satisfaction_globale_precedente * 100,
                "%",
                75,
                "higher",
                (
                    "50% baromètre + "
                    "25% satisfaction + "
                    "25% réclamations"
                ),
            ),

            (
                c2,
                "⚠️",
                "Réclamations traitées dans les délais",
                taux_reclamations,
                taux_reclamations_precedent,
                "%",
                100,
                "higher",
                "cible 100%",
            ),

            (
                c3,
                "📈",
                "Taux de satisfaction",
                taux_satisfaction,
                taux_satisfaction_precedent,
                "%",
                75,
                "higher",
                "cible 75%",
            ),

            (
                c4,
                "👥",
                "Taux de recueil de satisfaction",
                taux_recueil,
                taux_recueil_precedent,
                "%",
                80,
                "higher",
                "cible 80%",
            ),

            (
                c5,
                "⭐",
                "Taux de satisfaction du baromètre",
                get_csat_barometre() * 100,
                None,
                "%",
                75,
                "higher",
                "grande enquête fixe",
            ),
        ]

        for (
            colonne,
            icone,
            nom,
            valeur,
            precedent,
            unite,
            objectif,
            direction,
            commentaire,
        ) in cartes:

            with colonne:

                variation, _ = (
                    _variation_relative(
                        valeur,
                        precedent,
                    )
                )

                if variation != "—":

                    sous = (
                        f"{variation} "
                        "vs période précédente"
                    )

                else:

                    sous = commentaire

                if (
                    variation != "—"
                    and commentaire
                ):

                    sous += (
                        f" · {commentaire}"
                    )

                kpi_card(
                    icone,
                    nom,
                    _format_valeur(
                        valeur,
                        unite,
                    ),
                    sous,
                    _statut(
                        valeur,
                        objectif,
                        direction,
                    ),
                )

        # ====================================================
        # RÉCEPTION NUMÉRIQUE ET PHYSIQUE
        # ====================================================

        section(
            "RÉCEPTION NUMÉRIQUE ET PHYSIQUE"
        )

        c6, c7, c8, c9, c10 = (
            st.columns(5)
        )

        cartes_reception = [

            (
                c6,
                "👥",
                "Nombre de clients reçus",
                clients_recus,
                clients_recus_precedent,
                "clients",
                None,
                "higher",
            ),

            (
                c7,
                "📱",
                "Taux d'utilisation numérique",
                _get_valeur(
                    kpis_numerique,
                    "Part digitale",
                ),
                _get_valeur(
                    kpis_numerique_precedents,
                    "Part digitale",
                ),
                "%",
                50,
                "higher",
            ),

            (
                c8,
                "⏱️",
                "Clients pris en charge à temps",
                _get_valeur(
                    kpis_physique,
                    "Taux de prise en charge à temps",
                ),
                _get_valeur(
                    kpis_physique_precedents,
                    "Taux de prise en charge à temps",
                ),
                "%",
                80,
                "higher",
            ),

            (
                c9,
                "⏱️",
                "Temps moyen d'attente",
                _get_valeur(
                    kpis_physique,
                    "Temps d'attente moyen",
                ),
                _get_valeur(
                    kpis_physique_precedents,
                    "Temps d'attente moyen",
                ),
                "min",
                None,
                "lower",
            ),

            (
                c10,
                "✅",
                "Prise en charge < 15 min",
                _get_valeur(
                    kpis_physique,
                    "Taux de prise en charge < 15 min",
                ),
                _get_valeur(
                    kpis_physique_precedents,
                    "Taux de prise en charge < 15 min",
                ),
                "%",
                80,
                "higher",
            ),
        ]

        for (
            colonne,
            icone,
            nom,
            valeur,
            precedent,
            unite,
            objectif,
            direction,
        ) in cartes_reception:

            with colonne:

                variation, _ = (
                    _variation_relative(
                        valeur,
                        precedent,
                    )
                )

                sous = (
                    f"{variation} "
                    "vs période précédente"
                    if variation != "—"
                    else ""
                )

                kpi_card(
                    icone,
                    nom,
                    _format_valeur(
                        valeur,
                        unite,
                    ),
                    sous,
                    _statut(
                        valeur,
                        objectif,
                        direction,
                    ),
                )

        # ====================================================
        # CENTRE DE CONTACTS
        # ====================================================

        section(
            "RÉCEPTION TÉLÉPHONIQUE"
        )

        c11, c12, c13, c14 = (
            st.columns(4)
        )

        cartes_contacts = [

            (
                c11,
                "☎️",
                "Nombre d'appels reçus",
                _get_valeur(
                    kpis_cc,
                    "Appels reçus",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Appels reçus",
                ),
                "appels",
                None,
                "higher",
            ),

            (
                c12,
                "✅",
                "Taux de décroché",
                _get_valeur(
                    kpis_cc,
                    "Taux de décroché",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Taux de décroché",
                ),
                "%",
                80,
                "higher",
            ),

            (
                c13,
                "⏱️",
                "Appels dans le délai",
                _get_valeur(
                    kpis_cc,
                    "Taux d'appels dans le délai",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Taux d'appels dans le délai",
                ),
                "%",
                100,
                "higher",
            ),

            (
                c14,
                "⏱️",
                "Temps moyen de communication",
                _get_valeur(
                    kpis_cc,
                    "Temps moyen de communication",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Temps moyen de communication",
                ),
                "min",
                None,
                "lower",
            ),
        ]

        for (
            colonne,
            icone,
            nom,
            valeur,
            precedent,
            unite,
            objectif,
            direction,
        ) in cartes_contacts:

            with colonne:

                variation, _ = (
                    _variation_relative(
                        valeur,
                        precedent,
                    )
                )

                sous = (
                    f"{variation} "
                    "vs période précédente"
                    if variation != "—"
                    else ""
                )

                kpi_card(
                    icone,
                    nom,
                    _format_valeur(
                        valeur,
                        unite,
                    ),
                    sous,
                    _statut(
                        valeur,
                        objectif,
                        direction,
                    ),
                )

        c15, c16, c17 = (
            st.columns(3)
        )

        cartes_contacts_2 = [

            (
                c15,
                "📞",
                "Nombre d'appels émis",
                _get_valeur(
                    kpis_cc,
                    "Appels émis",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Appels émis",
                ),
                "appels",
                None,
                "higher",
            ),

            (
                c16,
                "🤝",
                "Taux de joignabilité",
                _get_valeur(
                    kpis_cc,
                    "Taux de joignabilité",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Taux de joignabilité",
                ),
                "%",
                50,
                "higher",
            ),

            (
                c17,
                "📅",
                "Taux de rendez-vous",
                _get_valeur(
                    kpis_cc,
                    "Taux de rendez-vous",
                ),
                _get_valeur(
                    kpis_cc_precedents,
                    "Taux de rendez-vous",
                ),
                "%",
                50,
                "higher",
            ),
        ]

        for (
            colonne,
            icone,
            nom,
            valeur,
            precedent,
            unite,
            objectif,
            direction,
        ) in cartes_contacts_2:

            with colonne:

                variation, _ = (
                    _variation_relative(
                        valeur,
                        precedent,
                    )
                )

                sous = (
                    f"{variation} "
                    "vs période précédente"
                    if variation != "—"
                    else ""
                )

                kpi_card(
                    icone,
                    nom,
                    _format_valeur(
                        valeur,
                        unite,
                    ),
                    sous,
                    _statut(
                        valeur,
                        objectif,
                        direction,
                    ),
                )


# ============================================================
# BAROMÈTRE
# ============================================================

def _render_barometre():

    with st.expander(
        (
            "⚙️ Grande enquête barométrique — "
            f"valeur actuelle : "
            f"{get_csat_barometre() * 100:.0f}%"
        ),
        expanded=False,
    ):

        st.caption(
            "Cette valeur ne change qu'après "
            "une nouvelle grande enquête annuelle."
        )

        col1, col2 = st.columns(
            [2, 1]
        )

        with col1:

            nouvelle_valeur = (
                st.number_input(
                    "Nouveau taux de satisfaction du baromètre (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=(
                        get_csat_barometre()
                        * 100
                    ),
                    step=0.1,
                    key="input_barometre",
                )
            )

        with col2:

            if st.button(
                "💾 Enregistrer",
                key="btn_save_barometre",
                use_container_width=True,
            ):

                set_csat_barometre(
                    nouvelle_valeur / 100
                )

                st.success(
                    "Valeur mise à jour : "
                    f"{nouvelle_valeur:.1f}%"
                )

                st.rerun()


# ============================================================
# POINT GLOBAL
# ============================================================

def render_point_global(
    dex: dict,
):

    bases_requises = [
        "DIGITAL",
        "PHYSIQUE",
        "RC & SATISFACTION",
        "MESSAGERIE",
        "CALLCENTER",
        "DESHERENCE",
    ]

    manquantes = [
        base
        for base in bases_requises
        if (
            base not in dex
            or dex[base] is None
            or dex[base].empty
        )
    ]

    if manquantes:

        st.error(
            "Bases manquantes : "
            + ", ".join(manquantes)
        )

        return

    dex = {
        cle:
            _normaliser_date_colonnes(df)
        for cle, df in dex.items()
    }

    df_digital = dex[
        "DIGITAL"
    ]

    df_physique = dex[
        "PHYSIQUE"
    ]

    df_rc_sat = dex[
        "RC & SATISFACTION"
    ]

    df_messagerie = dex[
        "MESSAGERIE"
    ]

    df_cc = dex[
        "CALLCENTER"
    ]

    df_desherence = dex[
        "DESHERENCE"
    ]

    if "Date" not in df_rc_sat.columns:

        st.error(
            "La colonne 'Date' est absente "
            "de la base Satisfaction et Réclamations."
        )

        return

    # ========================================================
    # ANNÉES DISPONIBLES
    # ========================================================

    annees = _annees_disponibles(
        dex
    )

    if not annees:

        st.warning(
            "Aucune année exploitable "
            "dans les données."
        )

        return

    # ========================================================
    # FILTRES
    #
    # GRANULARITÉ
    #       ↓
    # ANNÉE
    #       ↓
    # PÉRIODE
    #       ↓
    # AGENCE
    # ========================================================

    section(
        "FILTRES DE PILOTAGE"
    )

    f1, f2, f3, f4 = st.columns(
        [1, 1, 1.6, 1.4]
    )

    # --------------------------------------------------------
    # GRANULARITÉ
    # --------------------------------------------------------

    with f1:

        granularite = st.selectbox(
            "Granularité",
            GRANULARITES,
            index=2,
            key="point_global_granularite",
        )

    # --------------------------------------------------------
    # ANNÉE
    # --------------------------------------------------------

    with f2:

        annee = st.selectbox(
            "Année",
            annees,
            index=len(annees) - 1,
            key="point_global_annee",
        )

    # --------------------------------------------------------
    # PÉRIODES DE L'ANNÉE
    # --------------------------------------------------------

    periodes = (
        _construire_periodes_annee(
            granularite,
            int(annee),
        )
    )

    if not periodes:

        st.warning(
            "Aucune période disponible "
            "pour cette année."
        )

        return

    # --------------------------------------------------------
    # DERNIÈRE DATE DISPONIBLE
    # --------------------------------------------------------

    dates_toutes = []

    for df in dex.values():

        if "Date" not in df.columns:
            continue

        dates = (
            pd.to_datetime(
                df["Date"],
                dayfirst=True,
                errors="coerce",
            )
            .dropna()
        )

        if not dates.empty:
            dates_toutes.append(
                dates.max()
            )

    if dates_toutes:

        derniere_date = max(
            dates_toutes
        )

    else:

        derniere_date = pd.Timestamp(
            f"{annee}-12-31"
        )

    periodes = [
        periode
        for periode in periodes
        if periode.debut
        <= derniere_date
    ]

    if not periodes:

        st.warning(
            "Aucune période disponible "
            "pour cette année."
        )

        return

    # --------------------------------------------------------
    # PÉRIODE
    # --------------------------------------------------------

    with f3:

        labels = [
            periode.label
            for periode in periodes
        ]

        periode_label = (
            st.selectbox(
                "Période",
                labels,
                index=len(labels) - 1,
                key="point_global_periode",
            )
        )

    periode = next(
        periode
        for periode in periodes
        if periode.label
        == periode_label
    )

    periode_avant = (
        periode_precedente(
            periode
        )
    )

    # --------------------------------------------------------
    # AGENCE
    # --------------------------------------------------------

    agences = _obtenir_agences(
        dex
    )

    with f4:

        agence_label = (
            st.selectbox(
                "Agence",
                [
                    "Toutes les agences"
                ]
                + agences,
                key="point_global_agence",
            )
        )

    agence = (
        None
        if agence_label
        == "Toutes les agences"
        else agence_label
    )

    # ========================================================
    # VUE D'ENSEMBLE
    #
    # LE CONTENU RESTE LE MÊME.
    # ========================================================

    _render_vue_ensemble(
        df_rc_sat,
        df_digital,
        df_physique,
        df_cc,
        periode,
        periode_avant,
        agence,
    )

    # ========================================================
    # DÉTAIL PAR POINT
    # ========================================================

    section(
        "DÉTAIL PAR POINT"
    )

    df_par_cle = {

        "DIGITAL":
            df_digital,

        "PHYSIQUE":
            df_physique,

        "RC & SATISFACTION":
            df_rc_sat,

        "MESSAGERIE":
            df_messagerie,

        "CALLCENTER":
            df_cc,

        "DESHERENCE":
            df_desherence,
    }

    for configuration in (
        DOMAINES_DETAIL
    ):

        _render_point_detail(
            configuration,
            df_par_cle[
                configuration["cle"]
            ],
            periode,
            periode_avant,
            agence,
            granularite,
            int(annee),
        )

    # ========================================================
    # PARAMÈTRE BAROMÈTRE
    # ========================================================

    _render_barometre()