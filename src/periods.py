"""
Moteur de périodes dynamique pour le dashboard NSIA DEX.

Le module est volontairement indépendant de Streamlit et des KPI.
Il fournit :
- les 7 granularités métier ;
- la construction des périodes à partir des dates réellement disponibles ;
- la période sélectionnée ;
- la période précédente ;
- les bornes de chaque période ;
- le filtrage d'un DataFrame ;
- les variations absolues et relatives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd


GRANULARITES = (
    "Journalier",
    "Hebdomadaire",
    "Mensuel",
    "Bimestriel",
    "Trimestriel",
    "Semestriel",
    "Annuel",
)


MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}


@dataclass(frozen=True)
class Periode:
    granularite: str
    debut: pd.Timestamp
    fin: pd.Timestamp
    label: str
    cle: str

    @property
    def jours(self) -> int:
        return (self.fin.normalize() - self.debut.normalize()).days + 1


def normaliser_dates(df: pd.DataFrame, date_col: str = "Date") -> pd.Series:
    """Retourne une série de dates normalisées, NaT pour les valeurs invalides."""
    if date_col not in df.columns:
        raise KeyError(f"Colonne de date absente : {date_col}")
    return pd.to_datetime(df[date_col], errors="coerce", dayfirst=True).dt.normalize()


def _timestamp(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.normalize()


def _debut_semaine(ts: pd.Timestamp) -> pd.Timestamp:
    # Semaine ISO lundi -> dimanche.
    return ts - pd.Timedelta(days=ts.weekday())


def _fin_semaine(ts: pd.Timestamp) -> pd.Timestamp:
    return _debut_semaine(ts) + pd.Timedelta(days=6)


def _debut_bimestre(ts: pd.Timestamp) -> pd.Timestamp:
    mois = ((ts.month - 1) // 2) * 2 + 1
    return pd.Timestamp(year=ts.year, month=mois, day=1)


def _fin_bimestre(ts: pd.Timestamp) -> pd.Timestamp:
    debut = _debut_bimestre(ts)
    return debut + pd.offsets.MonthEnd(2)


def _debut_trimestre(ts: pd.Timestamp) -> pd.Timestamp:
    mois = ((ts.month - 1) // 3) * 3 + 1
    return pd.Timestamp(year=ts.year, month=mois, day=1)


def _fin_trimestre(ts: pd.Timestamp) -> pd.Timestamp:
    debut = _debut_trimestre(ts)
    return debut + pd.offsets.MonthEnd(3)


def _debut_semestre(ts: pd.Timestamp) -> pd.Timestamp:
    mois = 1 if ts.month <= 6 else 7
    return pd.Timestamp(year=ts.year, month=mois, day=1)


def _fin_semestre(ts: pd.Timestamp) -> pd.Timestamp:
    debut = _debut_semestre(ts)
    return debut + pd.offsets.MonthEnd(6)


def periode_depuis_date(ts, granularite: str) -> Periode:
    """Construit la période contenant la date donnée."""
    ts = _timestamp(ts)

    if granularite not in GRANULARITES:
        raise ValueError(
            f"Granularité inconnue : {granularite}. "
            f"Valeurs attendues : {', '.join(GRANULARITES)}"
        )

    if granularite == "Journalier":
        debut, fin = ts, ts
        label = ts.strftime("%d/%m/%Y")
        cle = ts.strftime("%Y-%m-%d")

    elif granularite == "Hebdomadaire":
        debut, fin = _debut_semaine(ts), _fin_semaine(ts)
        iso = debut.isocalendar()
        label = f"S{int(iso.week)} {int(iso.year)}"
        cle = f"{int(iso.year)}-S{int(iso.week):02d}"

    elif granularite == "Mensuel":
        debut = ts.replace(day=1)
        fin = debut + pd.offsets.MonthEnd(1)
        label = f"{MOIS_FR[ts.month]} {ts.year}"
        cle = ts.strftime("%Y-%m")

    elif granularite == "Bimestriel":
        debut = _debut_bimestre(ts)
        fin = _fin_bimestre(ts)
        bimestre = ((ts.month - 1) // 2) + 1
        label = f"B{bimestre} {ts.year}"
        cle = f"{ts.year}-B{bimestre}"

    elif granularite == "Trimestriel":
        debut = _debut_trimestre(ts)
        fin = _fin_trimestre(ts)
        trimestre = ((ts.month - 1) // 3) + 1
        label = f"T{trimestre} {ts.year}"
        cle = f"{ts.year}-T{trimestre}"

    elif granularite == "Semestriel":
        debut = _debut_semestre(ts)
        fin = _fin_semestre(ts)
        semestre = 1 if ts.month <= 6 else 2
        label = f"S{semestre} {ts.year}"
        cle = f"{ts.year}-S{semestre}"

    else:  # Annuel
        debut = pd.Timestamp(year=ts.year, month=1, day=1)
        fin = pd.Timestamp(year=ts.year, month=12, day=31)
        label = str(ts.year)
        cle = str(ts.year)

    return Periode(granularite, debut, fin, label, cle)


def periode_precedente(periode: Periode) -> Periode:
    """Retourne la période immédiatement précédente, de même granularité."""
    if periode.granularite == "Journalier":
        cible = periode.debut - pd.Timedelta(days=1)
    elif periode.granularite == "Hebdomadaire":
        cible = periode.debut - pd.Timedelta(days=7)
    elif periode.granularite == "Mensuel":
        cible = periode.debut - pd.offsets.MonthBegin(1)
    elif periode.granularite == "Bimestriel":
        cible = periode.debut - pd.DateOffset(months=2)
    elif periode.granularite == "Trimestriel":
        cible = periode.debut - pd.DateOffset(months=3)
    elif periode.granularite == "Semestriel":
        cible = periode.debut - pd.DateOffset(months=6)
    elif periode.granularite == "Annuel":
        cible = periode.debut - pd.DateOffset(years=1)
    else:
        raise ValueError(f"Granularité inconnue : {periode.granularite}")

    return periode_depuis_date(cible, periode.granularite)


def construire_periodes(
    df: pd.DataFrame,
    granularite: str,
    date_col: str = "Date",
) -> list[Periode]:
    """Retourne toutes les périodes couvertes par les dates valides du DataFrame."""
    dates = normaliser_dates(df, date_col).dropna()
    if dates.empty:
        return []

    debut = dates.min()
    fin = dates.max()

    # Pour une granularité donnée, on génère les périodes calendrier entre
    # la première et la dernière date réellement disponibles.
    courante = periode_depuis_date(debut, granularite)
    resultat = []

    while courante.debut <= fin:
        resultat.append(courante)
        if granularite == "Journalier":
            prochaine_date = courante.debut + pd.Timedelta(days=1)
        elif granularite == "Hebdomadaire":
            prochaine_date = courante.debut + pd.Timedelta(days=7)
        elif granularite == "Mensuel":
            prochaine_date = courante.debut + pd.DateOffset(months=1)
        elif granularite == "Bimestriel":
            prochaine_date = courante.debut + pd.DateOffset(months=2)
        elif granularite == "Trimestriel":
            prochaine_date = courante.debut + pd.DateOffset(months=3)
        elif granularite == "Semestriel":
            prochaine_date = courante.debut + pd.DateOffset(months=6)
        else:
            prochaine_date = courante.debut + pd.DateOffset(years=1)

        courante = periode_depuis_date(prochaine_date, granularite)

    return resultat


def filtrer_periode(
    df: pd.DataFrame,
    periode: Periode,
    date_col: str = "Date",
) -> pd.DataFrame:
    """Filtre les lignes dont la date tombe dans la période."""
    dates = normaliser_dates(df, date_col)
    masque = dates.between(periode.debut, periode.fin, inclusive="both")
    return df.loc[masque].copy()


def plage_dates_dex(datasets: dict[str, pd.DataFrame], date_col: str = "Date"):
    """Trouve la première et la dernière date disponibles dans toutes les bases."""
    dates = []

    for df in datasets.values():
        if date_col not in df.columns:
            continue
        serie = normaliser_dates(df, date_col).dropna()
        if not serie.empty:
            dates.extend([serie.min(), serie.max()])

    if not dates:
        return None, None

    return min(dates), max(dates)


def variation(actuel: float, precedent: float) -> tuple[float, Optional[float]]:
    """Retourne variation absolue et variation %.

    Le pourcentage n'est pas calculé si la valeur précédente est nulle.
    """
    actuel = float(actuel or 0)
    precedent = float(precedent or 0)
    delta = actuel - precedent

    if precedent == 0:
        pct = None
    else:
        pct = (delta / abs(precedent)) * 100

    return delta, pct


def resume_comparaison(
    actuel: float,
    precedent: float,
    periode: Periode,
) -> dict:
    """Structure prête à être consommée par les cartes KPI."""
    delta, pct = variation(actuel, precedent)
    prev = periode_precedente(periode)

    return {
        "periode_actuelle": periode.label,
        "periode_precedente": prev.label,
        "actuel": actuel,
        "precedent": precedent,
        "variation": delta,
        "variation_pct": pct,
        "label_comparaison": f"{periode.label} vs {prev.label}",
    }