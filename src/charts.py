"""
Graphiques réutilisables pour les onglets NSIA DEX.

Objectif : offrir aux onglets métiers (Digital, Physique, Satisfaction,
Réclamations, Messagerie, Déshérence) les mêmes briques visuelles que
« Point Global », sans dupliquer le code ni modifier la structure
existante des pages.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from periods import construire_periodes, filtrer_periode


PALETTE = [
    "#1769E0",
    "#D6A84F",
    "#20A464",
    "#7048E8",
    "#F59E0B",
    "#E5484D",
]


def trend_chart(labels, valeurs, titre, couleur="#1769E0", objectif=None, unite="%"):
    """Courbe d'évolution dans le style de Point Global."""

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=valeurs,
            mode="lines+markers",
            name=titre,
            line=dict(color=couleur, width=3, shape="spline"),
            marker=dict(size=7, color=couleur, line=dict(color="#FFFFFF", width=2)),
            hovertemplate="<b>%{x}</b><br>" + titre + " : %{y:.1f}<extra></extra>",
        )
    )

    if objectif is not None:
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=[objectif] * len(labels),
                mode="lines",
                name="Objectif",
                line=dict(color="#D6A84F", width=2, dash="dash"),
                hovertemplate="Objectif : %{y:.1f}<extra></extra>",
            )
        )

    fig.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Arial", color="#51617D"),
        title=dict(text=titre, font=dict(size=14, color="#102044"), x=0.02),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        xaxis=dict(showgrid=False, linecolor="#E5EAF3", tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", zeroline=False, tickfont=dict(size=10)),
    )

    return fig


def bar_chart_categories(categories, valeurs, titre, couleur="#1769E0", unite=""):
    """Barres par catégorie (agence, canal, ...) dans le style Point Global."""

    if not categories:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=categories,
            y=valeurs,
            marker_color=couleur,
            text=[f"{v:,.0f}".replace(",", " ") + (f" {unite}" if unite else "") for v in valeurs],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:,.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Arial", color="#51617D"),
        title=dict(text=titre, font=dict(size=14, color="#102044"), x=0.02),
        showlegend=False,
        xaxis=dict(showgrid=False, linecolor="#E5EAF3", tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", zeroline=False, tickfont=dict(size=10)),
    )

    return fig


def grouped_bar_categories(categories, series, titre, couleurs=None):
    """Barres groupées par catégorie. `series` = {nom_serie: [valeurs...]}"""

    if not categories or not series:
        return None

    couleurs = couleurs or PALETTE

    fig = go.Figure()

    for i, (nom, valeurs) in enumerate(series.items()):
        fig.add_trace(
            go.Bar(
                name=nom,
                x=categories,
                y=valeurs,
                marker_color=couleurs[i % len(couleurs)],
                hovertemplate="<b>%{x}</b><br>" + nom + " : %{y:,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="group",
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Arial", color="#51617D"),
        title=dict(text=titre, font=dict(size=14, color="#102044"), x=0.02),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, linecolor="#E5EAF3", tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", zeroline=False, tickfont=dict(size=10)),
    )

    return fig


def serie_kpi_par_periode(df, granularite, kpi_builder, nom_kpi, date_col="Date", max_points=12):
    """Reconstruit labels/valeurs/objectif/unité pour un KPI, période par période,
    pour la granularité choisie, à partir des dates réellement disponibles."""

    if df is None or df.empty or date_col not in df.columns:
        return [], [], None, "%"

    periodes = construire_periodes(df, granularite, date_col=date_col)

    if not periodes:
        return [], [], None, "%"

    periodes = periodes[-max_points:]

    labels, valeurs = [], []
    objectif, unite = None, "%"

    for periode in periodes:

        sous_df = filtrer_periode(df, periode, date_col=date_col)

        try:
            kpis = kpi_builder(sous_df)
        except Exception:
            kpis = []

        kpi = next((k for k in kpis if k["name"] == nom_kpi), None)

        labels.append(periode.label)

        if kpi is None:
            valeurs.append(None)
            continue

        valeur = kpi.get("value")

        try:
            valeur = float(valeur) if valeur is not None else None
        except (TypeError, ValueError):
            valeur = None

        valeurs.append(valeur)
        objectif = kpi.get("objective", objectif)
        unite = kpi.get("unit", unite)

    return labels, valeurs, objectif, unite


def afficher_tendance(df, granularite, kpi_builder, nom_kpi, couleur="#1769E0", key=None):
    """
    Calcule et affiche directement une courbe de tendance pour un KPI donné.
    Version stable sans erreur NotFoundError.
    """
    labels, valeurs, objectif, unite = serie_kpi_par_periode(df, granularite, kpi_builder, nom_kpi)

    if not any(v is not None for v in valeurs):
        return

    fig = trend_chart(labels, valeurs, nom_kpi, couleur=couleur, objectif=objectif, unite=unite)

    # Utiliser une clé fixe pour éviter les erreurs de réconciliation React
    # La clé est composée du nom du KPI + un identifiant stable
    chart_key = f"trend_{nom_kpi.replace(' ', '_')}_{granularite}"
    if key:
        chart_key = f"{chart_key}_{key}"

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=chart_key)


def afficher_repartition_agence(df, agence_col, value_cols, titre, key=None):
    """Barres groupées : somme des colonnes numériques indiquées, par agence."""

    if df is None or df.empty or agence_col not in df.columns:
        return

    cols_presentes = [c for c in value_cols if c in df.columns]

    if not cols_presentes:
        return

    groupe = df.copy()
    groupe[agence_col] = groupe[agence_col].astype(str).str.strip()
    groupe = groupe[groupe[agence_col] != ""]

    if groupe.empty:
        return

    for c in cols_presentes:
        groupe[c] = pd.to_numeric(groupe[c], errors="coerce").fillna(0)

    agg = groupe.groupby(agence_col)[cols_presentes].sum().reset_index()
    agg = agg.sort_values(cols_presentes[0], ascending=False)

    series = {c: agg[c].tolist() for c in cols_presentes}

    fig = grouped_bar_categories(agg[agence_col].tolist(), series, titre)

    if fig is not None:
        chart_key = f"bar_{titre.replace(' ', '_')}"
        if key:
            chart_key = f"{chart_key}_{key}"
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=chart_key)