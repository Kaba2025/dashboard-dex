"""
KPI pour les nouvelles sources (Réclamation, Call Center, Messagerie) et
pour le "Point Global" (satisfaction globale pondérée officielle).

Formule confirmée par Kaba pour la Satisfaction Globale du Point Global :
    Satisfaction Globale = 0,50 x CSAT_BAROMETRE (fixe, saisi manuellement,
                                                   ne change qu'après une
                                                   nouvelle grande enquête)
                          + 0,25 x Taux de satisfaction (période choisie)
                          + 0,25 x Taux de réclamation (période choisie)
Les trois termes s'additionnent tels quels (confirmé explicitement, pas de
soustraction ni d'inversion du taux de réclamation).
"""
from __future__ import annotations

import pandas as pd

from periods import Periode
from settings import get_csat_barometre, DEFAUT_CSAT_BAROMETRE

# Valeur par défaut si le fichier de config n'existe pas encore.
CSAT_BAROMETRE_FIXE = DEFAUT_CSAT_BAROMETRE

PONDERATION_GLOBALE = {"baromètre": 0.50, "satisfaction": 0.25, "reclamation": 0.25}


def satisfaction_globale_officielle(taux_satisfaction: float, taux_reclamation: float,
                                     csat_barometre: float | None = None) -> float:
    if csat_barometre is None:
        csat_barometre = get_csat_barometre()
    return (
        PONDERATION_GLOBALE["baromètre"] * csat_barometre
        + PONDERATION_GLOBALE["satisfaction"] * taux_satisfaction
        + PONDERATION_GLOBALE["reclamation"] * taux_reclamation
    )


# ---------------------------------------------------------------------------
# Réclamation
# ---------------------------------------------------------------------------
def _filtrer_recla(df: pd.DataFrame, periode: Periode, agence: str | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    # Utiliser "Date" comme colonne de date pour les réclamations
    if "Date" in df.columns:
        mask = (df["Date"] >= periode.debut) & (df["Date"] <= periode.fin)
    elif "Date_reception" in df.columns:
        mask = (df["Date_reception"] >= periode.debut) & (df["Date_reception"] <= periode.fin)
    else:
        return df
    if agence:
        mask &= df["Libelle agence"] == agence
    return df[mask]


def kpis_reclamation(df: pd.DataFrame, periode: Periode, agence: str | None = None) -> dict:
    """Les 4 indicateurs de délai + taux global de réclamations traitées à
    temps (utilisé aussi comme composante du Point Global)."""
    g = _filtrer_recla(df, periode, agence)
    out = {"total_reclamations": len(g)}

    for cat in ["Standard", "Base Echue", "Commission", "Commission Base Echue"]:
        if "Categorie_Delai" in g.columns:
            sous = g[g["Categorie_Delai"] == cat]
        else:
            sous = pd.DataFrame()
        if "Dans_les_delais" in sous.columns:
            traitees = sous["Dans_les_delais"].dropna()
        else:
            traitees = pd.Series()
        out[cat] = {
            "total": len(sous),
            "traitees": int(sous["Date_cloture"].notna().sum()) if "Date_cloture" in sous.columns else 0,
            "taux_dans_delai": float(traitees.mean()) if len(traitees) else None,
        }

    # Taux global tous types confondus
    if "Dans_les_delais" in g.columns:
        toutes_traitees = g["Dans_les_delais"].dropna()
        out["taux_global_dans_delai"] = float(toutes_traitees.mean()) if len(toutes_traitees) else 0.0
    else:
        out["taux_global_dans_delai"] = 0.0
    return out


def recap_journalier_reclamation(df: pd.DataFrame, periode: Periode, agence: str | None = None) -> pd.DataFrame:
    g = _filtrer_recla(df, periode, agence)
    if g.empty:
        return pd.DataFrame()
    rows = []
    # Utiliser la colonne de date disponible
    date_col = "Date" if "Date" in g.columns else "Date_reception" if "Date_reception" in g.columns else None
    if date_col is None:
        return pd.DataFrame()
    for jour, gj in g.groupby(g[date_col].dt.date):
        row = {"Date": jour}
        for cat in ["Standard", "Base Echue", "Commission", "Commission Base Echue"]:
            if "Categorie_Delai" in gj.columns:
                sous = gj[gj["Categorie_Delai"] == cat]
            else:
                sous = pd.DataFrame()
            if "Dans_les_delais" in sous.columns:
                traitees = sous["Dans_les_delais"].dropna()
                row[cat] = float(traitees.mean()) if len(traitees) else None
            else:
                row[cat] = None
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Date")


# ---------------------------------------------------------------------------
# Call Center
# ---------------------------------------------------------------------------
def _filtrer_cc(df: pd.DataFrame, periode: Periode) -> pd.DataFrame:
    if df.empty:
        return df
    # Utiliser "Date" comme colonne de date (c'est le nom dans les données fictives)
    if "Date" in df.columns:
        # Convertir en datetime si nécessaire
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            df = df.copy()
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        mask = (df["Date"] >= periode.debut) & (df["Date"] <= periode.fin)
        return df[mask]
    # Fallback sur Date_parsed si présent
    elif "Date_parsed" in df.columns:
        mask = (df["Date_parsed"] >= periode.debut) & (df["Date_parsed"] <= periode.fin)
        return df[mask]
    return df


def kpis_callcenter(df: pd.DataFrame, periode: Periode) -> dict:
    g = _filtrer_cc(df, periode)
    if g.empty:
        return {k: 0 for k in [
            "appels_recus", "taux_decroche", "taux_echange_delai", "temps_moyen_com",
            "appels_emis", "taux_appels_emis", "clients_joints", "taux_clients_joints",
            "rdv_pris", "taux_rdv_pris", "objectif_emis"
        ]}

    # Noms des colonnes dans les données fictives
    col_appels_recus = "Appels reçus" if "Appels reçus" in g.columns else "Appels recus"
    col_appels_decroches = "Appels décrochés" if "Appels décrochés" in g.columns else "Appels decroches"
    col_appels_delai = "Appels reçus dans le délai" if "Appels reçus dans le délai" in g.columns else "Appels recus dans le delai"
    col_appels_emis = "Appels émis" if "Appels émis" in g.columns else "Appels emis"
    col_objectif_emis = "Objectif appels émis" if "Objectif appels émis" in g.columns else "Objectif appels emis"
    col_clients_joints = "Clients joints"
    col_rdv_pris = "RDV pris" if "RDV pris" in g.columns else "RDV Pris"
    col_appels_rdv = "Appels pour RDV" if "Appels pour RDV" in g.columns else "Appels pour RDV"
    col_temps_com = "Temps moyen de communication" if "Temps moyen de communication" in g.columns else "Temps moyen de com"

    appels_recus = int(pd.to_numeric(g[col_appels_recus], errors="coerce").sum())
    appels_decroches = int(pd.to_numeric(g[col_appels_decroches], errors="coerce").sum())
    appels_dans_delai = int(pd.to_numeric(g[col_appels_delai], errors="coerce").sum()) if col_appels_delai in g.columns else 0
    appels_emis = int(pd.to_numeric(g[col_appels_emis], errors="coerce").sum())
    objectif_emis = int(pd.to_numeric(g[col_objectif_emis], errors="coerce").sum()) if col_objectif_emis in g.columns else 0
    clients_joints = int(pd.to_numeric(g[col_clients_joints], errors="coerce").sum()) if col_clients_joints in g.columns else 0
    rdv_pris = int(pd.to_numeric(g[col_rdv_pris], errors="coerce").sum()) if col_rdv_pris in g.columns else 0
    appels_pour_rdv = int(pd.to_numeric(g[col_appels_rdv], errors="coerce").sum()) if col_appels_rdv in g.columns else 0
    temps_moyen_com = pd.to_numeric(g[col_temps_com], errors="coerce").mean() if col_temps_com in g.columns else 0

    return {
        "appels_recus": appels_recus,
        "appels_decroches": appels_decroches,
        "taux_decroche": appels_decroches / appels_recus if appels_recus else 0,
        "appels_dans_delai": appels_dans_delai,
        "taux_echange_delai": appels_dans_delai / appels_decroches if appels_decroches else 0,
        "temps_moyen_com": temps_moyen_com,
        "appels_emis": appels_emis,
        "objectif_emis": objectif_emis,
        "taux_appels_emis": appels_emis / objectif_emis if objectif_emis else 0,
        "clients_joints": clients_joints,
        "taux_clients_joints": clients_joints / appels_emis if appels_emis else 0,
        "rdv_pris": rdv_pris,
        "appels_pour_rdv": appels_pour_rdv,
        "taux_rdv_pris": rdv_pris / appels_pour_rdv if appels_pour_rdv else 0,
    }


# ---------------------------------------------------------------------------
# Messagerie
# ---------------------------------------------------------------------------
def _filtrer_messagerie(df: pd.DataFrame, periode: Periode) -> pd.DataFrame:
    if df.empty:
        return df
    if "Date" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            df = df.copy()
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        mask = (df["Date"] >= periode.debut) & (df["Date"] <= periode.fin)
        return df[mask]
    elif "Date_parsed" in df.columns:
        mask = (df["Date_parsed"] >= periode.debut) & (df["Date_parsed"] <= periode.fin)
        return df[mask]
    return df


def kpis_messagerie(df: pd.DataFrame, periode: Periode) -> dict:
    if df.empty:
        return {"whatsapp_recues": 0, "whatsapp_cloturees": 0, "taux_whatsapp": 0,
                "mail_recues": 0, "mail_cloturees": 0, "taux_mail": 0}
    g = _filtrer_messagerie(df, periode)
    if g.empty:
        return {"whatsapp_recues": 0, "whatsapp_cloturees": 0, "taux_whatsapp": 0,
                "mail_recues": 0, "mail_cloturees": 0, "taux_mail": 0}

    # Noms des colonnes dans les données fictives
    col_wa_recues = "WhatsApp reçues" if "WhatsApp reçues" in g.columns else "WhatsApp recues"
    col_wa_cloturees = "WhatsApp clôturées" if "WhatsApp clôturées" in g.columns else "WhatsApp cloturees"
    col_mail_recues = "Mail reçus" if "Mail reçus" in g.columns else "Mail recus"
    col_mail_cloturees = "Mail clôturés" if "Mail clôturés" in g.columns else "Mail clotures"

    wa_recues = int(pd.to_numeric(g[col_wa_recues], errors="coerce").sum())
    wa_clo = int(pd.to_numeric(g[col_wa_cloturees], errors="coerce").sum())
    mail_recues = int(pd.to_numeric(g[col_mail_recues], errors="coerce").sum()) if col_mail_recues in g.columns else 0
    mail_clo = int(pd.to_numeric(g[col_mail_cloturees], errors="coerce").sum()) if col_mail_cloturees in g.columns else 0
    
    return {
        "whatsapp_recues": wa_recues,
        "whatsapp_cloturees": wa_clo,
        "taux_whatsapp": wa_clo / wa_recues if wa_recues else 0,
        "mail_recues": mail_recues,
        "mail_cloturees": mail_clo,
        "taux_mail": mail_clo / mail_recues if mail_recues else 0,
    }