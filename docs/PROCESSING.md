# Traitement des Données Textuelles - Documentation

Ce document explique en détail le système de traitement de texte mis en place pour préparer les données collectées à l'analyse et à la vectorisation.

## Aperçu du Pipeline de Traitement

1. **Collecte de données brutes** (WebCollector, RSSCollector)
2. **Nettoyage et prétraitement des textes** (TextProcessor)
3. **Extraction d'informations structurées** (liens, mots-clés)
4. **Préparation pour la vectorisation** (normalisation)
5. **Sauvegarde dans des formats interopérables** (JSON, CSV)

## Architecture du Système

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
      └── ...

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

## Fonctionnalités du TextProcessor

### Nettoyage HTML

Le système utilise BeautifulSoup pour nettoyer efficacement le HTML:

```python
def _clean_html(self, html_content: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Nettoie le HTML et extrait les liens
    """
    # Utilisation de BeautifulSoup pour un nettoyage robuste
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraction des liens
    links = []
    for a_tag in soup.find_all('a', href=True):
        link_text = a_tag.get_text().strip()
        href = a_tag['href']
        links.append({"text": link_text, "url": href})
    
    # Extraction du texte sans balises
    text = soup.get_text(separator=' ', strip=True)
    
    return text, links
```

### Extraction de Liens

Tous les liens présents dans le contenu HTML sont identifiés et conservés avec leur texte d'ancrage, permettant:
- La préservation des références originales
- Le suivi des sources primaires
- La construction potentielle d'un graphe d'information
- La détection des relations entre documents

### Normalisation du Texte

Pour préparer le texte à la vectorisation, plusieurs étapes de normalisation sont appliquées:

```python
def _clean_text(self, text: str) -> str:
    """
    Nettoie un texte (sans balises HTML)
    """
    # Supprimer les URL
    text = re.sub(r'https?://\S+', '', text)
    
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les caractères spéciaux
    text = re.sub(r'[^\w\s.,;:!?\(\)\[\]\'\"«»]', '', text)
    
    return text.strip()
```

### Extraction de Mots-Clés

Une méthode simple d'extraction de mots-clés basée sur la fréquence est implémentée:

1. Tokenisation du texte
2. Filtrage des mots courts (< 3 caractères) et des mots vides (stop words)
3. Comptage des occurrences
4. Tri par fréquence décroissante
5. Sélection des N mots les plus fréquents

Ces mots-clés peuvent servir à:
- Indexer rapidement le contenu
- Filtrer ou classifier les documents
- Enrichir les métadonnées pour la recherche

## Structure des Données Traitées

Chaque document traité contient les champs suivants:

| Champ | Description |
|-------|-------------|
| `title` | Titre original |
| `cleaned_title` | Titre nettoyé |
| `content` | Contenu HTML original |
| `cleaned_content` | Texte extrait sans HTML |
| `normalized_text` | Texte préparé pour vectorisation |
| `summary` | Résumé original (si disponible) |
| `cleaned_summary` | Résumé nettoyé |
| `all_links` | Tous les liens extraits |
| `content_links` | Liens du contenu principal |
| `summary_links` | Liens du résumé |
| `keywords` | Mots-clés extraits automatiquement |
| `collected_at` | Date/heure de collecte |
| `processed_at` | Date/heure de traitement |
| `source_name` | Nom de la source |
| `category` | Catégorie (post-quantum, cybersecurity, ...) |

## Utilisation du Module de Traitement

### Via la Ligne de Commande

```bash
python src/run_processors.py [options]
```

Options disponibles:
- `--input-dir DIR` : Répertoire des données brutes (défaut: data/raw)
- `--output-dir DIR` : Répertoire de sortie (défaut: data/processed)
- `--sequential` : Utiliser le traitement séquentiel
- `--workers N` : Nombre de workers pour le traitement parallèle (défaut: 4)
- `--no-csv` : Ne pas générer de fichier CSV

### Programmatiquement

```python
from src.processors.text_processor import process_all_data

# Traitement avec paramètres personnalisés
stats = process_all_data(
    input_dir="data/raw",
    output_dir="data/processed",
    parallel=True,
    max_workers=4
)

# Statistiques de traitement
print(f"Articles traités: {stats['total_articles']}")
print(f"  - Articles Web: {stats['web_articles']}")
print(f"  - Articles RSS: {stats['rss_articles']}")
```

## Prochaines Étapes & Améliorations Possibles

1. **Extraction d'entités nommées**: Identification des personnes, organisations, lieux, etc.
2. **Analyse de sentiment**: Évaluation de la tonalité et du sentiment des textes
3. **Classification automatique**: Catégorisation du contenu par thématique
4. **Détection de langues**: Identification et traitement spécifique selon la langue
5. **Résumé automatique**: Génération de résumés pour les contenus longs
6. **Extraction de relations**: Identification des relations entre entités
7. **Gestion des doublons sémantiques**: Détection de contenus similaires

---

Ce système de traitement de texte fournit une base solide pour la préparation des données textuelles avant leur vectorisation et leur exploitation dans des applications d'IA, de recherche sémantique ou d'analyse textuelle. 