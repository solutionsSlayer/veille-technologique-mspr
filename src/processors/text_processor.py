import json
import os
import re
import logging
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TextProcessor")

class TextProcessor:
    """
    Processeur de texte pour les données collectées avec fonctionnalités améliorées:
    - Nettoyage des balises HTML
    - Extraction des liens
    - Préparation pour la vectorisation
    """
    
    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        """
        Initialise le processeur
        
        Args:
            input_dir (str): Répertoire d'entrée contenant les données brutes
            output_dir (str): Répertoire de sortie pour les données traitées
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Crée le répertoire de sortie s'il n'existe pas"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _clean_html(self, html_content: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Nettoie le HTML et extrait les liens
        
        Args:
            html_content (str): Contenu HTML à nettoyer
            
        Returns:
            Tuple[str, List[Dict[str, str]]]: 
                - Texte nettoyé
                - Liste de liens extraits avec leur texte et URL
        """
        if not html_content:
            return "", []
        
        # Utiliser BeautifulSoup pour un nettoyage HTML plus robuste
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraire les liens avant de nettoyer le texte
            links = []
            for a_tag in soup.find_all('a', href=True):
                link_text = a_tag.get_text().strip()
                href = a_tag['href']
                links.append({
                    "text": link_text, 
                    "url": href
                })
            
            # Extraire le texte
            text = soup.get_text(separator=' ', strip=True)
            
            # Nettoyer davantage si nécessaire
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text, links
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage HTML: {e}")
            # Fallback au nettoyage par regex en cas d'erreur
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return clean_text.strip(), []
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie un texte (sans balises HTML)
        
        Args:
            text (str): Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
        
        # Supprimer les URL
        text = re.sub(r'https?://\S+', '', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères spéciaux inutiles
        text = re.sub(r'[^\w\s.,;:!?\(\)\[\]\'\"«»]', '', text)
        
        return text.strip()
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extrait des mots-clés à partir du texte (simple implémentation)
        
        Args:
            text (str): Texte d'entrée
            max_keywords (int): Nombre maximum de mots-clés à extraire
            
        Returns:
            List[str]: Liste de mots-clés
        """
        if not text:
            return []
            
        # Conversion en minuscules et tokenisation basique
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # Filtrer les mots communs (stop words) - liste minimaliste
        stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'pour', 'par', 'sur', 'dans', 'en', 'qui', 'que', 'quoi',
                     'dont', 'avec', 'sans', 'the', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'at', 'from', 'by', 'with'}
        filtered_words = [w for w in words if w not in stop_words]
        
        # Compter les occurrences
        word_counts = {}
        for word in filtered_words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        
        # Trier par fréquence et retourner les plus fréquents
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def process_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un article
        
        Args:
            article (Dict[str, Any]): Article à traiter
            
        Returns:
            Dict[str, Any]: Article traité
        """
        processed = article.copy()
        extracted_links = []
        
        # Traitement du contenu
        if "content" in processed:
            clean_content, content_links = self._clean_html(processed["content"])
            processed["cleaned_content"] = clean_content
            processed["content_links"] = content_links
            extracted_links.extend(content_links)
        
        # Traitement du résumé
        if "summary" in processed:
            clean_summary, summary_links = self._clean_html(processed["summary"])
            processed["cleaned_summary"] = clean_summary
            processed["summary_links"] = summary_links
            
            # Ajouter des liens qui ne sont pas déjà dans le contenu
            for link in summary_links:
                if link not in extracted_links:
                    extracted_links.append(link)
        
        # Normalisation du texte pour la vectorisation
        if "cleaned_content" in processed:
            # Utilisé pour la vectorisation
            processed["normalized_text"] = self._clean_text(processed["cleaned_content"])
            
            # Extraire des mots-clés
            processed["keywords"] = self._extract_keywords(processed["normalized_text"])
        
        # S'assurer qu'il y a un champ "title" nettoyé
        if "title" in processed and processed["title"]:
            processed["cleaned_title"] = self._clean_text(processed["title"])
        
        # Conserver tous les liens extraits
        processed["all_links"] = extracted_links
        
        # Ajouter des métadonnées
        processed["processed_at"] = datetime.now().isoformat()
        
        return processed
    
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Traite un fichier de données
        
        Args:
            file_path (str): Chemin du fichier à traiter
            
        Returns:
            List[Dict[str, Any]]: Liste des articles traités
        """
        try:
            logger.info(f"Traitement du fichier: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            processed_data = []
            for article in data:
                processed = self.process_article(article)
                processed_data.append(processed)
                
            logger.info(f"Fichier traité avec succès: {len(processed_data)} articles")
            return processed_data
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier {file_path}: {e}")
            return []
    
    def save_to_json(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """
        Sauvegarde les données au format JSON
        
        Args:
            data (List[Dict[str, Any]]): Données à sauvegarder
            output_path (str): Chemin de sortie
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Données sauvegardées au format JSON: {output_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde JSON: {e}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """
        Sauvegarde les données au format CSV
        
        Args:
            data (List[Dict[str, Any]]): Données à sauvegarder
            output_path (str): Chemin de sortie
        """
        try:
            # Convertir en DataFrame
            df = pd.DataFrame(data)
            
            # Convertir les colonnes contenant des listes/dictionnaires en JSON
            for col in df.columns:
                if isinstance(df[col].iloc[0], (list, dict)) if not df.empty and len(df[col]) > 0 else False:
                    df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if x else None)
            
            # Sauvegarder en CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Données sauvegardées au format CSV: {output_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde CSV: {e}")
    
    def process_all_files(self, save_csv: bool = True) -> Dict[str, Any]:
        """
        Traite tous les fichiers du répertoire d'entrée
        
        Args:
            save_csv (bool): Indique s'il faut également sauvegarder au format CSV
            
        Returns:
            Dict[str, Any]: Statistiques de traitement
        """
        stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_articles": 0,
            "web_articles": 0,
            "rss_articles": 0
        }
        
        all_processed_data = []
        
        # Liste des fichiers JSON dans le répertoire d'entrée
        for filename in os.listdir(self.input_dir):
            if not filename.endswith(".json"):
                continue
                
            stats["total_files"] += 1
            
            file_path = os.path.join(self.input_dir, filename)
            processed_data = self.process_file(file_path)
            
            if processed_data:
                # Création du nom de fichier de sortie
                output_filename = f"processed_{filename}"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Sauvegarde des données traitées au format JSON
                self.save_to_json(processed_data, output_path)
                
                # Mettre à jour les statistiques
                stats["processed_files"] += 1
                stats["total_articles"] += len(processed_data)
                
                # Compter les articles par type
                if filename.startswith("web_"):
                    stats["web_articles"] += len(processed_data)
                elif filename.startswith("rss_"):
                    stats["rss_articles"] += len(processed_data)
                
                # Ajouter à la liste complète
                all_processed_data.extend(processed_data)
                
                logger.info(f"Fichier traité: {filename} -> {output_filename} ({len(processed_data)} articles)")
        
        # Sauvegarder toutes les données traitées dans un seul fichier
        if all_processed_data:
            combined_json_path = os.path.join(self.output_dir, "all_processed_data.json")
            self.save_to_json(all_processed_data, combined_json_path)
            
            if save_csv:
                combined_csv_path = os.path.join(self.output_dir, "all_processed_data.csv")
                self.save_to_csv(all_processed_data, combined_csv_path)
        
        return stats

    def process_files_parallel(self, max_workers: int = 4, save_csv: bool = True) -> Dict[str, Any]:
        """
        Traite tous les fichiers du répertoire d'entrée en parallèle
        
        Args:
            max_workers (int): Nombre maximum de workers pour le traitement parallèle
            save_csv (bool): Indique s'il faut également sauvegarder au format CSV
            
        Returns:
            Dict[str, Any]: Statistiques de traitement
        """
        stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_articles": 0,
            "web_articles": 0,
            "rss_articles": 0
        }
        
        # Liste des fichiers JSON dans le répertoire d'entrée
        json_files = [f for f in os.listdir(self.input_dir) if f.endswith(".json")]
        stats["total_files"] = len(json_files)
        
        all_processed_data = []
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            # Soumettre les tâches
            for filename in json_files:
                file_path = os.path.join(self.input_dir, filename)
                futures[executor.submit(self.process_file, file_path)] = filename
            
            # Traiter les résultats
            for future in concurrent.futures.as_completed(futures):
                filename = futures[future]
                try:
                    processed_data = future.result()
                    
                    if processed_data:
                        # Création du nom de fichier de sortie
                        output_filename = f"processed_{filename}"
                        output_path = os.path.join(self.output_dir, output_filename)
                        
                        # Sauvegarde des données traitées au format JSON
                        self.save_to_json(processed_data, output_path)
                        
                        # Mettre à jour les statistiques
                        stats["processed_files"] += 1
                        stats["total_articles"] += len(processed_data)
                        
                        # Compter les articles par type
                        if filename.startswith("web_"):
                            stats["web_articles"] += len(processed_data)
                        elif filename.startswith("rss_"):
                            stats["rss_articles"] += len(processed_data)
                        
                        # Ajouter à la liste complète
                        all_processed_data.extend(processed_data)
                        
                        logger.info(f"Fichier traité: {filename} -> {output_filename} ({len(processed_data)} articles)")
                
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du fichier {filename}: {e}")
        
        # Sauvegarder toutes les données traitées dans un seul fichier
        if all_processed_data:
            combined_json_path = os.path.join(self.output_dir, "all_processed_data.json")
            self.save_to_json(all_processed_data, combined_json_path)
            
            if save_csv:
                combined_csv_path = os.path.join(self.output_dir, "all_processed_data.csv")
                self.save_to_csv(all_processed_data, combined_csv_path)
        
        return stats

def process_all_data(input_dir: str = "data/raw", output_dir: str = "data/processed", 
                    parallel: bool = True, max_workers: int = 4) -> Dict[str, Any]:
    """
    Fonction utilitaire pour traiter toutes les données collectées
    
    Args:
        input_dir (str): Répertoire d'entrée
        output_dir (str): Répertoire de sortie
        parallel (bool): Utiliser le traitement parallèle
        max_workers (int): Nombre maximum de workers pour le traitement parallèle
        
    Returns:
        Dict[str, Any]: Statistiques de traitement
    """
    processor = TextProcessor(input_dir, output_dir)
    
    if parallel:
        return processor.process_files_parallel(max_workers=max_workers)
    else:
        return processor.process_all_files() 