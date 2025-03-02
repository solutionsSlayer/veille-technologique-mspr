import feedparser
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from .base_collector import BaseCollector
from concurrent.futures import ThreadPoolExecutor, as_completed

class RSSCollector(BaseCollector):
    """
    Collecteur de données à partir de flux RSS
    """
    
    def __init__(self, output_dir: str = "data/raw", cache_dir: str = "data/cache",
                 max_workers: int = 5, cache_expiry: int = 3600):
        """
        Initialise le collecteur RSS
        
        Args:
            output_dir (str): Répertoire de sortie pour les données collectées
            cache_dir (str): Répertoire pour le cache
            max_workers (int): Nombre maximum de threads simultanés
            cache_expiry (int): Durée de validité du cache en secondes (1h par défaut)
        """
        super().__init__(output_dir, cache_dir, max_workers, cache_expiry)
    
    def collect_from_feed(self, feed_info: Dict[str, str], use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Collecte les articles d'un flux RSS avec gestion du cache
        
        Args:
            feed_info (Dict[str, str]): Informations sur le flux RSS
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            List[Dict[str, Any]]: Liste des articles collectés
        """
        url = feed_info["url"]
        cache_path = self._get_cache_path(url)
        
        # Récupération des IDs déjà collectés pour éviter les doublons
        category = feed_info["category"]
        known_ids = self._get_known_ids(category)
        
        # Vérification du cache si activé
        cached_data = None
        if use_cache and self._is_cache_valid(cache_path):
            print(f"Utilisation du cache pour {feed_info['name']} ({url})")
            cached_data = self._read_cache(cache_path)
            
        try:
            print(f"Collecte du flux RSS: {feed_info['name']} ({url})")
            
            # Si on a des données en cache, on les utilise comme base et on complétera
            articles = []
            if cached_data:
                articles = cached_data
                
            # Chargement du flux RSS
            feed = feedparser.parse(url)
            new_articles = []
            
            for entry in feed.entries:
                # Utilisation du lien comme identifiant unique
                link = entry.get("link", "")
                if link and link in known_ids:
                    continue  # Article déjà collecté
                
                # Extraction du contenu sous différents formats possibles
                content = ""
                
                # Méthode 1: Via la clé 'content'
                if 'content' in entry:
                    for content_item in entry.content:
                        if 'value' in content_item:
                            content += content_item.value + "\n\n"
                
                # Méthode 2: Via la clé 'description'
                elif 'description' in entry:
                    content += entry.description + "\n\n"
                
                # Méthode 3: Via la clé 'summary_detail'
                elif 'summary_detail' in entry and 'value' in entry.summary_detail:
                    content += entry.summary_detail.value + "\n\n"
                
                # Méthode 4: Via la clé 'summary'
                elif 'summary' in entry:
                    content += entry.summary + "\n\n"
                
                # Si aucun contenu trouvé, utiliser le résumé comme contenu
                if not content.strip() and 'summary' in entry:
                    content = entry.summary
                
                article = {
                    "title": entry.get("title", ""),
                    "link": link,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "content": content,
                    "source_name": feed_info["name"],
                    "category": category,
                    "collected_at": datetime.now().isoformat()
                }
                
                # Ajouter seulement les nouveaux articles
                if link not in [a.get("link", "") for a in articles]:
                    new_articles.append(article)
            
            # Combinaison des anciens et nouveaux articles
            articles.extend(new_articles)
            
            # Mise en cache des résultats
            if use_cache and new_articles:
                self._write_cache(cache_path, articles)
            
            print(f"Articles collectés: {len(new_articles)} nouveaux, {len(articles)} total")
            return articles
        except Exception as e:
            print(f"Erreur lors de la collecte du flux {feed_info['name']}: {e}")
            return cached_data if cached_data else []
    
    def collect_from_feeds(self, feeds: List[Dict[str, str]], use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collecte les articles de plusieurs flux RSS en parallèle
        
        Args:
            feeds (List[Dict[str, str]]): Liste des flux RSS
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionnaire des articles collectés par catégorie
        """
        result = {}
        
        # Création de la liste des tâches à exécuter
        tasks = []
        for feed in feeds:
            tasks.append((feed, use_cache))
        
        # Exécution des tâches en parallèle
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumission des tâches
            future_to_feed = {executor.submit(self.collect_from_feed, feed, use_cache): feed 
                              for feed, use_cache in tasks}
            
            # Traitement des résultats
            for future in as_completed(future_to_feed):
                feed = future_to_feed[future]
                try:
                    articles = future.result()
                    
                    category = feed["category"]
                    if category not in result:
                        result[category] = []
                    
                    result[category].extend(articles)
                except Exception as e:
                    print(f"Exception lors de la collecte du flux {feed['name']}: {e}")
        
        return result

def collect_rss_feeds(feeds: List[Dict[str, str]], output_dir: str = "data/raw",
                    cache_dir: str = "data/cache", max_workers: int = 5,
                    use_cache: bool = True) -> None:
    """
    Fonction utilitaire pour collecter des données à partir de flux RSS
    
    Args:
        feeds (List[Dict[str, str]]): Liste des flux RSS
        output_dir (str): Répertoire de sortie
        cache_dir (str): Répertoire pour le cache
        max_workers (int): Nombre maximum de threads simultanés
        use_cache (bool): Utiliser le cache si disponible
    """
    collector = RSSCollector(output_dir, cache_dir, max_workers)
    data = collector.collect_from_feeds(feeds, use_cache)
    collector.save_collected_data(data) 