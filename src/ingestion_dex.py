"""
Ingestion centrale de la base DEX NSIA.

Le dashboard doit fonctionner à partir d'UN SEUL fichier Excel contenant
les 6 feuilles métiers :
    - DIGITAL
    - MESSAGERIE
    - RC & SATISFACTION
    - PHYSIQUE
    - CALLCENTER
    - DESHERENCE

Ce module ne calcule pas encore les KPI et ne dessine rien : il se limite à
charger, normaliser et contrôler la base source. Les onglets seront adaptés
à ce contrat dans les étapes suivantes.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEX_DIR = DATA_DIR / "dex"
DEX_FILE_PREFIX = "NSIA_DEX_dernier_envoi"

# Colonnes demandées par le cahier des charges. On les conserve dans leur
# écriture métier afin que les futurs KPI puissent les utiliser directement.
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "DIGITAL": [
        "Date", "Agence", "Code", "Prestations Digital", "Total Prestations",
        "Contre Performance", "Initiative", "Semaine", "Mois",
        "EST VIDE CONTRE", "EST VIDE INIT", "Filtre",
    ],
    "MESSAGERIE": [
        "Date", "WhatsApp clôturées", "Objectif Jour WhatsApp", "WhatsApp reçues",
        "CP WhatsApp", "INITIA WhatsApp", "Mail clôturés", "Objectif Jour Mail",
        "Mail reçus", "CP ÉCOUTE CI", "INITIATIVE ÉCOUTE", "Semaine", "Mois", "Filtre",
    ],
    "RC & SATISFACTION": [
        "Date", "Recueil de satisfaction", "Total clients reçus", "Clients satisfaits",
        "Observations", "Initiative", "Réclamations MOIS traitées dans les délais",
        "Réclamations MOIS reçues", "Réclamations ANNÉE traitées dans les délais",
        "Réclamations ANNÉE reçues", "Réclamations COMMISSION traitées dans les délais",
        "Réclamations COMMISSION reçues", "Réclamations ANNULATION COMMISSION reçues",
        "Nombre de mise à jour journalière", "Contre Performance", "Semaine", "Mois",
        "Filtre", "Date2",
    ],
    "PHYSIQUE": [
        "Date", "Agence", "Code", "TIME OK", "Temps de présence", "Clients ON TIME",
        "Clients reçus", "Temps d'attente", "Temps de prise en charge",
        "Nombre de clients attendus en moins de 15 minutes",
        "Nombre de clients pris en charge en moins de 15 minutes", "CP ATTENTE",
        "INITIATIVE ATTENTE", "CP PRISE EN CHARGE", "INITIATIVE PRISE EN CHARGE",
        "QUICK", "Semaine", "Mois", "EST VIDE ATT", "EST VIDE PC", "Filtre", "Date2",
    ],
    "CALLCENTER": [
        "Date", "Appels décrochés", "Appels reçus", "Appels reçus dans le délai",
        "Temps moyen de communication", "Appels émis", "Objectif appels émis", "Clients joints",
        "RDV pris", "Appels pour RDV", "CP Appels Entrants", "CP Appels Sortants",
        "INITIA Appels Entrants", "INITIA Appels Sortants", "Semaine", "Mois",
        "EST VIDE CONT", "EST VIDE INIT", "Filtre", "Date2",
    ],
    "DESHERENCE": [
        "CP Appels Entrants", "CP Appels Sortants", "INITIA Appels Entrants",
        "INITIA Appels Sortants", "Semaine", "Mois", "EST VIDE CONT", "EST VIDE INIT",
        "Filtre", "Date", "Date2",
    ],
}

# Plusieurs écritures peuvent être rencontrées dans un fichier Excel réel.
# On les résout sans modifier le nom métier retourné au dashboard.
SHEET_ALIASES: dict[str, set[str]] = {
    "DIGITAL": {"digital", "base digital"},
    "MESSAGERIE": {"messagerie", "base messagerie"},
    "RC & SATISFACTION": {
        "rc & satisfaction", "rc et satisfaction", "base rc & satisfaction",
        "base rc et satisfaction", "satisfaction", "rc satisfaction",
    },
    "PHYSIQUE": {"physique", "base physique", "reception physique", "réception physique"},
    "CALLCENTER": {"callcenter", "call center", "base callcenter", "base call center"},
    "DESHERENCE": {"desherence", "déshérence", "base desherence", "base déshérence"},
}

DATE_COLUMNS = {
    "DIGITAL": ["Date"],
    "MESSAGERIE": ["Date"],
    "RC & SATISFACTION": ["Date", "Date2"],
    "PHYSIQUE": ["Date", "Date2"],
    "CALLCENTER": ["Date", "Date2"],
    "DESHERENCE": ["Date", "Date2"],
}


@dataclass
class DEXValidation:
    ok: bool
    sheet_map: dict[str, str]
    missing_sheets: list[str]
    missing_columns: dict[str, list[str]]
    warnings: list[str]

    @property
    def issues(self) -> list[str]:
        issues: list[str] = []
        issues.extend([f"Feuille absente : {x}" for x in self.missing_sheets])
        for sheet, cols in self.missing_columns.items():
            if cols:
                issues.append(f"{sheet} : colonnes absentes : {', '.join(cols)}")
        issues.extend(self.warnings)
        return issues


def normalize_label(value: Any) -> str:
    """Normalise un nom de feuille/colonne pour comparaison uniquement."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text.strip().lower())
    return text


def _sheet_aliases_for(canonical: str) -> set[str]:
    return {normalize_label(canonical), *(normalize_label(x) for x in SHEET_ALIASES.get(canonical, set()))}


def _find_sheet(sheet_names: list[str], canonical: str) -> str | None:
    aliases = _sheet_aliases_for(canonical)
    for name in sheet_names:
        if normalize_label(name) in aliases:
            return name
    return None


def _rename_columns_to_canonical(df: pd.DataFrame, expected: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Mappe les colonnes par nom normalisé, sans casser les noms métier."""
    normalized_actual: dict[str, str] = {}
    for col in df.columns:
        key = normalize_label(col)
        if key not in normalized_actual:
            normalized_actual[key] = str(col)

    missing: list[str] = []
    rename_map: dict[str, str] = {}
    for wanted in expected:
        actual = normalized_actual.get(normalize_label(wanted))
        if actual is None:
            missing.append(wanted)
        elif actual != wanted:
            rename_map[actual] = wanted

    out = df.rename(columns=rename_map).copy()
    return out, missing


def _read_excel(path: Path) -> dict[str, pd.DataFrame]:
    # sheet_name=None lit toutes les feuilles en une seule lecture.
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")


def _latest_dex_file() -> Path | None:
    if not DEX_DIR.exists():
        return None
    candidates = [
        p for p in DEX_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm", ".xls", ".csv"}
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def save_uploaded_dex(uploaded_file) -> Path:
    """Enregistre le dernier Excel central. Les anciens fichiers sont remplacés."""
    if uploaded_file is None:
        raise ValueError("Aucun fichier DEX n'a été fourni.")

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".xlsx", ".xlsm", ".xls"}:
        raise ValueError("La base DEX doit être un fichier Excel (.xlsx, .xlsm ou .xls).")

    DEX_DIR.mkdir(parents=True, exist_ok=True)
    for old in DEX_DIR.iterdir():
        if old.is_file():
            old.unlink()

    destination = DEX_DIR / f"{DEX_FILE_PREFIX}{suffix}"
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def validate_workbook(path: Path) -> DEXValidation:
    """Vérifie les 6 feuilles et leurs colonnes avant tout calcul."""
    if not path.exists():
        return DEXValidation(False, {}, list(REQUIRED_COLUMNS), {}, ["Fichier DEX introuvable."])

    try:
        workbook = _read_excel(path)
    except Exception as exc:
        return DEXValidation(False, {}, [], {}, [f"Impossible de lire le fichier Excel : {exc}"])

    sheet_names = list(workbook.keys())
    sheet_map: dict[str, str] = {}
    missing_sheets: list[str] = []
    missing_columns: dict[str, list[str]] = {}
    warnings: list[str] = []

    for canonical, expected in REQUIRED_COLUMNS.items():
        actual_sheet = _find_sheet(sheet_names, canonical)
        if actual_sheet is None:
            missing_sheets.append(canonical)
            continue
        sheet_map[canonical] = actual_sheet
        _, missing = _rename_columns_to_canonical(workbook[actual_sheet], expected)
        missing_columns[canonical] = missing

        if workbook[actual_sheet].empty:
            warnings.append(f"{canonical} : feuille vide.")

    ok = not missing_sheets and not any(missing_columns.values())
    return DEXValidation(ok, sheet_map, missing_sheets, missing_columns, warnings)


def _prepare_sheet(df: pd.DataFrame, canonical: str) -> pd.DataFrame:
    expected = REQUIRED_COLUMNS[canonical]
    out, missing = _rename_columns_to_canonical(df, expected)
    if missing:
        raise ValueError(f"{canonical}: colonnes manquantes: {', '.join(missing)}")

    # On conserve aussi d'éventuelles colonnes supplémentaires du fichier.
    # Les colonnes attendues restent prioritaires et dans l'ordre du cahier des charges.
    extras = [c for c in out.columns if c not in expected]
    out = out[expected + extras].copy()

    for col in DATE_COLUMNS.get(canonical, []):
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], dayfirst=True, errors="coerce").dt.normalize()

    # Les champs Semaine/Mois peuvent être numériques ou texte selon Excel.
    for col in ["Semaine", "Mois"]:
        if col in out.columns:
            numeric = pd.to_numeric(out[col], errors="coerce")
            if numeric.notna().sum() >= max(1, int(len(out) * 0.8)):
                out[col] = numeric
            else:
                out[col] = out[col].astype("string").str.strip()

    return out


@st.cache_data(show_spinner="Lecture de la base DEX...")
def load_dex(_fingerprint: tuple) -> dict[str, pd.DataFrame]:
    """Charge les 6 feuilles et retourne un dictionnaire indexé par nom métier."""
    path = _latest_dex_file()
    if path is None:
        return {}

    workbook = _read_excel(path)
    validation = validate_workbook(path)
    if not validation.ok:
        details = "\n".join(f"- {issue}" for issue in validation.issues)
        raise ValueError(f"La base DEX est invalide :\n{details}")

    return {
        canonical: _prepare_sheet(workbook[actual_sheet], canonical)
        for canonical, actual_sheet in validation.sheet_map.items()
    }


def _fingerprint() -> tuple:
    path = _latest_dex_file()
    if path is None:
        return ()
    stat = path.stat()
    return (str(path), stat.st_size, stat.st_mtime_ns)


def get_dex_data() -> dict[str, pd.DataFrame]:
    """Point d'entrée public utilisé par app.py."""
    return load_dex(_fingerprint())


def quality_report(datasets: dict[str, pd.DataFrame]) -> list[str]:
    """Rapport simple de qualité avant construction des KPI."""
    issues: list[str] = []
    for sheet, df in datasets.items():
        if df.empty:
            issues.append(f"{sheet} : aucune ligne de données.")

        date_cols = [c for c in DATE_COLUMNS.get(sheet, []) if c in df.columns]
        if date_cols:
            main_date = date_cols[0]
            invalid = int(df[main_date].isna().sum())
            if invalid:
                issues.append(f"{sheet} : {invalid} ligne(s) avec une date {main_date} invalide ou vide.")

        if sheet in {"DIGITAL", "PHYSIQUE"} and "Agence" in df.columns:
            missing_agency = int(df["Agence"].isna().sum())
            if missing_agency:
                issues.append(f"{sheet} : {missing_agency} ligne(s) sans agence.")

    return issues