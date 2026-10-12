"""URL routes for the portfolio site."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
import pages.views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("", pages.views.homepage, name="home"),
    path("projects/", pages.views.projects, name="project-list"),
    path("experience/", pages.views.experience_list, name="experience-list"),
    path(
        "experience/<int:experience_id>/",
        pages.views.experience_detail,
        name="experience-detail",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
