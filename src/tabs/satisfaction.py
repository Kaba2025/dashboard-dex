from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from periods import GRANULARITES, Periode, construire_periodes, periode_precedente
from settings import get_csat_barometre
from theme import (
    BLUE_ACCENT,
    GOLD,
    GREEN_ACCENT,
    NAVY_DARK,
    PURPLE_ACCENT,
    kpi_card,
    section,
)


# ============================================================
# UTILITAIRES
# ============================================================

def _prepare_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare la colonne Date.
    """
    out = df.copy()

    if "Date" not in out.columns:
        return out

    out["Date"] = pd.to_datetime(
        out["Date"],
        errors="coerce",
        dayfirst=True,
    ).dt.normalize()

    return out.dropna(subset=["Date"])


def _num(
    df: pd.DataFrame,
    column: str,
) -> float:
    """
    Somme numérique sécurisée d'une colonne.
    """
    if column not in df.columns:
        return 0.0

    return float(
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


def _ratio(
    numerator: float,
    denominator: float,
) -> float | None:
    """
    Retourne un pourcentage.
    """
    if denominator <= 0:
        return None

    return numerator / denominator * 100.0


def _filtrer_periode(
    df: pd.DataFrame,
    periode: Periode,
) -> pd.DataFrame:
    """
    Filtre les données sur une période.
    """
    if df.empty:
        return df.copy()

    dates = pd.to_datetime(
        df["Date"],
        errors="coerce",
        dayfirst=True,
    ).dt.normalize()

    return df.loc[
        dates.between(
            periode.debut,
            periode.fin,
            inclusive="both",
        )
    ].copy()


def _fmt_pct(
    value: float | None,
) -> str:
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.1f}%"


def _fmt_number(
    value: float | None,
) -> str:
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):,.0f}".replace(",", " ")


def _fmt_pts(
    value: float | None,
) -> str:
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):+.1f} pts"


# ============================================================
# KPI
# ============================================================

def _kpi_periode(
    df: pd.DataFrame,
) -> dict:
    """
    Calcule les indicateurs Satisfaction pour une période.
    """

    recueil = _num(
        df,
        "Recueil de satisfaction",
    )

    satisfaits = _num(
        df,
        "Clients satisfaits",
    )

    clients_recus = _num(
        df,
        "Total clients reçus",
    )

    recla_traitees = _num(
        df,
        "Réclamations MOIS traitées dans les délais",
    )

    recla_recues = _num(
        df,
        "Réclamations MOIS reçues",
    )

    # --------------------------------------------------------
    # TAUX
    # --------------------------------------------------------

    taux_satisfaction = _ratio(
        satisfaits,
        recueil,
    )

    taux_recueil = _ratio(
        recueil,
        clients_recus,
    )

    taux_recla_temps = _ratio(
        recla_traitees,
        recla_recues,
    )

    # --------------------------------------------------------
    # BAROMÈTRE
    # --------------------------------------------------------

    try:
        grande_enquete = (
            float(get_csat_barometre()) * 100.0
        )
    except Exception:
        grande_enquete = 68.0

    # --------------------------------------------------------
    # SATISFACTION GLOBALE
    # --------------------------------------------------------

    if (
        taux_satisfaction is not None
        and taux_recla_temps is not None
    ):
        satisfaction_globale = (
            grande_enquete * 0.50
            + taux_satisfaction * 0.25
            + taux_recla_temps * 0.25
        )

    elif taux_satisfaction is not None:

        satisfaction_globale = (
            grande_enquete * 0.50
            + taux_satisfaction * 0.50
        )

    else:

        satisfaction_globale = None

    return {
        "satisfaction_globale": satisfaction_globale,
        "taux_satisfaction": taux_satisfaction,
        "taux_recueil": taux_recueil,
        "taux_recla_temps": taux_recla_temps,
        "grande_enquete": grande_enquete,
        "clients_recus": clients_recus,
        "recueil": recueil,
        "clients_satisfaits": satisfaits,
        "reclamations_recues": recla_recues,
        "reclamations_traitees": recla_traitees,
    }


# ============================================================
# VARIATIONS
# ============================================================

def _variation_pts(
    actuel: float | None,
    precedent: float | None,
) -> float | None:

    if actuel is None or precedent is None:
        return None

    return actuel - precedent


# ============================================================
# LABEL PÉRIODE
# ============================================================

def _periode_libelle(
    periode: Periode,
) -> str:

    if periode.granularite == "Journalier":

        return periode.debut.strftime(
            "%d/%m"
        )

    return periode.label


# ============================================================
# SOUS-PÉRIODES
# ============================================================

def _sous_periodes(
    periode: Periode,
) -> list[Periode]:

    # --------------------------------------------------------
    # JOURNALIER
    # --------------------------------------------------------

    if periode.granularite == "Journalier":
        return [periode]

    # --------------------------------------------------------
    # HEBDOMADAIRE
    # --------------------------------------------------------

    if periode.granularite == "Hebdomadaire":

        result = []

        current = periode.debut

        while current <= periode.fin:

            end = min(
                current + pd.Timedelta(days=6),
                periode.fin,
            )

            result.append(
                Periode(
                    "Hebdomadaire",
                    current,
                    end,
                    (
                        f"S{int(current.isocalendar().week)} "
                        f"({current.strftime('%d/%m')} - "
                        f"{end.strftime('%d/%m')})"
                    ),
                    current.strftime("%Y-%m-%d"),
                )
            )

            current = end + pd.Timedelta(days=1)

        return result

    # --------------------------------------------------------
    # MENSUEL
    # --------------------------------------------------------

    if periode.granularite == "Mensuel":

        result = []

        current = periode.debut.replace(
            day=1
        )

        while current <= periode.fin:

            end = min(
                current + pd.offsets.MonthEnd(1),
                periode.fin,
            )

            result.append(
                Periode(
                    "Mensuel",
                    current,
                    end,
                    current.strftime("%B %Y"),
                    current.strftime("%Y-%m"),
                )
            )

            current = (
                end + pd.Timedelta(days=1)
            ).replace(day=1)

        return result

    # --------------------------------------------------------
    # TRIMESTRIEL / AUTRES
    # --------------------------------------------------------

    result = []

    current = periode.debut.replace(
        day=1
    )

    while current <= periode.fin:

        end = min(
            current + pd.offsets.MonthEnd(1),
            periode.fin,
        )

        result.append(
            Periode(
                "Mensuel",
                current,
                end,
                current.strftime("%B %Y"),
                current.strftime("%Y-%m"),
            )
        )

        current = (
            end + pd.Timedelta(days=1)
        ).replace(day=1)

    return result


# ============================================================
# RÉCAPITULATIF
# ============================================================

def _build_recap(
    df: pd.DataFrame,
    periode: Periode,
) -> pd.DataFrame:

    rows = []

    precedent_global = None

    sous_periodes = _sous_periodes(
        periode
    )

    for sub in sous_periodes:

        df_sub = _filtrer_periode(
            df,
            sub,
        )

        k = _kpi_periode(
            df_sub
        )

        variation = _variation_pts(
            k["satisfaction_globale"],
            precedent_global,
        )

        rows.append(
            {
                "Période":
                    _periode_libelle(sub),

                "Satisfaction globale":
                    k["satisfaction_globale"],

                "Taux de recueil":
                    k["taux_recueil"],

                "Taux de satisfaction":
                    k["taux_satisfaction"],

                "Réclamations traitées à temps":
                    k["taux_recla_temps"],

                "Clients reçus":
                    k["clients_recus"],

                "Réponses":
                    k["recueil"],

                "Variation":
                    variation,
            }
        )

        if k["satisfaction_globale"] is not None:

            precedent_global = (
                k["satisfaction_globale"]
            )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    if len(rows) > 1:

        total = _kpi_periode(
            _filtrer_periode(
                df,
                periode,
            )
        )

        rows.append(
            {
                "Période":
                    f"TOTAL — {periode.label}",

                "Satisfaction globale":
                    total["satisfaction_globale"],

                "Taux de recueil":
                    total["taux_recueil"],

                "Taux de satisfaction":
                    total["taux_satisfaction"],

                "Réclamations traitées à temps":
                    total["taux_recla_temps"],

                "Clients reçus":
                    total["clients_recus"],

                "Réponses":
                    total["recueil"],

                "Variation":
                    None,
            }
        )

    return pd.DataFrame(rows)


def _render_recap_table(
    recap: pd.DataFrame,
) -> None:

    if recap.empty:

        st.info(
            "Aucune donnée disponible "
            "pour cette période."
        )

        return

    display = recap.copy()

    # --------------------------------------------------------
    # POURCENTAGES
    # --------------------------------------------------------

    percentage_columns = [
        "Satisfaction globale",
        "Taux de recueil",
        "Taux de satisfaction",
        "Réclamations traitées à temps",
        "Variation",
    ]

    for column in percentage_columns:

        if column in display.columns:

            display[column] = display[
                column
            ].apply(
                lambda x:
                    "—"
                    if pd.isna(x)
                    else f"{float(x):.1f}%"
            )

    # --------------------------------------------------------
    # VOLUMES
    # --------------------------------------------------------

    for column in [
        "Clients reçus",
        "Réponses",
    ]:

        if column in display.columns:

            display[column] = display[
                column
            ].apply(
                lambda x:
                    "—"
                    if pd.isna(x)
                    else _fmt_number(x)
            )

    # --------------------------------------------------------
    # TABLEAU
    # --------------------------------------------------------

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=min(
            430,
            100 + len(display) * 38,
        ),
        column_config={

            "Période":
                st.column_config.TextColumn(
                    "Période",
                    width="medium",
                ),

            "Satisfaction globale":
                st.column_config.TextColumn(
                    "Satisfaction globale",
                    width="medium",
                ),

            "Taux de recueil":
                st.column_config.TextColumn(
                    "Taux de recueil",
                    width="medium",
                ),

            "Taux de satisfaction":
                st.column_config.TextColumn(
                    "Taux de satisfaction",
                    width="medium",
                ),

            "Réclamations traitées à temps":
                st.column_config.TextColumn(
                    "Réclamations traitées à temps",
                    width="large",
                ),

            "Clients reçus":
                st.column_config.TextColumn(
                    "Clients reçus",
                    width="medium",
                ),

            "Réponses":
                st.column_config.TextColumn(
                    "Réponses",
                    width="medium",
                ),

            "Variation":
                st.column_config.TextColumn(
                    "Variation",
                    width="small",
                ),
        },
    )


# ============================================================
# DONNÉES POUR GRAPHIQUE D'ÉVOLUTION
# ============================================================

def _evolution_data(
    df_annee: pd.DataFrame,
    granularite: str,
):

    periodes = construire_periodes(
        df_annee[["Date"]],
        granularite,
    )

    labels = []

    series = {
        "Satisfaction globale": [],
        "Taux de satisfaction": [],
        "Taux de recueil": [],
        "Réclamations traitées à temps": [],
    }

    for periode in periodes:

        df_p = _filtrer_periode(
            df_annee,
            periode,
        )

        k = _kpi_periode(
            df_p
        )

        values = [
            k["satisfaction_globale"],
            k["taux_satisfaction"],
            k["taux_recueil"],
            k["taux_recla_temps"],
        ]

        if all(
            value is None
            for value in values
        ):
            continue

        labels.append(
            _periode_libelle(periode)
        )

        for name, value in zip(
            series.keys(),
            values,
        ):
            series[name].append(
                value
            )

    return labels, series


# ============================================================
# GRAPHIQUE ÉVOLUTION
# ============================================================

def _plot_evolution(
    labels,
    series,
    granularite,
    annee,
):

    if not labels:

        st.info(
            "Pas assez de données pour afficher "
            "l'évolution."
        )

        return

    fig = go.Figure()

    traces = [

        (
            "Satisfaction globale",
            GREEN_ACCENT,
            4,
        ),

        (
            "Taux de satisfaction",
            BLUE_ACCENT,
            3,
        ),

        (
            "Taux de recueil",
            GOLD,
            3,
        ),

        (
            "Réclamations traitées à temps",
            PURPLE_ACCENT,
            3,
        ),
    ]

    for name, color, width in traces:

        fig.add_trace(
            go.Scatter(
                x=labels,
                y=series[name],
                mode="lines+markers",
                name=name,
                connectgaps=False,

                line=dict(
                    color=color,
                    width=width,
                    shape="spline",
                ),

                marker=dict(
                    size=7,
                    color=color,
                    line=dict(
                        width=1,
                        color="#FFFFFF",
                    ),
                ),

                hovertemplate=(
                    "<b>"
                    + name
                    + "</b><br>"
                    "%{x}<br>"
                    "<b>%{y:.1f}%</b>"
                    "<extra></extra>"
                ),
            )
        )

    # --------------------------------------------------------
    # OBJECTIF
    # --------------------------------------------------------

    fig.add_hline(
        y=75,
        line_dash="dash",
        line_width=1.3,
        line_color="rgba(255,255,255,0.35)",
        annotation_text="Objectif 75%",
        annotation_position="top left",
    )

    fig.update_layout(

        height=430,

        margin=dict(
            l=20,
            r=20,
            t=65,
            b=25,
        ),

        title=dict(
            text=(
                f"Évolution des indicateurs — "
                f"{annee}"
            ),
            font=dict(
                size=17,
                color="#FFFFFF",
            ),
            x=0.01,
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor=NAVY_DARK,

        font=dict(
            family="Inter, Arial",
            color="#EAF0FA",
        ),

        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font=dict(
                size=11,
            ),
        ),

        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            tickfont=dict(
                size=10,
            ),
        ),

        yaxis=dict(
            range=[0, 105],
            ticksuffix="%",
            showgrid=True,
            gridcolor=(
                "rgba(255,255,255,0.08)"
            ),
            zeroline=False,
            tickfont=dict(
                size=10,
            ),
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
        key=(
            "satisfaction_evolution_"
            f"{annee}_{granularite}"
        ),
    )


# ============================================================
# GRAPHIQUE VOLUMES
# ============================================================

def _plot_volumes(
    df_annee: pd.DataFrame,
    granularite: str,
    annee: int,
):

    periodes = construire_periodes(
        df_annee[["Date"]],
        granularite,
    )

    labels = []
    clients = []
    reponses = []
    satisfaits = []

    for periode in periodes:

        df_p = _filtrer_periode(
            df_annee,
            periode,
        )

        k = _kpi_periode(
            df_p
        )

        labels.append(
            _periode_libelle(periode)
        )

        clients.append(
            k["clients_recus"]
        )

        reponses.append(
            k["recueil"]
        )

        satisfaits.append(
            k["clients_satisfaits"]
        )

    if not labels:
        return

    fig = go.Figure()

    # --------------------------------------------------------
    # CLIENTS REÇUS
    # --------------------------------------------------------

    fig.add_trace(
        go.Bar(
            x=labels,
            y=clients,
            name="Clients reçus",
            marker_color=BLUE_ACCENT,
            opacity=0.72,

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Clients reçus : "
                "<b>%{y:,.0f}</b>"
                "<extra></extra>"
            ),
        )
    )

    # --------------------------------------------------------
    # RÉPONSES
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=reponses,
            name="Réponses",
            mode="lines+markers",

            line=dict(
                color=GOLD,
                width=3,
                shape="spline",
            ),

            marker=dict(
                size=7,
                color=GOLD,
                line=dict(
                    width=1,
                    color="#FFFFFF",
                ),
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Réponses : "
                "<b>%{y:,.0f}</b>"
                "<extra></extra>"
            ),
        )
    )

    # --------------------------------------------------------
    # CLIENTS SATISFAITS
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=satisfaits,
            name="Clients satisfaits",
            mode="lines+markers",

            line=dict(
                color=GREEN_ACCENT,
                width=3,
                shape="spline",
            ),

            marker=dict(
                size=7,
                color=GREEN_ACCENT,
                line=dict(
                    width=1,
                    color="#FFFFFF",
                ),
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Clients satisfaits : "
                "<b>%{y:,.0f}</b>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(

        height=390,

        margin=dict(
            l=20,
            r=20,
            t=65,
            b=25,
        ),

        title=dict(
            text=(
                f"Volumes et réponses — "
                f"{annee}"
            ),
            font=dict(
                size=17,
                color="#FFFFFF",
            ),
            x=0.01,
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor=NAVY_DARK,

        font=dict(
            family="Inter, Arial",
            color="#EAF0FA",
        ),

        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font=dict(
                size=11,
            ),
        ),

        xaxis=dict(
            showgrid=False,
            tickfont=dict(
                size=10,
            ),
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor=(
                "rgba(255,255,255,0.08)"
            ),
            zeroline=False,
            tickfont=dict(
                size=10,
            ),
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
        key=(
            "satisfaction_volumes_"
            f"{annee}_{granularite}"
        ),
    )


# ============================================================
# COMMENTAIRES
# ============================================================

def _resume_commentaires(
    df: pd.DataFrame,
) -> None:

    candidates = [
        column
        for column in [
            "Commentaire",
            "Commentaires",
            "Observations",
            "Observation",
        ]
        if column in df.columns
    ]

    if not candidates:

        st.caption(
            "Aucune colonne de commentaires "
            "ou observations n'est disponible."
        )

        return

    values = (
        df[candidates[0]]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[
        values.ne("")
    ]

    if values.empty:

        st.caption(
            "Aucun commentaire renseigné "
            "pour cette période."
        )

        return

    normalized = (
        values.str.replace(
            r"\s+",
            " ",
            regex=True,
        )
    )

    counts = Counter(
        normalized
    )

    for text, count in counts.most_common(8):

        suffix = (
            f" · {count} occurrences"
            if count > 1
            else ""
        )

        st.markdown(
            f"""
            <div style="
                padding:10px 0;
                border-bottom:
                    1px solid
                    rgba(255,255,255,0.06);
                color:
                    rgba(255,255,255,0.82);
                font-size:0.82rem;
            ">
                • {text}
                <span style="
                    color:
                        rgba(255,255,255,0.38);
                ">
                    {suffix}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander(
        f"Voir les {min(len(values), 20)} derniers commentaires",
        expanded=False,
    ):

        for text in (
            normalized
            .tail(20)
            .tolist()[::-1]
        ):

            st.write(
                f"— {text}"
            )


# ============================================================
# PAGE SATISFACTION
# ============================================================

def render(
    df: pd.DataFrame,
):

    # ========================================================
    # TITRE
    # ========================================================

    st.markdown(
        "## 😊 Satisfaction"
    )

    st.caption(
        "Pilotage de la satisfaction client, "
        "du recueil et des réclamations traitées à temps."
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if df is None or df.empty:

        st.warning(
            "Aucune donnée disponible dans "
            "la base RC & SATISFACTION."
        )

        return

    if "Date" not in df.columns:

        st.warning(
            "La colonne Date n'est pas présente "
            "dans la base Satisfaction."
        )

        return

    df = _prepare_dates(
        df
    )

    if df.empty:

        st.warning(
            "Aucune date exploitable dans "
            "la base Satisfaction."
        )

        return

    # ========================================================
    # FILTRES
    # ========================================================

    section(
        "FILTRES DE PILOTAGE"
    )

    f1, f2, f3 = st.columns(
        [1, 1, 1.6]
    )

    # ========================================================
    # GRANULARITÉ
    # ========================================================

    with f1:

        granularite = st.selectbox(
            "Granularité",
            GRANULARITES,
            index=(
                GRANULARITES.index("Mensuel")
                if "Mensuel" in GRANULARITES
                else 0
            ),
            key="satisfaction_granularite",
        )

    # ========================================================
    # ANNÉE
    # ========================================================

    annees = sorted(
        df["Date"]
        .dt.year
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if not annees:

        st.warning(
            "Aucune année disponible."
        )

        return

    with f2:

        annee_sel = st.selectbox(
            "Année",
            annees,
            index=len(annees) - 1,
            key="satisfaction_annee",
        )

    # ========================================================
    # IMPORTANT :
    # L'ANNÉE EST FILTRÉE AVANT LES PÉRIODES
    # ========================================================

    df_annee = df.loc[
        df["Date"].dt.year
        == int(annee_sel)
    ].copy()

    # ========================================================
    # PÉRIODES DE L'ANNÉE SÉLECTIONNÉE
    # ========================================================

    periodes = construire_periodes(
        df_annee[["Date"]],
        granularite,
    )

    if not periodes:

        st.warning(
            f"Aucune période disponible "
            f"pour {annee_sel}."
        )

        return

    with f3:

        labels = [
            periode.label
            for periode in periodes
        ]

        periode_label = st.selectbox(
            "Période",
            labels,
            index=len(labels) - 1,
            key="satisfaction_periode",
        )

    periode = next(
        periode
        for periode in periodes
        if periode.label
        == periode_label
    )

    # ========================================================
    # PÉRIODE PRÉCÉDENTE
    # ========================================================

    periode_avant = periode_precedente(
        periode
    )

    # ========================================================
    # DONNÉES
    # ========================================================

    df_actuel = _filtrer_periode(
        df,
        periode,
    )

    df_precedent = _filtrer_periode(
        df,
        periode_avant,
    )

    k_actuel = _kpi_periode(
        df_actuel
    )

    k_precedent = _kpi_periode(
        df_precedent
    )

    # ========================================================
    # KPI PRINCIPAUX
    # ========================================================

    section(
        "INDICATEURS CLÉS — SATISFACTION"
    )

    cards = [

        (
            "🏅",
            "Satisfaction globale",
            k_actuel[
                "satisfaction_globale"
            ],
            k_precedent[
                "satisfaction_globale"
            ],
            75,
            (
                "Composition : "
                "50% baromètre · "
                "25% satisfaction · "
                "25% réclamations"
            ),
        ),

        (
            "⭐",
            "Taux de satisfaction",
            k_actuel[
                "taux_satisfaction"
            ],
            k_precedent[
                "taux_satisfaction"
            ],
            75,
            "Cible 75%",
        ),

        (
            "👥",
            "Taux de recueil",
            k_actuel[
                "taux_recueil"
            ],
            k_precedent[
                "taux_recueil"
            ],
            80,
            "Cible 80%",
        ),

        (
            "⚠️",
            "Réclamations traitées à temps",
            k_actuel[
                "taux_recla_temps"
            ],
            k_precedent[
                "taux_recla_temps"
            ],
            100,
            "Cible 100%",
        ),
    ]

    cols = st.columns(4)

    for col, (
        icon,
        name,
        value,
        previous,
        target,
        description,
    ) in zip(
        cols,
        cards,
    ):

        with col:

            variation = _variation_pts(
                value,
                previous,
            )

            if value is None:

                status = "neutral"

            else:

                # Conversion % -> ratio
                ratio_value = (
                    float(value) / 100.0
                )

                ratio_target = (
                    float(target) / 100.0
                )

                # status_for est prévu pour
                # recevoir un ratio
                try:

                    from theme import status_for

                    status = status_for(
                        ratio_value,
                        ratio_target,
                    )

                except Exception:

                    status = "neutral"

            if variation is not None:

                comparaison = (
                    f"{_fmt_pts(variation)} "
                    "vs période précédente"
                )

            else:

                comparaison = (
                    "Pas de comparaison disponible"
                )

            kpi_card(
                icon,
                name,
                _fmt_pct(value),
                (
                    f"{comparaison} · "
                    f"{description}"
                ),
                status,
            )

    # ========================================================
    # KPI VOLUMES
    # ========================================================

    st.markdown(
        "<div style='height:8px'></div>",
        unsafe_allow_html=True,
    )

    volume_cols = st.columns(3)

    with volume_cols[0]:

        kpi_card(
            "👥",
            "Clients reçus",
            _fmt_number(
                k_actuel[
                    "clients_recus"
                ]
            ),
            (
                f"Période : "
                f"{periode.label}"
            ),
            "neutral",
        )

    with volume_cols[1]:

        kpi_card(
            "📝",
            "Réponses recueillies",
            _fmt_number(
                k_actuel[
                    "recueil"
                ]
            ),
            (
                "Clients satisfaits : "
                + _fmt_number(
                    k_actuel[
                        "clients_satisfaits"
                    ]
                )
            ),
            "neutral",
        )

    with volume_cols[2]:

        kpi_card(
            "📨",
            "Réclamations reçues",
            _fmt_number(
                k_actuel[
                    "reclamations_recues"
                ]
            ),
            (
                "Traitées dans les délais : "
                + _fmt_number(
                    k_actuel[
                        "reclamations_traitees"
                    ]
                )
            ),
            "neutral",
        )

    # ========================================================
    # BAROMÈTRE
    # ========================================================

    st.caption(
        "Grande enquête barométrique fixe : "
        f"**{k_actuel['grande_enquete']:.0f}%**. "
        "Elle constitue 50% de la satisfaction globale."
    )

    # ========================================================
    # RÉCAPITULATIF
    # IMPORTANT :
    # AUCUN KPI ICI
    # ========================================================

    st.markdown("---")

    section(
        f"RÉCAPITULATIF — "
        f"{periode.label.upper()}"
    )

    recap = _build_recap(
        df,
        periode,
    )

    _render_recap_table(
        recap
    )

    # ========================================================
    # ÉVOLUTION
    # ========================================================

    st.markdown("---")

    section(
        f"ÉVOLUTION DES INDICATEURS — "
        f"{annee_sel}"
    )

    labels_evolution, series_evolution = (
        _evolution_data(
            df_annee,
            granularite,
        )
    )

    _plot_evolution(
        labels_evolution,
        series_evolution,
        granularite,
        int(annee_sel),
    )

    # ========================================================
    # VOLUMES
    # ========================================================

    _plot_volumes(
        df_annee,
        granularite,
        int(annee_sel),
    )

    # ========================================================
    # COMMENTAIRES
    # ========================================================

    st.markdown("---")

    section(
        f"OBSERVATIONS ET COMMENTAIRES — "
        f"{periode.label.upper()}"
    )

    _resume_commentaires(
        df_actuel
    )