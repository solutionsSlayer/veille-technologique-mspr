import json
import os
from typing import Dict, List, Any

def load_sources() -> Dict[str, List[Dict[str, Any]]]:
    """
    Charge les sources de données définies dans le fichier sources.json
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionnaire contenant les sources RSS et sites web
    """
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sources_path = os.path.join(current_dir, 'sources.json')
        
        with open(sources_path, 'r', encoding='utf-8') as file:
            sources = json.load(file)
        
        return sources
    except Exception as e:
        print(f"Erreur lors du chargement des sources: {e}")
        return {"rss_feeds": [], "websites": []}

def load_environment_variables():
    """
    Charge les variables d'environnement depuis le fichier .env
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Vérification de la présence de la clé API OpenAI
    if not os.environ.get('OPENAI_API_KEY'):
        print("ATTENTION: La clé API OpenAI n'est pas définie dans le fichier .env")
        print("Veuillez copier le fichier .env.example en .env et ajouter votre clé API") 