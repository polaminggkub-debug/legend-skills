"""Offline tests for provider/model selection."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from worker_provider import ProviderError, resolve_selection  # noqa: E402


class ProviderSelectionTests(unittest.TestCase):
    def test_go_default_is_fully_qualified_and_uses_native_credential(self):
        settings = {
            "default_provider": "opencode-go",
            "default_model": "deepseek-v4.1-flash",
            "allowed_providers": ["opencode-go"],
        }

        selection = resolve_selection(settings)

        self.assertEqual(
            selection,
            {
                "provider_id": "opencode-go",
                "provider_label": "OpenCode Go",
                "model": "opencode-go/deepseek-v4.1-flash",
                "credential_env": "OPENCODE_API_KEY",
                "cost_basis": "OpenCode-reported estimate; OpenCode Go Use balance may charge Zen after Go limits; not a Zen/OpenRouter billing receipt",
            },
        )

    def test_go_model_override_keeps_selected_provider(self):
        settings = {
            "default_provider": "opencode-go",
            "default_model": "deepseek-v4.1-flash",
            "allowed_providers": ["opencode-go"],
        }

        selection = resolve_selection(settings, "mimo-v2.5-pro")

        self.assertEqual(selection["provider_id"], "opencode-go")
        self.assertEqual(selection["model"], "opencode-go/mimo-v2.5-pro")
        self.assertEqual(selection["credential_env"], "OPENCODE_API_KEY")

    def test_legacy_settings_without_provider_remain_openrouter(self):
        selection = resolve_selection({"default_model": "deepseek/deepseek-v4.1-flash"})

        self.assertEqual(selection["provider_id"], "openrouter")
        self.assertEqual(selection["provider_label"], "OpenRouter")
        self.assertEqual(selection["model"], "openrouter/deepseek/deepseek-v4.1-flash")
        self.assertEqual(selection["credential_env"], "OPENROUTER_API_KEY")

    def test_model_provider_mismatch_is_rejected_before_selection(self):
        settings = {
            "default_provider": "opencode-go",
            "default_model": "deepseek-v4.1-flash",
            "allowed_providers": ["opencode-go"],
        }

        with self.assertRaisesRegex(ProviderError, "does not match selected provider"):
            resolve_selection(settings, "openrouter/deepseek/deepseek-v4.1-flash")

    def test_disallowed_provider_is_rejected_without_secret_in_error(self):
        settings = {
            "default_provider": "openrouter",
            "default_model": "deepseek/deepseek-v4.1-flash",
            "allowed_providers": ["opencode-go"],
            "credential": "fixture-secret-must-not-appear",
        }

        with self.assertRaises(ProviderError) as raised:
            resolve_selection(settings)

        self.assertNotIn("fixture-secret", str(raised.exception))
        self.assertIn("not allowed", str(raised.exception))

    def test_unknown_provider_is_not_silently_fallback_to_default(self):
        with self.assertRaisesRegex(ProviderError, "Unsupported provider"):
            resolve_selection({"default_provider": "unknown-provider", "default_model": "model"})

    def test_conflicting_provider_aliases_are_rejected(self):
        with self.assertRaisesRegex(ProviderError, "Provider settings disagree"):
            resolve_selection(
                {
                    "default_provider": "opencode-go",
                    "provider": "openrouter",
                    "default_model": "deepseek-v4.1-flash",
                }
            )


if __name__ == "__main__":
    unittest.main()
