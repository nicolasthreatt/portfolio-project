"""Load homepage content independently of the reusable page templates."""

import json
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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

    text_fields = ("heading", "location", "description", "headshot_path")
    if not isinstance(content, dict) or any(
        not isinstance(content.get(field), str) for field in text_fields
    ):
        raise ImproperlyConfigured(
            "Homepage heading, location, description, and headshot_path must be strings."
        )
    paragraphs = content.get("paragraphs")
    if not isinstance(paragraphs, list) or any(
        not isinstance(paragraph, str) for paragraph in paragraphs
    ):
        raise ImproperlyConfigured("Homepage paragraphs must be a list of strings.")

    image_path = PurePosixPath(content["headshot_path"])
    if image_path.is_absolute() or ".." in image_path.parts or "\\" in str(image_path):
        raise ImproperlyConfigured("Homepage headshot_path must be relative to MEDIA_ROOT.")
    return content
