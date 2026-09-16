"""Pure provider and model selection for the OpenCode worker.

Provider selection is deliberately separate from credential I/O and process
launch.  A caller can validate a settings object and a per-run model override
before it reads a credential or starts OpenCode.  The returned model is always
fully qualified as ``provider/model``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, Optional


class ProviderError(ValueError):
    """Raised when provider settings or a model selection is unsafe."""


_OPENROUTER = "openrouter"
_OPENCODE_GO = "opencode-go"

# These values are metadata, not credentials.  Keep the identifiers stable so
# reports and future settings migrations can distinguish provider accounting.
_PROVIDERS = {
    _OPENCODE_GO: {
        "provider_id": _OPENCODE_GO,
        "provider_label": "OpenCode Go",
        "credential_env": "OPENCODE_API_KEY",
        "cost_basis": "OpenCode-reported estimate; OpenCode Go Use balance may charge Zen after Go limits; not a Zen billing receipt",
        "default_model": "opencode-go/deepseek-v4.1-flash",
    },
    _OPENROUTER: {
        "provider_id": _OPENROUTER,
        "provider_label": "OpenRouter",
        "credential_env": "OPENROUTER_API_KEY",
        "cost_basis": "OpenCode-reported estimate; not an OpenRouter billing receipt",
        "default_model": "openrouter/deepseek/deepseek-v4.1-flash",
    },
}

SUPPORTED_PROVIDERS = tuple(_PROVIDERS)
DEFAULT_PROVIDER = _OPENCODE_GO
DEFAULT_MODEL = _PROVIDERS[_OPENCODE_GO]["default_model"]


def _unsupported_provider(provider: Any) -> ProviderError:
    value = repr(provider) if isinstance(provider, str) else type(provider).__name__
    return ProviderError(
        "Unsupported provider " + value + "; supported providers: " + ", ".join(SUPPORTED_PROVIDERS)
    )


def _provider_setting(settings: Mapping[str, Any]) -> Optional[str]:
    """Read the provider setting, rejecting conflicting aliases."""

    values = []
    for key in ("default_provider", "provider_id", "provider"):
        if key not in settings or settings[key] is None:
            continue
        value = settings[key]
        if not isinstance(value, str) or not value.strip():
            raise ProviderError(key + " must be a non-empty provider ID")
        values.append((key, value.strip()))
    if not values:
        return None
    selected = values[0][1]
    if any(value != selected for _, value in values[1:]):
        raise ProviderError("Provider settings disagree")
    return selected


def _allowed_providers(settings: Mapping[str, Any]) -> Optional[tuple[str, ...]]:
    raw = settings.get("allowed_providers")
    if raw is None:
        return None
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise ProviderError("allowed_providers must be a list of provider IDs")
    result = []
    for value in raw:
        if not isinstance(value, str) or not value.strip():
            raise ProviderError("allowed_providers must contain non-empty provider IDs")
        provider = value.strip()
        if provider not in _PROVIDERS:
            raise _unsupported_provider(provider)
        if provider not in result:
            result.append(provider)
    return tuple(result)


def _model_for(provider: str, value: Any, *, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderError(source + " must be a non-empty model ID")
    model = value.strip()
    if model.startswith("/") or model.endswith("/"):
        raise ProviderError(source + " must be a valid model ID")
    if "/" in model:
        model_provider, model_id = model.split("/", 1)
        # OpenRouter's model IDs commonly contain a vendor/model path (for
        # example ``deepseek/deepseek-v4.1-flash``) without the worker's
        # provider prefix.  Only a known worker provider prefix is treated as
        # an explicit provider and therefore checked for a mismatch.
        if model_provider in _PROVIDERS and model_provider != provider:
            raise ProviderError(
                "Model provider " + repr(model_provider) + " does not match selected provider " + repr(provider)
            )
        if model_provider in _PROVIDERS and not model_id:
            raise ProviderError(source + " must include a model ID after the provider prefix")
        if model_provider in _PROVIDERS:
            return model
    return provider + "/" + model


def resolve_selection(settings: Mapping[str, Any], model_override: Optional[str] = None) -> Dict[str, str]:
    """Resolve one provider/model selection without touching credentials.

    ``default_provider`` is the current settings key.  ``provider`` and
    ``provider_id`` are accepted aliases so a future settings schema can move
    the field without changing the selection boundary.  If no provider is
    supplied, an existing settings object is treated as legacy OpenRouter
    configuration; this preserves old installations until they are migrated.
    """

    if not isinstance(settings, Mapping):
        raise ProviderError("Provider settings must be a JSON object")

    provider = _provider_setting(settings) or _OPENROUTER
    if provider not in _PROVIDERS:
        raise _unsupported_provider(provider)

    allowed = _allowed_providers(settings)
    if allowed is not None and provider not in allowed:
        raise ProviderError(
            "Provider " + repr(provider) + " is not allowed; allowed providers: " + ", ".join(allowed)
        )

    if model_override is not None:
        model = _model_for(provider, model_override, source="model override")
    elif "default_model" in settings:
        model = _model_for(provider, settings["default_model"], source="default_model")
    else:
        model = _PROVIDERS[provider]["default_model"]

    metadata = _PROVIDERS[provider]
    return {
        "provider_id": metadata["provider_id"],
        "provider_label": metadata["provider_label"],
        "model": model,
        "credential_env": metadata["credential_env"],
        "cost_basis": metadata["cost_basis"],
    }


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "ProviderError",
    "SUPPORTED_PROVIDERS",
    "resolve_selection",
]
