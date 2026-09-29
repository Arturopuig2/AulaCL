import pytest
from app.image_sync import normalize_text, find_matching_spanish_text, strip_articles
from app import models

def test_normalize_text():
    assert normalize_text("El globus de Lúa!") == "el globus de lua"
    assert normalize_text("L'ós Pol") == "l os pol"
    assert normalize_text("La bicicleta d'Eli") == "la bicicleta d eli"
    assert normalize_text("¿El muñeco de nieve?") == "el muneco de nieve"
    assert normalize_text("¡Perrito perdido!") == "perrito perdido"
    assert normalize_text("Els bigots de renat") == "els bigots de renat"

def test_user_reported_reading_pairs():
    es_abejas = models.Text(id=1, title="Las abejas", course_level="1P", language="es", image_path="/img/abejas.png")
    es_renato = models.Text(id=2, title="El gato Renato", course_level="1P", language="es", image_path="/img/renato.png")
    es_perrito = models.Text(id=3, title="¡Perrito perdido!", course_level="1P", language="es", image_path="/img/perrito.png")
    es_bigotes = models.Text(id=4, title="Los bigotes de Renato", course_level="1P", language="es", image_path="/img/bigotes.png")
    es_barco = models.Text(id=5, title="El barco de papel", course_level="1P", language="es", image_path="/img/barco.png")
    es_galletas = models.Text(id=6, title="Receta de galletas", course_level="1P", language="es", image_path="/img/galletas.png")
    es_clase = models.Text(id=7, title="En clase", course_level="1P", language="es", image_path="/img/clase.png")

    es_texts = [es_abejas, es_renato, es_perrito, es_bigotes, es_barco, es_galletas, es_clase]

    # Valencian texts
    val_abelles = models.Text(id=101, title="Les abelles", course_level="1P", language="val")
    assert find_matching_spanish_text(val_abelles, es_texts) == es_abejas

    val_renat = models.Text(id=102, title="El gat Renat", course_level="1P", language="val")
    assert find_matching_spanish_text(val_renat, es_texts) == es_renato

    val_gosset = models.Text(id=103, title="Gosset perdut!", course_level="1P", language="val")
    assert find_matching_spanish_text(val_gosset, es_texts) == es_perrito

    val_bigots = models.Text(id=104, title="Els bigots de renat", course_level="1P", language="val")
    assert find_matching_spanish_text(val_bigots, es_texts) == es_bigotes

    val_vaixell = models.Text(id=105, title="El vaixell de paper", course_level="1P", language="val")
    assert find_matching_spanish_text(val_vaixell, es_texts) == es_barco

    val_recepta = models.Text(id=106, title="Recepta de galletes", course_level="1P", language="val")
    assert find_matching_spanish_text(val_recepta, es_texts) == es_galletas

    val_classe = models.Text(id=107, title="En classe", course_level="1P", language="val")
    assert find_matching_spanish_text(val_classe, es_texts) == es_clase
