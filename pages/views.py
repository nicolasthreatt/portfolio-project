from django.core.files.storage import default_storage
from django.shortcuts import render

from .content import load_home_content


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
