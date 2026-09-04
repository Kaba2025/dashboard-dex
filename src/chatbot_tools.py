"""
Outils exposés au chatbot (function calling via Ollama).

Plutôt que de donner au modèle un résumé figé du tableau de bord, on lui
donne des FONCTIONS qu'il peut appeler lui-même selon la question posée :
il ne charge que ce dont il a besoin, peut combiner plusieurs appels pour
répondre à une question complexe, et reste à jour avec les données
actuelles à chaque appel (pas de contexte périmé).
"""
from __future__ import annotations

import json

from kpi import (
    GRANULARITES, OBJECTIFS, BOUNDS_FN, semaine_bounds,
    kpis_pour_periode, recap_par_agence, detail_reception_agence,
    recap_journalier, tendance_mensuelle, variation_pts,
)


def _resoudre_periode(df_sat, granularite, idx, annee):
    """Résout une période à partir de paramètres optionnels ; si rien n'est
    précisé, prend la période la plus récente disponible dans les données."""
    if annee is None:
        annee = int(df_sat["Annee_ISO"].max())
    if granularite is None or granularite not in GRANULARITES:
        granularite = "Bimestriel"
    if idx is None:
        if granularite == "Semaine/Jour":
            idx = int(df_sat[df_sat["Annee_ISO"] == annee]["Semaine_ISO"].max())
        elif granularite == "Mois":
            idx = int(df_sat[df_sat["Annee_ISO"] == annee]["Date"].dt.month.max())
        elif granularite == "Bimestriel":
            idx = 4
        elif granularite == "Trimestriel":
            idx = 3
        elif granularite == "Semestriel":
            idx = 2
        else:
            idx = 1
    if granularite == "Semaine/Jour":
        return semaine_bounds(annee, idx)
    return BOUNDS_FN[granularite](annee, idx)


def build_tools(df_sat, rec_by_agency, freq, agences_toutes):
    """Renvoie (tool_specs, tool_functions) prêts à passer à Ollama."""

    def kpis_periode(granularite: str = None, idx: int = None, annee: int = None, agence: str = None) -> dict:
        periode = _resoudre_periode(df_sat, granularite, idx, annee)
        agence_reelle = None
        if agence and agence.lower() not in ("toutes", "toutes les agences", "global", "réseau"):
            match = [a for a in agences_toutes if agence.lower() in a.lower()]
            agence_reelle = match[0] if match else agence
        k = kpis_pour_periode(df_sat, freq, periode, agence_reelle)
        return {
            "periode": periode.label, "date_debut": str(periode.date_debut), "date_fin": str(periode.date_fin),
            "agence": agence_reelle or "toutes agences",
            "satisfaction_globale_pct": round(k["satisfaction_globale"] * 100, 1),
            "csat_barometre_pct": round(k["csat_barometre"] * 100, 1),
            "taux_recueil_pct": round(k["taux_recueil"] * 100, 1),
            "taux_satisfaction_pct": round(k["taux_satisfaction"] * 100, 1),
            "taux_reclamation_pct": round(k["taux_reclamation"] * 100, 1),
            "nb_reclamations": k["nb_reclamations"],
            "pseudo_nps": round(k["pseudo_nps"] * 100, 1),
            "clients_recus": k["total_clients_recus"],
            "reponses_enquete": k["total_reponses"],
            "objectifs": {k2: f"{v*100:.0f}%" for k2, v in OBJECTIFS.items()},
        }

    def classement_agences(granularite: str = None, idx: int = None, annee: int = None) -> dict:
        periode = _resoudre_periode(df_sat, granularite, idx, annee)
        ra = recap_par_agence(df_sat, freq, periode, agences_toutes)
        if ra.empty:
            return {"periode": periode.label, "classement": []}
        return {
            "periode": periode.label,
            "classement": [
                {"agence": row["Agence"], "satisfaction_globale_pct": round(row["satisfaction_globale"] * 100, 1),
                 "taux_recueil_pct": round(row["taux_recueil"] * 100, 1), "reponses": row["total_reponses"],
                 "taux_reclamation_pct": round(row["taux_reclamation"] * 100, 1)}
                for _, row in ra.iterrows()
            ],
        }

    def detail_reception(agence: str, granularite: str = None, idx: int = None, annee: int = None) -> dict:
        periode = _resoudre_periode(df_sat, granularite, idx, annee)
        match = [a for a in agences_toutes if agence.lower() in a.lower()]
        agence_reelle = match[0] if match else agence
        det = detail_reception_agence(rec_by_agency, agence_reelle, periode)
        if not det or det.get("total_clients_recus", 0) == 0:
            return {"agence": agence_reelle, "periode": periode.label, "info": "aucune donnée de réception sur cette période"}
        out = {"agence": agence_reelle, "periode": periode.label, "clients_recus": det["total_clients_recus"]}
        if det.get("is_vallon"):
            out.update({
                "type": "Vallon (délais disponibles)",
                "temps_attente_moyen_min": det["attente_moyenne_min"],
                "pct_servis_sous_15min": det["pct_attente_15min"],
                "temps_transaction_moyen_min": det["transaction_moyenne_min"],
                "pct_usage_appli_mobile": det["pct_app_mobile"],
            })
        else:
            out.update({
                "type": "standard", "gestionnaire": det.get("gestionnaire", "—"),
                "pct_tickets_clotures": det.get("pct_cloture", 0),
                "top_motifs": det.get("top_motifs").to_dict() if det.get("top_motifs") is not None else {},
            })
        return out

    def rechercher_client(recherche: str) -> dict:
        resultats = df_sat[
            df_sat["Identifiant"].astype(str).str.contains(recherche, case=False, na=False)
            | df_sat["Nom client"].astype(str).str.contains(recherche, case=False, na=False)
        ]
        if resultats.empty:
            return {"trouve": False, "message": f"Aucun client ne correspond à « {recherche} »"}
        rows = resultats.head(5)
        return {
            "trouve": True, "nombre_resultats": len(resultats),
            "clients": [
                {"identifiant": str(r["Identifiant"]), "nom": r["Nom client"], "agence": r["Libelle agence"],
                 "date": r["Date"].strftime("%d/%m/%Y"), "satisfaction": r["Satisfaction"],
                 "reclamation": bool(r["Reclamation_bin"]), "commentaire": r["Commentaire"] or None}
                for _, r in rows.iterrows()
            ],
        }

    def tendance() -> dict:
        tm = tendance_mensuelle(df_sat, freq)
        if tm.empty:
            return {"mois": []}
        return {"mois": [
            {"mois": row["Mois"], "satisfaction_globale_pct": round(row["satisfaction_globale"] * 100, 1),
             "csat_barometre_pct": round(row["csat_barometre"] * 100, 1), "taux_recueil_pct": round(row["taux_recueil"] * 100, 1)}
            for _, row in tm.iterrows()
        ]}

    def comparer_periodes(granularite: str, idx_a: int, annee_a: int, idx_b: int, annee_b: int, agence: str = None) -> dict:
        periode_a = _resoudre_periode(df_sat, granularite, idx_a, annee_a)
        periode_b = _resoudre_periode(df_sat, granularite, idx_b, annee_b)
        agence_reelle = None
        if agence and agence.lower() not in ("toutes", "toutes les agences"):
            match = [a for a in agences_toutes if agence.lower() in a.lower()]
            agence_reelle = match[0] if match else agence
        ka = kpis_pour_periode(df_sat, freq, periode_a, agence_reelle)
        kb = kpis_pour_periode(df_sat, freq, periode_b, agence_reelle)
        return {
            "periode_a": periode_a.label, "periode_b": periode_b.label, "agence": agence_reelle or "toutes agences",
            "satisfaction_globale_a_pct": round(ka["satisfaction_globale"] * 100, 1),
            "satisfaction_globale_b_pct": round(kb["satisfaction_globale"] * 100, 1),
            "variation_pts": round(variation_pts(kb["satisfaction_globale"], ka["satisfaction_globale"]), 1),
            "taux_recueil_a_pct": round(ka["taux_recueil"] * 100, 1), "taux_recueil_b_pct": round(kb["taux_recueil"] * 100, 1),
            "taux_reclamation_a_pct": round(ka["taux_reclamation"] * 100, 1), "taux_reclamation_b_pct": round(kb["taux_reclamation"] * 100, 1),
        }

    def jours_extremes(granularite: str = None, idx: int = None, annee: int = None, agence: str = None) -> dict:
        periode = _resoudre_periode(df_sat, granularite, idx, annee)
        agence_reelle = None
        if agence and agence.lower() not in ("toutes", "toutes les agences"):
            match = [a for a in agences_toutes if agence.lower() in a.lower()]
            agence_reelle = match[0] if match else agence
        rj = recap_journalier(df_sat, freq, periode, agence_reelle)
        if rj.empty:
            return {"info": "pas de données journalières sur cette période"}
        meilleur = rj.loc[rj["satisfaction_globale"].idxmax()]
        pire = rj.loc[rj["satisfaction_globale"].idxmin()]
        return {
            "periode": periode.label,
            "meilleur_jour": {"date": str(meilleur["Date"]), "satisfaction_globale_pct": round(meilleur["satisfaction_globale"] * 100, 1)},
            "pire_jour": {"date": str(pire["Date"]), "satisfaction_globale_pct": round(pire["satisfaction_globale"] * 100, 1)},
            "nombre_jours": len(rj),
            "jours_sous_objectif": int((rj["satisfaction_globale"] < OBJECTIFS["satisfaction_globale"]).sum()),
        }

    def liste_agences() -> dict:
        return {"agences": agences_toutes}

    tool_functions = {
        "kpis_periode": kpis_periode,
        "classement_agences": classement_agences,
        "detail_reception": detail_reception,
        "rechercher_client": rechercher_client,
        "tendance": tendance,
        "comparer_periodes": comparer_periodes,
        "jours_extremes": jours_extremes,
        "liste_agences": liste_agences,
    }

    tool_specs = [
        {"type": "function", "function": {
            "name": "kpis_periode",
            "description": "KPI de satisfaction (Satisfaction Globale, CSAT, taux de recueil, réclamations, Pseudo-NPS) pour une période et une agence. Sans paramètre, renvoie la période la plus récente, toutes agences.",
            "parameters": {"type": "object", "properties": {
                "granularite": {"type": "string", "enum": GRANULARITES},
                "idx": {"type": "integer", "description": "numéro de semaine/mois/bimestre/trimestre/semestre selon la granularité"},
                "annee": {"type": "integer"},
                "agence": {"type": "string", "description": "nom d'agence (ex: Bouaké, Vallon) ou 'toutes'"},
            }},
        }},
        {"type": "function", "function": {
            "name": "classement_agences",
            "description": "Classe toutes les agences par Satisfaction Globale sur une période donnée.",
            "parameters": {"type": "object", "properties": {
                "granularite": {"type": "string", "enum": GRANULARITES}, "idx": {"type": "integer"}, "annee": {"type": "integer"},
            }},
        }},
        {"type": "function", "function": {
            "name": "detail_reception",
            "description": "Détail réception physique d'une agence précise : délais/appli mobile pour Vallon, gestionnaire/motifs de visite pour les autres.",
            "parameters": {"type": "object", "properties": {
                "agence": {"type": "string", "description": "nom de l'agence, ex: Vallon, Bouaké"},
                "granularite": {"type": "string", "enum": GRANULARITES}, "idx": {"type": "integer"}, "annee": {"type": "integer"},
            }, "required": ["agence"]},
        }},
        {"type": "function", "function": {
            "name": "rechercher_client",
            "description": "Recherche un client par identifiant ou nom (recherche partielle) et renvoie son profil et sa satisfaction.",
            "parameters": {"type": "object", "properties": {
                "recherche": {"type": "string", "description": "identifiant ou nom (ou partie du nom) du client"},
            }, "required": ["recherche"]},
        }},
        {"type": "function", "function": {
            "name": "tendance",
            "description": "Évolution mensuelle (Satisfaction Globale, CSAT, % Recueil) depuis janvier jusqu'à aujourd'hui, toutes agences.",
            "parameters": {"type": "object", "properties": {}},
        }},
        {"type": "function", "function": {
            "name": "comparer_periodes",
            "description": "Compare les KPI entre deux périodes de même granularité (ex: bimestre 3 vs bimestre 4) pour voir l'évolution.",
            "parameters": {"type": "object", "properties": {
                "granularite": {"type": "string", "enum": GRANULARITES},
                "idx_a": {"type": "integer"}, "annee_a": {"type": "integer"},
                "idx_b": {"type": "integer"}, "annee_b": {"type": "integer"},
                "agence": {"type": "string"},
            }, "required": ["granularite", "idx_a", "annee_a", "idx_b", "annee_b"]},
        }},
        {"type": "function", "function": {
            "name": "jours_extremes",
            "description": "Meilleur et pire jour (Satisfaction Globale) sur une période, et nombre de jours sous l'objectif.",
            "parameters": {"type": "object", "properties": {
                "granularite": {"type": "string", "enum": GRANULARITES}, "idx": {"type": "integer"}, "annee": {"type": "integer"},
                "agence": {"type": "string"},
            }},
        }},
        {"type": "function", "function": {
            "name": "liste_agences",
            "description": "Liste des noms exacts de toutes les agences NSIA suivies dans le dashboard.",
            "parameters": {"type": "object", "properties": {}},
        }},
    ]

    return tool_specs, tool_functions


def executer_tool(nom: str, arguments: dict, tool_functions: dict) -> str:
    """Exécute un outil en toute sécurité : jamais d'exception qui remonte
    au modèle, toujours un JSON (résultat ou message d'erreur clair)."""
    fn = tool_functions.get(nom)
    if fn is None:
        return json.dumps({"erreur": f"Outil inconnu : {nom}"})
    try:
        resultat = fn(**arguments) if arguments else fn()
        return json.dumps(resultat, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"erreur": f"Échec de l'appel à {nom}({arguments}) : {e}"}, ensure_ascii=False)
