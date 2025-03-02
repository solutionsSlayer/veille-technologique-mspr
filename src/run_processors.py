#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal pour lancer les processeurs de données
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Ajout du répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des modules
from src.utils.config_loader import load_environment_variables
from src.processors.text_processor import process_all_data

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_processors")

def parse_arguments():
    """
    Parse les arguments de la ligne de commande
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(description="Traitement des données collectées")
    
    parser.add_argument(
        "--input-dir", 
        default="data/raw",
        help="Répertoire contenant les données brutes (défaut: data/raw)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="data/processed",
        help="Répertoire de sortie pour les données traitées (défaut: data/processed)"
    )
    
    parser.add_argument(
        "--sequential", 
        action="store_true",
        help="Utiliser le traitement séquentiel au lieu du parallèle"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=4,
        help="Nombre de workers pour le traitement parallèle (défaut: 4)"
    )
    
    parser.add_argument(
        "--no-csv", 
        action="store_true",
        help="Ne pas sauvegarder les données au format CSV"
    )
    
    return parser.parse_args()

def main():
    """
    Fonction principale pour lancer les processeurs
    """
    args = parse_arguments()
    
    logger.info("=== Démarrage du traitement des données ===")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Chargement des variables d'environnement
    load_environment_variables()
    
    # Création des répertoires de données
    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Traitement des données
    logger.info("\n=== Traitement des données ===")
    logger.info(f"Répertoire d'entrée: {args.input_dir}")
    logger.info(f"Répertoire de sortie: {args.output_dir}")
    logger.info(f"Mode: {'séquentiel' if args.sequential else 'parallèle'}")
    
    if not args.sequential:
        logger.info(f"Nombre de workers: {args.workers}")
    
    # Exécution du traitement
    stats = process_all_data(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        parallel=not args.sequential,
        max_workers=args.workers
    )
    
    # Affichage des statistiques
    logger.info("\n=== Statistiques de traitement ===")
    logger.info(f"Fichiers traités: {stats['processed_files']}/{stats['total_files']}")
    logger.info(f"Articles traités: {stats['total_articles']}")
    logger.info(f"  - Articles Web: {stats.get('web_articles', 0)}")
    logger.info(f"  - Articles RSS: {stats.get('rss_articles', 0)}")
    
    logger.info("\n=== Traitement des données terminé ===")

if __name__ == "__main__":
    main() 