import plotly.graph_objects as go
import streamlit as st

from kpi import kpis_pour_periode, variation_pts, iter_periodes_annee, MOIS_FR
from kpi_extra import kpis_reclamation, kpis_callcenter, satisfaction_globale_officielle
from settings import get_csat_barometre, set_csat_barometre
from theme import kpi_card, section, status_for, render_html, GOLD, GREEN, NAVY_CARD


def _label_periode(granularite, idx, annee):
    if granularite == "Semaine/Jour":
        return f"S{idx}"
    if granularite == "Mois":
        return MOIS_FR[idx][:3]
    if granularite == "Bimestriel":
        return f"B{idx}"
    if granularite == "Trimestriel":
        return f"T{idx}"
    if granularite == "Semestriel":
        return f"S{idx}"
    return str(annee)


def render(df_sat, freq, df_recla, df_cc, periode, agence, periode_b, annee_sel, granularite_sel, idx_sel):
    with st.expander(f"⚙️ Grande enquête barométrique — valeur actuelle : {get_csat_barometre()*100:.0f}% (modifiable uniquement après une nouvelle enquête)"):
        nouvelle_valeur = st.number_input("Nouveau taux de satisfaction (grande enquête, en %)", min_value=0.0, max_value=100.0,
                                           value=get_csat_barometre() * 100, step=0.1, key="input_barometre")
        if st.button("Enregistrer cette valeur", key="btn_save_barometre"):
            set_csat_barometre(nouvelle_valeur / 100)
            st.success(f"Valeur mise à jour : {nouvelle_valeur:.1f}%. Elle s'applique maintenant partout dans le dashboard.")
            st.rerun()

    k_sat = kpis_pour_periode(df_sat, freq, periode, agence)
    k_recla = kpis_reclamation(df_recla, periode, agence)
    k_cc = kpis_callcenter(df_cc, periode)

    satisfaction_globale = satisfaction_globale_officielle(
        taux_satisfaction=k_sat["taux_satisfaction"], taux_reclamation=k_recla["taux_global_dans_delai"])

    k_sat_b = k_recla_b = None
    if periode_b:
        k_sat_b = kpis_pour_periode(df_sat, freq, periode_b, agence)
        k_recla_b = kpis_reclamation(df_recla, periode_b, agence)
        sg_b = satisfaction_globale_officielle(k_sat_b["taux_satisfaction"], k_recla_b["taux_global_dans_delai"])
    else:
        sg_b = None

    # ------------------------------------------------------------------
    section("SECTION 1 — TAUX GLOBAL DE SATISFACTION CLIENT")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        var = variation_pts(satisfaction_globale, sg_b) if sg_b is not None else None
        kpi_card("🏅", "Satisfaction Globale", f"{satisfaction_globale*100:.1f}%",
                  f"{var:+.1f} pts vs période B" if var is not None else "50%CSAT+25%Sat.+25%Récla",
                  status_for(satisfaction_globale, 0.75))
    with c2:
        kpi_card("⚠️", "% Réclamations traitées (10j)", f"{k_recla['taux_global_dans_delai']*100:.1f}%",
                  f"{k_recla['total_reclamations']} réclamations", status_for(k_recla['taux_global_dans_delai'], 1.0))
    with c3:
        kpi_card("📈", "Taux satisfaction dernière enquête", f"{k_sat['taux_satisfaction']*100:.1f}%",
                  "cible 75%", status_for(k_sat['taux_satisfaction'], 0.75))
    with c4:
        kpi_card("👥", "Taux de recueil de satisfaction", f"{k_sat['taux_recueil']*100:.1f}%",
                  "cible 80%", status_for(k_sat['taux_recueil'], 0.80))
    with c5:
        kpi_card("⭐", "Taux satisfaction baromètre", f"{get_csat_barometre()*100:.0f}%",
                  "cible 75% · grande enquête (fixe)", status_for(get_csat_barometre(), 0.75))

    # ------------------------------------------------------------------
    section("SECTION 2 — RÉCEPTION DIGITALE ET PHYSIQUE")
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        kpi_card("👥", "Nombre de clients reçus", f"{k_sat['total_clients_recus']}", "", "neutral")
    with c7:
        kpi_card("📱", "Taux d'utilisation agences numériques", "N/A", "base Digital à venir", "neutral")
    with c8:
        kpi_card("⏱️", "% Clients attendus < 15 min", "N/A", "voir onglet Physique (Vallon)", "neutral")
    with c9:
        kpi_card("⏱️", "Temps moyen d'attente", "N/A", "voir onglet Physique (Vallon)", "neutral")
    with c10:
        kpi_card("✅", "% Clients pris en charge", "N/A", "voir onglet Physique (Vallon)", "neutral")
    render_html('<div style="font-size:0.72rem; color:#8FA0BF; margin:-0.3rem 0 0.5rem 0;">'
                'Les délais détaillés (attente, prise en charge) ne sont mesurés que pour Vallon actuellement — '
                'voir l\'onglet Physique.</div>')

    # ------------------------------------------------------------------
    section("SECTION 3 — RÉCEPTION TÉLÉPHONIQUE")
    c11, c12, c13, c14 = st.columns(4)
    with c11:
        kpi_card("☎️", "Nombre d'appels reçus", f"{k_cc['appels_recus']}", "", "neutral")
    with c12:
        kpi_card("✅", "% Appels entrants répondus", f"{k_cc['taux_decroche']*100:.1f}%", "", status_for(k_cc['taux_decroche'], 0.80))
    with c13:
        kpi_card("⏱️", "% Échanges dans les délais (3min)", f"{k_cc['taux_echange_delai']*100:.1f}%", "", status_for(k_cc['taux_echange_delai'], 1.0))
    with c14:
        kpi_card("⏱️", "Délai moyen de communication", f"{k_cc['temps_moyen_com']:.2f} min", "cible 3 min", "neutral")
    c15, c16, c17 = st.columns(3)
    with c15:
        kpi_card("📞", "Nombre d'appels émis", f"{k_cc['appels_emis']}", f"objectif {k_cc['objectif_emis']}", "neutral")
    with c16:
        kpi_card("🤝", "% Clients joints (sortants)", f"{k_cc['taux_clients_joints']*100:.1f}%", "", status_for(k_cc['taux_clients_joints'], 0.50))
    with c17:
        kpi_card("📅", "% RDV pris", f"{k_cc['taux_rdv_pris']*100:.1f}%", "", status_for(k_cc['taux_rdv_pris'], 0.50))

    # ------------------------------------------------------------------
    section(f"ÉVOLUTION DE LA SATISFACTION GLOBALE — VUE {granularite_sel.upper()}")
    labels, valeurs = [], []
    for idx, p in iter_periodes_annee(granularite_sel, annee_sel):
        ks = kpis_pour_periode(df_sat, freq, p, agence)
        kr = kpis_reclamation(df_recla, p, agence)
        if ks["total_reponses"] == 0:
            continue
        sg = satisfaction_globale_officielle(ks["taux_satisfaction"], kr["taux_global_dans_delai"])
        labels.append(_label_periode(granularite_sel, idx, annee_sel))
        valeurs.append(sg * 100)

    if valeurs:
        fig = go.Figure(go.Scatter(x=labels, y=valeurs, mode="lines+markers", line=dict(color=GREEN, width=3)))
        fig.add_hline(y=75, line_dash="dash", line_color="rgba(255,255,255,0.3)", annotation_text="Objectif 75%")
        fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), yaxis_range=[0, 105],
                           plot_bgcolor=NAVY_CARD, paper_bgcolor="rgba(0,0,0,0)", font_color="#EAF0FA")
        st.plotly_chart(fig, use_container_width=True, key="pg_tab_evolution")
    else:
        st.caption("Pas assez de données pour tracer l'évolution sur cette granularité.")
