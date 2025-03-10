# Collecteur de Données pour la Veille Technologique

Ce projet fournit un système efficace pour collecter, stocker et traiter des données provenant de diverses sources web telles que les sites web et les flux RSS.

## Fonctionnalités

- **Collecte parallèle** : Traitement concurrent pour une collecte plus rapide
- **Mise en cache intelligente** : Évite de télécharger à nouveau le même contenu
- **Dédoublonnage** : Empêche la collecte répétée des mêmes articles/contenus
- **Gestion automatique des erreurs** : Reprise en cas d'échec et journalisation
- **Options configurables** : Nombre de workers, utilisation du cache, etc.
- **Traitement de texte avancé** : Nettoyage HTML, extraction de liens, génération de mots-clés
- **Préparation pour vectorisation** : Normalisation du texte optimisée pour les embeddings

## Architecture

Le système utilise une architecture modulaire avec les composants suivants :

- `BaseCollector` : Classe de base avec fonctionnalités communes (cache, parallélisme)
- `WebCollector` : Collecte de données depuis des sites web
- `RSSCollector` : Collecte d'articles depuis des flux RSS
- `TextProcessor` : Traitement et préparation des textes pour l'analyse

### Structure de répertoires

```
data/
  ├── raw/                  # Données collectées brutes
  │   ├── web_*.json        # Données des pages web
  │   └── rss_*.json        # Données des flux RSS
  │
  ├── processed/            # Données après traitement
  │   ├── processed_*.json  # Fichiers individuels traités
  │   ├── all_processed_data.json  # Données combinées (JSON)
  │   └── all_processed_data.csv   # Données combinées (CSV)
  │
  └── cache/                # Cache de collecte

src/
  ├── collectors/           # Modules de collecte
  │   ├── base_collector.py
  │   ├── web_collector.py
  │   └── rss_collector.py
  │
  ├── processors/           # Modules de traitement
  │   └── text_processor.py # Processeur de texte
  │
  ├── run_collectors.py     # Script d'exécution de la collecte
  └── run_processors.py     # Script d'exécution du traitement
```

## Installation

1. Clonez le dépôt
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Configuration des sources

Les sources de données sont définies dans le fichier `sources.json` à la racine du projet :

```json
{
  "rss_feeds": [
    {
      "name": "Nom du flux",
      "url": "https://example.com/rss",
      "category": "catégorie"
    }
  ],
  "websites": [
    {
      "name": "Nom du site",
      "url": "https://example.com",
      "selector": "div.content",
      "category": "catégorie"
    }
  ]
}
```

### Collecte des données

Pour exécuter la collecte de données :

```bash
python src/run_collectors.py
```

Options disponibles :

- `--no-cache` : Désactive l'utilisation du cache
- `--workers N` : Définit le nombre de workers simultanés (par défaut: 5)
- `--output-dir DIR` : Spécifie le répertoire de sortie pour les données collectées
- `--cache-dir DIR` : Spécifie le répertoire pour le cache
- `--rss-only` : Collecte uniquement les flux RSS
- `--web-only` : Collecte uniquement les sites web

Exemple :
```bash
python src/run_collectors.py --workers 10 --no-cache
```

### Traitement des données

Pour traiter les données collectées et les préparer pour l'analyse :

```bash
python src/run_processors.py
```

Options disponibles :

- `--input-dir DIR` : Répertoire des données brutes (défaut: data/raw)
- `--output-dir DIR` : Répertoire de sortie (défaut: data/processed)
- `--sequential` : Utiliser le traitement séquentiel au lieu du parallèle
- `--workers N` : Nombre de workers pour le traitement parallèle (défaut: 4)
- `--no-csv` : Ne pas sauvegarder les données au format CSV

Exemple :
```bash
python src/run_processors.py --workers 8 --input-dir custom/input --output-dir custom/output
```

## Structure des données

### Données brutes

Les données collectées sont stockées au format JSON dans le répertoire `data/raw` avec la structure suivante :

- Fichiers RSS : `rss_[catégorie]_[timestamp].json`
- Fichiers Web : `web_[catégorie]_[timestamp].json`

### Données traitées

Les données traitées contiennent les champs suivants :

| Champ | Description |
|-------|-------------|
| `title` | Titre original |
| `cleaned_title` | Titre nettoyé |
| `content` | Contenu HTML original |
| `cleaned_content` | Texte extrait sans HTML |
| `normalized_text` | Texte préparé pour vectorisation |
| `all_links` | Tous les liens extraits |
| `keywords` | Mots-clés extraits automatiquement |
| `collected_at` | Date/heure de collecte |
| `processed_at` | Date/heure de traitement |
| `source_name` | Nom de la source |
| `category` | Catégorie (post-quantum, cybersecurity, ...) |

## Optimisations

### Collecte de données

- **Parallélisme** : Utilisation de `ThreadPoolExecutor` pour exécuter les tâches en parallèle
- **Cache** : Mise en cache des résultats avec expiration configurable
- **Incrémental** : Ne collecte que les nouveaux articles dans les flux RSS
- **Efficacité mémoire** : Traitement optimisé pour limiter l'utilisation de la mémoire

### Traitement de texte

- **Nettoyage HTML** : Utilisation de BeautifulSoup pour extraire proprement le texte
- **Extraction de liens** : Préservation des liens pour la construction de graphes d'information
- **Traitement parallèle** : Utilisation de ProcessPoolExecutor pour le traitement multi-fichiers
- **Formats multiples** : Sauvegarde en JSON et CSV pour diverses utilisations

## Synthèse du pipeline complet

Le système implémente un pipeline de traitement complet pour la veille technologique :

1. **Collecte des données brutes** : Les collecteurs WebCollector et RSSCollector récupèrent le contenu HTML et les métadonnées.
2. **Prétraitement des données** : Le TextProcessor nettoie le HTML, extrait les informations structurées, normalise le texte.
3. **Préparation pour l'analyse** : Génération de texte normalisé, optimisé pour la vectorisation ultérieure.
4. **Exportation structurée** : Les données traitées sont disponibles en JSON pour l'API et CSV pour l'analyse.

L'ensemble du système est conçu selon les principes SOLID avec :
- Une architecture modulaire facilitant l'extension
- Une séparation claire des responsabilités (collecte vs traitement)
- Des interfaces de ligne de commande flexibles et bien documentées
- Des optimisations de performance pour le traitement de grands volumes de données

Ce pipeline constitue la première partie d'un système de veille technologique, préparant les données pour leur vectorisation et exploitation ultérieure dans un moteur de recherche sémantique.

Pour plus de détails sur les optimisations et le traitement, consultez les documents :
- [OPTIMIZATIONS.md](OPTIMIZATIONS.md) - Détails des optimisations de performance
- [PROCESSING.md](PROCESSING.md) - Documentation détaillée du système de traitement de texte
