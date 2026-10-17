import unicodedata

from django.utils.translation import get_language


def search(value):
    """Normalize text for case and accent-insensitive search comparisons."""
    return "".join(
        character for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


def get_experience_content(experience):
    """Prepare translated content, falling back to English when available."""
    language = (get_language() or "en").split("-")[0]
    translations = {text.language: text for text in experience.translations.all()}
    english = translations.get("en")
    if english is None:
        return None
    text = translations.get(language, english)
    return {
        "id": experience.pk,
        "slug": experience.slug,
        "company": experience.company,
        "company_url": experience.company_url,
        "start_date": experience.start_date,
        "end_date": experience.end_date,
        "logo": experience.logo,
        "technologies": experience.technologies,
        "role": text.role,
        "location": text.location,
        "overview": text.overview,
        "accomplishment_list": text.accomplishment_list,
        "language": text.language,
    }
