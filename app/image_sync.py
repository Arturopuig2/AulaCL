import unicodedata
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models

def normalize_text(text: str) -> str:
    """Normalize text: lowercased, ASCII only, no punctuation, normalized whitespace."""
    if not text:
        return ""
    # Normalize unicode (decompose accents)
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = nfkd.encode('ASCII', 'ignore').decode('utf-8').lower()
    # Replace non-alphanumeric with spaces
    clean_text = re.sub(r'[^a-z0-9]+', ' ', ascii_text)
    return clean_text.strip()

TITLE_MAPPINGS = {
    "el globus de lua": "el globo de lua",
    "el globo de lua": "el globo de lua",
    "globus de lua": "el globo de lua",
    "l os pol": "el oso pol",
    "el os pol": "el oso pol",
    "el oso pol": "el oso pol",
    "os pol": "el oso pol",
    "la recepta de les galetes": "la receta de las galletas",
    "la recepta de galetes": "la receta de las galletas",
    "les galetes": "la receta de las galletas",
    "la receta de las galletas": "la receta de las galletas",
    "la recepta de la llimonada": "la receta de la limonada",
    "la llimonada": "la receta de la limonada",
    "la receta de la limonada": "la receta de la limonada",
    "meli i el seu gat": "meli y su gato",
    "meli i el seu gatet": "meli y su gato",
    "meli y su gato": "meli y su gato",
    "la bicicleta d eli": "la bicicleta de eli",
    "la bicicleta de l eli": "la bicicleta de eli",
    "la bicicleta de eli": "la bicicleta de eli",
    "el ninot de neu": "el muneco de nieve",
    "el muneco de nieve": "el muneco de nieve",
    "un dia a la platja": "un dia en la playa",
    "un dia en la platja": "un dia en la playa",
    "un dia en la playa": "un dia en la playa",
    "a classe": "en clase",
    "en classe": "en clase",
    "en clase": "en clase",
    "el catxerulo": "la cometa",
    "l estel": "la cometa",
    "el estel": "la cometa",
    "la cometa": "la cometa",
    "el vaixellet de paper": "el barquito de papel",
    "el barquet de paper": "el barquito de paper",
    "el vaixell de paper": "el barquito de papel",
    "el barquito de papel": "el barquito de papel",
    "el tren de ramon": "el tren de ramon",
    "l avio de paper": "el avion de paper",
    "el avio de paper": "el avion de paper",
    "el avion de paper": "el avion de paper",
    "la magia dels colors": "la magia de los colores",
    "la magia de los colores": "la magia de los colores",
    "la meua tia": "mi tia",
    "la meva tia": "mi tia",
    "mi tia": "mi tia",
    "el gat renato": "el gato renato",
    "el gato renato": "el gato renato",
    "els bigotis de renato": "los bigotes de renato",
    "els bigots de renato": "los bigotes de renato",
    "los bigotes de renato": "los bigotes de renato",
    "la granota joana": "la rana juana",
    "la granota juana": "la rana juana",
    "la rana juana": "la rana juana",
    "el do d ada": "ada yey",
    "ada yey": "ada yey"
}

KEYWORD_RULES = [
    (lambda v, e: "lua" in v and "lua" in e),
    (lambda v, e: "pol" in v and "pol" in e),
    (lambda v, e: "eli" in v and "eli" in e),
    (lambda v, e: "renato" in v and "renato" in e and ("gat" in v or "gato" in v) and "gato" in e),
    (lambda v, e: "renato" in v and "renato" in e and ("bigot" in v or "bigote" in v) and "bigote" in e),
    (lambda v, e: ("joana" in v or "juana" in v or "granota" in v) and ("juana" in e or "rana" in e)),
    (lambda v, e: "ramon" in v and "ramon" in e),
    (lambda v, e: ("neu" in v or "ninot" in v) and ("nieve" in e or "muneco" in e)),
    (lambda v, e: ("platja" in v or "playa" in v) and "playa" in e),
    (lambda v, e: ("llimonada" in v or "limonada" in v) and "limonada" in e),
    (lambda v, e: ("galetes" in v or "galletas" in v) and "galletas" in e),
    (lambda v, e: ("vaixellet" in v or "barquet" in v or "barquito" in v) and "barquito" in e),
    (lambda v, e: ("avio" in v or "avion" in v) and "avion" in e),
    (lambda v, e: ("catxerulo" in v or "estel" in v or "cometa" in v) and "cometa" in e),
    (lambda v, e: ("colors" in v or "colores" in v) and "colores" in e),
    (lambda v, e: "tia" in v and "tia" in e),
    (lambda v, e: "ada" in v and "ada" in e),
    (lambda v, e: ("classe" in v or "clase" in v) and "clase" in e),
    (lambda v, e: "meli" in v and "meli" in e),
]

def find_matching_spanish_text(val_text: models.Text, es_texts: List[models.Text]) -> Optional[models.Text]:
    """Find the corresponding Spanish text for a Valencian text."""
    v_norm = normalize_text(val_text.title)
    
    # 1. Direct title mapping
    target_es_norm = TITLE_MAPPINGS.get(v_norm)
    if target_es_norm:
        for es in es_texts:
            if normalize_text(es.title) == target_es_norm:
                return es

    # 2. Exact normalized title match
    for es in es_texts:
        if normalize_text(es.title) == v_norm:
            return es

    # 3. Order match (if both course_level match and order > 0)
    if val_text.order and val_text.order > 0:
        for es in es_texts:
            if es.order == val_text.order:
                return es

    # 4. Keyword heuristic matching
    for es in es_texts:
        e_norm = normalize_text(es.title)
        for rule in KEYWORD_RULES:
            if rule(v_norm, e_norm):
                return es

    return None

def sync_all_matching_illustrations(db: Session) -> int:
    """
    Synchronizes illustrations between matching Spanish and Valencian readings (especially for 1P).
    Returns the number of texts updated.
    """
    updated_count = 0
    
    courses = ["1P", "2P", "3P", "4P", "5P", "6P", "1ESO", "2ESO"]
    for course in courses:
        es_texts = db.query(models.Text).filter(
            models.Text.course_level == course,
            models.Text.language == "es"
        ).all()
        
        val_texts = db.query(models.Text).filter(
            models.Text.course_level == course,
            models.Text.language == "val"
        ).all()
        
        if not es_texts or not val_texts:
            continue
            
        for val_text in val_texts:
            match_es = find_matching_spanish_text(val_text, es_texts)
            if match_es:
                # If Spanish has image and Valencian doesn't (or has different), copy it
                if match_es.image_path and val_text.image_path != match_es.image_path:
                    val_text.image_path = match_es.image_path
                    updated_count += 1
                # If Valencian has image and Spanish doesn't, copy to Spanish
                elif val_text.image_path and not match_es.image_path:
                    match_es.image_path = val_text.image_path
                    updated_count += 1

    if updated_count > 0:
        db.commit()
        
    return updated_count
