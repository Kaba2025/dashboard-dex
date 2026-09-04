"""
Génère les données fictives pour le pipeline complet :

1) UN SEUL fichier "satisfaction" partagé par toutes les agences depuis
   janvier (chaque agence y ajoute ses lignes, distinguées par "Libelle
   agence"). C'est la source des réponses à l'enquête de satisfaction.

2) DES fichiers "réception physique", UN PAR AGENCE (même format pour
   toutes), qui donnent le nombre RÉEL de clients reçus par jour (avec ou
   sans réponse à l'enquête) + le nom du gestionnaire. Vallon a un format
   différent, avec en plus les délais (attente, transaction) et l'usage de
   l'appli mobile.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

random.seed(11)
fake = Faker("fr_FR")
Faker.seed(11)

BASE = Path("/home/claude/nsia_dashboard/data")
SAT_DIR = BASE / "satisfaction"
REC_DIR = BASE / "reception"
SAT_DIR.mkdir(parents=True, exist_ok=True)
REC_DIR.mkdir(parents=True, exist_ok=True)

AGENCES = [
    "NSIA VIE ASSURANCE VALLON",
    "NSIA VIE ASSURANCE KOUMASSI",
    "NSIA VIE ASSURANCE MAN",
    "NSIA VIE ASSURANCE BOUAKE",
    "NSIA VIE ASSURANCE DALOA",
    "NSIA VIE ASSURANCE KORHOGO",
    "NSIA VIE ASSURANCE SAN PEDRO",
    "NSIA VIE ASSURANCE YAMOUSSOUKRO",
]

VOLUME_BASE = {  # (min, max) clients reçus par jour -- footfall réel
    "NSIA VIE ASSURANCE VALLON": (90, 165),
    "NSIA VIE ASSURANCE KOUMASSI": (3, 11),
    "NSIA VIE ASSURANCE MAN": (4, 13),
    "NSIA VIE ASSURANCE BOUAKE": (18, 45),
    "NSIA VIE ASSURANCE DALOA": (10, 26),
    "NSIA VIE ASSURANCE KORHOGO": (5, 14),
    "NSIA VIE ASSURANCE SAN PEDRO": (7, 19),
    "NSIA VIE ASSURANCE YAMOUSSOUKRO": (16, 40),
}

GESTIONNAIRE = {
    "NSIA VIE ASSURANCE VALLON": "TABLETTE CENTRALE",
    "NSIA VIE ASSURANCE KOUMASSI": "KOFFI ARMAND",
    "NSIA VIE ASSURANCE MAN": "BAMBA FATOU",
    "NSIA VIE ASSURANCE BOUAKE": "DOUA MARINA",
    "NSIA VIE ASSURANCE DALOA": "GOUEKOU",
    "NSIA VIE ASSURANCE KORHOGO": "TRAORE ISSA",
    "NSIA VIE ASSURANCE SAN PEDRO": "AGENT SAN PEDRO",
    "NSIA VIE ASSURANCE YAMOUSSOUKRO": "SIALLOU",
}

MOTIFS_VISITE = ["Reclamations", "Rachat Partiel", "Demande d'informations", "Retrait de reglement",
                  "Rachat Total", "Resiliation", "Declaration sinistre", "Modification sur contrat"]
STATUTS_TICKET = ["Cloture", "Cloture", "Cloture", "En cours"]

SATISFACTION_CHOICES = ["Tres Satisfait", "Satisfait", "Peu Satisfait", "Insatisfait"]
MOTIFS_AUTRES = ["", "", "", "", "Régularisation de mes paiements", "Ajout de dossier de sinistre",
                  "Mise à jour des bénéficiaires", "Changement de coordonnées"]
COMMENTAIRES_INSATISFAIT = [
    "Délai d'attente trop long avant la prise en charge.",
    "Règlement indisponible au moment de mon passage en caisse.",
    "Manque d'information claire sur mon contrat.",
]


def business_days(start, end):
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


DATES = business_days(datetime(2026, 1, 1), datetime(2026, 8, 13))
MOIS_FR = {1: "JANVIER", 2: "FEVRIER", 3: "MARS", 4: "AVRIL", 5: "MAI", 6: "JUIN", 7: "JUILLET", 8: "AOUT"}


def satisfaction_weights_for(d):
    progression = (d - DATES[0]).days / max((DATES[-1] - DATES[0]).days, 1)
    tres_satisfait = min(max(0.68 + 0.16 * progression + random.uniform(-0.05, 0.05), 0.55), 0.92)
    reste = 1 - tres_satisfait
    return [tres_satisfait, reste * 0.55, reste * 0.30, reste * 0.15]


# ---------------------------------------------------------------------------
# 1) Fichier satisfaction unique (toutes agences confondues)
#
# Un sous-ensemble de "clients récurrents" est pré-créé par agence : ils
# reviennent plusieurs fois sur la période (comme de vrais assurés), ce qui
# permet à la Fiche Client de montrer un historique et une évolution dans
# le temps. Le reste des lignes reste des clients "one-shot" (une seule
# interaction), comme dans les données précédentes.
# ---------------------------------------------------------------------------
CLIENTS_RECURRENTS = {
    agence: [{"nom": fake.name(), "contact": fake.phone_number(), "police": f"POL-{random.randint(100000,999999)}",
              "premiere_interaction": random.choice(DATES[:40])}
             for _ in range(60)]
    for agence in AGENCES
}

identifiant_counter = 500000
all_satisfaction_records = []
footfall_par_agence_jour = {}  # (agence, date) -> total clients reçus (pour cohérence recueil)

for agence in AGENCES:
    vmin, vmax = VOLUME_BASE[agence]
    recurrents = CLIENTS_RECURRENTS[agence]
    for d in DATES:
        total_recus = random.randint(vmin, vmax)
        footfall_par_agence_jour[(agence, d)] = total_recus
        taux_recueil_jour = random.uniform(0.78, 0.97)
        n_reponses = max(1, round(total_recus * taux_recueil_jour))
        weights = satisfaction_weights_for(d)

        for _ in range(n_reponses):
            identifiant_counter += 1
            satisfaction = random.choices(SATISFACTION_CHOICES, weights=weights, k=1)[0]
            reclamation = "OUI" if satisfaction in ("Peu Satisfait", "Insatisfait") and random.random() < 0.6 else "NON"
            commentaire = random.choice(COMMENTAIRES_INSATISFAIT) if satisfaction in ("Peu Satisfait", "Insatisfait") else ""
            heure = timedelta(hours=random.randint(8, 16), minutes=random.randint(0, 59))

            est_recurrent = random.random() < 0.30 and d >= recurrents[0]["premiere_interaction"]
            if est_recurrent:
                client = random.choice(recurrents)
                if d < client["premiere_interaction"]:
                    continue
                nom, contact = client["nom"], client["contact"]
            else:
                nom, contact = fake.name(), fake.phone_number()

            all_satisfaction_records.append({
                "Identifiant": identifiant_counter,
                "Nom client": nom,
                "Contact client": contact,
                "Addresse mail": "xxx@xxx.com",
                "Autres": random.choice(MOTIFS_AUTRES),
                "Libelle agence": agence,
                "Information sur contrat": random.choices(["OUI", "NON"], weights=[0.3, 0.7])[0],
                "Disponibilite du reglement": random.choices(["OUI", "NON"], weights=[0.25, 0.75])[0],
                "Demande de prestation": random.choices(["OUI", "NON"], weights=[0.35, 0.65])[0],
                "Reclamation": reclamation,
                "Satisfaction": satisfaction,
                "Commentaire": commentaire,
                "Provenance": GESTIONNAIRE[agence],
                "DATE DE CREATION": (d + heure).strftime("%d/%m/%Y %H:%M"),
            })

df_satisfaction = pd.DataFrame(all_satisfaction_records)
sat_path = SAT_DIR / "NSIA_SATISFACTION_TOUTES_AGENCES_dernier_envoi.xlsx"
df_satisfaction.to_excel(sat_path, index=False, sheet_name="Satisfaction")
print(f"Satisfaction (1 fichier, toutes agences) : {len(df_satisfaction)} lignes -> {sat_path.name}")

# ---------------------------------------------------------------------------
# 2) Fichiers réception physique, un par agence (Vallon = format spécial)
# ---------------------------------------------------------------------------
for agence in AGENCES:
    agence_dir = REC_DIR / agence.replace(" ", "_")
    agence_dir.mkdir(exist_ok=True)
    is_vallon = "VALLON" in agence
    gestionnaire = GESTIONNAIRE[agence]

    rows = []
    for d in DATES:
        total_recus = footfall_par_agence_jour[(agence, d)]
        for i in range(total_recus):
            heure = timedelta(hours=random.randint(8, 16), minutes=random.randint(0, 59))
            dt = d + heure
            if is_vallon:
                attente = random.randint(3, 55)
                transaction = random.randint(2, 20)
                rows.append({
                    "Service": random.choice(["Demande d'informations", "Retrait de reglement", "Sinistre deces", "Demande de prestations"]),
                    "Motif": random.choice(["Rachat partiel", "Rachat total", "Information sur contrat", "Complément de dossiers", "Terme", "Avance"]),
                    "Numero du ticket": i + 1,
                    "Contact": fake.msisdn()[:9],
                    "Observation": "",
                    "Email": random.choices(["OUI", "NON"], weights=[0.4, 0.6])[0],
                    "Has App Mobile": random.choices(["OUI", "NON"], weights=[0.45, 0.55])[0],
                    "Temps d'attente": attente,
                    "Temps de transaction": transaction,
                    "Date": dt.strftime("%d/%m/%Y %H:%M"),
                })
            else:
                rows.append({
                    "Date reception": d.strftime("%d/%m/%Y"),
                    "Nom et Prenoms": fake.name().upper(),
                    "Numeros police": random.randint(20000000, 79999999),
                    "Contact": fake.msisdn()[:10],
                    "Gestionnaire": gestionnaire,
                    "Motifs visite": random.choice(MOTIFS_VISITE),
                    "Statut Ticket": random.choice(STATUTS_TICKET),
                    "Rec_Mois": MOIS_FR[d.month],
                })

    df_rec = pd.DataFrame(rows)
    fpath = agence_dir / "reception_dernier_envoi.xlsx"
    df_rec.to_excel(fpath, index=False, sheet_name="Reception")
    print(f"Réception {agence} ({'VALLON' if is_vallon else 'standard'}) : {len(df_rec)} lignes -> {fpath.relative_to(BASE)}")

print(f"\nPériode : {DATES[0].strftime('%d/%m/%Y')} -> {DATES[-1].strftime('%d/%m/%Y')} ({len(DATES)} jours ouvrés)")
