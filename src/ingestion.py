"""
Ingestion des deux sources de données :

1) SATISFACTION — un seul fichier partagé par toutes les agences depuis
   janvier. On lit le fichier le plus récent trouvé dans data/satisfaction/
   (il grossit jour après jour, jamais remplacé par un autre découpage).

2) RÉCEPTION — un fichier par agence dans data/reception/<AGENCE>/, qui
   donne le nombre RÉEL de clients reçus par jour (répondants + non-
   répondants) et le nom du gestionnaire. Le format Vallon est détecté
   automatiquement (présence de la colonne "Temps d'attente") : il a des
   colonnes en plus (délais, appli mobile) que les autres agences n'ont pas.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAT_DIR = DATA_DIR / "satisfaction"
REC_DIR = DATA_DIR / "reception"

SAT_COLUMNS = [
    "Identifiant", "Nom client", "Contact client", "Addresse mail", "Autres",
    "Libelle agence", "Information sur contrat", "Disponibilite du reglement",
    "Demande de prestation", "Reclamation", "Satisfaction", "Commentaire",
    "Provenance", "DATE DE CREATION",
]
SATISFAIT_VALUES = {"Tres Satisfait", "Satisfait"}
PROMOTEUR_VALUES = {"Tres Satisfait"}
DETRACTEUR_VALUES = {"Peu Satisfait", "Insatisfait"}

REC_COLUMNS_STANDARD = ["Date reception", "Nom et Prenoms", "Numeros police", "Contact",
                         "Gestionnaire", "Motifs visite", "Statut Ticket", "Rec_Mois"]
REC_COLUMNS_VALLON = ["Service", "Motif", "Numero du ticket", "Contact", "Observation",
                       "Email", "Has App Mobile", "Temps d'attente", "Temps de transaction", "Date"]


# ---------------------------------------------------------------------------
# Localisation fichiers
# ---------------------------------------------------------------------------
def _latest_file(folder: Path) -> Path | None:
    if not folder.exists():
        return None
    candidates = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def _latest_file_per_agency(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    out = {}
    for agence_dir in root.iterdir():
        if agence_dir.is_dir():
            f = _latest_file(agence_dir)
            if f:
                out[agence_dir.name] = f
    return out


def _fingerprint() -> tuple:
    files = []
    sat = _latest_file(SAT_DIR)
    if sat:
        files.append(sat)
    files.extend(_latest_file_per_agency(REC_DIR).values())
    return tuple((str(f), f.stat().st_size, f.stat().st_mtime) for f in files)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)


# ---------------------------------------------------------------------------
# Contrôle qualité
# ---------------------------------------------------------------------------
def quality_report(df_sat: pd.DataFrame, rec_by_agency: dict[str, pd.DataFrame]) -> list[str]:
    issues = []
    if df_sat.empty:
        issues.append("Aucun fichier satisfaction trouvé dans data/satisfaction/")
    else:
        for col in ["Identifiant", "Libelle agence", "Satisfaction", "DATE DE CREATION"]:
            n_missing = df_sat[col].isna().sum() if col in df_sat.columns else len(df_sat)
            if n_missing:
                issues.append(f"Satisfaction : {n_missing} ligne(s) sans « {col} »")
        n_dupes = df_sat.duplicated(subset=["Identifiant"]).sum()
        if n_dupes:
            issues.append(f"Satisfaction : {n_dupes} Identifiant(s) en double (dernière occurrence conservée)")

    if not rec_by_agency:
        issues.append("Aucun fichier de réception trouvé dans data/reception/<agence>/")

    return issues


# ---------------------------------------------------------------------------
# Chargement SATISFACTION
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Lecture du fichier satisfaction...")
def load_satisfaction(_fingerprint: tuple) -> pd.DataFrame:
    path = _latest_file(SAT_DIR)
    if not path:
        return pd.DataFrame(columns=SAT_COLUMNS)

    df = _read(path)
    df.columns = [str(c).strip() for c in df.columns]
    for c in SAT_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[SAT_COLUMNS].copy()

    df["Date"] = pd.to_datetime(df["DATE DE CREATION"], dayfirst=True, errors="coerce").dt.normalize()
    df = df.drop_duplicates(subset=["Identifiant"], keep="last")
    df = df.dropna(subset=["Date", "Satisfaction", "Libelle agence"])

    df["Satisfait_bin"] = df["Satisfaction"].isin(SATISFAIT_VALUES)
    df["Promoteur_bin"] = df["Satisfaction"].isin(PROMOTEUR_VALUES)
    df["Detracteur_bin"] = df["Satisfaction"].isin(DETRACTEUR_VALUES)
    df["Reclamation_bin"] = df["Reclamation"].astype(str).str.strip().str.upper() == "OUI"

    iso = df["Date"].dt.isocalendar()
    df["Semaine_ISO"] = iso["week"]
    df["Annee_ISO"] = iso["year"]
    return df


# ---------------------------------------------------------------------------
# Chargement RÉCEPTION (par agence, Vallon détecté automatiquement)
# ---------------------------------------------------------------------------
def _is_vallon_format(raw_columns: list[str]) -> bool:
    return "Temps d'attente" in raw_columns


def _standardize_reception(raw: pd.DataFrame, agence_label: str) -> tuple[pd.DataFrame, bool]:
    raw.columns = [str(c).strip() for c in raw.columns]
    is_vallon = _is_vallon_format(list(raw.columns))

    if is_vallon:
        for c in REC_COLUMNS_VALLON:
            if c not in raw.columns:
                raw[c] = None
        df = raw[REC_COLUMNS_VALLON].copy()
        df["Date_parsed"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.normalize()
        df["Gestionnaire"] = "TABLETTE CENTRALE"
    else:
        for c in REC_COLUMNS_STANDARD:
            if c not in raw.columns:
                raw[c] = None
        df = raw[REC_COLUMNS_STANDARD].copy()
        df["Date_parsed"] = pd.to_datetime(df["Date reception"], dayfirst=True, errors="coerce").dt.normalize()

    df["Libelle agence"] = agence_label
    df["is_vallon"] = is_vallon
    df = df.dropna(subset=["Date_parsed"])
    return df, is_vallon


@st.cache_data(show_spinner="Lecture des fichiers de réception...")
def load_reception(_fingerprint: tuple) -> dict[str, pd.DataFrame]:
    """Un DataFrame standardisé par agence (clé = nom d'agence tel qu'il
    apparaît dans le fichier satisfaction, déduit du nom de dossier)."""
    latest = _latest_file_per_agency(REC_DIR)
    out = {}
    for agence_folder, path in latest.items():
        agence_label = agence_folder.replace("_", " ")
        raw = _read(path)
        df, _ = _standardize_reception(raw, agence_label)
        out[agence_label] = df
    return out


def reception_footfall_daily(rec_by_agency: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Une ligne par (agence, date) avec le total de clients reçus ce
    jour-là -- sert de dénominateur pour le % de recueil de satisfaction."""
    rows = []
    for agence, df in rec_by_agency.items():
        if df.empty:
            continue
        counts = df.groupby(df["Date_parsed"].dt.date).size()
        for d, n in counts.items():
            rows.append({"Libelle agence": agence, "Date": pd.Timestamp(d), "Total clients recus": int(n)})
    return pd.DataFrame(rows)


def get_data():
    fp = _fingerprint()
    df_sat = load_satisfaction(fp)
    rec_by_agency = load_reception(fp)
    freq = reception_footfall_daily(rec_by_agency)
    issues = quality_report(df_sat, rec_by_agency)
    return df_sat, rec_by_agency, freq, issues


def get_data():
    fp=_fingerprint
    df_sat = load_satisfaction(fp)
