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


def _fmt_fcfa(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f}".replace(",", " ") + " FCFA"


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
# de la feuille "DESHERENCE"
# ============================================================

def _kpi_periode(df: pd.DataFrame) -> dict:
    dossiers_ouverts = _num(df, "Dossiers ouverts")
    dossiers_traites = _num(df, "Dossiers traités")
    montant_recupere = _num(df, "Montant récupéré (FCFA)")
    contacts_reussis = _num(df, "Contacts réussis")

    taux_traitement = _ratio(dossiers_traites, dossiers_ouverts)
    taux_contact = _ratio(contacts_reussis, dossiers_ouverts)
    montant_moyen = (montant_recupere / dossiers_traites) if dossiers_traites > 0 else None

    return {
        "dossiers_ouverts": dossiers_ouverts,
        "dossiers_traites": dossiers_traites,
        "montant_recupere": montant_recupere,
        "contacts_reussis": contacts_reussis,
        "taux_traitement": taux_traitement,
        "taux_contact": taux_contact,
        "montant_moyen": montant_moyen,
    }


def _evolution_data(df_annee: pd.DataFrame, granularite: str):
    periodes = construire_periodes(df_annee[["Date"]], granularite)

    labels = []
    series = {
        "Taux de traitement": [],
        "Taux de contact réussi": [],
    }

    for periode in periodes:
        df_p = _filtrer_periode(df_annee, periode)
        k = _kpi_periode(df_p)

        values = [k["taux_traitement"], k["taux_contact"]]
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
        ("Taux de traitement", GREEN_ACCENT, 4),
        ("Taux de contact réussi", BLUE_ACCENT, 3),
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

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=65, b=25),
        title=dict(text=f"Évolution du traitement des dossiers — {annee}", font=dict(size=17, color="#FFFFFF"), x=0.01),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=NAVY_DARK,
        font=dict(family="Inter, Arial", color="#EAF0FA"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(ticksuffix="%", showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False, tickfont=dict(size=10)),
    )

    # Clé FIXE (ne dépend pas des filtres) : évite le remount du composant
    # à chaque changement de filtre, source de l'erreur React removeChild/insertBefore.
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="desherence_evolution_chart",
    )


def _plot_volumes(df_actuel: pd.DataFrame, df_precedent: pd.DataFrame, periode: Periode, periode_avant: Periode):
    labels = [periode_avant.label, periode.label]

    ouverts = [_num(df_precedent, "Dossiers ouverts"), _num(df_actuel, "Dossiers ouverts")]
    traites = [_num(df_precedent, "Dossiers traités"), _num(df_actuel, "Dossiers traités")]

    fig = go.Figure()

    fig.add_trace(go.Bar(x=labels, y=ouverts, name="Dossiers ouverts", marker_color=BLUE_ACCENT))
    fig.add_trace(go.Bar(x=labels, y=traites, name="Dossiers traités", marker_color=GREEN_ACCENT))

    fig.update_layout(
        height=420,
        barmode="group",
        margin=dict(l=20, r=20, t=65, b=25),
        title=dict(text="Volumes — dossiers ouverts vs traités", font=dict(size=17, color="#FFFFFF"), x=0.01),
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
        key="desherence_volumes_chart",
    )


# ============================================================
# TABLEAU DE PILOTAGE — Initiatives & contre-performances
# ============================================================
# C'est ce qui distingue cet onglet d'un simple onglet analytique :
# les colonnes "CP ..." (contre-performances / points bloquants signalés)
# et "INITIA ..." (initiatives / actions menées) sont des observations
# terrain en texte libre. On les remonte telles quelles, datées, pour que
# le pilote puisse voir QUOI a été fait / QUOI a bloqué, pas seulement
# des volumes chiffrés.

def _tableau_pilotage(df_actuel: pd.DataFrame):
    colonnes_pilotage = [
        "Date",
        "CP Appels Entrants",
        "CP Appels Sortants",
        "INITIA Appels Entrants",
        "INITIA Appels Sortants",
    ]

    colonnes_presentes = [c for c in colonnes_pilotage if c in df_actuel.columns]

    if "Date" not in colonnes_presentes:
        st.info("Colonne Date absente : impossible d'afficher le tableau de pilotage.")
        return

    base = df_actuel[colonnes_presentes].copy()

    texte_cols = [c for c in colonnes_presentes if c != "Date"]

    # On ne garde que les jours où au moins une observation (CP ou INITIA) a été saisie
    masque = pd.Series(False, index=base.index)
    for c in texte_cols:
        masque = masque | base[c].notna()

    base = base.loc[masque].copy()

    if base.empty:
        st.info("Aucune initiative ni contre-performance signalée sur la période sélectionnée.")
        return

    base["Date"] = pd.to_datetime(base["Date"], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")
    base = base.sort_values("Date")

    renommage = {
        "CP Appels Entrants": "⚠️ Contre-perf. — Entrants",
        "CP Appels Sortants": "⚠️ Contre-perf. — Sortants",
        "INITIA Appels Entrants": "✅ Initiative — Entrants",
        "INITIA Appels Sortants": "✅ Initiative — Sortants",
    }
    base = base.rename(columns=renommage)

    for c in base.columns:
        if c != "Date":
            base[c] = base[c].fillna("—")

    st.dataframe(base, use_container_width=True, height=320, hide_index=True)

    # Synthèse rapide : quelles initiatives / contre-performances reviennent le plus
    synth_cols = st.columns(2)

    with synth_cols[0]:
        cp_all = pd.concat(
            [
                df_actuel.get("CP Appels Entrants"),
                df_actuel.get("CP Appels Sortants"),
            ]
        ).dropna()

        if not cp_all.empty:
            top_cp = cp_all.value_counts().head(3)
            st.caption("⚠️ **Contre-performances les plus signalées**")
            for libelle, occ in top_cp.items():
                st.caption(f"• {libelle} — {int(occ)} occurrence(s)")
        else:
            st.caption("⚠️ Aucune contre-performance signalée sur la période.")

    with synth_cols[1]:
        init_all = pd.concat(
            [
                df_actuel.get("INITIA Appels Entrants"),
                df_actuel.get("INITIA Appels Sortants"),
            ]
        ).dropna()

        if not init_all.empty:
            top_init = init_all.value_counts().head(3)
            st.caption("✅ **Initiatives les plus menées**")
            for libelle, occ in top_init.items():
                st.caption(f"• {libelle} — {int(occ)} occurrence(s)")
        else:
            st.caption("✅ Aucune initiative signalée sur la période.")


# ============================================================
# RENDER
# ============================================================

def render(df: pd.DataFrame):
    st.markdown("## 📉 Déshérence")
    st.caption("Pilotage du traitement des dossiers en déshérence : volumes, montants récupérés, initiatives et contre-performances terrain.")

    if df is None or df.empty:
        st.warning("Aucune donnée disponible dans la base DESHERENCE.")
        return

    if "Date" not in df.columns:
        st.warning("La colonne Date n'est pas présente dans la base Déshérence.")
        return

    df = _prepare_dates(df)

    if df.empty:
        st.warning("Aucune date exploitable dans la base Déshérence.")
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
            key="desherence_granularite",
        )

    annees = sorted(df["Date"].dt.year.dropna().astype(int).unique().tolist())
    if not annees:
        st.warning("Aucune année disponible.")
        return

    with f2:
        annee_sel = st.selectbox("Année", annees, index=len(annees) - 1, key="desherence_annee")

    df_annee = df.loc[df["Date"].dt.year == int(annee_sel)].copy()

    periodes = construire_periodes(df_annee[["Date"]], granularite)
    if not periodes:
        st.warning(f"Aucune période disponible pour {annee_sel}.")
        return

    with f3:
        labels = [p.label for p in periodes]
        periode_label = st.selectbox("Période", labels, index=len(labels) - 1, key="desherence_periode")

    periode = next(p for p in periodes if p.label == periode_label)
    periode_avant = periode_precedente(periode)

    df_actuel = _filtrer_periode(df, periode)
    df_precedent = _filtrer_periode(df, periode_avant)

    k_actuel = _kpi_periode(df_actuel)
    k_precedent = _kpi_periode(df_precedent)

    st.info(
        f"📅 **{periode.label}** : {periode.debut.strftime('%d/%m/%Y')} → {periode.fin.strftime('%d/%m/%Y')} "
        f"| Comparaison : **{periode_avant.label}**"
    )

    # --------------------------------------------------------
    # KPI PRINCIPAUX
    # --------------------------------------------------------

    section("INDICATEURS CLÉS — DÉSHÉRENCE")

    cards_pct = [
        ("📂", "Dossiers ouverts", k_actuel["dossiers_ouverts"], k_precedent["dossiers_ouverts"], False, None, "Volume ouvert sur la période"),
        ("✅", "Dossiers traités", k_actuel["dossiers_traites"], k_precedent["dossiers_traites"], False, None, "Volume traité sur la période"),
        ("🎯", "Taux de traitement", k_actuel["taux_traitement"], k_precedent["taux_traitement"], True, 80, "Traités vs ouverts"),
        ("💰", "Montant récupéré", k_actuel["montant_recupere"], k_precedent["montant_recupere"], False, None, "Cumul FCFA sur la période"),
    ]

    cols = st.columns(4)

    for col, (icon, name, value, previous, is_pct, target, description) in zip(cols, cards_pct):
        with col:
            if is_pct:
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
            elif name == "Montant récupéré":
                variation = _variation_relative(value, previous)
                comparaison = f"{_fmt_variation(variation)} vs période précédente" if variation is not None else "Pas de comparaison disponible"
                affichage = _fmt_fcfa(value)
                status = "neutral"
            else:
                variation = _variation_relative(value, previous)
                comparaison = f"{_fmt_variation(variation)} vs période précédente" if variation is not None else "Pas de comparaison disponible"
                affichage = _fmt_number(value)
                status = "neutral"

            kpi_card(icon, name, affichage, f"{comparaison} · {description}", status)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    cards_secondaires = [
        ("📞", "Contacts réussis", k_actuel["contacts_reussis"], k_precedent["contacts_reussis"], "Nombre de débiteurs effectivement joints"),
        ("📊", "Montant moyen récupéré / dossier traité", k_actuel["montant_moyen"], k_precedent["montant_moyen"], "Aide à la décision : rendement moyen par dossier"),
    ]

    cols2 = st.columns(2)

    for col, (icon, name, value, previous, description) in zip(cols2, cards_secondaires):
        with col:
            variation = _variation_relative(value, previous)
            comparaison = f"{_fmt_variation(variation)} vs période précédente" if variation is not None else "Pas de comparaison disponible"
            affichage = _fmt_fcfa(value) if "Montant" in name else _fmt_number(value)
            kpi_card(icon, name, affichage, f"{comparaison} · {description}", "neutral")

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

    # --------------------------------------------------------
    # TABLEAU DE PILOTAGE — Initiatives & contre-performances
    # --------------------------------------------------------

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section("TABLEAU DE PILOTAGE — INITIATIVES & CONTRE-PERFORMANCES")

    st.caption(
        "Actions menées et points bloquants signalés au jour le jour sur la période sélectionnée "
        "— pour piloter, pas seulement mesurer."
    )

    _tableau_pilotage(df_actuel)

    # --------------------------------------------------------
    # DONNÉES DE LA PÉRIODE
    # --------------------------------------------------------

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section("DONNÉES DE LA PÉRIODE")

    st.caption(f"{len(df_actuel)} ligne(s) pour la période sélectionnée.")

    if df_actuel.empty:
        st.info("Aucune donnée pour cette période.")
    else:
        st.dataframe(df_actuel, use_container_width=True, height=380)