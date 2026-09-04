import pandas as pd
import streamlit as st

from periods import plage_dates_dex
from kpi_dex import KPI_BUILDERS

from theme import (
    page_header,
    section,
    kpi_card,
    render_html,
)


# ============================================================
# CONFIGURATION
# ============================================================

DOMAINES = [
    ("DIGITAL", "🟦", "Digital", "Part digitale"),
    ("PHYSIQUE", "🏢", "Physique", "Taux ON TIME"),
    ("RC & SATISFACTION", "😊", "Satisfaction", "Taux de satisfaction"),
    ("MESSAGERIE", "💬", "Messagerie", "Taux clôture WhatsApp"),
    ("CALLCENTER", "🎧", "Call Center", "Taux de décroché"),
    ("DESHERENCE", "📉", "Déshérence", "CP appels entrants"),
]

DESCRIPTIONS = {
    "DIGITAL": "Suivi des usages et de la part des canaux digitaux dans la relation client.",
    "PHYSIQUE": "Performance des agences et respect des délais de traitement en physique.",
    "RC & SATISFACTION": "Réclamations reçues et niveau de satisfaction des assurés.",
    "MESSAGERIE": "Volumes et délais de traitement des échanges WhatsApp et messagerie.",
    "CALLCENTER": "Décroché, volumes d'appels et qualité de service du centre d'appels.",
    "DESHERENCE": "Suivi des contrats en déshérence et des appels entrants associés.",
}


# ============================================================
# UTILITAIRES
# ============================================================

def _format_value(valeur, unite: str = "") -> str:

    if valeur is None:
        return "—"

    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return str(valeur)

    if unite == "%":
        return f"{valeur:.1f}%"

    if unite:
        return f"{valeur:,.1f} {unite}".replace(",", " ")

    return f"{valeur:,.1f}".replace(",", " ")


def _status(valeur, objectif, direction: str = "higher") -> str:

    if valeur is None or objectif is None:
        return "neutral"

    try:
        valeur = float(valeur)
        objectif = float(objectif)
    except (TypeError, ValueError):
        return "neutral"

    if direction == "lower":
        if valeur <= objectif:
            return "good"
        if valeur <= objectif * 1.1:
            return "warn"
        return "bad"

    if valeur >= objectif:
        return "good"
    if valeur >= objectif - 5:
        return "warn"
    return "bad"


def _kpi_global(df: pd.DataFrame, nom_base: str, nom_kpi: str):

    builder = KPI_BUILDERS.get(nom_base)

    if builder is None:
        return None

    try:
        liste_kpi = builder(df)
    except Exception:
        return None

    for kpi in liste_kpi:
        if kpi["name"] == nom_kpi:
            return kpi

    return None


# ============================================================
# RENDU
# ============================================================

def render(dex: dict | None = None):

    # --------------------------------------------------------
    # EN-TÊTE
    # --------------------------------------------------------

    page_header(
        "Accueil",
        "Vue d'ensemble de l'expérience client — Groupe NSIA",
    )

    if not dex:

        render_html(
            """
            <div class="nsia-panel" style="text-align:center; padding:2.2rem 1.5rem;">
                <div style="font-size:1.05rem; font-weight:800; color:#102044;">
                    👋 Bienvenue sur le Dashboard NSIA — Expérience Client
                </div>
                <div style="margin-top:0.6rem; color:#71809A; font-size:0.88rem;">
                    Importez la base DEX centrale depuis le menu à gauche pour
                    activer la vue d'ensemble des 6 domaines suivis.
                </div>
            </div>
            """
        )

        return

    debut, fin = plage_dates_dex(dex)

    periode_txt = (
        f"Données du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}"
        if debut is not None and fin is not None
        else "Période de données non disponible"
    )

    # --------------------------------------------------------
    # BANNIÈRE DE BIENVENUE
    # --------------------------------------------------------

    render_html(
        f"""
        <div class="nsia-panel" style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:1rem;
            flex-wrap:wrap;
            margin-bottom:0.4rem;
        ">
            <div>
                <div style="font-size:1.15rem; font-weight:850; color:#102044;">
                    👋 Bienvenue sur votre espace de pilotage
                </div>
                <div style="margin-top:0.3rem; color:#71809A; font-size:0.85rem;">
                    Cette application centralise la performance de l'expérience
                    client à partir de la base DEX, sur les six métiers du groupe.
                </div>
            </div>
            <div class="badge" style="background:#E9F8F0; color:#20A464;">
                ✅ Base DEX active
            </div>
        </div>
        """
    )

    st.caption(f"🗓️ {periode_txt}")

    # --------------------------------------------------------
    # VUE D'ENSEMBLE — KPI PRINCIPAUX
    # --------------------------------------------------------

    section("Vue d'ensemble des 6 domaines")

    st.caption(
        "Indicateur clé de chaque domaine, calculé sur l'ensemble "
        "de la base DEX importée."
    )

    colonnes = st.columns(3)

    for index, (nom_base, icone, label, nom_kpi) in enumerate(DOMAINES):

        df = dex.get(nom_base)

        kpi = (
            _kpi_global(df, nom_base, nom_kpi)
            if isinstance(df, pd.DataFrame)
            else None
        )

        if kpi is None:

            with colonnes[index % 3]:

                kpi_card(
                    icone,
                    label,
                    "—",
                    "Donnée indisponible",
                    "neutral",
                )

            continue

        valeur = kpi.get("value")
        unite = kpi.get("unit", "%")
        objectif = kpi.get("objective")
        direction = kpi.get("direction", "higher")

        sous_texte = (
            f"Objectif {_format_value(objectif, unite)}"
            if objectif is not None
            else nom_kpi
        )

        with colonnes[index % 3]:

            kpi_card(
                icone,
                f"{label} — {nom_kpi}",
                _format_value(valeur, unite),
                sous_texte,
                _status(valeur, objectif, direction),
            )

    # --------------------------------------------------------
    # VOLUMES DE DONNÉES
    # --------------------------------------------------------

    section("Volumes de données par domaine")

    colonnes = st.columns(6)

    for index, (nom_base, icone, label, _) in enumerate(DOMAINES):

        df = dex.get(nom_base)

        volume = (
            f"{len(df):,}".replace(",", " ")
            if isinstance(df, pd.DataFrame)
            else "—"
        )

        with colonnes[index]:

            render_html(
                f"""
                <div class="profile-card" style="text-align:center; min-height:100px;">
                    <div style="font-size:1.3rem;">{icone}</div>
                    <div style="
                        margin-top:0.35rem;
                        font-size:0.63rem;
                        font-weight:750;
                        letter-spacing:0.04em;
                        text-transform:uppercase;
                        color:#8290A8;
                    ">
                        {label}
                    </div>
                    <div style="
                        margin-top:0.25rem;
                        font-size:1.15rem;
                        font-weight:850;
                        color:#102044;
                    ">
                        {volume}
                    </div>
                </div>
                """
            )

    # --------------------------------------------------------
    # ACCÈS RAPIDE AUX DOMAINES
    # --------------------------------------------------------

    section("Accès rapide")

    st.caption(
        "Retrouvez le détail de chaque domaine via le menu de "
        "navigation à gauche."
    )

    colonnes = st.columns(3)

    for index, (nom_base, icone, label, _) in enumerate(DOMAINES):

        with colonnes[index % 3]:

            render_html(
                f"""
                <div class="profile-card" style="min-height:118px; margin-bottom:0.9rem;">
                    <div style="display:flex; align-items:center; gap:0.55rem;">
                        <div style="font-size:1.2rem;">{icone}</div>
                        <div style="font-weight:800; color:#102044; font-size:0.92rem;">
                            {label}
                        </div>
                    </div>
                    <div style="margin-top:0.5rem; font-size:0.76rem; color:#71809A;">
                        {DESCRIPTIONS.get(nom_base, "")}
                    </div>
                </div>
                """
            )

    # --------------------------------------------------------
    # PIED DE PAGE INFORMATIF
    # --------------------------------------------------------

    st.success(
        "✅ La base DEX centrale constitue la source unique des "
        "données du dashboard. Rendez-vous dans « 📊 Point Global » "
        "pour l'analyse détaillée par période et par agence."
    )
