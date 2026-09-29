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

def strip_articles(text: str) -> str:
    """Remove common leading articles/prefixes in Spanish and Valencian for comparison."""
    norm = normalize_text(text)
    # Strip prefixes like "receta", "recepta"
    norm = re.sub(r'^(receta|recepta)\s+', '', norm).strip()
    return re.sub(r'^(el|la|los|las|els|les|un|una|uns|unes|l)\s+', '', norm).strip()

TITLE_MAPPINGS = {
    # ==================== 1P (1º PRIMARIA) ====================
    # Las abejas <-> Les abelles
    "les abelles": "las abejas",
    "abelles": "las abejas",
    "la abella": "las abejas",
    "las abejas": "las abejas",
    "abejas": "las abejas",

    # El gat Renat <-> El gato Renato
    "el gat renat": "el gato renato",
    "gat renat": "el gato renato",
    "el gat renato": "el gato renato",
    "gat renato": "el gato renato",
    "el gato renat": "el gato renato",
    "el gato renato": "el gato renato",

    # ¡Perrito perdido! <-> Gosset perdut!
    "gosset perdut": "perrito perdido",
    "el gosset perdut": "perrito perdido",
    "gos perdut": "perrito perdido",
    "perrito perdido": "perrito perdido",
    "el perrito perdido": "perrito perdido",

    # Los bigotes de Renato <-> Els bigots de renat
    "els bigots de renat": "los bigotes de renato",
    "bigots de renat": "los bigotes de renato",
    "els bigotis de renat": "los bigotes de renato",
    "bigotis de renat": "los bigotes de renato",
    "els bigotis de renato": "los bigotes de renato",
    "els bigots de renato": "los bigotes de renato",
    "los bigotes de renat": "los bigotes de renato",
    "los bigotes de renato": "los bigotes de renato",

    # El barco de papel <-> El vaixell de paper
    "el vaixell de paper": "el barco de papel",
    "vaixell de paper": "el barco de papel",
    "el vaixellet de paper": "el barco de papel",
    "vaixellet de paper": "el barco de papel",
    "el barquet de paper": "el barco de papel",
    "barquet de paper": "el barco de papel",
    "el barco de papel": "el barco de papel",
    "barco de papel": "el barco de papel",
    "el barquito de papel": "el barco de papel",
    "barquito de papel": "el barco de papel",

    # Receta de galletas <-> Recepta de galletes
    "recepta de galletes": "receta de galletas",
    "la recepta de galetes": "receta de galletas",
    "la recepta de les galetes": "receta de galletas",
    "les galetes": "receta de galletas",
    "receta de galletas": "receta de galletas",
    "la receta de las galletas": "receta de galletas",
    "la receta de galletas": "receta de galletas",

    # En clase <-> En classe
    "en classe": "en clase",
    "a classe": "en clase",
    "classe": "en clase",
    "en clase": "en clase",
    "clase": "en clase",

    # Receta de limonada <-> Recepta de llimonada
    "recepta de llimonada": "receta de limonada",
    "la recepta de llimonada": "receta de limonada",
    "la recepta de la llimonada": "receta de limonada",
    "la llimonada": "receta de limonada",
    "receta de limonada": "receta de limonada",
    "la receta de la limonada": "receta de limonada",
    "la receta de limonada": "receta de limonada",

    # El globo de Lúa <-> El globus de Lúa
    "el globus de lua": "el globo de lua",
    "globus de lua": "el globo de lua",
    "el globo de lua": "el globo de lua",
    "globo de lua": "el globo de lua",

    # El oso Pol <-> L'ós Pol
    "l os pol": "el oso pol",
    "el os pol": "el oso pol",
    "el oso pol": "el oso pol",
    "os pol": "el oso pol",
    "oso pol": "el oso pol",

    # Meli y su gato <-> Meli i el seu gat
    "meli i el seu gat": "meli y su gato",
    "meli i el seu gatet": "meli y su gato",
    "meli y su gato": "meli y su gato",

    # La bicicleta de Eli <-> La bicicleta d'Eli
    "la bicicleta d eli": "la bicicleta de eli",
    "la bicicleta de l eli": "la bicicleta de eli",
    "la bicicleta de eli": "la bicicleta de eli",
    "bicicleta d eli": "la bicicleta de eli",
    "bicicleta de eli": "la bicicleta de eli",

    # El muñeco de nieve <-> El ninot de neu
    "el ninot de neu": "el muneco de nieve",
    "ninot de neu": "el muneco de nieve",
    "el muneco de nieve": "el muneco de nieve",
    "muneco de nieve": "el muneco de nieve",

    # Un día en la playa <-> Un dia a la platja
    "un dia a la platja": "un dia en la playa",
    "un dia en la platja": "un dia en la playa",
    "dia a la platja": "un dia en la playa",
    "un dia en la playa": "un dia en la playa",
    "dia en la playa": "un dia en la playa",

    # La cometa <-> El catxerulo / L'estel
    "el catxerulo": "la cometa",
    "catxerulo": "la cometa",
    "l estel": "la cometa",
    "el estel": "la cometa",
    "estel": "la cometa",
    "la cometa": "la cometa",
    "cometa": "la cometa",

    # El tren de Ramón <-> El tren de Ramon
    "el tren de ramon": "el tren de ramon",
    "tren de ramon": "el tren de ramon",

    # El avión de papel <-> L'avió de paper
    "l avio de paper": "el avion de paper",
    "el avio de paper": "el avion de paper",
    "avio de paper": "el avion de paper",
    "el avion de paper": "el avion de paper",
    "avion de paper": "el avion de paper",

    # La magia de los colores <-> La màgia dels colors
    "la magia dels colors": "la magia de los colores",
    "magia dels colors": "la magia de los colores",
    "la magia de los colores": "la magia de los colores",

    # Mi tía <-> La meua tia
    "la meua tia": "mi tia",
    "la meva tia": "mi tia",
    "meua tia": "mi tia",
    "mi tia": "mi tia",

    # La rana Juana <-> La granota Joana
    "la granota joana": "la rana juana",
    "granota joana": "la rana juana",
    "la granota juana": "la rana juana",
    "la rana juana": "la rana juana",
    "rana juana": "la rana juana",

    # Ada Yey <-> El do d'Ada
    "el do d ada": "ada yey",
    "do d ada": "ada yey",
    "ada yey": "ada yey",

    # ==================== 2P (2º PRIMARIA) ====================
    # 1. El tambor de Pol <-> El tambor de Pol
    "el tambor de pol": "el tambor de pol",
    "tambor de pol": "el tambor de pol",

    # 2. El mono divertido <-> El mico divertit
    "el mico divertit": "el mono divertido",
    "mico divertit": "el mono divertido",
    "el mono divertit": "el mono divertido",

    # 3. Las hormigas trabajadoras <-> Les formigues treballadores
    "les formigues treballadores": "las hormigas trabajadoras",
    "formigues treballadores": "las hormigas trabajadoras",
    "les formigues": "las hormigas trabajadoras",
    "formigues": "las hormigas trabajadoras",
    "las hotmigas trabajadoras": "las hormigas trabajadoras",
    "las hormigas trabajadoras": "las hormigas trabajadoras",

    # 4. El vampiro Casimiro <-> El vampir Casimir
    "el vampir casimir": "el vampiro casimiro",
    "vampir casimir": "el vampiro casimiro",
    "el vampir casimiro": "el vampiro casimiro",
    "vampir casimiro": "el vampiro casimiro",
    "el vampiro casimiro": "el vampiro casimiro",

    # 5. El otoño <-> La tardor
    "la tardor": "el otono",
    "tardor": "el otono",
    "el otono": "el otono",
    "otono": "el otono",

    # 6. El oso goloso <-> L'os llépol
    "l os llepol": "el oso goloso",
    "el os llepol": "el oso goloso",
    "os llepol": "el oso goloso",
    "el oso goloso": "el oso goloso",
    "oso goloso": "el oso goloso",

    # 7. Brochetas de fruta con chocolate <-> Broquetes de fruita amb xocolate
    "broquetes de fruita amb xocolate": "brochetas de fruta con chocolate",
    "broquetes de fruita amb xocolata": "brochetas de fruta con chocolate",
    "broquetes de fruita": "brochetas de fruta con chocolate",
    "broquetes": "brochetas de fruta con chocolate",
    "brochetas de fruta con chocolate": "brochetas de fruta con chocolate",

    # 8. El submarino de cartón <-> El submarí de cartó
    "el submari de carto": "el submarino de carton",
    "submari de carto": "el submarino de carton",
    "el submari": "el submarino de carton",
    "submari": "el submarino de carton",
    "el submarino de carton": "el submarino de carton",
    "submarino de carton": "el submarino de carton",

    # 9. El invierno <-> L'Hivern
    "l hivern": "el invierno",
    "el hivern": "el invierno",
    "hivern": "el invierno",
    "el invierno": "el invierno",
    "invierno": "el invierno",

    # 10. Receta: Tarta de manzana <-> Pastís de poma
    "pastis de poma": "receta tarta de manzana",
    "el pastis de poma": "receta de tarta de manzana",
    "tarta de poma": "receta tarta de manzana",
    "recepta pastis de poma": "receta tarta de manzana",
    "recepta pastis poma": "receta tarta de manzana",
    "recepta tarta de poma": "receta tarta de manzana",
    "tarta de manzana": "receta tarta de manzana",
    "receta tarta de manzana": "receta tarta de manzana",
    "receta de tarta de manzana": "receta tarta de manzana",

    # 11. El ovillo de Mica <-> El cabdell de Mica
    "el cabdell de mica": "el ovillo de mica",
    "cabdell de mica": "el ovillo de mica",
    "el ovillo de mica": "el ovillo de mica",
    "ovillo de mica": "el ovillo de mica",

    # 12. Jack, el pirata aventurero <-> Jack, el pirata
    "jack el pirata": "jack el pirata aventurero",
    "el pirata jack": "jack el pirata aventurero",
    "jack el pirata aventurer": "jack el pirata aventurero",
    "jack el pirata aventurero": "jack el pirata aventurero",

    # 13. El tesoro del Pirata Jack <-> El tresor del pirata Jack
    "el tresor del pirata jack": "el tesoro del pirata jack",
    "tresor del pirata jack": "el tesoro del pirata jack",
    "el tresor de jack": "el tesoro del pirata jack",
    "tresor de jack": "el tesoro del pirata jack",
    "el tesoro del pirata jack": "el tesoro del pirata jack",

    # 14. Poesía del pirata <-> Poesia del pirata
    "poesia del pirata": "poesia del pirata",
    "poesia de pirata": "poesia del pirata",

    # 15. Viaje a la Luna <-> Viatge a la Lluna
    "viatge a la lluna": "viaje a la luna",
    "viatge a lluna": "viaje a la luna",
    "la lluna brillant": "la luna brillante",
    "lluna brillant": "la luna brillante",
    "la lluna": "viaje a la luna",
    "lluna": "viaje a la luna",
    "viaje a la luna": "viaje a la luna",
    "la luna brillante": "la luna brillante",

    # 16. Tito, ratoncito <-> Tonet, ratolinet
    "tonet ratolinet": "tito ratoncito",
    "ratoli tonet": "tito ratoncito",
    "el ratoli tonet": "tito ratoncito",
    "tonet": "tito ratoncito",
    "tito ratoncito": "tito ratoncito",
    "ratoncito tito": "tito ratoncito",

    # 17. La primavera <-> La Primavera
    "la primavera": "la primavera",
    "primavera": "la primavera",

    # 18. Mi merienda <-> El meu berenar
    "el meu berenar": "mi merienda",
    "meu berenar": "mi merienda",
    "berenar": "mi merienda",
    "mi merienda": "mi merienda",
    "merienda": "mi merienda",

    # 19. La gata Mica <-> La gata Mica
    "la gata mica": "la gata mica",
    "gata mica": "la gata mica",

    # 20. El verano <-> L'estiu
    "l estiu": "el verano",
    "el estiu": "el verano",
    "estiu": "el verano",
    "el verano": "el verano",
    "verano": "el verano",

    # 21. El arcoíris <-> L'arc de Sant Martí
    "l arc de sant marti": "el arcoiris",
    "arc de sant marti": "el arcoiris",
    "l arc iris": "el arcoiris",
    "arc iris": "el arcoiris",
    "el arcoiris": "el arcoiris",
    "el arco iris": "el arcoiris",
    "arcoiris": "el arcoiris",

    # La liebre y la tortuga <-> La llebre i la tortuga
    "la llebre i la tortuga": "la liebre y la tortuga",
    "llebre i la tortuga": "la liebre y la tortuga",
    "la llebre i tortuga": "la liebre y la tortuga",
    "llebre i tortuga": "la liebre y la tortuga",
    "la liebre y la tortuga": "la liebre y la tortuga",
    "liebre y la tortuga": "la liebre y la tortuga",

    # Ada tiene un don / El don de Ada <-> Ada té un do / El do d'Ada
    "ada te un do": "ada tiene un don",
    "ada te do": "ada tiene un don",
    "ada tiene un don": "ada tiene un don",
    "el don de ada": "el don de ada",

    # Radar llega a casa <-> Radar arriba a casa
    "radar arriba a casa": "radar llega a casa",
    "radar arriba": "radar llega a casa",
    "arriba a casa": "radar llega a casa",
    "radar la gata": "radar la gata",
    "la gata radar": "radar la gata",
    "radar": "radar",
    "radar llega a casa": "radar llega a casa",
    "radar llega": "radar llega a casa",

    # El taller de Fortunio <-> El taller de Fortunio / Fortunio i els invents
    "el taller de fortunio": "el taller de fortunio",
    "taller de fortunio": "el taller de fortunio",
    "fortunio i els seus invents": "fortunio y sus inventos",
    "fortunio i els invents": "fortunio y sus inventos",
    "fortunio y sus inventos": "fortunio y sus inventos",
    "fortunio": "fortunio",

    # Radar en el taller <-> Radar al taller
    "radar al taller": "radar en el taller",
    "radar en el taller": "radar en el taller",
}

KEYWORD_RULES = [
    # 2P: Tambor Pol
    (lambda v, e: "tambor" in v and "tambor" in e and "pol" in v and "pol" in e),
    # 2P: Mono / Mico
    (lambda v, e: ("mico" in v or "mono" in v) and ("mono" in e or "mico" in e)),
    # 2P: Hormigas / Formigues
    (lambda v, e: ("formig" in v) and ("hormig" in e or "hotmig" in e)),
    # 2P: Vampiro / Vampir Casimir
    (lambda v, e: ("vampir" in v) and ("vampir" in e) and ("casimir" in v) and ("casimir" in e)),
    # 2P: Tardor / Otoño
    (lambda v, e: ("tardor" in v) and ("oton" in e)),
    # 2P: Oso goloso / Os llepol
    (lambda v, e: ("llepol" in v or "golos" in v) and ("golos" in e or "llepol" in e)),
    # 2P: Brochetas / Broquetes chocolate
    (lambda v, e: ("broquet" in v) and ("brochet" in e)),
    # 2P: Submarino cartón / Submari carto
    (lambda v, e: ("submari" in v) and ("submarin" in e)),
    # 2P: Invierno / Hivern
    (lambda v, e: ("hivern" in v) and ("inviern" in e)),
    # 2P: Tarta manzana / Pastis poma
    (lambda v, e: ("poma" in v or "pastis" in v) and ("manzan" in e or "tarta" in e)),
    # 2P: Ovillo / Cabdell Mica
    (lambda v, e: ("cabdell" in v or "ovillo" in v) and ("mica" in v) and ("ovillo" in e or "cabdell" in e) and ("mica" in e)),
    # 2P: Pirata Jack tesoro
    (lambda v, e: ("tresor" in v) and ("tesor" in e) and ("jack" in v and "jack" in e)),
    # 2P: Pirata Jack / Jack pirata aventurero
    (lambda v, e: ("jack" in v and "jack" in e) and ("pirat" in v and "pirat" in e)),
    # 2P: Poesia pirata
    (lambda v, e: ("poesi" in v and "poesi" in e) and ("pirat" in v and "pirat" in e)),
    # 2P: Tito / Tonet ratoncito / ratolinet
    (lambda v, e: ("tonet" in v or "ratoli" in v) and ("tito" in e or "raton" in e)),
    # 2P: Primavera
    (lambda v, e: ("primaver" in v) and ("primaver" in e)),
    # 2P: Berenar / Merienda
    (lambda v, e: ("berenar" in v) and ("meriend" in e)),
    # 2P: Gata Mica
    (lambda v, e: ("gata" in v and "mica" in v) and ("gata" in e and "mica" in e)),
    # 2P: Estiu / Verano
    (lambda v, e: ("estiu" in v) and ("veran" in e)),
    # 2P: Arc Sant Marti / Arcoiris
    (lambda v, e: ("marti" in v or "arc" in v) and ("arco" in e or "iris" in e)),
    # 2P: Liebre y tortuga
    (lambda v, e: ("llebre" in v or "tortuga" in v) and ("liebre" in e or "tortuga" in e)),
    # 2P: Luna / Lluna
    (lambda v, e: ("lluna" in v) and ("luna" in e)),
    # 2P: Radar
    (lambda v, e: ("radar" in v) and ("radar" in e)),
    # 2P: Fortunio
    (lambda v, e: ("fortunio" in v) and ("fortunio" in e)),

    # 1P: Abejas / Abelles
    (lambda v, e: ("abel" in v or "abell" in v) and ("abej" in e)),
    # 1P: Perro / Gosset
    (lambda v, e: ("gos" in v or "gosset" in v or "perdut" in v) and ("perr" in e or "perdit" in e or "perdid" in e)),
    # 1P: Bigotes Renato
    (lambda v, e: "renat" in v and "renat" in e and ("bigot" in v or "bigotis" in v) and ("bigot" in e or "bigotes" in e)),
    # 1P: Gato Renato
    (lambda v, e: "renat" in v and "renat" in e and ("gat" in v or "gato" in v or "renat" in v) and ("gat" in e or "gato" in e)),
    # 1P: Barco papel
    (lambda v, e: ("vaixell" in v or "barquet" in v or "barco" in v or "barquit" in v) and ("paper" in v or "papel" in v) and ("barc" in e or "barqu" in e) and ("papel" in e or "paper" in e)),
    # 1P: Galletas / Galetes
    (lambda v, e: ("galet" in v or "galletes" in v) and ("gallet" in e or "galletas" in e)),
    # 1P: Limonada / Llimonada
    (lambda v, e: ("llimon" in v) and ("limon" in e)),
    # 1P: Clase / Classe
    (lambda v, e: ("class" in v) and ("clas" in e)),
    # 1P: Lúa
    (lambda v, e: "lua" in v and "lua" in e),
    # 1P: Pol
    (lambda v, e: "pol" in v and "pol" in e),
    # 1P: Eli
    (lambda v, e: "eli" in v and "eli" in e),
    # 1P: Ramón
    (lambda v, e: "ramon" in v and "ramon" in e),
    # 1P: Nieve / Ninot
    (lambda v, e: ("neu" in v or "ninot" in v) and ("niev" in e or "munec" in e)),
    # 1P: Playa / Platja
    (lambda v, e: ("platj" in v) and ("play" in e)),
    # 1P: Avión
    (lambda v, e: ("avio" in v) and ("avion" in e)),
    # 1P: Cometa
    (lambda v, e: ("catxerul" in v or "estel" in v or "comet" in v) and ("comet" in e)),
    # 1P: Colores
    (lambda v, e: ("color" in v) and ("color" in e)),
    # 1P: Tía
    (lambda v, e: ("tia" in v) and ("tia" in e)),
    # 1P: Ada
    (lambda v, e: ("ada" in v) and ("ada" in e)),
    # 1P: Meli
    (lambda v, e: ("meli" in v) and ("meli" in e)),
    # 1P: Juana / Granota
    (lambda v, e: ("joana" in v or "juana" in v or "granot" in v) and ("juan" in e or "ran" in e)),
]

def find_matching_spanish_text(val_text: models.Text, es_texts: List[models.Text]) -> Optional[models.Text]:
    """Find the corresponding Spanish text for a Valencian text."""
    v_norm = normalize_text(val_text.title)
    v_stripped = strip_articles(val_text.title)
    
    # 1. Direct title mapping
    target_es_norm = TITLE_MAPPINGS.get(v_norm) or TITLE_MAPPINGS.get(v_stripped)
    if target_es_norm:
        target_stripped = strip_articles(target_es_norm)
        for es in es_texts:
            e_norm = normalize_text(es.title)
            e_stripped = strip_articles(es.title)
            if (e_norm == target_es_norm or e_stripped == target_es_norm or
                e_norm == target_stripped or e_stripped == target_stripped or
                target_es_norm in e_norm or e_norm in target_es_norm or
                target_stripped in e_stripped or e_stripped in target_stripped):
                return es

    # 2. Exact normalized title match
    for es in es_texts:
        if normalize_text(es.title) == v_norm or strip_articles(es.title) == v_stripped:
            return es

    # 3. Keyword heuristic matching
    for es in es_texts:
        e_norm = normalize_text(es.title)
        for rule in KEYWORD_RULES:
            if rule(v_norm, e_norm):
                return es

    # 4. Order match (if both course_level match and order > 0)
    if val_text.order and val_text.order > 0:
        for es in es_texts:
            if es.order == val_text.order:
                return es

    return None

def sync_all_matching_illustrations(db: Session) -> int:
    """
    Synchronizes illustrations between matching Spanish and Valencian readings (across all course levels).
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
