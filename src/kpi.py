"""
Calculs des indicateurs.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from periods import Periode, GRANULARITES, filtrer_periode as filtrer_periode_periods

MOIS_FR = {1: "JANVIER", 2: "FEVRIER", 3: "MARS", 4: "AVRIL", 5: "MAI", 6: "JUIN",
           7: "JUILLET", 8: "AOUT", 9: "SEPTEMBRE", 10: "OCTOBRE", 11: "NOVEMBRE", 12: "DECEMBRE"}

CSAT_BAROMETRE_FIXE = 0.68

OBJECTIFS = {"satisfaction_globale": 0.78, "taux_recueil": 0.80, "taux_satisfaction": 0.75, "taux_satisfaction_baro": 0.75}
PONDERATION = {"csat_barometre": 0.50, "satisfaction_enquete": 0.25, "reclamation": 0.25}


# ---------------------------------------------------------------------------
# Bornes de période
# ---------------------------------------------------------------------------
def semaine_bounds(annee: int, semaine: int) -> Periode:
    debut = date.fromisocalendar(annee, semaine, 1)
    fin = date.fromisocalendar(annee, semaine, 5)
    debut_ts = pd.Timestamp(debut)
    fin_ts = pd.Timestamp(fin)
    return Periode("Semaine/Jour", debut_ts, fin_ts, f"Semaine {semaine} ({MOIS_FR[fin.month]} {fin.year})", f"{annee}-S{semaine:02d}")


def mois_bounds(annee: int, mois: int) -> Periode:
    debut_ts = pd.Timestamp(date(annee, mois, 1))
    if mois < 12:
        fin_ts = pd.Timestamp(date(annee, mois + 1, 1)) - pd.Timedelta(days=1)
    else:
        fin_ts = pd.Timestamp(date(annee, 12, 31))
    return Periode("Mois", debut_ts, fin_ts, f"{MOIS_FR[mois]} {annee}", f"{annee}-{mois:02d}")


def _mois_range_bounds(annee: int, mois_debut: int, mois_fin: int, label_prefix: str, granularite: str) -> Periode:
    debut_ts = pd.Timestamp(date(annee, mois_debut, 1))
    if mois_fin < 12:
        fin_ts = pd.Timestamp(date(annee, mois_fin + 1, 1)) - pd.Timedelta(days=1)
    else:
        fin_ts = pd.Timestamp(date(annee, 12, 31))
    label = f"{label_prefix} ({MOIS_FR[mois_debut][:3]}-{MOIS_FR[mois_fin][:3]} {annee})"
    cle = f"{annee}-{label_prefix.replace(' ', '')}"
    return Periode(granularite, debut_ts, fin_ts, label, cle)


def bimestre_bounds(annee: int, bimestre: int) -> Periode:
    m1 = (bimestre - 1) * 2 + 1
    return _mois_range_bounds(annee, m1, m1 + 1, f"Bimestre {bimestre}", "Bimestriel")


def trimestre_bounds(annee: int, trimestre: int) -> Periode:
    m1 = (trimestre - 1) * 3 + 1
    return _mois_range_bounds(annee, m1, m1 + 2, f"Trimestre {trimestre}", "Trimestriel")


def semestre_bounds(annee: int, semestre: int) -> Periode:
    m1 = 1 if semestre == 1 else 7
    return _mois_range_bounds(annee, m1, m1 + 5, f"Semestre {semestre}", "Semestriel")


def annee_bounds(annee: int) -> Periode:
    debut_ts = pd.Timestamp(date(annee, 1, 1))
    fin_ts = pd.Timestamp(date(annee, 12, 31))
    return Periode("Annuel", debut_ts, fin_ts, f"Année {annee}", str(annee))


def periode_precedente(granularite: str, annee: int, idx: int) -> tuple[int, int]:
    if granularite == "Mois":
        return (annee - 1, 12) if idx == 1 else (annee, idx - 1)
    if granularite == "Bimestriel":
        return (annee - 1, 6) if idx == 1 else (annee, idx - 1)
    if granularite == "Trimestriel":
        return (annee - 1, 4) if idx == 1 else (annee, idx - 1)
    if granularite == "Semestriel":
        return (annee - 1, 2) if idx == 1 else (annee, idx - 1)
    if granularite == "Annuel":
        return (annee - 1, idx)
    return (annee, idx)


BOUNDS_FN = {
    "Mois": mois_bounds, "Bimestriel": bimestre_bounds, "Trimestriel": trimestre_bounds,
    "Semestriel": semestre_bounds, "Annuel": lambda a, i: annee_bounds(a),
}


# ---------------------------------------------------------------------------
# Filtrage
# ---------------------------------------------------------------------------
def filtrer_periode(df: pd.DataFrame, periode: Periode) -> pd.DataFrame:
    return filtrer_periode_periods(df, periode)


def _pct(numer, denom) -> float:
    return (numer / denom) if denom else 0.0


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
def footfall_for(freq: pd.DataFrame | None, periode: Periode, agence: str | None = None) -> int:
    """Calcule le nombre de clients reçus."""
    if freq is None or freq.empty:
        return 0
    
    mask = (freq["Date"] >= periode.debut) & (freq["Date"] <= periode.fin)
    if agence and "Agence" in freq.columns:
        mask &= freq["Agence"] == agence
    
    if "Total clients reçus" in freq.columns:
        return int(pd.to_numeric(freq.loc[mask, "Total clients reçus"], errors="coerce").sum())
    return 0


def kpis_pour_periode(df: pd.DataFrame, freq: pd.DataFrame | None, periode: Periode, agence: str | None = None,
                       csat_barometre: float = CSAT_BAROMETRE_FIXE) -> dict:
    """
    Calcule les KPI pour une période donnée.
    
    Colonnes disponibles dans RC & SATISFACTION (d'après le fichier Excel) :
    - Date, Recueil de satisfaction, Total clients reçus, Clients satisfaits
    - Observations, Initiative, Réclamations MOIS traitées dans les délais
    - Réclamations MOIS reçues, Réclamations ANNÉE traitées dans les délais
    - Réclamations ANNÉE reçues, Réclamations COMMISSION traitées dans les délais
    - Réclamations COMMISSION reçues, Réclamations ANNULATION COMMISSION reçues
    - Nombre de mise à jour journalière, Contre Performance, Semaine, Mois, Filtre, Date2
    """
    sous_ens = filtrer_periode(df, periode)
    
    if agence and "Agence" in sous_ens.columns:
        sous_ens = sous_ens[sous_ens["Agence"] == agence]
    
    total_reponses = len(sous_ens)
    
    # Clients satisfaits
    if "Clients satisfaits" in sous_ens.columns:
        satisfaits = int(pd.to_numeric(sous_ens["Clients satisfaits"], errors="coerce").sum())
    else:
        satisfaits = 0
    
    # Total clients reçus depuis la table RC & SATISFACTION
    if "Total clients reçus" in sous_ens.columns:
        total_clients = int(pd.to_numeric(sous_ens["Total clients reçus"], errors="coerce").sum())
    else:
        total_clients = 0
    
    # Footfall depuis la table physique (freq) si disponible, sinon utiliser total_clients
    footfall = footfall_for(freq, periode, agence)
    footfall = max(footfall, total_clients, total_reponses)
    
    # Réclamations reçues
    if "Réclamations MOIS reçues" in sous_ens.columns:
        reclamations = int(pd.to_numeric(sous_ens["Réclamations MOIS reçues"], errors="coerce").sum())
    else:
        reclamations = 0
    
    # Réclamations traitées dans les délais
    if "Réclamations MOIS traitées dans les délais" in sous_ens.columns:
        reclamations_traitees = int(pd.to_numeric(sous_ens["Réclamations MOIS traitées dans les délais"], errors="coerce").sum())
    else:
        reclamations_traitees = 0
    
    taux_recueil = _pct(total_reponses, footfall) if footfall > 0 else 0
    taux_satisfaction = _pct(satisfaits, total_reponses) if total_reponses > 0 else 0
    taux_reclamation = _pct(reclamations, total_reponses) if total_reponses > 0 else 0
    taux_reclamation_traitee = _pct(reclamations_traitees, reclamations) if reclamations > 0 else 0
    
    # Satisfaction Globale (formule officielle)
    satisfaction_globale = (
        PONDERATION["csat_barometre"] * csat_barometre
        + PONDERATION["satisfaction_enquete"] * taux_satisfaction
        + PONDERATION["reclamation"] * taux_reclamation
    )
    
    # Pseudo-NPS approximatif
    pseudo_nps = taux_satisfaction * 0.5
    
    return {
        "total_clients_recus": footfall,
        "total_reponses": total_reponses,
        "clients_satisfaits": satisfaits,
        "taux_recueil": taux_recueil,
        "csat_barometre": csat_barometre,
        "taux_satisfaction": taux_satisfaction,
        "satisfaction_globale": satisfaction_globale,
        "pseudo_nps": pseudo_nps,
        "promoteurs": int(satisfaits * 0.7) if satisfaits > 0 else 0,
        "detracteurs": int(satisfaits * 0.1) if satisfaits > 0 else 0,
        "taux_reclamation": taux_reclamation,
        "taux_reclamation_traitee": taux_reclamation_traitee,
        "nb_reclamations": reclamations,
        "nb_reclamations_traitees": reclamations_traitees,
    }


def recap_journalier(df: pd.DataFrame, freq: pd.DataFrame | None, periode: Periode, agence: str | None = None) -> pd.DataFrame:
    sous_ens = filtrer_periode(df, periode)
    if agence and "Agence" in sous_ens.columns:
        sous_ens = sous_ens[sous_ens["Agence"] == agence]
    if sous_ens.empty:
        return pd.DataFrame()
    
    rows = []
    for jour, g in sous_ens.groupby(sous_ens["Date"].dt.date):
        jour_periode = Periode("Journalier", pd.Timestamp(jour), pd.Timestamp(jour), 
                               jour.strftime("%d/%m/%Y"), jour.strftime("%Y-%m-%d"))
        # Créer un DataFrame avec les données du jour
        df_jour = df[df["Date"].dt.date == jour]
        k = kpis_pour_periode(df_jour, freq, jour_periode, agence)
        rows.append({"Date": jour, **k})
    return pd.DataFrame(rows).sort_values("Date")


def recap_par_agence(df: pd.DataFrame, freq: pd.DataFrame | None, periode: Periode, agences: list[str]) -> pd.DataFrame:
    rows = []
    for agence in agences:
        k = kpis_pour_periode(df, freq, periode, agence)
        rows.append({"Agence": agence, **k})
    out = pd.DataFrame(rows)
    return out.sort_values("satisfaction_globale", ascending=False) if not out.empty else out


def detail_reception_agence(rec_by_agency: dict[str, pd.DataFrame], agence: str, periode: Periode) -> dict:
    df = rec_by_agency.get(agence) if rec_by_agency else None
    if df is None or df.empty:
        return {}
    mask = (df["Date"] >= periode.debut) & (df["Date"] <= periode.fin)
    g = df[mask]
    if g.empty:
        return {"total_clients_recus": 0}

    is_vallon = bool(g["is_vallon"].iloc[0]) if "is_vallon" in g.columns else False
    out = {"total_clients_recus": len(g), "is_vallon": is_vallon}

    if is_vallon:
        out["attente_moyenne_min"] = round(g["Temps d'attente"].mean(), 1) if "Temps d'attente" in g.columns else 0
        out["transaction_moyenne_min"] = round(g["Temps de transaction"].mean(), 1) if "Temps de transaction" in g.columns else 0
        out["pct_attente_15min"] = round((g["Temps d'attente"] <= 15).mean() * 100, 1) if "Temps d'attente" in g.columns else 0
        out["pct_app_mobile"] = round((g["Has App Mobile"] == "OUI").mean() * 100, 1) if "Has App Mobile" in g.columns else 0
    else:
        out["gestionnaire"] = g["Gestionnaire"].mode().iloc[0] if "Gestionnaire" in g.columns and not g["Gestionnaire"].mode().empty else "—"
        out["top_motifs"] = g["Motifs visite"].value_counts().head(5) if "Motifs visite" in g.columns else pd.Series()
        out["pct_cloture"] = round((g["Statut Ticket"] == "Cloture").mean() * 100, 1) if "Statut Ticket" in g.columns else 0

    return out


def tendance_mensuelle(df: pd.DataFrame, freq: pd.DataFrame | None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    tmp = df.copy()
    tmp["AnneeMois"] = tmp["Date"].dt.to_period("M")
    rows = []
    for periode_m, g in tmp.groupby("AnneeMois"):
        ts = periode_m.to_timestamp()
        p = Periode("Mois", ts, ts + pd.offsets.MonthEnd(0), 
                   periode_m.strftime("%b %Y"), periode_m.strftime("%Y-%m"))
        k = kpis_pour_periode(df, freq, p)
        rows.append({"Mois": periode_m.strftime("%b %Y"), "ordre": ts, **k})
    return pd.DataFrame(rows).sort_values("ordre")


def tendance_generique(df: pd.DataFrame, freq: pd.DataFrame | None, granularite: str, annee: int,
                        agence: str | None = None) -> pd.DataFrame:
    rows = []
    for idx, p in iter_periodes_annee(granularite, annee):
        k = kpis_pour_periode(df, freq, p, agence)
        if k["total_reponses"] == 0 and k["total_clients_recus"] == 0:
            continue
        rows.append({"label": p.label, "idx": idx, **k})
    return pd.DataFrame(rows)


def variation_pts(actuel: float, precedent: float | None) -> float | None:
    return None if precedent is None else (actuel - precedent) * 100


def iter_periodes_annee(granularite: str, annee: int):
    if granularite == "Semaine/Jour":
        for s in range(1, 54):
            try:
                yield s, semaine_bounds(annee, s)
            except ValueError:
                continue
    elif granularite == "Mois":
        for m in range(1, 13):
            yield m, mois_bounds(annee, m)
    elif granularite == "Bimestriel":
        for i in range(1, 7):
            yield i, bimestre_bounds(annee, i)
    elif granularite == "Trimestriel":
        for i in range(1, 5):
            yield i, trimestre_bounds(annee, i)
    elif granularite == "Semestriel":
        for i in range(1, 3):
            yield i, semestre_bounds(annee, i)
    else:
        yield 1, annee_bounds(annee)


# ---------------------------------------------------------------------------
# Score de fidélité ESTIMÉ
# ---------------------------------------------------------------------------
_SATISFACTION_SCORE = {"Tres Satisfait": 1.0, "Satisfait": 0.72, "Peu Satisfait": 0.32, "Insatisfait": 0.0}


def score_fidelite_estime(satisfaction: str, reclamation: bool) -> dict:
    base = _SATISFACTION_SCORE.get(satisfaction, 0.5)
    score = base * 0.75 + (0.25 if not reclamation else 0.0)
    score = round(score * 100)

    if score >= 80:
        label, niveau = "Très fidèle (estimation)", "good"
    elif score >= 55:
        label, niveau = "Fidélité modérée (estimation)", "warn"
    else:
        label, niveau = "Risque de départ (estimation)", "bad"

    return {"score": score, "label": label, "niveau": niveau}