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


def _fmt_pts(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):+.1f} pts"


def _variation_pts(actuel: float | None, precedent: float | None) -> float | None:
    if actuel is None or precedent is None:
        return None
    return actuel - precedent


def _periode_libelle(periode: Periode) -> str:
    if periode.granularite == "Journalier":
        return periode.debut.strftime("%d/%m")
    return periode.label


# ============================================================
# KPI — construits uniquement à partir des colonnes réelles
# de la feuille "MESSAGERIE"
# ============================================================

def _kpi_periode(df: pd.DataFrame) -> dict:
    whatsapp_recues = _num(df, "WhatsApp reçues")
    whatsapp_cloturees = _num(df, "WhatsApp clôturées")

    mail_recus = _num(df, "Mail reçus")
    mail_clotures = _num(df, "Mail clôturés")

    return {
        "whatsapp_recues": whatsapp_recues,
        "taux_whatsapp": _ratio(whatsapp_cloturees, whatsapp_recues),
        "mail_recus": mail_recus,
        "taux_mail": _ratio(mail_clotures, mail_recus),
        "whatsapp_cloturees": whatsapp_cloturees,
        "mail_clotures": mail_clotures,
    }


def _evolution_data(df_annee: pd.DataFrame, granularite: str):
    periodes = construire_periodes(df_annee[["Date"]], granularite)

    labels = []
    series = {
        "Taux clôture WhatsApp": [],
        "Taux clôture Mail": [],
    }

    for periode in periodes:
        df_p = _filtrer_periode(df_annee, periode)
        k = _kpi_periode(df_p)

        values = [k["taux_whatsapp"], k["taux_mail"]]
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
        ("Taux clôture WhatsApp", GREEN_ACCENT, 4),
        ("Taux clôture Mail", BLUE_ACCENT, 3),
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
        title=dict(text=f"Évolution des taux de clôture — {annee}", font=dict(size=17, color="#FFFFFF"), x=0.01),
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
        key="messagerie_evolution_chart",
    )


def _plot_volumes(df_actuel: pd.DataFrame, df_precedent: pd.DataFrame, periode: Periode, periode_avant: Periode):
    labels = [periode_avant.label, periode.label]

    whatsapp_recues = [_num(df_precedent, "WhatsApp reçues"), _num(df_actuel, "WhatsApp reçues")]
    whatsapp_cloturees = [_num(df_precedent, "WhatsApp clôturées"), _num(df_actuel, "WhatsApp clôturées")]
    mail_recus = [_num(df_precedent, "Mail reçus"), _num(df_actuel, "Mail reçus")]
    mail_clotures = [_num(df_precedent, "Mail clôturés"), _num(df_actuel, "Mail clôturés")]

    fig = go.Figure()

    fig.add_trace(go.Bar(x=labels, y=whatsapp_recues, name="WhatsApp reçues", marker_color=BLUE_ACCENT))
    fig.add_trace(go.Bar(x=labels, y=whatsapp_cloturees, name="WhatsApp clôturées", marker_color=GREEN_ACCENT))
    fig.add_trace(go.Bar(x=labels, y=mail_recus, name="Mail reçus", marker_color=GOLD))
    fig.add_trace(go.Bar(x=labels, y=mail_clotures, name="Mail clôturés", marker_color="#8B5CF6"))

    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=20, r=20, t=65, b=25),
        title=dict(text="Volumes — reçues vs clôturées (WhatsApp / Mail)", font=dict(size=17, color="#FFFFFF"), x=0.01),
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
        key="messagerie_volumes_chart",
    )


# ============================================================
# RENDER
# ============================================================

def render(df: pd.DataFrame):
    st.markdown("## 💬 Messagerie")
    st.caption("Suivi des flux WhatsApp et Mail : volumes reçus et taux de clôture.")

    if df is None or df.empty:
        st.warning("Aucune donnée disponible dans la base MESSAGERIE.")
        return

    if "Date" not in df.columns:
        st.warning("La colonne Date n'est pas présente dans la base Messagerie.")
        return

    df = _prepare_dates(df)

    if df.empty:
        st.warning("Aucune date exploitable dans la base Messagerie.")
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
            key="messagerie_granularite",
        )

    annees = sorted(df["Date"].dt.year.dropna().astype(int).unique().tolist())
    if not annees:
        st.warning("Aucune année disponible.")
        return

    with f2:
        annee_sel = st.selectbox("Année", annees, index=len(annees) - 1, key="messagerie_annee")

    df_annee = df.loc[df["Date"].dt.year == int(annee_sel)].copy()

    periodes = construire_periodes(df_annee[["Date"]], granularite)
    if not periodes:
        st.warning(f"Aucune période disponible pour {annee_sel}.")
        return

    with f3:
        labels = [p.label for p in periodes]
        periode_label = st.selectbox("Période", labels, index=len(labels) - 1, key="messagerie_periode")

    periode = next(p for p in periodes if p.label == periode_label)
    periode_avant = periode_precedente(periode)

    df_actuel = _filtrer_periode(df, periode)
    df_precedent = _filtrer_periode(df, periode_avant)

    k_actuel = _kpi_periode(df_actuel)
    k_precedent = _kpi_periode(df_precedent)

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    section("INDICATEURS CLÉS — MESSAGERIE")

    cards = [
        ("💬", "WhatsApp reçues", k_actuel["whatsapp_recues"], k_precedent["whatsapp_recues"], None, "Volume reçu sur la période"),
        ("✅", "Taux clôture WhatsApp", k_actuel["taux_whatsapp"], k_precedent["taux_whatsapp"], 100, "Cible 100%"),
        ("📧", "Mail reçus", k_actuel["mail_recus"], k_precedent["mail_recus"], None, "Volume reçu sur la période"),
        ("✅", "Taux clôture Mail", k_actuel["taux_mail"], k_precedent["taux_mail"], 100, "Cible 100%"),
    ]

    cols = st.columns(4)

    for col, (icon, name, value, previous, target, description) in zip(cols, cards):
        with col:
            is_pct = target is not None

            if is_pct:
                variation = _variation_pts(value, previous)
                comparaison = f"{_fmt_pts(variation)} vs période précédente" if variation is not None else "Pas de comparaison disponible"
                affichage = _fmt_pct(value)

                if value is None:
                    status = "neutral"
                else:
                    try:
                        status = status_for(float(value) / 100.0, float(target) / 100.0)
                    except Exception:
                        status = "neutral"
            else:
                ecart = None if (value is None or previous is None) else value - previous
                comparaison = f"{_fmt_number(ecart)} vs période précédente" if ecart is not None else "Pas de comparaison disponible"
                affichage = _fmt_number(value)
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