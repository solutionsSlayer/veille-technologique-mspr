#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal pour lancer la collecte de données
"""

import os
import sys
import time
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajout du répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des modules
from src.utils.config_loader import load_sources, load_environment_variables
from src.collectors.rss_collector import collect_rss_feeds
from src.collectors.web_collector import collect_websites

def parse_arguments():
    """
    Parse les arguments de la ligne de commande
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(description="Collecte de données à partir de sources RSS et web")
    parser.add_argument("--no-cache", action="store_true", help="Désactive l'utilisation du cache")
    parser.add_argument("--workers", type=int, default=5, help="Nombre de workers simultanés (par défaut: 5)")
    parser.add_argument("--output-dir", type=str, default=None, help="Répertoire de sortie pour les données collectées")
    parser.add_argument("--cache-dir", type=str, default=None, help="Répertoire pour le cache")
    parser.add_argument("--rss-only", action="store_true", help="Collecte uniquement les flux RSS")
    parser.add_argument("--web-only", action="store_true", help="Collecte uniquement les sites web")
    
    return parser.parse_args()

def main():
    """
    Fonction principale pour lancer la collecte de données
    """
    start_time = time.time()
    
    print("=== Démarrage de la collecte de données ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parsing des arguments
    args = parse_arguments()
    
    # Chargement des variables d'environnement
    load_environment_variables()
    
    # Création des répertoires de données
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    raw_dir = args.output_dir if args.output_dir else os.path.join(data_dir, "raw")
    cache_dir = args.cache_dir if args.cache_dir else os.path.join(data_dir, "cache")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    
    # Configuration des options
    use_cache = not args.no_cache
    max_workers = args.workers
    
    print(f"Répertoire de données: {raw_dir}")
    print(f"Répertoire de cache: {cache_dir}")
    print(f"Utilisation du cache: {'Non' if args.no_cache else 'Oui'}")
    print(f"Workers simultanés: {max_workers}")
    
    # Chargement des sources
    sources = load_sources()
    
    # Affichage des informations
    rss_count = len(sources.get('rss_feeds', []))
    web_count = len(sources.get('websites', []))
    print(f"Sources RSS: {rss_count}")
    print(f"Sites web: {web_count}")
    
    # Exécution de la collecte en parallèle si les deux types de sources sont demandés
    if not args.rss_only and not args.web_only and rss_count > 0 and web_count > 0:
        print("\n=== Collecte parallèle des flux RSS et sites web ===")
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            rss_future = executor.submit(
                collect_rss_feeds, 
                sources.get("rss_feeds", []), 
                raw_dir, 
                cache_dir, 
                max_workers, 
                use_cache
            )
            
            web_future = executor.submit(
                collect_websites, 
                sources.get("websites", []), 
                raw_dir, 
                cache_dir, 
                max_workers, 
                use_cache
            )
            
            # Attente des résultats
            for future in as_completed([rss_future, web_future]):
                try:
                    future.result()
                except Exception as e:
                    print(f"Une erreur s'est produite: {e}")
    else:
        # Collecte des données RSS si demandé
        if not args.web_only and rss_count > 0:
            print("\n=== Collecte des flux RSS ===")
            collect_rss_feeds(sources.get("rss_feeds", []), raw_dir, cache_dir, max_workers, use_cache)
        
        # Collecte des sites web si demandé
        if not args.rss_only and web_count > 0:
            print("\n=== Collecte des sites web ===")
            collect_websites(sources.get("websites", []), raw_dir, cache_dir, max_workers, use_cache)
    
    # Affichage du temps d'exécution
    elapsed_time = time.time() - start_time
    print(f"\n=== Collecte de données terminée en {elapsed_time:.2f} secondes ===")

if __name__ == "__main__":
    main() 