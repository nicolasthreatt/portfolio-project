"""Load homepage content independently of the reusable page templates."""

import json
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language


def _validate_text(content):
    if not isinstance(content, dict):
        raise ImproperlyConfigured("Homepage content must be a JSON object.")

    for field in ("heading", "location", "description"):
        if not isinstance(content.get(field), str):
            raise ImproperlyConfigured(f"Homepage {field} must be a string.")

    paragraphs = content.get("paragraphs")
    if not isinstance(paragraphs, list) or any(not isinstance(paragraph, str) for paragraph in paragraphs):
        raise ImproperlyConfigured("Homepage paragraphs must be a list of strings.")


def load_home_content():
    """Read plain-text homepage content from the configured local JSON file."""
    path = Path(settings.HOME_CONTENT_FILE)
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImproperlyConfigured(
            "Cannot read homepage content. Check PORTFOLIO_HOME_CONTENT_FILE "
            "and ensure it points to a valid UTF-8 JSON file."
        ) from exc

    _validate_text(content)
    if not isinstance(content.get("headshot_path"), str):
        raise ImproperlyConfigured("Homepage headshot_path must be a string.")

    image_path = PurePosixPath(content["headshot_path"])
    if image_path.is_absolute() or ".." in image_path.parts or "\\" in str(image_path):
        raise ImproperlyConfigured("Homepage headshot_path must be relative to MEDIA_ROOT.")
    translations = content.get("translations", {})
    if not isinstance(translations, dict):
        raise ImproperlyConfigured("Homepage translations must be an object keyed by language code.")
    supported_languages = dict(settings.LANGUAGES)
    for code, translated in translations.items():
        if code not in supported_languages:
            raise ImproperlyConfigured("Homepage translations must use supported language codes.")
        _validate_text(translated)

    default_language = settings.LANGUAGE_CODE
    language = (get_language() or default_language).split("-")[0]
    translated = translations.get(language)
    result = {**content, "language": default_language}
    if translated is not None:
        for field in ("heading", "location", "description", "paragraphs"):
            result[field] = translated[field]
        result["language"] = language
    return result
