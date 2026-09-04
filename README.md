# Dashboard Expérience Client — NSIA Vie Assurance

Tableau de bord Streamlit pour la Direction de l'Expérience Client (DEX) de NSIA Vie Assurance CI : Digital, Physique, Satisfaction, Réclamations, Messagerie, Call Center, Déshérence, et une vue Point Global.

## Installation locale

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Au premier lancement, importez la base DEX (fichier Excel) depuis le menu de gauche pour activer les onglets.

## Déploiement (Streamlit Community Cloud)

1. Poussez ce dépôt sur GitHub (voir les étapes fournies séparément).
2. Allez sur https://share.streamlit.io et connectez-vous avec votre compte GitHub.
3. Cliquez sur **"New app"**, sélectionnez ce dépôt, la branche `main`, et le fichier principal `app.py`.
4. Cliquez sur **Deploy**. Streamlit installe automatiquement `requirements.txt` et démarre l'app.
5. Une fois déployée, vous obtenez un lien du type `https://<nom-app>.streamlit.app` à partager.

Le thème (couleurs, mode sombre) est déjà configuré dans `.streamlit/config.toml` et sera repris automatiquement en ligne.

## Structure du dépôt

```
app.py                  # point d'entrée : navigation, routage vers les onglets
src/                     # logique métier (ingestion, KPI, thème, onglets)
assets/                  # logos NSIA
.streamlit/config.toml   # thème Streamlit
requirements.txt
data/                    # créé automatiquement à l'import d'une base (non versionné)
```

## Point d'attention — Assistant IA (Ollama)

`src/chatbot.py` et `src/chatbot_tools.py` existent dans le code mais **ne sont pas branchés** dans `app.py` (aucun import, aucun onglet ne les utilise) : ils n'ont donc aucun impact sur le déploiement. Ils dépendent d'un serveur Ollama local (`http://localhost:11434`) qui n'existe pas sur Streamlit Cloud — si un jour vous voulez les activer en ligne, il faudra les remplacer par un appel à une API cloud (ex. API Anthropic/OpenAI) plutôt que Ollama en local.

## Données

Chaque session attend l'import manuel de la base DEX (6 feuilles : DIGITAL, MESSAGERIE, RC & SATISFACTION, PHYSIQUE, CALLCENTER, DESHERENCE). Rien n'est pré-chargé dans le dépôt — aucune donnée client n'est donc exposée publiquement sur GitHub.
