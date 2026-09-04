from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from periods import GRANULARITES, Periode, construire_periodes, periode_precedente
from theme import BLUE_ACCENT, GOLD, GREEN_ACCENT, NAVY_DARK, kpi_card, section, status_for


# ============================================================
# UTILITAIRES
# ============================================================

def _prepare_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Date" not in out.columns:
        return out
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce", dayfirst=True).dt.normalize()
    return out.dropna(subset=["Date"])


def _num(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator * 100.0


def _filtrer_periode(df: pd.DataFrame, periode: Periode) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    dates = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True).dt.normalize()
    return df.loc[dates.between(periode.debut, periode.fin, inclusive="both")].copy()


def _fmt_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.1f}%"


def _fmt_number(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f}".replace(",", " ")


def _variation_relative(actuel: float | None, precedent: float | None) -> float | None:
    """Variation en % RELATIF (et non en points) : ((actuel - précédent) / précédent) * 100."""
    if actuel is None or precedent is None or precedent == 0:
        return None
    return (actuel - precedent) / precedent * 100.0


def _fmt_variation(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:+.1f}%"


def _periode_libelle(periode: Periode) -> str:
    if periode.granularite == "Journalier":
        return periode.debut.strftime("%d/%m")
    return periode.label


# ============================================================
# KPI — construits uniquement à partir des colonnes réelles
# de la feuille "CALLCENTER"
# ============================================================

def _kpi_periode(df: pd.DataFrame) -> dict:
    recus = _num(df, "Appels reçus")
    decroches = _num(df, "Appels décrochés")
    dans_delai = _num(df, "Appels reçus dans le délai")

    emis = _num(df, "Appels émis")
    objectif_emis = _num(df, "Objectif appels émis")

    rdv_pris = _num(df, "RDV pris")
    appels_pour_rdv = _num(df, "Appels pour RDV")

    return {
        "recus": recus,
        "decroches": decroches,
        "emis": emis,
        "taux_decroche": _ratio(decroches, recus),
        "taux_dans_delai": _ratio(dans_delai, recus),
        "taux_realisation_emis": _ratio(emis, objectif_emis),
        "taux_rdv_pris": _ratio(rdv_pris, appels_pour_rdv),
    }


def _evolution_data(df_annee: pd.DataFrame, granularite: str):
    periodes = construire_periodes(df_annee[["Date"]], granularite)

    labels = []
    series = {
        "Taux de décroché": [],
        "Taux appels dans le délai": [],
    }

    for periode in periodes:
        df_p = _filtrer_periode(df_annee, periode)
        k = _kpi_periode(df_p)

        values = [k["taux_decroche"], k["taux_dans_delai"]]
        if all(v is None for v in values):
            continue

        labels.append(_periode_libelle(periode))
        for name, value in zip(series.keys(), values):
            series[name].append(value)

    return labels, series


def _plot_evolution(labels, series, annee):
    if not labels:
        st.info("Pas assez de données pour afficher l'évolution.")
        return

    fig = go.Figure()

    traces = [
        ("Taux de décroché", GREEN_ACCENT, 4),
        ("Taux appels dans le délai", BLUE_ACCENT, 3),
    ]

    for name, color, width in traces:
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=series[name],
                mode="lines+markers",
                name=name,
                connectgaps=False,
                line=dict(color=color, width=width, shape="spline"),
                marker=dict(size=7, color=color, line=dict(width=1, color="#FFFFFF")),
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br><b>%{{y:.1f}}%</b><extra></extra>",
            )
        )

    fig.add_hline(
        y=100,
        line_dash="dash",
        line_width=1.3,
        line_color="rgba(255,255,255,0.35)",
        annotation_text="Objectif 100%",
        annotation_position="top left",
    )

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=65, b=25),
        title=dict(text=f"Évolution des taux d'accueil — {annee}", font=dict(size=17, color="#FFFFFF"), x=0.01),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=NAVY_DARK,
        font=dict(family="Inter, Arial", color="#EAF0FA"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(range=[0, 105], ticksuffix="%", showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False, tickfont=dict(size=10)),
    )

    # Clé FIXE (ne dépend pas des filtres) : évite le remount du composant
    # à chaque changement de filtre, source de l'erreur React removeChild/insertBefore.
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="callcenter_evolution_chart",
    )


def _plot_volumes(df_actuel: pd.DataFrame, df_precedent: pd.DataFrame, periode: Periode, periode_avant: Periode):
    labels = [periode_avant.label, periode.label]

    recus = [_num(df_precedent, "Appels reçus"), _num(df_actuel, "Appels reçus")]
    decroches = [_num(df_precedent, "Appels décrochés"), _num(df_actuel, "Appels décrochés")]
    emis = [_num(df_precedent, "Appels émis"), _num(df_actuel, "Appels émis")]
    objectif = [_num(df_precedent, "Objectif appels émis"), _num(df_actuel, "Objectif appels émis")]

    fig = go.Figure()

    fig.add_trace(go.Bar(x=labels, y=recus, name="Appels reçus", marker_color=BLUE_ACCENT))
    fig.add_trace(go.Bar(x=labels, y=decroches, name="Appels décrochés", marker_color=GREEN_ACCENT))
    fig.add_trace(go.Bar(x=labels, y=emis, name="Appels émis", marker_color=GOLD))
    fig.add_trace(go.Bar(x=labels, y=objectif, name="Objectif appels émis", marker_color="#8B5CF6"))

    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=20, r=20, t=65, b=25),
        title=dict(text="Volumes — entrants (reçus/décrochés) vs sortants (émis/objectif)", font=dict(size=17, color="#FFFFFF"), x=0.01),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=NAVY_DARK,
        font=dict(family="Inter, Arial", color="#EAF0FA"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False, tickfont=dict(size=10)),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="callcenter_volumes_chart",
    )


# ============================================================
# RENDER
# ============================================================

def render(df: pd.DataFrame):
    st.markdown("## 🎧 Call Center")
    st.caption("Suivi des appels entrants (décroché, délai) et sortants (émission, RDV).")

    if df is None or df.empty:
        st.warning("Aucune donnée disponible dans la base CALLCENTER.")
        return

    if "Date" not in df.columns:
        st.warning("La colonne Date n'est pas présente dans la base Call Center.")
        return

    df = _prepare_dates(df)

    if df.empty:
        st.warning("Aucune date exploitable dans la base Call Center.")
        return

    # --------------------------------------------------------
    # FILTRES
    # --------------------------------------------------------

    section("FILTRES DE PILOTAGE")

    f1, f2, f3 = st.columns([1, 1, 1.6])

    with f1:
        granularite = st.selectbox(
            "Granularité",
            GRANULARITES,
            index=GRANULARITES.index("Mensuel") if "Mensuel" in GRANULARITES else 0,
            key="callcenter_granularite",
        )

    annees = sorted(df["Date"].dt.year.dropna().astype(int).unique().tolist())
    if not annees:
        st.warning("Aucune année disponible.")
        return

    with f2:
        annee_sel = st.selectbox("Année", annees, index=len(annees) - 1, key="callcenter_annee")

    df_annee = df.loc[df["Date"].dt.year == int(annee_sel)].copy()

    periodes = construire_periodes(df_annee[["Date"]], granularite)
    if not periodes:
        st.warning(f"Aucune période disponible pour {annee_sel}.")
        return

    with f3:
        labels = [p.label for p in periodes]
        periode_label = st.selectbox("Période", labels, index=len(labels) - 1, key="callcenter_periode")

    periode = next(p for p in periodes if p.label == periode_label)
    periode_avant = periode_precedente(periode)

    df_actuel = _filtrer_periode(df, periode)
    df_precedent = _filtrer_periode(df, periode_avant)

    k_actuel = _kpi_periode(df_actuel)
    k_precedent = _kpi_periode(df_precedent)

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    section("INDICATEURS CLÉS — CALL CENTER")

    cards = [
        ("📞", "Taux de décroché", k_actuel["taux_decroche"], k_precedent["taux_decroche"], 100, "Cible 100%"),
        ("⏱️", "Taux appels dans le délai", k_actuel["taux_dans_delai"], k_precedent["taux_dans_delai"], 100, "Cible 100%"),
        ("📤", "Taux réalisation appels émis", k_actuel["taux_realisation_emis"], k_precedent["taux_realisation_emis"], 100, "Émis vs objectif"),
        ("🗓️", "Taux de RDV pris", k_actuel["taux_rdv_pris"], k_precedent["taux_rdv_pris"], 100, "RDV pris vs appels pour RDV"),
    ]

    cols = st.columns(4)

    for col, (icon, name, value, previous, target, description) in zip(cols, cards):
        with col:
            variation = _variation_relative(value, previous)
            comparaison = f"{_fmt_variation(variation)} vs période précédente" if variation is not None else "Pas de comparaison disponible"
            affichage = _fmt_pct(value)

            if value is None:
                status = "neutral"
            else:
                try:
                    status = status_for(float(value) / 100.0, float(target) / 100.0)
                except Exception:
                    status = "neutral"

            kpi_card(icon, name, affichage, f"{comparaison} · {description}", status)

    # --------------------------------------------------------
    # GRAPHIQUES (2)
    # --------------------------------------------------------

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section("ÉVOLUTION")

    g1, g2 = st.columns(2)

    with g1:
        labels_evo, series_evo = _evolution_data(df_annee, granularite)
        _plot_evolution(labels_evo, series_evo, annee_sel)

    with g2:
        _plot_volumes(df_actuel, df_precedent, periode, periode_avant)