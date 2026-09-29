import pytest
from app.image_sync import normalize_text, find_matching_spanish_text, TITLE_MAPPINGS
from app import models

def test_normalize_text():
    assert normalize_text("El globus de Lúa!") == "el globus de lua"
    assert normalize_text("L'ós Pol") == "l os pol"
    assert normalize_text("La bicicleta d'Eli") == "la bicicleta d eli"
    assert normalize_text("¿El muñeco de nieve?") == "el muneco de nieve"

def test_find_matching_spanish_text_exact_and_mapping():
    es_pol = models.Text(id=1, title="El oso Pol", course_level="1P", language="es", image_path="/static/images/uploads/pol.png", order=0)
    es_lua = models.Text(id=2, title="El globo de Lúa", course_level="1P", language="es", image_path="/static/images/uploads/lua.png", order=0)
    es_galletas = models.Text(id=3, title="La receta de las galletas", course_level="1P", language="es", image_path="/static/images/uploads/galletas.png", order=0)
    es_bici = models.Text(id=4, title="La bicicleta de Eli", course_level="1P", language="es", image_path="/static/images/uploads/bici.png", order=0)
    es_neu = models.Text(id=5, title="El muñeco de nieve", course_level="1P", language="es", image_path="/static/images/uploads/nieve.png", order=0)
    es_rana = models.Text(id=6, title="La rana Juana", course_level="1P", language="es", image_path="/static/images/uploads/rana.png", order=0)
    
    es_texts = [es_pol, es_lua, es_galletas, es_bici, es_neu, es_rana]

    # Test Valencian counterparts
    val_lua = models.Text(id=10, title="El globus de Lúa", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_lua, es_texts) == es_lua

    val_pol = models.Text(id=11, title="L'ós Pol", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_pol, es_texts) == es_pol

    val_galletes = models.Text(id=12, title="La recepta de les galetes", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_galletes, es_texts) == es_galletas

    val_bici = models.Text(id=13, title="La bicicleta d'Eli", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_bici, es_texts) == es_bici

    val_ninot = models.Text(id=14, title="El ninot de neu", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_ninot, es_texts) == es_neu

    val_granota = models.Text(id=15, title="La granota Joana", course_level="1P", language="val", order=0)
    assert find_matching_spanish_text(val_granota, es_texts) == es_rana
