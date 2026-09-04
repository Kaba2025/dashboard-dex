import pandas as pd


def num(df, column):
    if column not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def total(df, column):
    return float(num(df, column).sum())


def ratio(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator * 100


def mean(df, column):
    if column not in df.columns:
        return None

    values = pd.to_numeric(df[column], errors="coerce").dropna()

    if values.empty:
        return None

    return float(values.mean())


def metric(name, value, unit="", objective=None, direction="higher"):
    return {
        "name": name,
        "value": value,
        "unit": unit,
        "objective": objective,
        "direction": direction,
    }


def last_valid(df, column):
    """Dernière valeur non nulle d'une colonne (utile pour les indicateurs
    d'enquête/baromètre qui ne varient pas ligne à ligne)."""
    if column not in df.columns:
        return None

    values = pd.to_numeric(df[column], errors="coerce").dropna()

    if values.empty:
        return None

    return float(values.iloc[-1])


# ============================================================
# DIGITAL
# ============================================================

def digital_kpis(df):

    digital = total(df, "Prestations Digital")
    prestations = total(df, "Total Prestations")

    return [
        metric(
            "Prestations digitales",
            digital,
            "prestations"
        ),

        metric(
            "Total prestations",
            prestations,
            "prestations"
        ),

        metric(
            "Part digitale",
            ratio(digital, prestations),
            "%"
        ),

        metric(
            "Contre-performance",
            total(df, "Contre Performance"),
            "CP",
            direction="lower"
        ),
    ]


# ============================================================
# PHYSIQUE
# ============================================================

def physique_kpis(df):

    clients = total(df, "Clients reçus")
    on_time = total(df, "Clients ON TIME")

    attendus_15 = total(
        df,
        "Nombre de clients attendus en moins de 15 minutes"
    )

    pris_15 = total(
        df,
        "Nombre de clients pris en charge en moins de 15 minutes"
    )

    return [

        metric(
            "Clients reçus",
            clients,
            "clients"
        ),

        metric(
            "Clients ON TIME",
            on_time,
            "clients"
        ),

        metric(
            "Taux ON TIME",
            ratio(on_time, clients),
            "%"
        ),

        metric(
            "Taux prise en charge < 15 min",
            ratio(pris_15, attendus_15),
            "%"
        ),

        metric(
            "Temps d'attente moyen",
            mean(df, "Temps d'attente"),
            "min",
            direction="lower"
        ),

        metric(
            "Temps de prise en charge moyen",
            mean(df, "Temps de prise en charge"),
            "min",
            direction="lower"
        ),

        metric(
            "Temps de présence en agence (moyen)",
            mean(df, "Temps de présence"),
            "min",
            objective=30,
            direction="lower"
        ),

        metric(
            "CP attente",
            total(df, "CP ATTENTE"),
            "CP",
            direction="lower"
        ),

        metric(
            "CP prise en charge",
            total(df, "CP PRISE EN CHARGE"),
            "CP",
            direction="lower"
        ),
    ]


# ============================================================
# SATISFACTION
# ============================================================

def satisfaction_kpis(df):

    recus = total(
        df,
        "Total clients reçus"
    )

    satisfaits = total(
        df,
        "Clients satisfaits"
    )

    return [

        metric(
            "Clients reçus",
            recus,
            "clients"
        ),

        metric(
            "Clients satisfaits",
            satisfaits,
            "clients"
        ),

        metric(
            "Taux de satisfaction",
            ratio(satisfaits, recus),
            "%"
        ),

        metric(
            "Recueil de satisfaction",
            total(df, "Recueil de satisfaction"),
            "réponses"
        ),

        metric(
            "Taux de recueil de satisfaction",
            ratio(total(df, "Recueil de satisfaction"), recus),
            "%",
            objective=80,
        ),

        metric(
            "Taux de satisfaction dernière enquête",
            mean(df, "Satisfaction dernière enquête"),
            "%",
            objective=75,
        ),

        metric(
            "Taux de satisfaction baromètre",
            mean(df, "Satisfaction baromètre"),
            "%",
            objective=75,
        ),

        metric(
            "CSAT annuelle enquête",
            last_valid(df, "CSAT annuelle enquête"),
            "%",
        ),

        metric(
            "Contre-performance",
            total(df, "Contre Performance"),
            "CP",
            direction="lower"
        ),
    ]


# ============================================================
# RECLAMATION
# ============================================================

def reclamation_kpis(df):

    mois_recues = total(
        df,
        "Réclamations MOIS reçues"
    )

    mois_traitees = total(
        df,
        "Réclamations MOIS traitées dans les délais"
    )

    an_recues = total(
        df,
        "Réclamations ANNÉE reçues"
    )

    an_traitees = total(
        df,
        "Réclamations ANNÉE traitées dans les délais"
    )

    commission_recues = total(
        df,
        "Réclamations COMMISSION reçues"
    )

    commission_traitees = total(
        df,
        "Réclamations COMMISSION traitées dans les délais"
    )

    base_echue_recues = total(
        df,
        "Réclamations MOIS reçues (base échue)"
    )

    base_echue_traitees = total(
        df,
        "Réclamations MOIS traitées dans les délais (base échue)"
    )

    commission_echue_recues = total(
        df,
        "Réclamations COMMISSION reçues (base échue)"
    )

    commission_echue_traitees = total(
        df,
        "Réclamations COMMISSION traitées dans les délais (base échue)"
    )

    return [

        metric(
            "Taux réclamations traitées dans le délai",
            ratio(mois_traitees, mois_recues),
            "%",
            objective=100,
        ),

        metric(
            "Taux réclamations traitées dans les délais (base échue)",
            ratio(base_echue_traitees, base_echue_recues),
            "%",
            objective=100,
        ),

        metric(
            "Taux réclamations \"Commissions\" traitées dans les délais",
            ratio(
                commission_traitees,
                commission_recues
            ),
            "%",
            objective=100,
        ),

        metric(
            "Taux réclamations \"Commissions\" traitées dans les délais (base échue)",
            ratio(
                commission_echue_traitees,
                commission_echue_recues
            ),
            "%",
            objective=100,
        ),

        metric(
            "Taux réclamations année traitées dans les délais",
            ratio(an_traitees, an_recues),
            "%",
            objective=100,
        ),

        metric(
            "CSAT annuelle enquête",
            last_valid(df, "CSAT annuelle enquête"),
            "%",
        ),

        metric(
            "Réclamations reçues",
            mois_recues,
            "réclamations"
        ),

        metric(
            "Réclamations traitées dans les délais",
            mois_traitees,
            "réclamations"
        ),
    ]


# ============================================================
# MESSAGERIE
# ============================================================

def messagerie_kpis(df):

    whatsapp_recus = total(
        df,
        "WhatsApp reçues"
    )

    whatsapp_clotures = total(
        df,
        "WhatsApp clôturées"
    )

    mails_recus = total(
        df,
        "Mail reçus"
    )

    mails_clotures = total(
        df,
        "Mail clôturés"
    )

    ecoute_recues = total(
        df,
        "Ecoute.ci reçues"
    )

    ecoute_clotures = total(
        df,
        "Ecoute.ci clôturées"
    )

    return [

        metric(
            "WhatsApp reçues",
            whatsapp_recus,
            "messages"
        ),

        metric(
            "WhatsApp clôturées",
            whatsapp_clotures,
            "messages"
        ),

        metric(
            "Taux clôture WhatsApp",
            ratio(
                whatsapp_clotures,
                whatsapp_recus
            ),
            "%",
            objective=100,
        ),

        metric(
            "Mails reçus",
            mails_recus,
            "mails"
        ),

        metric(
            "Mails clôturés",
            mails_clotures,
            "mails"
        ),

        metric(
            "Taux clôture Mail",
            ratio(
                mails_clotures,
                mails_recus
            ),
            "%",
            objective=100,
        ),

        metric(
            "Conversations Ecoute.ci reçues",
            ecoute_recues,
            "conversations"
        ),

        metric(
            "Conversations Ecoute.ci traitées",
            ecoute_clotures,
            "conversations"
        ),

        metric(
            "Taux de traitement Ecoute.ci",
            ratio(
                ecoute_clotures,
                ecoute_recues
            ),
            "%",
            objective=100,
        ),
    ]


# ============================================================
# CALL CENTER
# ============================================================

def callcenter_kpis(df):

    recus = total(
        df,
        "Appels reçus"
    )

    decroches = total(
        df,
        "Appels décrochés"
    )

    dans_delai = total(
        df,
        "Appels reçus dans le délai"
    )

    emis = total(
        df,
        "Appels émis"
    )

    objectif = total(
        df,
        "Objectif appels émis"
    )

    joints = total(
        df,
        "Clients joints"
    )

    rdv = total(
        df,
        "RDV pris"
    )

    appels_rdv = total(
        df,
        "Appels pour RDV"
    )

    return [

        metric(
            "Appels reçus",
            recus,
            "appels"
        ),

        metric(
            "Appels décrochés",
            decroches,
            "appels"
        ),

        metric(
            "Taux de décroché",
            ratio(decroches, recus),
            "%"
        ),

        metric(
            "Taux appels dans le délai",
            ratio(dans_delai, recus),
            "%"
        ),

        metric(
            "Appels émis",
            emis,
            "appels"
        ),

        metric(
            "Atteinte objectif appels émis",
            ratio(emis, objectif),
            "%"
        ),

        metric(
            "Taux de joignabilité",
            ratio(joints, emis),
            "%"
        ),

        metric(
            "Taux RDV",
            ratio(rdv, appels_rdv),
            "%"
        ),

        metric(
            "Temps moyen communication",
            mean(
                df,
                "Temps moyen de communication"
            ),
            "min",
            direction="lower"
        ),
    ]


# ============================================================
# DESHERENCE
# ============================================================

def desherence_kpis(df):

    # Les indicateurs "Base totale" / "Sur 2025" sont des photographies
    # (état du stock à date), pas des flux journaliers : on prend donc la
    # dernière valeur connue de la période plutôt qu'une somme.
    base_clients = last_valid(df, "Base totale clients") or 0
    base_trouves = last_valid(df, "Base totale clients trouvés liquidés") or 0

    base_2025_clients = last_valid(df, "Sur 2025 base clients") or 0
    base_2025_trouves = last_valid(df, "Sur 2025 clients trouvés liquidés") or 0

    appels_emis = total(df, "Appels émis désherence")
    appels_total = total(df, "Total appels désherence")
    clients_joints = total(df, "Clients joints désherence")

    return [

        metric(
            "Base totale — % clients trouvés (liquidés)",
            ratio(base_trouves, base_clients),
            "%"
        ),

        metric(
            "Base totale — Montant récupérable",
            last_valid(df, "Base totale montant FCFA"),
            "FCFA"
        ),

        metric(
            "Base totale — Montant trouvé",
            last_valid(df, "Base totale montant trouvé FCFA"),
            "FCFA"
        ),

        metric(
            "Sur 2025 — % clients trouvés (liquidés)",
            ratio(base_2025_trouves, base_2025_clients),
            "%"
        ),

        metric(
            "Sur 2025 — Montant récupérable",
            last_valid(df, "Sur 2025 montant FCFA"),
            "FCFA"
        ),

        metric(
            "Sur 2025 — Montant trouvé",
            last_valid(df, "Sur 2025 montant trouvé FCFA"),
            "FCFA"
        ),

        metric(
            "% Clients émis (appels)",
            ratio(appels_emis, appels_total),
            "%",
            objective=100,
        ),

        metric(
            "% Clients joints / appels émis",
            ratio(clients_joints, appels_emis),
            "%"
        ),

        metric(
            "Dossiers ouverts",
            total(df, "Dossiers ouverts"),
            "dossiers"
        ),

        metric(
            "Dossiers traités",
            total(df, "Dossiers traités"),
            "dossiers"
        ),

        metric(
            "Montant récupéré",
            total(df, "Montant récupéré (FCFA)"),
            "FCFA"
        ),

        metric(
            "CP appels entrants",
            total(
                df,
                "CP Appels Entrants"
            ),
            "CP",
            direction="lower"
        ),

        metric(
            "CP appels sortants",
            total(
                df,
                "CP Appels Sortants"
            ),
            "CP",
            direction="lower"
        ),
    ]


KPI_BUILDERS = {

    "DIGITAL": digital_kpis,

    "PHYSIQUE": physique_kpis,

    "RC & SATISFACTION": satisfaction_kpis,

    "MESSAGERIE": messagerie_kpis,

    "CALLCENTER": callcenter_kpis,

    "DESHERENCE": desherence_kpis,
}