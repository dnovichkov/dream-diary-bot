"""Localization module for the bot."""

import json
from pathlib import Path
from typing import Any


class LocaleManager:
    """Manages translations for multiple languages."""

    def __init__(self) -> None:
        self.translations: dict[str, dict[str, Any]] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all translation files from the locales directory."""
        locales_dir = Path(__file__).parent
        for file_path in locales_dir.glob("*.json"):
            lang_code = file_path.stem
            with open(file_path, encoding="utf-8") as f:
                self.translations[lang_code] = json.load(f)

    def get(self, lang: str, key: str, **kwargs: Any) -> str:
        """
        Get translated text by key with optional formatting.

        Args:
            lang: Language code (e.g., "en", "ru")
            key: Dot-separated key path (e.g., "buttons.new_dream")
            **kwargs: Format arguments for the string

        Returns:
            Translated string, or key if not found
        """
        # Fallback to English if language not found
        translations = self.translations.get(lang, self.translations.get("en", {}))

        # Navigate through nested keys
        value: Any = translations
        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        if value is None:
            return key

        if not isinstance(value, str):
            return key

        # Apply format arguments if provided
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return value


# Global instance
locale = LocaleManager()
