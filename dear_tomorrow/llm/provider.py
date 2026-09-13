"""get_model() -- returns a Strands model instance based on the MODEL_PROVIDER env var.

Every agent should call get_model() instead of constructing a provider directly, so
switching providers (e.g. if the Groq/LiteLLM path turns out to be unreliable) is a
one-line env var change instead of an edit to every agent file.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_GROQ_MODEL_ID = "groq/openai/gpt-oss-120b"


def get_model():
    provider = os.environ.get("MODEL_PROVIDER", "").lower()

    if provider == "groq":
        from strands.models.litellm import LiteLLMModel

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("MODEL_PROVIDER=groq but GROQ_API_KEY is not set in the environment.")
        model_id = os.environ.get("GROQ_MODEL_ID", DEFAULT_GROQ_MODEL_ID)
        return LiteLLMModel(model_id=model_id, client_args={"api_key": api_key})

    if provider == "gemini":
        raise NotImplementedError("Gemini provider not wired up yet -- set MODEL_PROVIDER=groq for now.")

    if provider == "anthropic":
        raise NotImplementedError("Anthropic provider not wired up yet -- set MODEL_PROVIDER=groq for now.")

    raise ValueError(
        f"Unknown or unset MODEL_PROVIDER: {provider!r}. Expected one of: groq, gemini, anthropic."
    )
