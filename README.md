# Assistant IA responsable et conforme au RGPD

Application web d'assistance par IA pour les étudiants et le personnel d'un établissement, conçue autour de la protection des données personnelles (RGPD) et de la supervision humaine. Projet du module **Éthique et Droit du Numérique** (ENSA Béni Mellal, filière Intelligence Artificielle et Cybersécurité, 2025-2026).

**Réalisé par :** Sabrine Ouarchane et Salwa Hamdaoui

## Fonctionnalités

- Inscription et connexion (mots de passe hachés, jamais stockés en clair)
- Acceptation obligatoire des conditions d'utilisation
- Chat avec un modèle d'IA (`llama-3.3-70b-versatile` via l'API Groq) avec historique de la conversation
- **Filtre RGPD** : blocage de la saisie de données personnelles (e-mail, téléphone, CIN, mot de passe, longs numéros), y compris certaines tentatives de contournement simples
- **Mode dégradé** : réponses de secours si le service IA est indisponible
- Historique des échanges par utilisateur, avec suppression d'une discussion (droit à l'effacement)
- Page de profil (modification des informations)
- Espace administrateur qui n'affiche que des métadonnées (jamais le contenu des messages)

## Technologies

Python, Flask, SQLite, HTML/CSS (templates Jinja2), API Groq, python-dotenv.

## Structure

```
├── app.py            # routes Flask et appel à l'IA
├── database.py       # base SQLite (utilisateurs, historique)
├── rgpd.py           # détection des données personnelles
├── degrade.py        # réponses de secours
├── templates/        # pages HTML
├── requirements.txt
└── .env.example      # modèle du fichier de configuration
```

## Installation

```bash
git clone https://github.com/sabrine-ouarchane/NOM-DU-DEPOT.git
cd NOM-DU-DEPOT
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copie `.env.example` en `.env` et remplis :

- `GROQ_API_KEY` : ta clé sur [console.groq.com](https://console.groq.com)
- `SECRET_KEY` : une longue chaîne aléatoire (par exemple `python -c "import secrets; print(secrets.token_hex(32))"`)

## Lancer

```bash
python app.py
```

Puis ouvre l'adresse affichée dans le terminal (en général `http://127.0.0.1:5000`). La base `donnees_locales.db` est créée automatiquement au premier lancement.

## Cadre juridique et éthique

L'analyse complète (base légale, droits des personnes, AIPD, gouvernance, matrice des risques, politique d'usage) se trouve dans le rapport du projet.

*À COMPLÉTER : ajoute le rapport dans un dossier `docs/` (avec l'accord de ta coéquipière) et le lien ici.*

## Limites

Prototype pédagogique : il n'est pas destiné à un déploiement en production.

*À COMPLÉTER : captures d'écran du projet (page de chat, filtre RGPD, historique) dans un dossier `images/`.*
