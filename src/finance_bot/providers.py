"""Proveedores de IA intercambiables. Cada uno recibe un prompt y devuelve texto."""

from typing import Protocol

from google import genai
from google.genai import types

from finance_bot.config import Settings


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        # response_mime_type pide JSON directamente; el parseo y la validación están en interpreter.py.
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return response.text


def make_provider(settings: Settings) -> LLMProvider:
    if settings.ai_provider == "gemini":
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    raise ValueError(f"Proveedor de IA no soportado todavía: {settings.ai_provider}")
