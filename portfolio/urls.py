"""URL routes for the portfolio site."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
import blogs.views
import pages.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", pages.views.homepage, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
