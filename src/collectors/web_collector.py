import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from .base_collector import BaseCollector
from concurrent.futures import ThreadPoolExecutor, as_completed

class WebCollector(BaseCollector):
    """
    Collecteur de données à partir de sites web
    """
    
    def __init__(self, output_dir: str = "data/raw", cache_dir: str = "data/cache",
                 max_workers: int = 5, cache_expiry: int = 3600):
        """
        Initialise le collecteur web
        
        Args:
            output_dir (str): Répertoire de sortie pour les données collectées
            cache_dir (str): Répertoire pour le cache
            max_workers (int): Nombre maximum de threads simultanés
            cache_expiry (int): Durée de validité du cache en secondes (1h par défaut)
        """
        super().__init__(output_dir, cache_dir, max_workers, cache_expiry)
        
    def collect_from_website(self, website_info: Dict[str, str], use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Collecte les informations d'un site web avec gestion du cache
        
        Args:
            website_info (Dict[str, str]): Informations sur le site web
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            Optional[Dict[str, Any]]: Informations collectées ou None en cas d'erreur
        """
        url = website_info["url"]
        cache_path = self._get_cache_path(url)
        
        # Vérification du cache si activé
        if use_cache and self._is_cache_valid(cache_path):
            print(f"Utilisation du cache pour {website_info['name']} ({url})")
            cached_data = self._read_cache(cache_path)
            if cached_data:
                return cached_data
        
        try:
            print(f"Collecte du site web: {website_info['name']} ({url})")
            
            # Configuration des entêtes pour simuler un navigateur
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            
            # Requête HTTP avec un timeout plus long et gestion des erreurs
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parsing du HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraction du titre
            title = soup.title.get_text() if soup.title else ""
            
            # Extraction du contenu en fonction du sélecteur CSS
            content = ""
            if "selector" in website_info and website_info["selector"]:
                print(f"Utilisation du sélecteur: {website_info['selector']}")
                elements = soup.select(website_info["selector"])
                
                if elements:
                    for element in elements:
                        # Extraction du texte avec préservation des espaces
                        extracted_text = element.get_text(separator="\n", strip=True)
                        if extracted_text:
                            content += extracted_text + "\n\n"
                    print(f"Contenu extrait avec le sélecteur ({len(content)} caractères)")
                else:
                    print(f"Aucun élément trouvé avec le sélecteur: {website_info['selector']}")
                    # Fallback: utiliser le corps de la page
                    content = self._extract_main_content(soup)
            else:
                # Si aucun sélecteur n'est spécifié, on extrait le contenu principal
                content = self._extract_main_content(soup)
            
            # Création de l'objet de résultat
            result = {
                "url": url,
                "title": title,
                "content": content,
                "source_name": website_info["name"],
                "category": website_info["category"],
                "collected_at": datetime.now().isoformat()
            }
            
            # Mise en cache des résultats
            if use_cache:
                self._write_cache(cache_path, result)
            
            return result
        except Exception as e:
            print(f"Erreur lors de la collecte du site {website_info['name']}: {e}")
            return {
                "url": url,
                "title": "",
                "content": "",
                "source_name": website_info["name"],
                "category": website_info["category"],
                "collected_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Tente d'extraire le contenu principal d'une page web
        
        Args:
            soup (BeautifulSoup): Objet BeautifulSoup
            
        Returns:
            str: Contenu principal extrait
        """
        content = ""
        
        # Stratégie 1: Rechercher les balises d'article
        main_elements = soup.find_all(["article", "main", "div", "section"], 
                                      class_=lambda c: c and any(x in str(c).lower() for x in ["content", "main", "article", "text"]))
        
        if main_elements:
            for element in main_elements:
                # Éliminer les éléments non pertinents
                for tag in element.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()
                    
                content += element.get_text(separator="\n", strip=True) + "\n\n"
            
            return content
        
        # Stratégie 2: Prendre le corps en entier si rien d'autre ne fonctionne
        if not content and soup.body:
            # Éliminer les éléments non pertinents
            for tag in soup.body.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()
                
            content = soup.body.get_text(separator="\n", strip=True)
        
        return content
    
    def collect_from_websites(self, websites: List[Dict[str, str]], use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collecte les informations de plusieurs sites web en parallèle
        
        Args:
            websites (List[Dict[str, str]]): Liste des sites web
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionnaire des informations collectées par catégorie
        """
        result = {}
        
        # Création de la liste des tâches à exécuter
        tasks = []
        for website in websites:
            tasks.append((website, use_cache))
        
        # Exécution des tâches en parallèle
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumission des tâches
            future_to_website = {executor.submit(self.collect_from_website, website, use_cache): website 
                                for website, use_cache in tasks}
            
            # Traitement des résultats
            for future in as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    website_data = future.result()
                    if website_data:
                        category = website["category"]
                        if category not in result:
                            result[category] = []
                        result[category].append(website_data)
                except Exception as e:
                    print(f"Exception lors de la collecte du site {website['name']}: {e}")
        
        return result

def collect_websites(websites: List[Dict[str, str]], output_dir: str = "data/raw", 
                   cache_dir: str = "data/cache", max_workers: int = 5, 
                   use_cache: bool = True) -> None:
    """
    Fonction utilitaire pour collecter des données à partir de sites web
    
    Args:
        websites (List[Dict[str, str]]): Liste des sites web
        output_dir (str): Répertoire de sortie
        cache_dir (str): Répertoire pour le cache
        max_workers (int): Nombre maximum de threads simultanés
        use_cache (bool): Utiliser le cache si disponible
    """
    collector = WebCollector(output_dir, cache_dir, max_workers)
    data = collector.collect_from_websites(websites, use_cache)
    collector.save_collected_data(data) 