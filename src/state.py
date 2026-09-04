"""
Filtres partagés entre tous les onglets via st.session_state : le choix
d'agence, d'année/granularité/période, et l'éventuelle comparaison entre
deux périodes restent les mêmes en changeant d'onglet.
"""
import streamlit as st

from kpi import (
    GRANULARITES, MOIS_FR, semaine_bounds, mois_bounds, bimestre_bounds,
    trimestre_bounds, semestre_bounds, annee_bounds, periode_precedente, BOUNDS_FN,
)

DEFAULTS = {"annee": None, "granularite": "Bimestriel", "idx": None, "agence": "Toutes les agences",
            "comparer": False, "annee_b": None, "idx_b": None}


def init_filters(df_sat):
    for k, v in DEFAULTS.items():
        if f"filtre_{k}" not in st.session_state:
            st.session_state[f"filtre_{k}"] = v
    if st.session_state["filtre_annee"] is None:
        st.session_state["filtre_annee"] = int(df_sat["Annee_ISO"].max())


def get_periode(annee, granularite, idx):
    if granularite == "Semaine/Jour":
        return semaine_bounds(annee, idx)
    if granularite == "Mois":
        return mois_bounds(annee, idx)
    if granularite == "Bimestriel":
        return bimestre_bounds(annee, idx)
    if granularite == "Trimestriel":
        return trimestre_bounds(annee, idx)
    if granularite == "Semestriel":
        return semestre_bounds(annee, idx)
    return annee_bounds(annee)


def render_filters_sidebar(df_sat, agences_toutes):
    """Barre latérale complète : agence tout en haut (visible sans
    scroller), puis période, puis comparaison optionnelle entre 2 périodes.
    Renvoie (periode, agence, periode_comparaison_ou_None)."""
    init_filters(df_sat)

    st.markdown("### 🏢 Agence")
    options = ["Toutes les agences"] + agences_toutes
    default_agence = st.session_state["filtre_agence"] if st.session_state["filtre_agence"] in options else options[0]
    agence_label = st.selectbox("Agence", options, index=options.index(default_agence), key="sb_agence",
                                 label_visibility="collapsed")
    st.session_state["filtre_agence"] = agence_label
    agence = None if agence_label == "Toutes les agences" else agence_label

    st.divider()
    st.markdown("### 🗓️ Période")
    annees = sorted(df_sat["Annee_ISO"].unique())
    annee = st.selectbox("Année", annees, index=annees.index(st.session_state["filtre_annee"]), key="sb_annee")
    st.session_state["filtre_annee"] = annee

    granularite = st.selectbox("Granularité", GRANULARITES,
                                index=GRANULARITES.index(st.session_state["filtre_granularite"]), key="sb_gran")
    st.session_state["filtre_granularite"] = granularite

    idx = _selecteur_periode(granularite, annee, "sb", st.session_state["filtre_idx"])
    st.session_state["filtre_idx"] = idx
    periode = get_periode(annee, granularite, idx)

    st.divider()
    comparer = st.checkbox("📊 Comparer deux périodes", value=st.session_state["filtre_comparer"], key="cb_comparer")
    st.session_state["filtre_comparer"] = comparer

    periode_b = None
    if comparer:
        st.caption("Période de comparaison")
        if granularite == "Annuel":
            annee_b_defaut = annee - 1
        else:
            annee_b_defaut, idx_b_defaut = periode_precedente(granularite, annee, idx)
        annee_b = st.selectbox("Année (comparaison)", annees if (annee - 1) in annees else annees + [annee - 1],
                                index=(annees.index(annee_b_defaut) if annee_b_defaut in annees else 0),
                                key="sb_annee_b")
        if granularite != "Annuel":
            idx_b = _selecteur_periode(granularite, annee_b, "sb_b", idx_b_defaut)
        else:
            idx_b = 1
        periode_b = get_periode(annee_b, granularite, idx_b)
        st.session_state["filtre_annee_b"] = annee_b
        st.session_state["filtre_idx_b"] = idx_b

    return periode, agence, periode_b


def _selecteur_periode(granularite, annee, key_prefix, valeur_defaut):
    if granularite == "Semaine/Jour":
        return st.slider("Semaine (ISO, 1-52)", 1, 53, value=valeur_defaut or 33, key=f"{key_prefix}_sem")
    if granularite == "Mois":
        return st.selectbox("Mois", list(range(1, 13)), format_func=lambda m: MOIS_FR[m],
                             index=(valeur_defaut or 8) - 1, key=f"{key_prefix}_mois")
    if granularite == "Bimestriel":
        return st.selectbox("Bimestre", [1, 2, 3, 4, 5, 6], format_func=lambda i: f"Bimestre {i}",
                             index=(valeur_defaut or 4) - 1, key=f"{key_prefix}_bim")
    if granularite == "Trimestriel":
        return st.selectbox("Trimestre", [1, 2, 3, 4], format_func=lambda i: f"Trimestre {i}",
                             index=(valeur_defaut or 3) - 1, key=f"{key_prefix}_tri")
    if granularite == "Semestriel":
        return st.selectbox("Semestre", [1, 2], format_func=lambda i: f"Semestre {i}",
                             index=(valeur_defaut or 2) - 1, key=f"{key_prefix}_sem2")
    return 1


def current_filters():
    return (st.session_state.get("filtre_annee"), st.session_state.get("filtre_granularite"),
            st.session_state.get("filtre_idx"))
