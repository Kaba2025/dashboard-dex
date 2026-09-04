"""
Connexion à Qwen2.5 via Ollama en local, avec function calling : le modèle
peut appeler les outils définis dans chatbot_tools.py pour aller chercher
exactement les données dont il a besoin (KPI, classement, réception,
recherche client, tendance, comparaison...), plutôt que de recevoir un
résumé figé. Il peut aussi répondre directement (salutations, questions
générales) sans appeler d'outil.

Conçu pour être robuste (présentation devant la direction) :
- jamais de crash qui remonte à l'utilisateur -> toujours un message clair
- boucle d'outils bornée (pas de boucle infinie)
- chaque appel d'outil est protégé individuellement
"""
import json

import requests

from chatbot_tools import executer_tool

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MODEL_NAME = "qwen2.5:7b-instruct"
MAX_TOOL_ROUNDS = 5
TIMEOUT_SECONDS = 120

SYSTEM_PROMPT = """Tu es l'assistant analyste du tableau de bord de satisfaction client de NSIA Vie Assurance.

RÈGLES :
- Réponds toujours en français, de façon claire, professionnelle et concise (c'est utilisé en présentation devant la direction).
- Pour toute question qui concerne le tableau de bord (KPI, agences, réclamations, tendances, clients, réception, délais...), utilise les outils disponibles pour aller chercher les vrais chiffres. Ne jamais inventer un chiffre : si tu n'as pas l'info via les outils, dis-le.
- Tu peux combiner plusieurs appels d'outils pour répondre à une question complexe (ex : comparer deux agences = appeler l'outil deux fois, ou classement_agences une fois).
- Si la question nécessite un calcul ou un raisonnement à partir des chiffres obtenus (moyenne, écart, meilleur/pire, tendance...), fais ce calcul toi-même à partir des résultats des outils et donne la réponse finale claire.
- Pour les salutations, remerciements, ou questions qui n'ont rien à voir avec le tableau de bord, réponds normalement et brièvement, sans utiliser d'outil -- reste utile et poli, ne refuse jamais de répondre.
- Si une question est ambiguë sur la période ou l'agence, utilise par défaut le contexte actuellement affiché (donné ci-dessous), sauf si la question précise autre chose.
- N'expose jamais de détails techniques (noms de fonctions, JSON brut) dans ta réponse finale : donne une réponse en langage naturel.

CONTEXTE ACTUEL DU TABLEAU DE BORD (ce que l'utilisateur regarde en ce moment) :
{contexte}
"""


def ollama_disponible() -> bool:
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=1.5)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _appel_ollama(messages: list, tools: list) -> dict:
    r = requests.post(
        OLLAMA_CHAT_URL,
        json={"model": MODEL_NAME, "messages": messages, "tools": tools, "stream": False},
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return r.json()


def demander_assistant(question: str, contexte_kpi: str, historique: list[dict],
                        tool_specs: list, tool_functions: dict) -> str:
    """Boucle question -> (éventuels appels d'outils) -> réponse finale.
    Ne lève jamais d'exception : renvoie toujours un message affichable."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(contexte=contexte_kpi)}]
    for m in historique[-8:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": question})

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            data = _appel_ollama(messages, tool_specs)
            message = data.get("message", {})
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                contenu = (message.get("content") or "").strip()
                return contenu or "Je n'ai pas de réponse à proposer pour cette question, peux-tu la reformuler ?"

            messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                nom = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                resultat_json = executer_tool(nom, args, tool_functions)
                messages.append({"role": "tool", "content": resultat_json})

        return ("Je n'arrive pas à conclure sur cette question après plusieurs recherches dans les données "
                "-- essaie de la reformuler plus simplement, ou précise la période/l'agence.")

    except requests.exceptions.ConnectionError:
        return (f"⚠️ Impossible de joindre Ollama en local. Lance `ollama run {MODEL_NAME}` "
                "dans un terminal sur ce PC (garde-le ouvert), puis réessaie.")
    except requests.exceptions.Timeout:
        return "⚠️ Le modèle met trop de temps à répondre (timeout). Réessaie, ou pose une question plus simple."
    except requests.exceptions.HTTPError as e:
        return f"⚠️ Erreur Ollama : {e}. Vérifie que le modèle « {MODEL_NAME} » est bien installé (`ollama list`)."
    except Exception as e:
        return f"⚠️ Erreur inattendue en contactant l'assistant : {e}"
