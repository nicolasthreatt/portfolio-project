from django.core.files.storage import default_storage
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language

from .content import load_home_content
from .models import Experience, Project
from .utils import get_experience_content, search


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
        term = search(query)
        cards = [
            project
            for project in cards
            if any(
                term in search(value)
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


def experience_list(request):
    records = Experience.objects.filter(is_published=True).prefetch_related("translations")
    experiences = [
        content for experience in records
        if (content := get_experience_content(experience)) is not None
    ]
    return render(
        request, "pages/experience_list.html",
        {"experiences": experiences},
    )


def experience_detail(request, experience_id):
    record = get_object_or_404(
        Experience.objects.filter(is_published=True).prefetch_related("translations"),
        pk=experience_id,
    )
    experience = get_experience_content(record)
    if experience is None:
        raise Http404
    return render(request, "pages/experience_detail.html", {"experience": experience})
