"""Shared template context for the portfolio."""

from django.conf import settings


def site_profile(request):
    """Expose only the public profile fields, not the environment or secrets."""
    return {"site_profile": settings.SITE_PROFILE}
