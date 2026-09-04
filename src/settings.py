"""
La valeur du baromètre (grande enquête annuelle) ne doit être modifiée que
lorsqu'une nouvelle enquête est réalisée -- pas à chaque redémarrage. Elle
est donc stockée dans un petit fichier de configuration, pas dans le code,
pour que Kaba puisse la mettre à jour depuis l'application elle-même.
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.json"
DEFAUT_CSAT_BAROMETRE = 0.68


def get_csat_barometre() -> float:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text()).get("csat_barometre", DEFAUT_CSAT_BAROMETRE)
        except Exception:
            return DEFAUT_CSAT_BAROMETRE
    return DEFAUT_CSAT_BAROMETRE


def set_csat_barometre(valeur: float):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"csat_barometre": valeur}))
