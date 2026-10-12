import re

from django import template
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.html import format_html, format_html_join


register = template.Library()
LINK_PATTERN = re.compile(r"\[([^\]\n]+)\]\(([^\s)]+)\)")
validate_url = URLValidator(schemes=["http", "https"])


@register.filter
def highlight_links(value):
    """Render [label](URL) links while escaping all other highlight text."""
    parts = []
    position = 0
    for match in LINK_PATTERN.finditer(value):
        parts.append(value[position:match.start()])
        label, url = match.groups()
        try:
            validate_url(url)
        except ValidationError:
            parts.append(match.group())
        else:
            parts.append(format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                url, label,
            ))
        position = match.end()
    parts.append(value[position:])
    return format_html_join("", "{}", ((part,) for part in parts))
