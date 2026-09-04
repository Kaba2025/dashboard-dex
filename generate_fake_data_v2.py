"""
Génère les nouvelles sources fictives : Réclamation (base unique, un
enregistrement par réclamation), Call Center (agrégat journalier unique),
Messagerie (agrégat journalier unique, WhatsApp + Ecoute.ci).

Hypothèses faites en l'absence de la structure exacte (à ajuster avec les
vrais fichiers de Kaba) :
- Réclamation : 4 catégories de délai (Standard 10j, Base Échue 15j,
  Commission 10j, Commission Base Échue 15j) -- champ "Categorie_Delai".
- Call Center et Messagerie : structure directement lisible sur les
  captures (agrégat journalier), reproduite fidèlement.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

random.seed(21)
fake = Faker("fr_FR")
Faker.seed(21)

BASE = Path("/home/claude/nsia_dashboard/data")

AGENCES = [
    "NSIA VIE ASSURANCE VALLON", "NSIA VIE ASSURANCE KOUMASSI", "NSIA VIE ASSURANCE MAN",
    "NSIA VIE ASSURANCE BOUAKE", "NSIA VIE ASSURANCE DALOA", "NSIA VIE ASSURANCE KORHOGO",
    "NSIA VIE ASSURANCE SAN PEDRO", "NSIA VIE ASSURANCE YAMOUSSOUKRO", "NSIA VIE ASSURANCE ABENGOUROU",
]

GESTIONNAIRES = ["KOROGHO Agent Accueil", "SANOGO NASSIATA GAELLE", "ADOU EKIA MARIE JEANNE",
                  "DOUA MARINA", "SIALLOU AMENA ESTELLE", "DRAME AMY NOURA", "BONY DAMAS JUNIOR YANN"]

MOTIFS_RECLA = ["Indisponibilité du règlement", "Contestation de la valeur suite à un rachat total",
                 "Contestation de la souscription du contrat", "Demande de prestations non traitée",
                 "Irrégularités primes", "Prélèvement après rachat total", "Réclamation sur prestations"]

CANAUX = ["Mail", "Téléphone", "Rencontre", "Courrier", "Facebook"]
CATEGORIES_DELAI = {
    "Standard": 10,
    "Base Echue": 15,
    "Commission": 10,
    "Commission Base Echue": 15,
}
CATEGORIE_WEIGHTS = [0.55, 0.20, 0.15, 0.10]


def business_days(start, end):
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


DATES = business_days(datetime(2026, 1, 1), datetime(2026, 8, 13))


# ---------------------------------------------------------------------------
# 1) RÉCLAMATION — un enregistrement par réclamation, fichier unique cumulatif
# ---------------------------------------------------------------------------
def gen_reclamation():
    records = []
    identifiant = 28000
    for d in DATES:
        n_recla = random.randint(2, 14)
        for _ in range(n_recla):
            identifiant += 1
            categorie = random.choices(list(CATEGORIES_DELAI.keys()), weights=CATEGORIE_WEIGHTS, k=1)[0]
            objectif_jours = CATEGORIES_DELAI[categorie]
            # Délai réel de traitement : centré autour de l'objectif, avec du dépassement fréquent (réaliste)
            delai_reel = max(1, int(random.gauss(objectif_jours * 1.15, objectif_jours * 0.6)))
            deja_traitee = random.random() < 0.82  # certaines réclamations récentes sont encore "EN COURS"
            date_recla = d
            date_cloture = date_recla + timedelta(days=delai_reel) if deja_traitee else None

            records.append({
                "N Reclamation": identifiant,
                "Police N1": random.randint(20000000, 79999999),
                "Nom": fake.last_name().upper(),
                "Prenoms": fake.first_name().upper(),
                "Contact du client": fake.msisdn()[:9],
                "Libelle agence": random.choice(AGENCES),
                "Gestionnaire": random.choice(GESTIONNAIRES),
                "Date de reclamation": date_recla.strftime("%d/%m/%Y"),
                "Date de cloture": date_cloture.strftime("%d/%m/%Y") if date_cloture else "",
                "Etat": "CLOTURE" if date_cloture else "EN COURS",
                "Categorie_Delai": categorie,
                "Objectif_Jours": objectif_jours,
                "Motif de la reclamation": random.choice(MOTIFS_RECLA),
                "Mode de declaration": random.choice(CANAUX),
            })
    return pd.DataFrame(records)


df_recla = gen_reclamation()
recla_dir = BASE / "reclamation"
recla_dir.mkdir(parents=True, exist_ok=True)
recla_path = recla_dir / "NSIA_RECLAMATIONS_dernier_envoi.xlsx"
df_recla.to_excel(recla_path, index=False, sheet_name="Reclamation")
print(f"Réclamation : {len(df_recla)} lignes -> {recla_path.name}")


# ---------------------------------------------------------------------------
# 2) CALL CENTER — agrégat journalier unique
# ---------------------------------------------------------------------------
def gen_callcenter():
    records = []
    for d in DATES:
        appels_recus = random.randint(500, 750)
        appels_decroches = int(appels_recus * random.uniform(0.60, 0.78))
        appels_dans_delai = int(appels_decroches * random.uniform(0.38, 0.55))
        temps_moyen = round(random.uniform(2.8, 4.3), 2)
        objectif_emis = 900
        appels_emis = int(objectif_emis * random.uniform(0.95, 1.05))
        clients_joints = int(appels_emis * random.uniform(0.55, 0.66))
        appels_pour_rdv = int(clients_joints * random.uniform(0.18, 0.24))
        rdv_pris = int(appels_pour_rdv * random.uniform(0.45, 0.62))

        records.append({
            "Date": d.strftime("%d/%m/%Y"),
            "Appels decroches": appels_decroches,
            "Appels recus": appels_recus,
            "Appels recus dans le delai": appels_dans_delai,
            "Temps moyen de com": temps_moyen,
            "Appels emis": appels_emis,
            "Objectif appels emis": objectif_emis,
            "Clients joints": clients_joints,
            "RDV Pris": rdv_pris,
            "Appels pour RDV": appels_pour_rdv,
        })
    return pd.DataFrame(records)


df_cc = gen_callcenter()
cc_dir = BASE / "callcenter"
cc_dir.mkdir(parents=True, exist_ok=True)
cc_path = cc_dir / "NSIA_CALLCENTER_dernier_envoi.xlsx"
df_cc.to_excel(cc_path, index=False, sheet_name="CallCenter")
print(f"Call Center : {len(df_cc)} lignes -> {cc_path.name}")


# ---------------------------------------------------------------------------
# 3) MESSAGERIE — agrégat journalier unique (WhatsApp + Ecoute.ci)
# ---------------------------------------------------------------------------
def gen_messagerie():
    records = []
    for d in DATES:
        wa_recues = random.randint(0, 55)
        wa_cloturees = int(wa_recues * random.uniform(0.7, 1.0)) if wa_recues else 0
        eco_recues = random.randint(120, 260)
        eco_cloturees = int(eco_recues * random.uniform(0.65, 1.05))

        records.append({
            "Date": d.strftime("%d/%m/%Y"),
            "WhatsApp cloturees": wa_cloturees,
            "Obj Jour WhatsApp": 50,
            "WhatsApp recues": wa_recues,
            "Mail cloturees": eco_cloturees,
            "Obj Jour Mail": 50,
            "Mail recues": eco_recues,
        })
    return pd.DataFrame(records)


df_msg = gen_messagerie()
msg_dir = BASE / "messagerie"
msg_dir.mkdir(parents=True, exist_ok=True)
msg_path = msg_dir / "NSIA_MESSAGERIE_dernier_envoi.xlsx"
df_msg.to_excel(msg_path, index=False, sheet_name="Messagerie")
print(f"Messagerie : {len(df_msg)} lignes -> {msg_path.name}")

print(f"\nPériode : {DATES[0].strftime('%d/%m/%Y')} -> {DATES[-1].strftime('%d/%m/%Y')} ({len(DATES)} jours ouvrés)")
