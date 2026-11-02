import os
import json
import traceback
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
load_dotenv(override=True)

def get_ai_provider():
    """
    Returns ('gemini' | 'openai' | None, client, model_name).
    Prefers Gemini if GEMINI_API_KEY is defined, falls back to OpenAI.
    """
    load_dotenv(override=True)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            client = genai.Client(api_key=gemini_key)
            return "gemini", client, model_name
        except Exception as e:
            print(f"Warning: Failed to initialize Google GenAI client: {e}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            client = openai.OpenAI(api_key=openai_key)
            return "openai", client, model_name
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")

    return None, None, None


def call_ai_json(prompt: str, system_instruction: str = "", temperature: float = 0.7) -> Dict[str, Any]:
    """
    Executes an AI call requesting a valid JSON response.
    Supports both Google Gemini and OpenAI.
    """
    provider, client, model_name = get_ai_provider()

    if not provider or not client:
        raise HTTPException(
            status_code=500,
            detail="No hay ningún proveedor de IA configurado. Por favor, añade GEMINI_API_KEY en las variables de entorno de Render."
        )

    if provider == "gemini":
        from google.genai import types
        try:
            config_kwargs = {
                "response_mime_type": "application/json",
                "temperature": temperature
            }
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )

            raw_text = response.text or ""
            # Strip any markdown fences if present
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)

        except Exception as e:
            err_str = str(e)
            print(f"❌ Error en Gemini AI ({model_name}): {err_str}")
            traceback.print_exc()

            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                raise HTTPException(
                    status_code=429,
                    detail="Límite de solicitudes de Gemini alcanzado. Espera unos segundos e inténtalo de nuevo."
                )
            if "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str:
                raise HTTPException(
                    status_code=401,
                    detail="La clave GEMINI_API_KEY no es válida o no tiene permisos suficientes."
                )

            raise HTTPException(
                status_code=500,
                detail=f"Error en el servicio Gemini ({model_name}): {err_str}"
            )

    elif provider == "openai":
        try:
            messages = []
            sys_msg = system_instruction or "Eres un asistente experto que SOLO responde en JSON válido."
            messages.append({"role": "system", "content": sys_msg})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content or ""
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)

        except Exception as e:
            err_str = str(e)
            print(f"❌ Error en OpenAI ({model_name}): {err_str}")
            traceback.print_exc()

            if "RateLimitError" in type(e).__name__ or "insufficient_quota" in err_str or "credit_balance_exhausted" in err_str:
                raise HTTPException(
                    status_code=429,
                    detail="Se ha agotado el saldo en OpenAI. Por favor, recarga saldo en platform.openai.com o configura GEMINI_API_KEY."
                )
            if "AuthenticationError" in type(e).__name__:
                raise HTTPException(
                    status_code=401,
                    detail="La clave de API de OpenAI no es válida o ha caducado."
                )

            raise HTTPException(
                status_code=500,
                detail=f"Error en el servicio OpenAI ({model_name}): {err_str}"
            )
