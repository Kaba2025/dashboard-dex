"""
Ingestion des nouvelles sources : Réclamation, Call Center, Messagerie.

Même principe que satisfaction.py : chaque source est UN SEUL fichier
(cumulatif, toujours réenvoyé enrichi), on lit systématiquement le plus
récent. Digital et Déshérence n'ont pas encore de base brute automatisée :
en attendant, l'équipe continue la saisie manuelle dans son outil habituel,
exporte en .xlsx, et ce fichier est déposé/importé ici de la même façon.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RECLA_DIR = DATA_DIR / "reclamation"
CC_DIR = DATA_DIR / "callcenter"
MSG_DIR = DATA_DIR / "messagerie"
DIGITAL_DIR = DATA_DIR / "digital"
DESHERENCE_DIR = DATA_DIR / "desherence"

RECLA_COLUMNS = [
    "N Reclamation", "Police N1", "Nom", "Prenoms", "Contact du client", "Libelle agence",
    "Gestionnaire", "Date de reclamation", "Date de cloture", "Etat", "Categorie_Delai",
    "Objectif_Jours", "Motif de la reclamation", "Mode de declaration",
]
CC_COLUMNS = [
    "Date", "Appels decroches", "Appels recus", "Appels recus dans le delai", "Temps moyen de com",
    "Appels emis", "Objectif appels emis", "Clients joints", "RDV Pris", "Appels pour RDV",
]
MSG_COLUMNS = [
    "Date", "WhatsApp cloturees", "Obj Jour WhatsApp", "WhatsApp recues",
    "Mail cloturees", "Obj Jour Mail", "Mail recues",
]


def _latest_file(folder: Path):
    if not folder.exists():
        return None
    candidates = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)


def _fingerprint(folder: Path) -> tuple:
    f = _latest_file(folder)
    return (str(f), f.stat().st_size, f.stat().st_mtime) if f else ()


# ---------------------------------------------------------------------------
# Réclamation
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Lecture des réclamations...")
def load_reclamation(_fp: tuple) -> pd.DataFrame:
    path = _latest_file(RECLA_DIR)
    if not path:
        return pd.DataFrame(columns=RECLA_COLUMNS)
    df = _read(path)
    df.columns = [str(c).strip() for c in df.columns]
    for c in RECLA_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[RECLA_COLUMNS].copy()

    df["Date_reception"] = pd.to_datetime(df["Date de reclamation"], dayfirst=True, errors="coerce")
    df["Date_cloture"] = pd.to_datetime(df["Date de cloture"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date_reception"])

    # Délai réel (jours calendaires) pour les réclamations clôturées uniquement
    df["Delai_reel"] = (df["Date_cloture"] - df["Date_reception"]).dt.days
    df["Objectif_Jours"] = pd.to_numeric(df["Objectif_Jours"], errors="coerce").fillna(10)
    df["Dans_les_delais"] = (df["Delai_reel"] <= df["Objectif_Jours"]).astype("object")
    # Non clôturée = ni dans les délais ni hors délais tant qu'elle n'est pas traitée
    df.loc[df["Date_cloture"].isna(), "Dans_les_delais"] = pd.NA

    return df


def get_reclamation() -> pd.DataFrame:
    return load_reclamation(_fingerprint(RECLA_DIR))


# ---------------------------------------------------------------------------
# Call Center
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Lecture des données call center...")
def load_callcenter(_fp: tuple) -> pd.DataFrame:
    path = _latest_file(CC_DIR)
    if not path:
        return pd.DataFrame(columns=CC_COLUMNS)
    df = _read(path)
    df.columns = [str(c).strip() for c in df.columns]
    for c in CC_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[CC_COLUMNS].copy()
    df["Date_parsed"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["Date_parsed"])


def get_callcenter() -> pd.DataFrame:
    return load_callcenter(_fingerprint(CC_DIR))


# ---------------------------------------------------------------------------
# Messagerie
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Lecture des données messagerie...")
def load_messagerie(_fp: tuple) -> pd.DataFrame:
    path = _latest_file(MSG_DIR)
    if not path:
        return pd.DataFrame(columns=MSG_COLUMNS)
    df = _read(path)
    df.columns = [str(c).strip() for c in df.columns]
    for c in MSG_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[MSG_COLUMNS].copy()
    df["Date_parsed"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["Date_parsed"])


def get_messagerie() -> pd.DataFrame:
    return load_messagerie(_fingerprint(MSG_DIR))


# ---------------------------------------------------------------------------
# Digital / Déshérence — pas encore de base brute : saisie manuelle + import
# ---------------------------------------------------------------------------
def save_manual_entry(folder: Path, df: pd.DataFrame, filename: str):
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*"):
        old.unlink()
    df.to_excel(folder / filename, index=False)


def get_digital() -> pd.DataFrame:
    path = _latest_file(DIGITAL_DIR)
    if not path:
        return pd.DataFrame()
    return _read(path)


def get_desherence() -> pd.DataFrame:
    path = _latest_file(DESHERENCE_DIR)
    if not path:
        return pd.DataFrame()
    return _read(path)
