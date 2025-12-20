
import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

content = """Once upon a time, there was a Hare who was very boastful that he was the fastest animal in the forest.
He was always showing off how fast he was to the other animals.
...and every morning, when he passed by the Tortoise, he would laugh at her, saying:
—Not so fast, you'll wear yourself out! Ha, ha, ha.
One day, the Tortoise answered:
—What would you wager that I could beat you in a race?
—Me? —said the Hare, laughing all the while. —I'd wager a sack full of carrots.
—I accept! —answered the Tortoise.
The following morning, all the animals were present, ready for the start of the race.
—Ready! Set!...
—Go! —said the Fox.
The Hare was off like a shot as soon as he heard the signal.
In no time at all, he was already halfway through the race... and he had an idea.
"If I stop here, I'll see the Tortoise come past and I can laugh at her".
And so just like that, the Hare stretched out under a tree to wait, and there he fell asleep.
After a while, slowly but surely, the Tortoise overtook the Hare, who was sleeping peacefully.
Shortly afterwards, the Hare woke up and...
Surprise! The Tortoise was already close to the finishing line.
The Hare ran as fast as he could but it was too late. The Tortoise finished first.
All the animals clapped.
She had won the race.
The Hare, humiliated, handed over the sack of carrots he had promised.
The Tortoise showed her appreciation for their support by sharing the carrots with all the other animals.
—Thank you, friends! Thank you!
And here our story ends."""

prompt = f"""
    Genera un examen de comprensión lectora basándote en el siguiente texto.
    
    REQUISITOS OBLIGATORIOS:
    1. Genera EXACTAMENTE 10 preguntas.
    2. Las primeras 5 deben ser de Selección Múltiple con 3 opciones (a, b, c).
    3. Las últimas 5 deben ser de Verdadero o Falso (2 opciones).
    4. Indica claramente la respuesta correcta (índice 0, 1, 2).
    5. Devuelve SOLO un JSON válido con esta estructura:
    
    [
      {{
        "question": "¿Pregunta?",
        "options": ["Opción A", "Opción B", "Opción C"],
        "correct_index": 0
      }},
      ...
    ]
    
    TEXTO:
    {content}
    """

try:
    print("Calling OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente educativo experto en crear evaluaciones de lectura."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    json_content = response.choices[0].message.content
    print("Raw Response:", json_content[:200] + "...")
    
    # Sanitize
    json_content = json_content.replace("```json", "").replace("```", "").strip()
    questions_data = json.loads(json_content)
    
    print(f"✅ Success! Generated {len(questions_data)} questions.")
    print("First Question:", questions_data[0])

except Exception as e:
    print(f"❌ Failed: {e}")
