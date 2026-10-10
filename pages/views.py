import unicodedata

from django.core.files.storage import default_storage
from django.db.models.functions import Lower
from django.shortcuts import render
from django.utils.translation import get_language

from .content import load_home_content
from .models import Project


def _normalize_search_text(value):
    return "".join(
        character for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


def homepage(request):
    content = load_home_content()
    headshot_url = (
        default_storage.url(content["headshot_path"]) if content["headshot_path"] else ""
    )
    return render(
        request,
        "pages/home.html",
        {"home_content": content, "headshot_url": headshot_url},
    )


def projects(request):
    language = (get_language() or "en").split("-")[0]
    records = Project.objects.filter(is_published=True).prefetch_related("translations")
    cards = []
    for project in records.order_by(Lower("title"), "pk"):
        translations = {text.language: text for text in project.translations.all()}
        english = translations.get("en")
        if english is None:
            continue
        text = translations.get(language, english)
        cards.append({
            "title": project.title,
            "repository_url": project.repository_url,
            "technologies": project.technologies,
            "category": text.category,
            "description": text.description,
            "language": text.language,
        })
    total = len(cards)
    query = request.GET.get("q", "").strip()
    if query:
        term = _normalize_search_text(query)
        cards = [
            project
            for project in cards
            if any(
                term in _normalize_search_text(value)
                for value in (
                    project["title"],
                    project["description"],
                    project["category"],
                    *project["technologies"],
                )
            )
        ]
    return render(
        request,
        "pages/projects.html",
        {
            "projects": cards,
            "project_query": query,
            "project_total": total,
            "project_count": len(cards),
        },
    )
