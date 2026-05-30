from __future__ import annotations

import os
from typing import Any, Dict

import config

PROVIDERS = {
    "openai": {
        "label": "OpenAI (GPT)",
        "needs_key": True,
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "needs_key": True,
        "models": [
            "claude-3-5-haiku-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-7-sonnet-latest",
        ],
    },
    "google": {
        "label": "Google (Gemini)",
        "needs_key": True,
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
    },
    "ollama": {
        "label": "Ollama (로컬·무료)",
        "needs_key": False,
        "models": [config.LLM_MODEL],
    },
}

def default_model(kind: str) -> str:
    models = PROVIDERS.get(kind, {}).get("models") or [""]
    return models[0]

def build_llm(provider: Dict[str, Any]):
    kind = (provider or {}).get("provider", "ollama")
    model = (provider or {}).get("model") or default_model(kind)
    key = (provider or {}).get("api_key", "")
    temp = config.DEFAULT_TEMPERATURE

    if kind == "openai":
        from langchain_openai import ChatOpenAI

        key = key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OpenAI API 키가 없습니다.")
        return ChatOpenAI(model=model or "gpt-4o-mini", temperature=temp, api_key=key)

    if kind == "anthropic":
        from langchain_anthropic import ChatAnthropic

        key = key or os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("Anthropic API 키가 없습니다.")
        return ChatAnthropic(
            model=model or "claude-3-5-haiku-latest", temperature=temp, api_key=key
        )

    if kind == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        key = key or os.getenv("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError("Google(Gemini) API 키가 없습니다.")
        return ChatGoogleGenerativeAI(
            model=model or "gemini-1.5-flash", temperature=temp, google_api_key=key
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model or config.LLM_MODEL,
        temperature=temp,
        num_ctx=config.DEFAULT_NUM_CTX,
    )

def build_ollama_fallback():
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=config.LLM_MODEL,
        temperature=config.DEFAULT_TEMPERATURE,
        num_ctx=config.DEFAULT_NUM_CTX,
    )

def default_provider() -> Dict[str, Any]:
    return {"provider": "ollama", "model": config.LLM_MODEL, "api_key": ""}
