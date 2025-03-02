import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

class BaseCollector:
    """
    Classe de base pour les collecteurs de données
    """
    
    def __init__(self, output_dir: str = "data/raw", cache_dir: str = "data/cache", 
                 max_workers: int = 5, cache_expiry: int = 3600):
        """
        Initialise le collecteur de base
        
        Args:
            output_dir (str): Répertoire de sortie pour les données collectées
            cache_dir (str): Répertoire pour le cache
            max_workers (int): Nombre maximum de threads simultanés
            cache_expiry (int): Durée de validité du cache en secondes (1h par défaut)
        """
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        self.cache_expiry = cache_expiry
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Crée les répertoires nécessaires s'ils n'existent pas"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, url: str) -> str:
        """
        Obtient le chemin du fichier de cache pour une URL
        
        Args:
            url (str): URL de la source
            
        Returns:
            str: Chemin du fichier de cache
        """
        # Création d'un nom de fichier sécurisé basé sur l'URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """
        Vérifie si le cache est valide (existe et n'est pas expiré)
        
        Args:
            cache_path (str): Chemin du fichier de cache
            
        Returns:
            bool: True si le cache est valide, False sinon
        """
        if not os.path.exists(cache_path):
            return False
            
        # Vérifie si le cache est expiré
        file_age = time.time() - os.path.getmtime(cache_path)
        return file_age < self.cache_expiry
    
    def _read_cache(self, cache_path: str) -> Optional[Dict]:
        """
        Lit les données du cache
        
        Args:
            cache_path (str): Chemin du fichier de cache
            
        Returns:
            Optional[Dict]: Données du cache ou None en cas d'erreur
        """
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors de la lecture du cache: {e}")
            return None
    
    def _write_cache(self, cache_path: str, data: Dict):
        """
        Écrit les données dans le cache
        
        Args:
            cache_path (str): Chemin du fichier de cache
            data (Dict): Données à mettre en cache
        """
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de l'écriture du cache: {e}")
    
    def save_collected_data(self, data: Dict[str, List[Dict[str, Any]]]):
        """
        Sauvegarde les données collectées
        
        Args:
            data (Dict[str, List[Dict[str, Any]]]): Données collectées par catégorie
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        total_items = 0
        for category, items in data.items():
            if not items:
                continue
                
            # Création d'un nom de fichier unique pour cette catégorie et ce collector
            collector_type = self.__class__.__name__.lower().replace("collector", "")
            filename = f"{collector_type}_{category}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            
            items_count = len(items)
            total_items += items_count
            print(f"Données sauvegardées: {filepath} ({items_count} éléments)")
        
        print(f"Total des éléments sauvegardés: {total_items}")
        
    def _get_known_ids(self, category: str) -> Set[str]:
        """
        Récupère les ID des éléments déjà collectés pour éviter les doublons
        
        Args:
            category (str): Catégorie des données
            
        Returns:
            Set[str]: Ensemble des ID connus
        """
        known_ids = set()
        
        # Recherche tous les fichiers de cette catégorie
        collector_type = self.__class__.__name__.lower().replace("collector", "")
        pattern = f"{collector_type}_{category}_"
        
        try:
            for filename in os.listdir(self.output_dir):
                if pattern in filename and filename.endswith('.json'):
                    filepath = os.path.join(self.output_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            items = json.load(f)
                            for item in items:
                                if 'link' in item:
                                    known_ids.add(item['link'])
                                elif 'url' in item:
                                    known_ids.add(item['url'])
                    except Exception as e:
                        print(f"Erreur lors de la lecture du fichier {filepath}: {e}")
        except Exception as e:
            print(f"Erreur lors de la recherche des fichiers existants: {e}")
        
        return known_ids 