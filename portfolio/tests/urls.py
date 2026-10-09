"""Isolated routes for tests of the shared site layout."""

from django.shortcuts import render
from django.urls import include, path


def page(request):
    return render(request, "base.html")


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", page, name="home"),
    path("blogs/", page, name="blog-list"),
    path("experience/", page, name="experience-list"),
    path("projects/", page, name="project-list"),
    path("resume/", page, name="resume"),
]
