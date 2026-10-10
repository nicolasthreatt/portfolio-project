from urllib.parse import urlsplit

from django.core.exceptions import ValidationError


def validate_repository_url(value):
    try:
        url = urlsplit(value)
        parts = url.path.strip("/").split("/")
        valid = (
            url.scheme == "https"
            and url.hostname == "github.com"
            and url.username is None
            and url.password is None
            and url.port in (None, 443)
            and len(parts) == 2
            and all(parts)
            and not url.query
            and not url.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValidationError("Enter an HTTPS GitHub repository URL.")


def validate_technologies(value):
    if (
        not isinstance(value, list) or
        any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValidationError("Technologies must be a list of nonempty strings.")
