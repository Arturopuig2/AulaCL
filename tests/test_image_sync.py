import pytest
from app.image_sync import normalize_text, find_matching_spanish_text, strip_articles
from app import models

def test_2p_all_user_reported_pairs():
    pairs = [
        ("El tambor de Pol", "El tambor de Pol"),
        ("El mono divertido", "El mico divertit"),
        ("Las hormigas trabajadoras", "Les formigues treballadores"),
        ("El vampiro Casimiro", "El vampir Casimir"),
        ("El otoño", "La tardor"),
        ("El oso goloso", "L'os llépol"),
        ("Brochetas de fruta con chocolate", "Broquetes de fruita amb xocolate"),
        ("El submarino de cartón", "El submarí de cartó"),
        ("El invierno", "L'Hivern"),
        ("Receta: Tarta de manzana", "Pastís de poma"),
        ("El ovillo de Mica", "El cabdell de Mica"),
        ("Jack, el pirata aventurero", "Jack, el pirata"),
        ("El tesoro del Pirata Jack", "El tresor del pirata Jack"),
        ("Poesía del pirata", "Poesia del pirata"),
        ("Viaje a la Luna", "Viatge a la Lluna"),
        ("Tito, ratoncito", "Tonet, ratolinet"),
        ("La primavera", "La Primavera"),
        ("Mi merienda", "El meu berenar"),
        ("La gata Mica", "La gata Mica"),
        ("El verano", "L'estiu"),
        ("El arcoíris", "L'arc de Sant Martí"),
    ]

    es_texts = [
        models.Text(id=i+1, title=es_title, course_level="2P", language="es", image_path=f"/img/{i+1}.png")
        for i, (es_title, _) in enumerate(pairs)
    ]

    for i, (es_title, val_title) in enumerate(pairs):
        val_text = models.Text(id=100+i, title=val_title, course_level="2P", language="val")
        matched_es = find_matching_spanish_text(val_text, es_texts)
        assert matched_es is not None, f"Failed to match Valencian text: {val_title}"
        assert matched_es.title == es_title, f"Expected {es_title}, got {matched_es.title} for {val_title}"
